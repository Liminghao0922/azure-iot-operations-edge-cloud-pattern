# MQTT Broker Setup Guide for Azure IoT Operations

Based on **Step 8: MQTT Broker Configuration** from the hands-on guide.

---

## Overview

The MQTT Broker is the central message hub for Azure IoT Operations. It handles all internal and external communication between edge components and cloud services.

## Architecture

```
┌─────────────────────────────────────────────┐
│        MQTT Broker (aio-mq-broker)         │
│                                             │
│  Internal Endpoint (ClusterIP)             │
│  ├─ Port: 1883                            │
│  ├─ Address: aio-mq-dmqtt-frontend:1883  │
│  ├─ Protocol: MQTT 3.1.1 / 5.0            │
│  ├─ Auth: None (internal only)            │
│  └─ Usage: Connectors, Data Flows, Pods   │
│                                             │
│  External Endpoint (LoadBalancer)         │
│  ├─ Listener Ports:                       │
│  │  ├─ 1883: Test (No Auth, No TLS)      │
│  │  └─ 8883: Prod (Auth + mTLS)          │
│  ├─ Address: <EXTERNAL-IP>               │
│  └─ Usage: MQTT clients, MQTTX tool      │
└─────────────────────────────────────────────┘
```

---

## Prerequisites

- ✅ Kubernetes cluster deployed (K3s)
- ✅ Azure Arc enabled
- ✅ Azure IoT Operations deployed
- ✅ kubectl configured and accessible
- ✅ Azure Portal access

---

## Step-by-Step Setup

### Step 1: Verify Broker Installation

```bash
# Check if MQTT broker pod is running
kubectl get pods -n azure-iot-operations -l app=mq-broker

# Expected output:
# NAME                    READY   STATUS    RESTARTS   AGE
# aio-mq-broker-xxx       1/1     Running   0          10m
```

### Step 2: Create LoadBalancer Listener

**Via Azure Portal:**

1. Navigate to your **Azure IoT Operations** instance
2. Under **Components**, select **MQTT Broker**
3. Click **Create** → **MQTT broker listener for LoadBalancer**

**Configuration:**

| Field | Value |
|-------|-------|
| Name | loadbalancer-listener |
| Service Type | LoadBalancer |

### Step 3: Configure Ports

#### Port 1883 - Test/Development

```
Service Type: TCP/MQTT
Port: 1883
Protocol: MQTT
Authentication: None
Authorization: None
TLS: Not configured
```

**Use Case:**
- Development and testing
- MQTTX client connections
- Internal POC (Proof of Concept)

⚠️ **Warning**: Do NOT use port 1883 in production!

#### Port 8883 - Production

```
Service Type: TCP/MQTT
Port: 8883
Protocol: MQTT
Authentication: default
Authorization: None
TLS: Automatic (cert-manager)
```

**TLS Configuration:**

| Parameter | Value |
|-----------|-------|
| TLS Mode | Automatic |
| Issuer Name | azure-iot-operations-aio-certificate-issuer |
| Issuer Kind | ClusterIssuer |
| Private Key Algorithm | Ec256 |
| Duration | 2160h (90 days) |
| Renew Before | 720h (30 days) |

**Use Case:**
- Production deployments
- Real device connections
- TLS-encrypted communication

### Step 4: Get External Endpoint

**Method 1: Azure Portal**
- Go to MQTT Broker → Listener details
- Copy the external endpoint IP/hostname

**Method 2: kubectl**
```bash
# Get LoadBalancer service
kubectl get svc -n azure-iot-operations loadbalancer-listener

# Expected output:
# NAME                     TYPE           CLUSTER-IP     EXTERNAL-IP      PORT(S)
# loadbalancer-listener    LoadBalancer   10.43.x.x      <external-ip>    1883:xxxxx/TCP,8883:xxxxx/TCP

# Save the EXTERNAL-IP for client connections
export MQTT_BROKER_IP=<external-ip>
```

**Method 3: DNS Name**
```bash
# If using DNS:
kubectl get svc loadbalancer-listener -n azure-iot-operations -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

---

## Connection Testing

### Test 1: TCP Connectivity

```bash
# Basic TCP check (port 1883 - test)
nc -zv <broker-ip> 1883

# Expected: Connection successful

# TLS port (8883 - production)
nc -zv <broker-ip> 8883
```

### Test 2: Using MQTTX

**Installation:**
1. Download from https://mqttx.app/
2. Install application

**Configuration:**

1. **Create New Connection**
   - Name: `AIO-Test`
   - Host: `<broker-ip>`
   - Port: `1883`
   - Protocol: `mqtt://`
   - Client ID: `test-client-001`
   - Auto Connect: Enabled

2. **Publish Message**
   ```
   Topic: sensors/temperature
   Message: {"temp": 22.5, "unit": "C"}
   QoS: 1
   ```

3. **Subscribe**
   ```
   Topic: sensors/#
   QoS: 1
   ```

### Test 3: Using Python MQTT Client

```python
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("sensors/#")

def on_message(client, userdata, msg):
    print(f"{msg.topic}: {msg.payload.decode()}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Connect to broker
client.connect("<broker-ip>", 1883, 60)
client.loop_forever()
```

Run:
```bash
python test_mqtt.py
```

---

## Topic Design

### Recommended Topic Structure

```
devices/                      # Device-related topics
├── <device-id>/status       Device status/health
├── <device-id>/telemetry    Sensor data
└── <device-id>/config       Configuration updates

sensors/                      # Sensor data grouped by type
├── temperature/             Temperature readings
├── humidity/                Humidity readings
├── pressure/                Pressure readings
└── motion/                  Motion detection

system/                      # System management
├── commands                 Control commands
├── alerts                   System alerts
└── metrics                  Performance metrics

wms/                         # WMS/API-sourced data
├── inventory/data          Inventory from API
├── inventory/low-stock     Low stock alerts
└── orders/                 Order information

api/external/               # External system data
├── erp/                    ERP system data
├── mes/                    Manufacturing execution
└── crm/                    CRM data
```

### QoS Levels

| Level | Guarantee | Use Case |
|-------|-----------|----------|
| 0 | Fire and forget | Non-critical telemetry |
| 1 | At least once | Important messages (recommended) |
| 2 | Exactly once | Financial/critical data |

**Recommendation**: Use QoS 1 for production data flows

---

## Authentication & Authorization

### Enable Authentication (Optional but Recommended)

**Via Azure Portal:**
1. Edit the Broker configuration
2. Set **Authentication**: `default`
3. Configure credentials (JWT, basic auth, certificate)

**Key Vault Storage:**
```bash
# Store credentials securely
az keyvault secret set --vault-name <kv-name> \
  --name mqtt-user-credentials \
  --value '{"username":"iot_user","password":"SecurePassword123!"}'
```

### Topic-Level Authorization

Configure authorization policies:
```yaml
# Example: Allow sensors/* to any client
# Restrict api/external/* to authenticated clients only
```

---

## Monitoring

### Broker Health

```bash
# Check broker status
kubectl get broker -n azure-iot-operations

# Get detailed info
kubectl describe broker default -n azure-iot-operations

# View broker logs
kubectl logs -n azure-iot-operations -l app=mq-broker -f

# Monitor resource usage
kubectl top pod -n azure-iot-operations -l app=mq-broker
```

### Connection Metrics

```bash
# Connect to broker and check system topics
mosquitto_sub -h <broker-ip> -t '$SYS/broker/clients/#'

# Monitor message throughput
mosquitto_sub -h <broker-ip> -t '$SYS/broker/messages/#'

# Check subscription count
mosquitto_sub -h <broker-ip> -t '$SYS/broker/subscriptions/#'
```

### Active Topics

```bash
# View all active topics (requires admin subscription)
mosquitto_sub -h <broker-ip> -t '#' -v

# Count messages per topic
mosquitto_sub -h <broker-ip> -t '#' | awk -F' ' '{print $1}' | sort | uniq -c
```

---

## Troubleshooting

### Connection Refused

```bash
# Verify broker is running
kubectl get pods -n azure-iot-operations | grep mq-broker

# Check listener status
kubectl get brokerlistener -n azure-iot-operations

# View broker events
kubectl describe brokerlistener loadbalancer-listener -n azure-iot-operations
```

### Port Not Accessible

```bash
# For K3s without external LoadBalancer provider:
# Ports are mapped to node ports instead
kubectl get svc loadbalancer-listener -n azure-iot-operations

# Use NodePort instead:
# kubectl port-forward svc/loadbalancer-listener 1883:1883 -n azure-iot-operations
```

### TLS Certificate Issues

```bash
# Check certificate status
kubectl get certificates -n azure-iot-operations

# View certificate details
kubectl describe certificate -n azure-iot-operations <cert-name>

# Check cert-manager logs
kubectl logs -n cert-manager -l app=cert-manager

# Manually renew if needed
kubectl annotate certificate <cert-name> -n azure-iot-operations \
  cert-manager.io/issue-temporary-certificate="true" --overwrite
```

### High Memory Usage

```bash
# Check current limits
kubectl get pod <broker-pod> -n azure-iot-operations -o yaml | grep -A 5 resources

# Increase if needed
kubectl set resources deployment mq-broker \
  -n azure-iot-operations \
  --limits=memory=2Gi,cpu=1000m \
  --requests=memory=512Mi,cpu=200m
```

---

## Performance Tuning

### For High Throughput

```yaml
# Increase these settings in Broker config:
messageRetentionSeconds: 3600
maxMessageSize: 1MB
maxConnections: 10000
```

### For Many Topics

```bash
# Monitor topic count
mosquitto_sub -h <broker-ip> -t '$SYS/broker/subscriptions/count'

# If too high, consider topic consolidation
```

### Memory Optimization

```bash
# Enable in-memory retention limits
---
inMemoryRetainedMessages:
  enabled: true
  maxRetainedMessages: 10000
```

---

## Security Best Practices

1. **Always Use TLS in Production**
   ```bash
   # Verify TLS is enabled
   kubectl describe brokerlistener -n azure-iot-operations | grep -i tls
   ```

2. **Enable Authentication**
   ```
   Use default authentication backend
   Store credentials in Key Vault
   Rotate regularly
   ```

3. **Network Policies**
   ```bash
   # Restrict broker access to authorized clients
   kubectl apply -f - <<EOF
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: mqtt-broker-policy
     namespace: azure-iot-operations
   spec:
     podSelector:
       matchLabels:
         app: mq-broker
     policyTypes:
     - Ingress
     ingress:
     - from:
       - namespaceSelector:
           matchLabels:
             name: azure-iot-operations
   EOF
   ```

4. **Use Short-Lived Credentials**
   ```
   JWT tokens with expiration
   SAS token rotation
   Certificate pinning
   ```

---

## Next Steps

1. [Create Data Flows](./data-flow-guide.md) to connect MQTT data to cloud
2. [Configure Data Transformations](../architecture/dataflow-architecture.md#data-transformation-optional)
3. [Setup Monitoring & Alerts](https://learn.microsoft.com/en-us/azure/iot-operations/manage-mqtt-broker/howto-configure-diagnostics)
4. [Integrate Real Devices](https://learn.microsoft.com/en-us/azure/iot-operations/discover-manage-assets/)

---

## References

- [Azure IoT Operations MQTT Broker Documentation](https://learn.microsoft.com/en-us/azure/iot-operations/manage-mqtt-broker/overview-mqtt-broker)
- [MQTT Topic Design Patterns](https://www.hivemq.com/blog/mqtt-topics-best-practices/)
- [mTLS Configuration Guide](https://learn.microsoft.com/en-us/azure/iot-operations/manage-mqtt-broker/howto-configure-authentication)
