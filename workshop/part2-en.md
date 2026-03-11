# Azure IoT Operations - Hands-On Part 2

This part continues from Part 1 and covers MQTT Broker setup, Data Flow build-out, and end-to-end testing.

**Prerequisite**: Complete [Part 1](./part1-en.md)

## Step 1: MQTT Broker Configuration (30 minutes)

### Step 1.1: Understand the MQTT Broker Architecture

Azure IoT Operations MQTT Broker supports multiple listeners:

- **Default endpoint**: In-cluster traffic
- **External endpoint**: Clients outside the cluster

### Step 1.2: Get frontend service info

```bash
# List MQTT broker services
kubectl get svc -n azure-iot-operations
```

### Step 1.3: Configure a BrokerListener for external access in Azure Portal

Create a new BrokerListener for external connections:

1. In Azure portal, open your IoT Operations instance
2. Under **Components**, select **MQTT Broker**
3. Select **MQTT broker listener for LoadBalancer** > **Create**

   ![MQTT Broker LoadBalancer creation](image/mqtt-broker-loadbalancer-create.png)
4. Basic configuration:

   - **Name**: e.g., `loadbalancer-listener`
   - **Service name**: leave empty (uses the listener name)
   - **Service type**: **LoadBalancer**
5. Under **Ports**, configure the first port (for testing):

   - **Port**: **1883**
   - **Authentication**: **None**
   - **Authorization**: **None**
   - **Protocol**: **MQTT**
   - **TLS**: none

   > **Important**: Test-only configuration. In production, enable TLS and authentication.
   >
6. Select **Add port entry** and add a second port (production):

   - **Port**: **8883**
   - **Authentication**: **default**
   - **Authorization**: **None**
   - **Protocol**: **MQTT**
   - **TLS**: **Add**
7. In **TLS configuration**, set:

   **Required**:

   - **TLS mode**: **Automatic** (cert-manager managed)
   - **Issuer name**: `azure-iot-operations-aio-certificate-issuer`
   - **Issuer kind**: **ClusterIssuer**

   **Optional** (keep defaults for test):

   - **Issuer group**: `cert-manager.io`
   - **Private key algorithm**: `Ec256`
   - **Private key rotation policy**: `Always`
   - **DNS names**: optional SANs
   - **IP addresses**: optional SANs
   - **Duration**: 90 days by default
   - **Renew before**: default

   Keep other settings as default and click **Apply**.

   > **Note**: Automatic mode uses the built-in issuer. In production, use a custom issuer.
   >
8. Select **Create listener**

### Step 1.4: Get the MQTT broker endpoint

After creating the LoadBalancer listener, get the external IP:

```bash
kubectl get svc -n azure-iot-operations
```

Find your listener service and note the endpoint, e.g., `<external-ip>:1883` (test) or `<external-ip>:8883` (TLS).

![Service endpoints](image/service-endpoints-kubectl.png)
---------------------------------------------------------

## Step 2: Create Microsoft Fabric Real-Time Intelligence Data Source (25 minutes)

### Step 2.1: Create an Event Stream

1. Sign in to [https://fabric.microsoft.com](https://fabric.microsoft.com)
2. Create or select a Workspace
3. Choose **New Item** → **Eventstream**
   ![New Eventstream](image/fabric-new-eventstream.png)
4. Name and create the event stream (e.g., `aio-eventstream`)
   ![Eventstream name](image/eventstream-naming.png)
5. Open the event stream editor

### Step 2.2: Add a custom endpoint

1. In the event stream, select **Add source** → **Custom endpoint**
   ![Add custom endpoint](image/eventstream-add-custom-endpoint.png)
2. In Custom endpoint configuration:
   - Name the source (e.g., `mqtt-iot-source`)
     ![Custom endpoint name](image/custom-endpoint-naming.png)
   - Click Publish
     ![Custom endpoint publish](image/custom-endpoint-publish.png)

**Reference**: [Add a Custom Endpoint or Custom App Source to an Eventstream - Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/add-source-custom-app?pivots=basic-features#add-custom-endpoint-data-as-a-source)

### Step 2.3: Get Kafka-compatible endpoint details

In the Details pane, note:

![Endpoint details](image/endpoint-connection-details.png)

- Event Hub compatible endpoint
- Shared access key
- Event stream name

---

## Step 3: Configure Data Flow 1 - MQTT client to Fabric (25 minutes)

### Step 3.1: Architecture - Flow 1

```
┌──────────────┐     ┌──────────────┐     ┌────────────┐
│  MQTT Client │────→│  MQTT Broker │────→│ Fabric RTI │
│   (MQTTX)    │     │   Default    │     │ Eventstream│
│              │     │   Endpoint   │     │            │
└──────────────┘     └──────────────┘     └────────────┘
                         (No Transform)
```

### Step 3.2: Create a Data Flow endpoint - Fabric RTI

1. Create a Managed Identity for Data Flow

   ```bash
   az identity create \
   --name mi-dataflow-fabric \
   --resource-group rg-demo-aio \
   --location japaneast
   ```
2. Get Client ID and Tenant ID

   ```bash
   DATAFLOW_MI_CLIENT_ID=$(az identity show \
   --name mi-dataflow-fabric \
   --resource-group rg-demo-aio \
   --query clientId -o tsv)

   TENANT_ID=$(az account show --query tenantId -o tsv)

   echo "Client ID: $DATAFLOW_MI_CLIENT_ID"
   echo "Tenant ID: $TENANT_ID"
   ```
3. Configure federated identity

   ```bash
   # Get OIDC Issuer
   OIDC_ISSUER=$(az connectedk8s show \
   --resource-group rg-demo-aio \
   --name aiocluster \
   --query oidcIssuerProfile.issuerUrl \
   --output tsv)

   # Create federated credential for Data Flow Service Account
   az identity federated-credential create \
   --name "dataflow-fabric-federation" \
   --identity-name mi-dataflow-fabric \
   --resource-group rg-demo-aio \
   --issuer $OIDC_ISSUER \
   --subject system:serviceaccount:azure-iot-operations:aio-dataflow \
   --audience api://AzureADTokenExchange
   ```
4. Grant Managed Identity access to Fabric
   ![Fabric managed identity permission](image/fabric-managed-identity-permission.png)
5. Sign in to [IoT Operations experience](https://iotoperations.azure.com/)
6. Select your instance
7. Go to **Data flow endpoints**
8. Create **Microsoft Fabric Real-Time Intelligence**
   ![Create data flow endpoint](image/dataflow-endpoint-create-fabric-rti.png)
9. Configure:

- **Name**: `fabric-rti-endpoint`
- **Authentication method**: **User assigned managed identity**
- **Host**: Fabric **Bootstrap server**
  ![Fabric Bootstrap Server](image/fabric-bootstrap-server.png)
- **Client ID**: from above
- **Tenant ID**: from above

10. Click **Apply**
    ![Apply endpoint](image/endpoint-apply.png)

### Step 3.3: Create Data Flow - MQTT to Fabric

1. In Data Flows, click **Create new**
   ![Create data flow](image/dataflow-create-new.png)
2. Configure:

   - **Source**: **Data flow endpoint** → **Default Endpoint**
   - **Topic**: e.g., `sensors/temperature` or `#`
   - **Message Schema**: click **Add** (required)

     > **Important**: If Message Schema is missing, Fabric shows `{}`.
     >

     Message Schema steps:

     1. Click **Add** in Message Schema
     2. Select an existing schema or click **Create new**
     3. Generate a schema using:
        - [Schema Generator Helper](https://azure-samples.github.io/explore-iot-operations/schema-gen-helper/)
        - Provide sample JSON; the tool generates schema
     4. Copy the schema to Azure IoT Operations Schema Registry
     5. Select that schema in Data Flow

     Reference: [Set Kafka Message Schema](https://learn.microsoft.com/en-us/azure/iot-operations/connect-to-cloud/howto-configure-kafka-endpoint?tabs=portal#set-kafka-message-schema)
   - **Transform**: None
   - **Destination**: **fabric-rti-endpoint**; set Topic from Fabric
     ![Data Flow config](image/dataflow-configure.png)
3. Click **Save**, enter settings, then **Save** again

   - **Data flow name**: e.g., **df-sensor-data**
   - **Enable data flow**: **Yes**
   - **Request data persistence**: **Yes**
   - **Data flow profile**: **default**
     ![Data Flow save settings](image/dataflow-save-settings.png)

### Step 3.4: Verify Data Flow

```bash
# Check data flow status
kubectl get dataflows -n azure-iot-operations

# Get details
kubectl describe dataflow -n azure-iot-operations
```

---

## Step 4: Test with MQTTX - Flow 1 (25 minutes)

### Step 4.1: Install MQTTX

1. Download [MQTTX - Open source MQTT Client](https://mqttx.app/)
2. Install the tool

### Step 4.2: Configure MQTTX connection

1. Open MQTTX
2. Create a new connection:

   - **Name**: `AIO-Cluster`
   - **Host**: MQTT broker endpoint IP/hostname
   - **Port**: `1883`
   - **Protocol**: `mqtt://`
   - **Client ID**: `mqttx-client-test`
   - **Username**: (if required)
   - **Password**: (if required)
3. Click **Connect**

### Step 4.3: Publish test messages

1. In MQTTX, open **Publish**
2. Configure:

   - **Topic**: `sensors/temperature`
   - **Payload**:

   ```json
   {
     "timestamp": "2026-02-26T10:30:00Z",
     "temperature": 22.5,
     "unit": "celsius",
     "sensorId": "sensor-001"
   }
   ```

   - **QoS**: 1
3. Click **Publish**
4. Send multiple messages with a few seconds between

### Step 4.4: Verify data in Fabric

1. Go back to Fabric Real-Time Intelligence
2. In the Eventstream, check:

   - **Data preview** or message log
   - Verify JSON objects
3. If you see data, Flow 1 is successful.

**Expected**: Messages sent via MQTTX appear in Fabric.

**Troubleshooting - if you see `{}`**:

- **Cause**: Message Schema missing in Data Flow Source
- **Fix**:
  1. Return to Data Flow config
  2. Edit Source
  3. Add **Message Schema** (see Step 3.3)
  4. Save and resend messages
  5. Refresh Data preview

> **Note**: Message Schema tells Data Flow how to parse JSON payloads. Without it, Fabric receives empty objects.

---

## Step 5: Pull data from REST API with HTTP Connector (30 minutes)

### Step 5.1: What HTTP Connector does

Azure IoT Operations HTTP/REST Connector can:

- Periodically pull inventory data from WMS (or other REST APIs)
- Convert data to MQTT messages
- Publish to the MQTT broker without custom code

This is simpler than building a custom container and supports auth and transforms.

### Step 5.2: Deploy mock WMS API (to Kubernetes)

To avoid network issues, deploy the mock WMS API as a Deployment and Service so the HTTP Connector can access it via in-cluster DNS.

#### Prerequisite: Install Docker

Verify Docker in WSL:

```bash
docker --version
```

**If Docker is not installed, run:**

```bash
# Update package index
sudo apt-get update

# Install Docker dependencies
sudo apt-get install -y \
  apt-transport-https \
  ca-certificates \
  curl \
  gnupg \
  lsb-release

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Start Docker service
sudo service docker start

# Verify
 docker --version
```

**Optional: allow docker without sudo**

```bash
# Add current user to docker group
sudo usermod -aG docker $USER

# Apply new group (log out/in, or run)
newgrp docker

# Verify
 docker ps
```

#### Deployment steps:

1. **Build the mock API Docker image**

   ```bash
   cd ~/projects/azure-iot-operations-edge-cloud-pattern
   ```

   Build with the repo Dockerfile:

   ```bash
   # Build image
   docker build -t mock-wms-api:latest -f app/Dockerfile app/

   # Verify image
   docker images | grep mock-wms-api
   ```
2. **Import image into K3s**

   K3s uses containerd, so import the Docker image:

   ```bash
   # Save image to tar
   docker save mock-wms-api:latest -o /tmp/mock-wms-api.tar

   # Import into K3s containerd
   sudo k3s ctr images import /tmp/mock-wms-api.tar

   # Verify image in K3s
   sudo k3s ctr images ls | grep mock-wms-api

   # Clean up
   rm /tmp/mock-wms-api.tar
   ```

   > **Note**: K3s uses containerd rather than Docker, so you must import the image.
   >
3. **Create a namespace (if needed)**

   ```bash
   # Create app namespace (ignore error if exists)
   kubectl create namespace app

   # Verify
   kubectl get namespace app
   ```
4. **Create Kubernetes Deployment**

   Use YAML and set `imagePullPolicy: Never` to use the local image:

   ```bash
   cat <<EOF | kubectl apply -f -
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: mock-wms-api
     namespace: app
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: mock-wms-api
     template:
       metadata:
         labels:
           app: mock-wms-api
       spec:
         containers:
         - name: mock-wms-api
           image: mock-wms-api:latest
           imagePullPolicy: Never
           ports:
           - containerPort: 8080
   EOF

   # Verify Deployment
   kubectl get deployment -n app | grep mock-wms-api

   # Watch Pod status
   kubectl get pods -n app -w
   ```

   > **Key setting**: `imagePullPolicy: Never` ensures Kubernetes uses the imported image.
   >
5. **Expose as a Service**

   ```bash
   kubectl expose deployment mock-wms-api \
     --port=8080 \
     --target-port=8080 \
     --type=ClusterIP \
     -n app

   # Verify Service
   kubectl get svc -n app | grep mock-wms-api

   # Describe Service
   kubectl describe svc mock-wms-api -n app
   ```
6. **Verify the mock API**

   ```bash
   # Method 1: curl image (recommended)
   kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n azure-iot-operations -- \
     curl http://mock-wms-api.app.svc.cluster.local:8080/api/inventory

   # Method 2: busybox
   kubectl run -it --rm debug --image=busybox --restart=Never -n azure-iot-operations -- \
     wget -qO- http://mock-wms-api.app.svc.cluster.local:8080/api/inventory
   ```

   Expected response (JSON):

   ```json
   [
     {"item_id": "ITEM-001", "name": "Product 1", "quantity": 45, "last_updated": "2026-03-05T10:30:00.123456"},
     {"item_id": "ITEM-002", "name": "Product 2", "quantity": 78, "last_updated": "2026-03-05T10:30:00.123456"},
     {"item_id": "ITEM-003", "name": "Product 3", "quantity": 32, "last_updated": "2026-03-05T10:30:00.123456"}
   ]
   ```

   > **Tip**: If the Pod exits before output shows, it may still be pulling. Wait a few seconds and retry, or watch with `kubectl get pods -n azure-iot-operations -w`.
   >
7. **Mock API code location**

   - **Source**: `app/src/mock_wms_api.py`
   - **Namespace**: `app`
   - **Service address**: `0.0.0.0:8080` (inside Pod)
   - **API endpoint**: `/api/inventory` (GET)
   - **Kubernetes Service DNS**:
     - Same namespace: `mock-wms-api:8080`
     - Cross-namespace: `mock-wms-api.app.svc.cluster.local:8080`
   - **Response**: inventory list (item_id, name, quantity, last_updated)

> **Note**: The mock API Pod runs in `app`. HTTP Connector runs in `azure-iot-operations`, so use the full service DNS `mock-wms-api.app.svc.cluster.local`.

### Step 5.3: Deploy HTTP Connector template

1. In Azure portal, go to your IoT Operations instance
2. Select **Connector templates**
3. Click **Create a connector template**
   ![Create connector template](image/http-connector-template-create.png)
4. Select:

   - **Connector name**: `Azure IoT Operations connector for REST/HTTP`
     ![Select REST/HTTP connector](image/http-connector-template-select.png)
5. Continue with defaults and click **Create**
   ![Confirm connector template](image/http-connector-template-review-create.png)

> **Note**: This template is created only once.

### Step 5.4: Verify mock API Deployment

```bash
# Pod status
kubectl get pods -n app -o wide | grep mock-wms-api

# Pod logs
kubectl logs -n app -l app=mock-wms-api -f

# Service status
kubectl get svc -n app | grep mock-wms-api
```

**Expected**:

- Pod: `Running` (1/1 Ready)
- Service: ClusterIP with internal IP

### Step 5.5: Create a device in Operations Experience

1. Sign in to [IoT Operations Experience](https://iotoperations.azure.com/)
2. Select your instance
3. Navigate to **Devices** → **Create device** or **Create new** → **Device**
   ![Create device](image/device-create.png)
4. Name the device, e.g., `wms-api-device`
5. Under **Microsoft.Http**, click **New** to add an HTTP endpoint
6. Configure the HTTP endpoint:

   - **Endpoint name**: `wms-endpoint`
   - **Endpoint URL**: `http://mock-wms-api.app.svc.cluster.local:8080`
     - Use full Service DNS for cross-namespace access
     - HTTP Connector is in `azure-iot-operations`, mock API in `app`
   - **Authentication mode**:
     - `Anonymous` (for testing)
     - `Username password` (if needed)
     - `X509 certificate` (if needed)
       ![HTTP endpoint configuration](image/http-endpoint-config.png)

   > **Network note**: Using full Service DNS enables cross-namespace access without host networking.
   >
7. Click **Save**
8. Click **Next** and add custom properties if needed
9. Click **Create**
   ![Create device confirmation](image/device-create-confirm.png)

### Step 5.6: Create asset and dataset

1. In **Assets**, select **Create asset** or **Create new** → **Asset**
   ![Create asset](image/asset-create.png)
2. Select the HTTP endpoint `wms-endpoint`
3. Enter asset name, e.g., `wms`
   ![Asset name](image/asset-name.png)
4. Click **Next**
5. **Create dataset** (click **Create dataset**):

   - **Dataset name**: `inventory`
   - **Data source**: `/api/inventory`
   - **Sampling interval**: `10000` (10 seconds, required)
   - **Destination**: `aio/data/wms/inventory`
   - **Transform**: empty

   > **Important**: **Sampling interval** is required; otherwise `Failed to parse dataset configuration`.
   > ![Dataset configuration](image/dataset-config.png)  (Sampling interval required)
   >
6. Click **Next**
7. Review and click **Create**
   ![Asset review](image/asset-review-create.png)

### Step 5.7: Verify data flow

Wait a few minutes for the HTTP Connector to poll:

```bash
# HTTP Connector Pod status
kubectl get pods -n azure-iot-operations | grep httpconnector

# HTTP Connector logs (last 100 lines)
kubectl logs -n azure-iot-operations $(kubectl get pods -n azure-iot-operations -o name | grep httpconnector) --tail=100

# HTTP Connector logs (follow)
kubectl logs -n azure-iot-operations $(kubectl get pods -n azure-iot-operations -o name | grep httpconnector) -f

# Asset configuration
kubectl get assets.namespaces.deviceregistry.microsoft.com wms  -n azure-iot-operations -o json
```

**Expected**: inventory data messages every 10 seconds.

---

## Step 6: Configure Data Flow 2 - HTTP Connector to Fabric (35 minutes)

### Step 6.1: Architecture - Flow 2

```
┌──────────────┐     ┌──────────────┐     ┌────────────────┐
│  WMS System  │     │   HTTP/REST  │     │ MQTT Broker    │     ┌─────────────────────┐
│   REST API   │────→│   Connector  │────→│ (MQTT topics)  │────→│ Fabric RTI          │
│              │     │  (Built-in)  │     │                │     │ Eventstream (WMS)   │
└──────────────┘     └──────────────┘     └────────────────┘     └─────────────────────┘
```

### Step 6.2: Create a second Fabric Event Stream (for WMS data)

1. Sign in to [https://fabric.microsoft.com](https://fabric.microsoft.com)
2. Create or select a Workspace
3. Choose **New Item** → **Eventstream**
4. Name it (e.g., `aio-wms-eventstream`)
5. Open the event stream editor
6. Select **Add source** → **Custom endpoint**
   - Name it (e.g., `mqtt-iot-wms`)
   - Click Publish

### Step 6.3: Get Event Stream connection details

In Details pane:
**Details** → **Kafka** → **Entra ID Authentication**

- Bootstrap server
- Topic name

**Reference**: [Add a Custom Endpoint to an Eventstream - Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/add-source-custom-app?pivots=basic-features#add-custom-endpoint-data-as-a-source)

### Step 6.4: Create a second Data Flow endpoint - Fabric RTI (WMS)

1. Sign in to [IoT Operations experience](https://iotoperations.azure.com/)
2. Select your instance
3. Go to **Data flow endpoints**
4. Create **Microsoft Fabric Real-Time Intelligence**
5. Configure:

   - **Name**: `fabric-rti-wms-endpoint`
   - **Authentication method**: **User assigned managed identity**
   - **Host**: Bootstrap server from WMS Event Stream
   - **Client ID**: from `mi-dataflow-fabric`
   - **Tenant ID**: same Tenant ID
6. Click **Apply**
   ![Fabric RTI endpoint for WMS](image/dataflow-endpoint-wms.png)

> **Note**: Both Data Flow endpoints use the same Managed Identity and different Fabric Event Streams.

### Step 6.5: Create Data Flow from HTTP Connector to Fabric

HTTP Connector publishes to `aio/data/wms/inventory`. Create a Data Flow to forward it to Fabric:

1. Sign in to [IoT Operations Experience](https://iotoperations.azure.com/)
2. Go to **Data Flows**
3. Click **Create new**
4. Configure Data Flow 2:

   - **Source**: **Asset** → previously created asset (e.g., **wms**)
   - **Source Details**: **Dataset** `inventory`
     ![Dataflow source asset selection](image/dataflow-wms-source-asset.png)
   - **Transform**: None
   - **Destination**: **fabric-rti-wms-endpoint**
   - Copy Topic from the WMS Event Stream
     ![Dataflow destination topic](image/dataflow-wms-destination-topic.png)
5. Click **Save**, enter settings, then **Save** again

   - **Data flow name**: e.g., **df-wms-inventory**
   - **Enable data flow**: **Yes**
   - **Request data persistence**: **Yes**
   - **Data flow profile**: **default**
     ![Dataflow save settings](image/dataflow-wms-save-settings.png)

## Step 7: End-to-end test for Flow 2 (25 minutes)

### Step 7.1: Verify WMS data in Fabric

1. Return to Fabric Real-Time Intelligence
2. In the Eventstream, check:

   - **Data preview** should show WMS inventory data
3. Confirm the data structure is correct

**Expected**: HTTP Connector pulls WMS data every 10 seconds and sends to Fabric via MQTT Broker.
![Fabric WMS data preview](image/fabric-wms-data-preview.png)
-------------------------------------------------------------

## Estimated Time (Part 2)

- MQTT Broker configuration: 30 minutes
- Fabric setup: 25 minutes
- Data flow configuration (Flow 1): 25 minutes
- MQTTX test: 25 minutes
- HTTP Connector setup: 30 minutes
- Data flow configuration (Flow 2): 35 minutes
- End-to-end test: 25 minutes
- Cleanup: 5 minutes

**Total: about 3-3.5 hours**

---

## End-to-end Flow Summary

```
🔵 Flow 1 (client scenario - Step 3-4):
MQTTX Client → MQTT Broker (external) → Data Flow → Fabric RTI

✅ Verify: Messages from MQTTX appear in Fabric

🟢 Flow 2 (integration scenario - Step 5-7 - HTTP Connector):
WMS API → HTTP Connector → MQTT Broker → Data Flow → Fabric RTI

✅ Verify: WMS data pulled by HTTP Connector appears in Fabric
```

---

## Key Resources

- [Azure IoT Operations - HTTP/REST Connector](https://learn.microsoft.com/en-us/azure/iot-operations/discover-manage-assets/howto-use-http-connector)
- [Azure IoT Operations - Data Flows](https://learn.microsoft.com/en-us/azure/iot-operations/connect-to-cloud/overview-dataflow)
- [Microsoft Fabric Real-Time Intelligence](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/overview)
- [MQTTX Documentation](https://docs.mqttx.app/)
- [Kubernetes Deployment Guide](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)

---

## Step 8: Cleanup (5 minutes)

When you no longer need resources, run:

```powershell
# Uninstall Ubuntu WSL
wsl --unregister Ubuntu
```

If you only want to delete Azure resources but keep WSL:

```bash
# Delete resource group (removes all Azure resources)
az group delete --name rg-demo-aio --yes

# Delete Arc connection
az connectedk8s delete --name aiocluster --resource-group rg-demo-aio --yes
```

---

**Last updated**: March 6, 2026
