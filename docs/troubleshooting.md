# Troubleshooting Guide

## Common Issues

### Pod Crashes

**Symptom:** Pods repeatedly crash with CrashLoopBackOff status

**Diagnosis:**
```bash
kubectl describe pod <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --previous
```

**Solutions:**
- Check resource limits are sufficient
- Verify all required secrets/configmaps exist
- Review application logs for initialization errors

---

### Service Connectivity Issues

**Symptom:** Services cannot communicate with each other

**Diagnosis:**
```bash
kubectl get svc
kubectl get endpoints
kubectl exec <pod> -- nslookup <service-name>
```

**Solutions:**
- Verify service DNS resolution
- Check network policies aren't blocking traffic
- Verify service ports match target ports
- Check RBAC permissions

---

### Data Flow Failures

**Symptom:** Data is not being processed or reaching destination

**Diagnosis:**
```bash
kubectl logs <pipeline-pod> | grep ERROR
kubectl describe dataflow <flow-name> -n <namespace>
```

**Solutions:**
- Verify source connectivity
- Check transformation logic
- Verify destination connectivity
- Review schema compatibility

---

### Performance Degradation

**Symptom:** System response time is slow

**Diagnosis:**
```bash
kubectl top nodes
kubectl top pods
# Check metrics in monitoring dashboard
```

**Solutions:**
- Check resource utilization (CPU, memory)
- Look for contention on shared resources
- Consider horizontal scaling
- Profile application performance

---

### Authentication Failures

**Symptom:** 401/403 errors when accessing services

**Diagnosis:**
```bash
kubectl get rolebindings -n <namespace>
kubectl describe rolebinding <name> -n <namespace>
```

**Solutions:**
- Verify token/certificate is valid
- Check RBAC role is properly configured
- Verify service account exists
- Check certificate expiration

---

## Debug Commands

### Cluster Diagnostics

```bash
# Check cluster health
kubectl cluster-info

# View cluster events
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# Check node status
kubectl get nodes -o wide

# Describe problematic nodes
kubectl describe node <node-name>
```

### Pod Diagnostics

```bash
# Get pod status details
kubectl describe pod <pod-name> -n <namespace>

# View current and previous logs
kubectl logs <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --previous

# Execute command in pod for debugging
kubectl exec -it <pod-name> -n <namespace> -- /bin/sh
```

### Network Diagnostics

```bash
# Test DNS resolution from pod
kubectl exec <pod> -- nslookup <service-name>

# Test connectivity
kubectl exec <pod> -- curl http://<service-name>:<port>

# Check network policies
kubectl get networkpolicies -n <namespace>
```

## Getting Help

### Collecting Debug Information

When reporting issues, please provide:

1. Cluster info: `kubectl version`, `kubectl cluster-info`
2. Pod status: `kubectl get pods -o wide`
3. Recent logs: `kubectl logs <pod-name>`
4. Events: `kubectl get events --sort-by='.lastTimestamp'`
5. Resource status: `kubectl describe <resource-type> <name>`

### Support Channels

- GitHub Issues: Report bugs and feature requests
- Documentation: Check [production-hardening.md](production-hardening.md)
- Architecture: See [../architecture/design-decisions.md](../architecture/design-decisions.md)

## Status Page

Check the [Status Page](https://status.example.com) for known issues and maintenance windows.
