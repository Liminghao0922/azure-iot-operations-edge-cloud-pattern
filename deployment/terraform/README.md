# Terraform Deployment Template

## Overview

This directory contains Terraform modules for deploying this pattern to Azure.

### Module Structure

```
.
├── main.tf          # Root module
├── variables.tf     # Input variables
├── outputs.tf       # Output values
├── terraform.tfvars # Variable values
└── modules/         # Reusable modules
    ├── network/
    ├── kubernetes/
    ├── storage/
    └── monitoring/
```

## Usage

```bash
# Initialize Terraform
terraform init

# Plan deployment
terraform plan -out=tfplan

# Apply configuration
terraform apply tfplan

# Destroy resources (when done)
terraform destroy
```

## Configuration

1. Update `terraform.tfvars` with your environment values
2. Ensure Azure credentials are configured
3. Run terraform commands

## State Management

- Remote state is recommended for production
- Configure backend in `backend.tf`
- Use Azure Storage Account for state storage

## Documentation

See [../../../docs/production-hardening.md](../../../docs/production-hardening.md) for deployment guidelines.
