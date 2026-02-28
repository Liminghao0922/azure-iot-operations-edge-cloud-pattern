#!/bin/bash
# Apply Kubernetes configurations for Azure IoT Operations
# Usage: ./apply-configs.sh [optional: namespace]

set -e

NAMESPACE="${1:-azure-iot-operations}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "================================================"
echo "Azure IoT Operations - Kubernetes Configuration"
echo "================================================"
echo "Namespace: $NAMESPACE"
echo "Script Directory: $SCRIPT_DIR"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo -e "${YELLOW}Creating namespace: $NAMESPACE${NC}"
    kubectl create namespace "$NAMESPACE"
fi

# Function to apply a manifest
apply_manifest() {
    local file=$1
    local name=$2
    
    if [ ! -f "$file" ]; then
        echo -e "${RED}✗ File not found: $file${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}Applying $name...${NC}"
    kubectl apply -f "$file" -n "$NAMESPACE"
    echo -e "${GREEN}✓ $name applied${NC}"
    echo ""
}

# Apply configurations
echo -e "${YELLOW}Step 1: MQTT Broker Configuration${NC}"
apply_manifest "$SCRIPT_DIR/mqtt-broker-config.yaml" "MQTT Broker Config"

echo -e "${YELLOW}Step 2: Data Flow Configuration${NC}"
apply_manifest "$SCRIPT_DIR/dataflow-config.yaml" "Data Flows"

# Verify deployments
echo ""
echo -e "${YELLOW}Verifying deployments...${NC}"
echo ""

echo "MQTT Broker Status:"
kubectl get pods -n "$NAMESPACE" -l app=mq-broker
echo ""

echo "Data Flow Status:"
kubectl get dataflow -n "$NAMESPACE"
echo ""

echo "Broker Listener Status:"
kubectl get brokerlistener -n "$NAMESPACE"
echo ""

# Get external endpoint information
echo -e "${YELLOW}External Broker Endpoint:${NC}"
echo ""

EXTERNAL_IP=$(kubectl get svc -n "$NAMESPACE" -l app.kubernetes.io/name=loadbalancer-listener \
    -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")

if [ -z "$EXTERNAL_IP" ]; then
    EXTERNAL_IP=$(kubectl get svc -n "$NAMESPACE" -l app.kubernetes.io/name=loadbalancer-listener \
        -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
fi

if [ -z "$EXTERNAL_IP" ]; then
    echo -e "${YELLOW}Note: External IP not yet assigned (normal for K3s without LoadBalancer provider)${NC}"
    echo "You can access the broker via port-forward:"
    echo "  kubectl port-forward svc/loadbalancer-listener 1883:1883 -n $NAMESPACE"
else
    echo -e "${GREEN}MQTT Broker Address: $EXTERNAL_IP${NC}"
    echo "  - Port 1883 (Test): mqtt://$EXTERNAL_IP:1883"
    echo "  - Port 8883 (Prod): mqtts://$EXTERNAL_IP:8883"
fi

echo ""
echo -e "${YELLOW}For Azure Event Hub connection string, retrieve from Key Vault:${NC}"
echo "  az keyvault secret show --vault-name <kv-name> \\"
echo "    --name event-hub-connection-string --query value -o tsv"
echo ""

echo -e "${GREEN}✓ Configuration applied successfully!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update Event Hub connection string in dataflow-config.yaml (5 locations)"
echo "2. Verify pods are running: kubectl get pods -n $NAMESPACE"
echo "3. Test MQTT connection: python app/src/mqtt_client.py --host <broker-ip> sub"
echo "4. Monitor logs: kubectl logs -n $NAMESPACE -l app=mq-broker -f"
echo ""
