# Helm Charts

## Overview

This directory contains Helm charts for deploying this pattern.

## Chart Structure

```
chart/
├── Chart.yaml          # Chart metadata
├── values.yaml         # Default values
├── values-prod.yaml    # Production overrides
└── templates/          # Kubernetes resource templates
```

## Installation

```bash
# Add chart repository
helm repo add myrepo <chart-url>

# Install chart
helm install my-release myrepo/mychart

# Override values
helm install my-release myrepo/mychart \
  -f values-prod.yaml

# Upgrade release
helm upgrade my-release myrepo/mychart
```

## Best Practices

- Pin chart versions in production
- Use separate values files for each environment
- Document all values in values.yaml
- Implement chart validation tests

## Documentation

See [../../../docs/production-hardening.md](../../../docs/production-hardening.md) for deployment guidelines.
