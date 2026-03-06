# Troubleshooting (Reference)

Scope: quick lookup for monitoring, logs, and common issues.

## Monitoring and Logs

### MQTT Broker

```bash
# View MQTT broker statistics
kubectl exec -it -n azure-iot-operations pod/aio-broker-frontend-0 -- \
   mosquitto_sub -h localhost -t '$SYS/#'
```

### Data Flow

```bash
# Get data flow status
kubectl describe dataflow -n azure-iot-operations

# Check endpoint connection status
kubectl get dataendpoint -n azure-iot-operations

# List dataflow-related pods
kubectl get pods -n azure-iot-operations | grep dataflow

# Follow dataflow logs (most common)
kubectl logs -n azure-iot-operations aio-dataflow-default-0 -f

# Recent dataflow logs
kubectl logs -n azure-iot-operations aio-dataflow-default-0 --tail=100

# All dataflow pod logs
kubectl logs -n azure-iot-operations -l app.kubernetes.io/name=aio-dataflow --tail=50

# Dataflow Service Account (for auth checks)
kubectl get sa aio-dataflow -n azure-iot-operations -o yaml

# Dataflow full config
kubectl get dataflow -n azure-iot-operations -o yaml
```

**Log hints**:

- `Average msg/min: X/Y/Z` - message throughput
- `AADSTS70025` - federated identity credential misconfiguration
- `No matching federated identity record found` - Service Account subject mismatch
- `Connection refused` - target endpoint unreachable

### HTTP Connector and MQTT

```bash
# HTTP Connector logs (MQTT connection diagnosis)
kubectl logs -n azure-iot-operations $(kubectl get pods -n azure-iot-operations -o name | grep httpconnector) --tail=200 | grep -i mqtt

# Check MQTT Broker default endpoint service
kubectl get svc -n azure-iot-operations | grep aio-broker

# Inspect MQTT Broker service details
kubectl get svc -n azure-iot-operations aio-broker -o yaml

# Test MQTT Broker port from inside the cluster
kubectl run -it --rm debug --image=busybox --restart=Never -n azure-iot-operations -- \
   nc -zv aio-broker 18883

# Verify HTTP Connector can reach the WMS API
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n azure-iot-operations -- \
  curl http://mock-wms-api.app.svc.cluster.local:8080/api/inventory
```

**Quick checks**:

If you see `Failed to connect MQTT session`, diagnose in this order:

1. **MQTT Broker status**

   ```bash
   kubectl get pods -n azure-iot-operations | grep aio-broker
   kubectl get svc -n azure-iot-operations | grep mqtt
   ```
2. **DNS resolution**

   ```bash
   kubectl run -it --rm debug --image=busybox --restart=Never -n azure-iot-operations -- \
     nslookup aio-broker
   ```
3. **Network policies**

   ```bash
   kubectl get networkpolicies -n azure-iot-operations
   ```
4. **MQTT Broker logs**

   ```bash
   kubectl logs -n azure-iot-operations -l app.kubernetes.io/name=aio-broker --tail=100
   ```

## Common Issues

| Issue | Symptom | Fix |
| --- | --- | --- |
| Fabric shows `{}` | Data preview shows `{}` instead of JSON | Add a Message Schema in the Data Flow source (see Step 3.3); use Schema Generator Helper to build the schema |
| Federated identity auth fails | Logs show `AADSTS70025` or `AADSTS70021` | Create the federated credential; ensure the subject is `system:serviceaccount:azure-iot-operations:aio-dataflow`; verify the OIDC issuer |
| Data Flow cannot connect to Fabric | Logs show connection/auth errors | Check Managed Identity client ID and tenant ID; verify the Fabric endpoint bootstrap server |
| HTTP Connector cannot connect to MQTT | Logs show `Failed to connect MQTT session` | Check MQTT Broker service: `kubectl get pods -l app.kubernetes.io/name=aio-broker`; verify DNS: `nslookup aio-broker`; check network policies; restart `aio-broker-frontend-0` if needed |
| HTTP Connector cannot pull data | Connector logs show connection errors | Check WMS API URL and reachability; verify the mock API is running; avoid localhost (see Step 5.4) |
| Dataset config parse failure | Logs show `Failed to parse dataset configuration` | The dataset must set **Sampling interval** so `samplingIntervalInMilliseconds` is written; otherwise parsing fails (recreate the dataset) |
| HTTP endpoint uses localhost | Connector cannot reach host API | Replace localhost with host IP; use `ip addr show eth0` to get the IP; localhost inside a pod points to itself |
| No MQTT data | MQTTX subscription shows no messages | Check Connector logs and HTTP endpoint config; confirm the HTTP Connector pod is running |
| Fabric receives no data | Eventstream has no new messages | Check Data Flow config and MQTT source topic; review dataflow logs |
| Fabric Event Hub connection fails | Connector logs show Event Hub errors | Verify the Event Hub connection string copied from Fabric; check Event Hub namespace permissions |
| Data Flow throughput is 0 | Logs show `Average msg/min: 0/0/0` | Check source topic; verify MQTT Broker receives messages; confirm the dataflow is enabled |
| Transform failure | WASM module error | Check WASM module URL; verify container registry credentials; review transform logs |
| Auth failure | Connector logs show 401/403 | Verify HTTP endpoint credentials (username/password or certificate) |
