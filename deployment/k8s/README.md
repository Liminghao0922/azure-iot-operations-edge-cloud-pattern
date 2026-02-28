# Kubernetes Manifests

## Overview

This directory contains Kubernetes resources for deploying the application.

### Structure

```
.
├── namespace.yaml       # Namespace definition
├── configmap.yaml       # Configuration data
├── secret.yaml          # Secrets (in base64, use external secret management in prod)
├── deployment.yaml      # Application deployment
├── service.yaml         # Service definition
├── ingress.yaml         # Ingress configuration
├── hpa.yaml             # Horizontal Pod Autoscaler
└── networkpolicy.yaml   # Network policies
```

## Deployment

```bash
# Create namespace
kubectl apply -f namespace.yaml

# Deploy all resources
kubectl apply -f .

# Verify deployment
kubectl get pods -n <namespace>
kubectl get services -n <namespace>
```

## Best Practices

- Use namespaces for isolation
- Define resource requests/limits
- Implement RBAC policies
- Enable network policies
- Use health checks (liveness/readiness probes)
- Implement pod disruption budgets

## Documentation

See [../../../docs/production-hardening.md](../../../docs/production-hardening.md) for deployment guidelines.
