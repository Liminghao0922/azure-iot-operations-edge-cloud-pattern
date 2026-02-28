# Workshop Part 1: Foundation

## 🎯 Learning Objectives

By completing this workshop, you will:

- [ ] Understand the architecture of this pattern
- [ ] Set up the development environment
- [ ] Deploy infrastructure
- [ ] Configure basic services

## ⏱ Estimated Duration: 3-4 hours

## 📋 Prerequisites

- Azure subscription
- Basic understanding of Kubernetes
- Docker knowledge
- CLI tools installed (az, kubectl, helm)

## 🚀 Steps

### Step 1: Environment Setup (30 min)

1. Clone this repository
2. Set up Azure CLI
3. Create resource group
4. Configure kubectl access

```bash
# Create resource group
az group create --name myapp-rg --location eastus

# Create AKS cluster (if not using existing)
az aks create --resource-group myapp-rg --name myapp-aks --node-count 3

# Get credentials
az aks get-credentials --resource-group myapp-rg --name myapp-aks
```

### Step 2: Infrastructure Deployment (60 min)

1. Review architecture diagram in `architecture/system-overview.png`
2. Deploy infrastructure using Bicep/Terraform
3. Verify all resources are created

```bash
# Deploy using Bicep
az deployment group create \
  --resource-group myapp-rg \
  --template-file deployment/bicep/main.bicep

# Verify deployment
kubectl get nodes
kubectl get pods -A
```

### Step 3: Deploy Core Services (60 min)

1. Apply Kubernetes manifests
2. Verify services are running
3. Check health endpoints

```bash
# Deploy services
kubectl apply -f deployment/k8s/

# Verify
kubectl get svc
kubectl get deployment
```

### Step 4: Configure Monitoring (30 min)

1. Deploy monitoring stack
2. Set up dashboards
3. Create alert rules

```bash
# Check monitoring
kubectl get pods -n monitoring
```

## ✅ Validation Checklist

- [ ] Cluster is running
- [ ] All pods are in Running state
- [ ] Services have IP addresses
- [ ] Health endpoints respond
- [ ] Logs are being collected
- [ ] Metrics are being collected

## 📌 Key Concepts

- **Namespaces**: Logical isolation
- **Deployments**: Manages pod replicas
- **Services**: Expose pods to network
- **Ingress**: Route traffic to services
- **ConfigMaps**: Non-secret configuration
- **Secrets**: Sensitive data management

## 🔗 Related Resources

- [Architecture Overview](../../architecture/design-decisions.md)
- [Production Hardening](../../docs/production-hardening.md)
- [Troubleshooting](../../docs/troubleshooting.md)

## 🆘 Common Issues

**Issue: Pods not starting**
- Check pod logs: `kubectl logs <pod-name>`
- Check resource limits: `kubectl describe pod <pod-name>`
- Verify secrets exist: `kubectl get secrets`

**Issue: Service not accessible**
- Check service endpoints: `kubectl get endpoints`
- Verify ingress configuration: `kubectl get ingress`
- Test connectivity: `kubectl exec -it <pod> -- curl <service>`

---

**Ready for Part 2?** Proceed to [part2.md](part2.md)
