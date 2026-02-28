#!/bin/bash
# Deploy Azure IoT Operations using Bicep template
# Usage: ./deploy.sh [environment] [location]

set -e

# Configuration
ENVIRONMENT="${1:-dev}"
LOCATION="${2:-eastus}"
RESOURCE_GROUP_PREFIX="rg-aio"
RESOURCE_GROUP="${RESOURCE_GROUP_PREFIX}-${ENVIRONMENT}-${LOCATION}"
CLUSTER_NAME="aiocluster"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Azure IoT Operations Bicep Deployment ===${NC}"
echo ""
echo "Configuration:"
echo "  Environment: $ENVIRONMENT"
echo "  Location: $LOCATION"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Cluster Name: $CLUSTER_NAME"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI not found. Please install it first.${NC}"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo -e "${YELLOW}Warning: kubectl not found. Please install it for cluster management.${NC}"
fi

# Login to Azure
echo -e "${YELLOW}Logging in to Azure...${NC}"
az login

# Get current subscription
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo -e "${GREEN}Using subscription: $SUBSCRIPTION_ID${NC}"

# Create resource group
echo ""
echo -e "${YELLOW}Creating resource group: $RESOURCE_GROUP${NC}"
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION"

# Deploy Bicep template
echo ""
echo -e "${YELLOW}Deploying Bicep template...${NC}"
az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file "main.bicep" \
  --parameters \
    location="$LOCATION" \
    environment="$ENVIRONMENT" \
    clusterName="$CLUSTER_NAME"

# Get outputs
echo ""
echo -e "${YELLOW}Retrieving deployment outputs...${NC}"
OUTPUTS=$(az deployment group show \
  --resource-group "$RESOURCE_GROUP" \
  --name "main" \
  --query "properties.outputs" \
  -o json)

# Extract key values
STORAGE_ACCOUNT=$(echo "$OUTPUTS" | jq -r '.storageAccountName.value')
EVENT_HUB_NAMESPACE=$(echo "$OUTPUTS" | jq -r '.eventHubNamespaceName.value')
EVENT_HUB_NAME=$(echo "$OUTPUTS" | jq -r '.eventHubName.value')
KEY_VAULT=$(echo "$OUTPUTS" | jq -r '.keyVaultName.value')

echo ""
echo -e "${GREEN}=== Deployment Completed Successfully ===${NC}"
echo ""
echo "Created Resources:"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo "  Event Hub Namespace: $EVENT_HUB_NAMESPACE"
echo "  Event Hub: $EVENT_HUB_NAME"
echo "  Key Vault: $KEY_VAULT"
echo ""

# Get Event Hub connection string
echo -e "${YELLOW}Retrieving Event Hub connection string...${NC}"
CONNECTION_STRING=$(az keyvault secret show \
  --vault-name "$KEY_VAULT" \
  --name "event-hub-connection-string" \
  --query value \
  -o tsv)

echo ""
echo -e "${GREEN}Event Hub Connection String:${NC}"
echo "$CONNECTION_STRING"
echo ""

# Save configuration to file
CONFIG_FILE="deployment-config.env"
cat > "$CONFIG_FILE" << EOF
# Azure IoT Operations Deployment Configuration
ENVIRONMENT=$ENVIRONMENT
LOCATION=$LOCATION
RESOURCE_GROUP=$RESOURCE_GROUP
SUBSCRIPTION_ID=$SUBSCRIPTION_ID
CLUSTER_NAME=$CLUSTER_NAME

# Deployed Resources
STORAGE_ACCOUNT=$STORAGE_ACCOUNT
EVENT_HUB_NAMESPACE=$EVENT_HUB_NAMESPACE
EVENT_HUB_NAME=$EVENT_HUB_NAME
KEY_VAULT=$KEY_VAULT

# Connection Strings
EVENT_HUB_CONNECTION_STRING=$CONNECTION_STRING

# Next Steps
# 1. Register Azure resource providers (if not already done)
# 2. Connect cluster to Azure Arc using az connectedk8s connect
# 3. Deploy Azure IoT Operations via Azure Portal
# 4. Configure MQTT Broker listener
# 5. Set up data flows
EOF

echo -e "${GREEN}Configuration saved to: $CONFIG_FILE${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Review and save the Event Hub connection string above"
echo "2. You'll need this for configuring Fabric Real-Time Intelligence"
echo "3. Follow the hands-on guide to complete IoT Operations setup"
echo ""

echo -e "${GREEN}Done!${NC}"
