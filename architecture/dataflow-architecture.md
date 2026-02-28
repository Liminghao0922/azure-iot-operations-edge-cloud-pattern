# Azure IoT Operations Data Flow Architecture

## Overview

This document explains the complete data flow architecture for Azure IoT Operations, including device data ingestion, API integration, and cloud connectivity.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Microsoft Azure Cloud                        │
├──────────────────────────────┬──────────────────────────────────┤
│  Management Plane            │  Data Plane                       │
│ (Azure Portal/CLI)           │ (Data Destinations)               │
│                              │                                  │
│ • Azure Arc                  │ • Microsoft Fabric Event Hub      │
│ • IoT Operations Portal      │ • Azure Event Hubs                │
│ • Device Registry            │ • Azure Storage (Data Lake)       │
│ • Bicep Deployment           │ • Azure Synapse Analytics         │
└──────────────────────────────┴──────────────────────────────────┘
           ↑                              ↑
           │ (Management Commands)        │ (Data Ingestion)
           │                              │
┌──────────────────────────────────────────────────────────────────┐
│           On-Premises / Edge Computing Environment              │
├──────────────────────────────────────────────────────────────────┤
│                     Kubernetes Cluster (K3s)                    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              MQTT Broker                            │       │
│  │  ┌──────────────────────────────────────────────┐   │       │
│  │  │ Port 1883 (Test)     Port 8883 (Production) │   │       │
│  │  │ No Auth, No TLS      Auth + TLS             │   │       │
│  │  │ (External LoadBalancer Access)              │   │       │
│  │  └──────────────────────────────────────────────┘   │       │
│  │                  ↑                                    │       │
│  │    ┌─────────────┼──────────────┐                   │       │
│  │    │             │              │                   │       │
│  └────┼─────────────┼──────────────┼───────────────────┘       │
│       │             │              │                           │
│   ┌───▼──┐  ┌──────▼──┐   ┌──────▼──┐                         │
│   │ MQTT │  │ MQTT    │   │  HTTP   │                         │
│   │Client│  │ Client  │   │Connector│                         │
│   │  A   │  │  B      │   │         │                         │
│   │      │  │         │   │         │                         │
│   │Device│  │Industrial   │WMS/ERP │                         │
│   │Sensor│  │Gateway  │   │  API    │                         │
│   └──────┘  └─────────┘   └────┬────┘                         │
│                                 │                              │
│                         ┌───────▼──────┐                       │
│                         │ Data Flows   │                       │
│                         └───────┬──────┘                       │
│                                 │                              │
│            ┌────────────────────┴────────────────┐             │
│            │                                     │             │
│      ┌─────▼────┐              ┌────────▼────┐  │             │
│      │Data Flow1│              │ Data Flow 2 │  │             │
│      │MQTT→Cloud               │HTTP→Cloud   │  │             │
│      └─────┬────┘              └────────┬────┘  │             │
│            │                           │       │             │
│            │ (Optional)                │       │             │
│            │ ┌──────────┐              │       │             │
│            ├─┤WASM      ├─┐            │       │             │
│            │ │Transform │ │            │       │             │
│            │ └──────────┘ │            │       │             │
│            │              │            │       │             │
│            │ ┌──────────────────┐      │       │             │
│            ├─┤Data Enrichment   ├─┐    │       │             │
│            │ │(Device Registry) │ │    │       │             │
│            │ └──────────────────┘ │    │       │             │
│            │                      │    │       │             │
│            │ ┌──────────────────┐ │    │       │             │
│            └─┤Event Hub Output  ├─┘    │       │             │
│              └──────────────────┘      │       │             │
│                                        │       │             │
│            ┌───────────────────────────┘       │             │
│            │                                   │             │
│            ▼                                   ▼             │
│  Cloud Endpoint (Event Hub)                                │
│  For Fabric Real-Time Intelligence                        │
│                                                            │
│  📊 All processed data transmitted here                   │
└────────────────────────────────────────────────────────────┘
```

---

## Data Flow Components

### 1. Edge Data Sources

#### MQTT Clients (Devices)
- **Devices A & B**: Physical IoT devices or gateways publishing sensor data
- **Protocol**: MQTT 3.1.1 / 5.0
- **Port**: 1883 (test) or 8883 (production with TLS)
- **Topics**: `sensors/temperature`, `sensors/humidity`, `devices/status`, etc.
- **Data Format**: JSON
- **Frequency**: Real-time streaming

#### HTTP/REST Connector
- **Purpose**: Integrates with enterprise systems (WMS, ERP, MES, etc.)
- **Mechanism**: Periodic polling of REST APIs
- **Default Interval**: 30 seconds (configurable)
- **Supported Auth**: Basic, API Key, OAuth 2.0, mTLS
- **Output**: Publishes to MQTT topics (e.g., `wms/inventory/data`)

### 2. MQTT Broker

**Role**: Central message hub for all edge communications

**Configurations**:
- **Internal Endpoint** (ClusterIP): For in-cluster communication
  - Default: `aio-mq-dmqtt-frontend:1883`
  - Used by data flows, connectors

- **External Endpoint** (LoadBalancer): For external clients
  - Port 1883: Test environment (no auth, no TLS)
  - Port 8883: Production (authentication + TLS with automatic cert management)

**Topic Subscriptions**:
```
sensors/+              # All sensor readings
devices/+              # Device status messages
wms/inventory/+        # WMS API data
api/external/#         # External API data
```

**QoS Levels**:
- QoS 0: Fire-and-forget
- QoS 1: At-least-once delivery (used for data flows)
- QoS 2: Exactly-once delivery (rarely needed)

### 3. Data Flows

#### Data Flow 1: Device Data → Fabric

**Path**: MQTT Broker → Data Flow → Event Hub → Fabric

```
Source Configuration:
├─ Protocol: MQTT
├─ Broker: default (aio-mq-dmqtt-frontend)
├─ Topics:
│  ├─ sensors/temperature
│  ├─ sensors/humidity
│  └─ devices/status
├─ QoS: 1
└─ Source Settings:
   └─ maxInFlightMessages: 100

Transformation (Optional):
├─ Type: WASM
├─ Function: transform_sensor_data
└─ Purpose: Filtering, unit conversion, aggregation

Destination Configuration:
├─ Protocol: Event Hub
├─ Connection: Fabric Real-Time Intelligence
├─ Authentication: Event Hub connection string from Key Vault
└─ Destination Settings:
   ├─ batchSize: 100
   ├─ batchTimeoutMs: 5000
   └─ maxRetries: 3
```

#### Data Flow 2: WMS API Data → Fabric

**Path**: HTTP Connector → MQTT Broker → Data Flow → Event Hub → Fabric

```
Source Configuration:
├─ Protocol: MQTT
├─ Topics:
│  ├─ wms/inventory/data
│  ├─ wms/inventory/low-stock
│  └─ api/external/#
└─ QoS: 1

Transformation (Optional):
├─ Type: WASM
├─ Function: enrich_inventory
└─ Purpose: Add device metadata, validate data quality

Destination Configuration:
├─ Same Event Hub or separate
├─ Authentication: Event Hub key vault secret
└─ Batch Configuration: Same as Flow 1
```

---

## Data Transformation (Optional)

### WASM Transformations

Custom data processing using WebAssembly provides:

1. **Language Support**: C, Rust, AssemblyScript compile to WASM
2. **Execution Model**: Sandboxed, secure, deterministic
3. **Performance**: Near-native speed, minimal overhead

### Example Transformation Use Cases

**1. Sensor Data Normalization**
```rust
// Convert raw sensor values to standard units
pub fn transform_sensor_data(input: &str) -> String {
    // Parse JSON
    // Convert Celsius to Fahrenheit if needed
    // Filter by temperature range
    // Serialize output
}
```

**2. Inventory Enrichment**
```rust
pub fn enrich_inventory(input: &str) -> String {
    // Add device metadata from Device Registry
    // Calculate stock ratios
    // Trigger alerts for low stock
}
```

**3. Data Filtering**
```rust
pub fn filter_high_frequency(input: &str) -> String {
    // Sample data: keep 1 in 10 messages (90% reduction)
    // Maintain moving average
}
```

---

## Data Destinations

### 1. Microsoft Fabric Real-Time Intelligence

**Configuration in Data Flow**:
- **Protocol**: Event Hub
- **Connection**: Event Hub namespace from Azure
- **Authentication**: Managed via Key Vault
- **Data Format**: JSON or Avro (Fabric RTI format)

**Capability**:
- Real-time ingestion of streaming data
- Automatic data warehouse loading
- KQL (Kusto Query Language) for analysis
- Power BI integration for visualizations
- Time-series analytics

### 2. Azure Event Hubs (Alternative)

For scenarios requiring:
- Multi-consumer support
- Kafka protocol support
- Persistent retention > 1 day
- Separate processing pipelines

### 3. Azure Storage (Data Lake)

For scenarios requiring:
- Long-term storage (years)
- Cost-effective archival
- Batch processing via Synapse Analytics
- Data lake governance (Delta format)

---

## Data Residency & Sovereignty

### Key Design Principle: In-Place Processing

```
Raw Data Generated at Edge
        ↓
    [Edge Processing]  ← All real-time computation happens here
        ↓
    Only Processed Data Flows to Cloud
        ↓
    [Cloud Analytics]
```

**Benefits**:
- ✅ Data never leaves premises until explicit aggregation/filtering
- ✅ Reduced network bandwidth (80-90% reduction)
- ✅ GDPR compliant (personal data processed locally)
- ✅ Low latency for real-time response (millisecond-level at edge)
- ✅ Offline resilience (continues operating without cloud connectivity)

### Compliance Scenarios

| Requirement | Implementation |
|------------|----------------|
| **GDPR** | PII processing at edge, aggregate metrics sent to cloud |
| **CCPA** | Sensitive data buffered locally, encrypted in transit |
| **Data Sovereignty** | Event Hub destination in specific Azure region |
| **Network Isolation** | Azure Arc Gateway for firewall-behind scenarios |

---

## Performance Characteristics

### Throughput

| Component | Capacity |
|-----------|----------|
| MQTT Broker | Up to 1M msg/sec (single instance) |
| Data Flow | Limited by destination (Event Hub ~10K msg/sec) |
| HTTP Connector | ~100-1000 requests/sec (polling dependent) |

### Latency

| Path | Typical Latency |
|------|----------------|
| MQTT Pub → Broker | ~5-10ms |
| MQTT → Data Flow → Event Hub | ~50-100ms |
| HTTP Connector Poll → MQTT → Event Hub | ~30-60s (per poll interval) |

### Storage

| Component | Capacity |
|-----------|----------|
| MQTT Message Queue (default) | ~100MB |
| Local Buffering | Host disk (typically 10-100GB) |

---

## Monitoring & Troubleshooting

### Key Metrics to Monitor

```bash
# MQTT Broker health
kubectl get service -n azure-iot-operations aio-mq-dmqtt-frontend

# Data Flow status
kubectl get dataflow -n azure-iot-operations -o wide

# Event Hub connection
az eventhubs namespace list --query "[].name"

# Check data flow metrics
kubectl describe dataflow mqtt-to-fabric -n azure-iot-operations
```

### Common Issues & Resolution

| Issue | Cause | Resolution |
|-------|-------|-----------|
| Data Flow not ingesting | MQTT broker unreachable | Verify broker endpoint, network policies |
| Event Hub connection fails | Invalid connection string | Retrieve from Key Vault, verify in Data Flow config |
| High latency | Broker overload or network congestion | Check CPU/memory usage, reduce message frequency |
| Messages not reaching Fabric | Data Flow destination misconfigured | Verify Event Hub namespace, authentication |

---

## Next Steps

1. **Deploy Bicep Template**: Run `./deploy.sh` to create Azure resources
2. **Configure MQTT Broker**: Apply `mqtt-broker-config.yaml` to cluster
3. **Create Data Flows**: Apply `dataflow-config.yaml` with Event Hub credentials
4. **Test Device Data**: Use `mqtt-client.py` to publish test messages
5. **Verify in Fabric**: Check Eventstream in Microsoft Fabric for incoming data
6. **Integrate APIs**: Deploy HTTP Connector and publish to WMS topics
7. **Monitor & Optimize**: Use kubectl commands to monitor data flows

---

## Related Documentation

- [Azure IoT Operations Data Flows](https://learn.microsoft.com/en-us/azure/iot-operations/connect-to-cloud/overview-dataflow)
- [MQTT Broker Configuration](https://learn.microsoft.com/en-us/azure/iot-operations/manage-mqtt-broker/overview-mqtt-broker)
- [Microsoft Fabric Real-Time Intelligence](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/overview)
- [Event Hub Connection Strings](https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-get-connection-string)
