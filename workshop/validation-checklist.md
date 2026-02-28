# Post-Workshop Validation Checklist

Use this checklist after completing the workshops to validate your deployment.

## ✅ Cluster Health

- [ ] Cluster version is supported
- [ ] All nodes are in Ready state
- [ ] Node resource availability > 20%
- [ ] No unschedulable pods
- [ ] All system pods running

```bash
# Verification commands
kubectl get nodes
kubectl get pods -A
kubectl describe nodes
```

## ✅ Application Health

- [ ] All application pods running
- [ ] Pod restart count is low
- [ ] No failed pods
- [ ] No pending pods
- [ ] Health probes passing

```bash
# Verification commands
kubectl get pods -l app=<app-name>
kubectl get hpa
```

## ✅ Networking

- [ ] Services have endpoints
- [ ] Ingress routes working
- [ ] DNS resolution working
- [ ] Network policies allowing traffic
- [ ] TLS/mTLS certificates valid

```bash
# Verification commands
kubectl get endpoints
kubectl get ingress
kubectl exec <pod> -- nslookup <service>
```

## ✅ Data Flow

- [ ] Data sources connected
- [ ] Data flowing through pipeline
- [ ] Data quality checks passing
- [ ] No data loss
- [ ] Target systems receiving data

```bash
# Verification commands
kubectl logs <data-pipeline-pod>
# Check target system for data
```

## ✅ AI Inference

- [ ] Models deployed successfully
- [ ] Models loaded without errors
- [ ] Inference requests succeeding
- [ ] Inference latency acceptable
- [ ] Model accuracy verified

```bash
# Verification commands
kubectl logs <model-serving-pod>
# Test inference endpoint
curl http://<inference-endpoint>/predict
```

## ✅ Monitoring & Logging

- [ ] Metrics collection working
- [ ] Logs being centralized
- [ ] Dashboards showing data
- [ ] Alerts configured
- [ ] Alert notification channels working

```bash
# Verification commands
kubectl get pods -n monitoring
# Check dashboard for metrics
```

## ✅ Security

- [ ] RBAC policies deployed
- [ ] Network policies active
- [ ] Secrets stored securely
- [ ] TLS enabled
- [ ] Audit logging enabled

```bash
# Verification commands
kubectl get rolebindings -A
kubectl get networkpolicies -A
kubectl get secrets -A
```

## ✅ Operational Readiness

- [ ] Backup procedure tested
- [ ] Disaster recovery plan documented
- [ ] Runbooks created
- [ ] Team trained
- [ ] Support contacts established

## 📋 Performance Verification

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| API Latency (p99) | <500ms | | ✅/❌ |
| Inference Latency (p99) | <200ms | | ✅/❌ |
| Throughput | >100 req/s | | ✅/❌ |
| Error Rate | <0.1% | | ✅/❌ |
| Availability | >99.5% | | ✅/❌ |

## 📝 Sign-Off

- [ ] All checks passed
- [ ] Performance targets met
- [ ] Security review completed
- [ ] Team approved for production
- [ ] Ready for production deployment

**Validation Completed By:** ___________________
**Date:** ___________________
**Approved By:** ___________________

---

For issues, see [Troubleshooting Guide](../../docs/troubleshooting.md)
