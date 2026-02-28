# Bicep Deployment Template

## Overview

This directory contains Azure Bicep templates for deploying this pattern.

### Main Template

The `main.bicep` file orchestrates the deployment of all resources.

### Parameters

Update `parameters.bicep` or create environment-specific parameter files:

```bash
az deployment group create \
  --resource-group <rg-name> \
  --template-file main.bicep \
  --parameters @parameters.bicep
```

### Modules

- `modules/networking.bicep` - VNet, Subnets, NSGs
- `modules/compute.bicep` - AKS Cluster
- `modules/storage.bicep` - Storage accounts
- `modules/monitoring.bicep` - App Insights, Log Analytics

## Usage

```bash
# Create resource group
az group create --name <rg-name> --location <location>

# Deploy infrastructure
az deployment group create \
  --resource-group <rg-name> \
  --template-file ./main.bicep \
  --parameters environment=prod

# Verify deployment
az deployment group list --resource-group <rg-name>
```

## Documentation

See [../../../docs/production-hardening.md](../../../docs/production-hardening.md) for deployment guidelines.
