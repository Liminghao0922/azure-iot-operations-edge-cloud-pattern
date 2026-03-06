[English](README.md) | [简体中文](README-zh_CN.md) | [日本語](README-ja.md)

---

# Workshop Part 2: MQTT and Data Flow Configuration

> **Production-Ready Reference Implementation for Industrial IoT Edge Computing**

A comprehensive hands-on guide demonstrating how to build and deploy a **data sovereignty-compliant, edge-first IoT architecture** using Azure IoT Operations, MQTT Broker, HTTP Connectors, and Microsoft Fabric Real-Time Intelligence.

[![Azure IoT Operations](https://img.shields.io/badge/Azure-IoT%20Operations-0078D4?logo=microsoft-azure)](https://learn.microsoft.com/azure/iot-operations/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-K3s%201.31-326CE5?logo=kubernetes)](https://k3s.io/)

---

## 📌 About This Workshop

This workshop provides a **step-by-step, production-grade hands-on guide** for building and deploying industrial IoT solutions with focus on:

- **Comply with data residency regulations** (GDPR, CCPA, industry-specific policies)
- **Integrate diverse data sources** (MQTT devices, REST APIs)
- **Enable real-time analytics** via Microsoft Fabric
- **Support offline operation** with local message buffering and automatic recovery

### What You'll Build

By completing this workshop, you will deploy:

```
┌─────────────────────────────────────────────┐
│  On-Premises / Edge (Your K3s Cluster)      │
│  ┌───────────────────────────────────────┐  │
│  │ MQTT Broker (Secure, Multi-Listener)   │  │
│  │   ↑         ↑            ↑             │  │
│  │   │         │            │             │  │
│  │ Devices  MQTTX    HTTP Connector       │  │
│  │                   (Polling WMS API)    │  │
│  │                                        │  │
│  │ Data Flows (Transform & Route)        │  │
│  │   ├─ Device Data → Fabric              │  │
│  │   └─ API Data → Fabric                 │  │
│  └───────────────────────────────────────┘  │
│  All production data stays local ✅         │
└─────────────────────────────────────────────┘
                     │
                     ↓ (Processed data only)
┌─────────────────────────────────────────────┐
│  Azure Cloud (Management & Analytics)       │
│  • Arc Control Plane (cluster management)   │
│  • Fabric Real-Time Intelligence (KQL)      │
│  • Schema Registry (data governance)        │
└─────────────────────────────────────────────┘
```

**Total Workshop Time**: 6.5-7 hours (can be split across multiple sessions)

---

## 🏗️ Azure IoT Operations Architecture Overview

Azure IoT Operations uses an **edge-cloud separation architecture** to achieve the perfect balance between data sovereignty and low-latency processing:

![Azure IoT Operations Architecture](https://learn.microsoft.com/en-us/azure/iot-operations/media/overview-iot-operations/azure-iot-operations-architecture.png)

### Core Components Explained

#### 🔵 **Edge Layer** (On-Premises / Edge Data Center)

Runs on your Kubernetes cluster (K3s/AKS/Arc-enabled):

- **MQTT Broker**

  - Role: Edge message hub
  - Features: Multiple listeners, TLS encryption, authentication/authorization
  - Connectivity: Internal communication (ClusterIP) + External access (LoadBalancer)
  - Capacity: Scales to millions of messages/second
- **HTTP/REST Connector**

  - Role: Third-party API integration
  - Functions: Periodic REST API polling, data transformation, auto-publish to MQTT
  - Supports: Authentication, retry logic, WASM data transformation
  - Use Cases: WMS systems, ERP interfaces, IoT gateway integration
- **OPC UA Asset Discovery (Akri)**

  - Role: Automatic industrial device discovery
  - Functions: Network scanning for OPC UA servers, auto-creating digital twins
  - Benefits: Zero-config asset registration, real-time device status sync
- **Data Flows**

  - Role: Data pipeline orchestration
  - Processing: MQTT → transformation → cloud data services
  - Configuration: Declarative topic mapping with flexible destination support

#### ☁️ **Cloud Management Layer** (Azure Portal)

Azure Portal and Azure Resource Manager provide centralized management:

- **Azure Arc**

  - Role: Hybrid cloud connectivity runtime
  - Functions: Remote cluster management from Azure Portal
  - Authentication: Workload Identity, role-based authentication
- **Device Registry**

  - Role: Device and asset metadata repository
  - Functions: Device tags, configuration templates, device grouping
  - Sync: Synchronizes with edge IoT Operations instances
- **Schema Registry**

  - Role: Data schema version management
  - Storage: Azure Blob Storage-based schema repository
  - Functions: Data serialization, version evolution, backward compatibility

#### 🌊 **Data Flow**

```
Devices/APIs → MQTT Broker → Data Flows → Microsoft Fabric / Event Hubs
                    ↓
             (Optional) Data Transformation (WASM)
                    ↓
             Data Enrichment (Device Registry)
                    ↓
             Cloud Storage/Analytics
```

**Key Characteristics**:

- All real-time processing happens at the edge (MQTT, Data Flow)
- Only processed data goes to the cloud
- Supports offline recovery with local message buffering

---

## 🌍 Data Residency & Data Sovereignty

Azure IoT Operations' innovation lies in **decoupling the management plane from the data plane**, giving enterprises cloud management convenience while ensuring data stays on-premises.

![Data Residency Architecture](https://learn.microsoft.com/en-us/azure/iot-operations/deploy-iot-ops/media/overview-deploy/data-residency.png)

### Three-Layer Separation Model

#### Layer 1: Management Resources

- **Location**: Azure Portal region (e.g., US West)
- **Content**: Resource Manager, IoT Operations instance definitions, configuration metadata
- **Characteristics**: Only for orchestration and governance, no production data
- **Purpose**: Remote control of edge clusters via Azure Portal/CLI

#### Layer 2: Edge Runtime

- **Location**: Enterprise on-premises or edge data center
- **Content**: MQTT Broker, Connectors, Data Flows, all operational workloads
- **Data**: Production-grade IoT data stored completely on-premises
- **Characteristics**: **Fully under customer control**, can run offline

#### Layer 3: Data Destinations

- **Location**: Flexibly chosen based on data residency requirements (e.g., Canada Central)
- **Content**: Databases, data warehouses, data lakes, Fabric Real-Time Intelligence
- **Data Flow**: Sent directly by edge Data Flows, no intermediate WASM plane
- **Examples**:
  - EU customers → Azure EU data centers
  - China operators → Azure China regions
  - US Government → Azure Government

### Why This Design Matters


| Scenario                      | Traditional IoT Issues                  | Azure IoT Ops Solution                            |
| ----------------------------- | --------------------------------------- | ------------------------------------------------- |
| **GDPR Compliance**           | Data forced to specific regions         | Edge processing, only aggregated results to cloud |
| **Low Latency Real-time**     | High cloud round-trip latency           | Edge real-time processing, millisecond response   |
| **Network Cost Optimization** | Three-layer separation wastes bandwidth | Minimize transmission, send only valuable data    |
| **Offline Robustness**        | Fails when disconnected                 | Edge autonomous operation, syncs after recovery   |
| **Data Sensitivity**          | Manufacturing secrets hard to protect   | Core business data never leaves the factory       |

### Real-World Deployment Example

```
┌─────────────────────────────────────────────────────────────┐
│                     Azure Regions                           │
├─────────────────────────┬─────────────────────────────────────┤
│  Management (US West)   │ Data Storage (Canada Central)       │
│  • Portal/CLI           │ • Azure Storage                     │
│  • Arc Control Plane    │ • Fabric Event Hub                  │
│  • Config metadata      │ • Synapse Analytics                 │
└─────────────────────────┴─────────────────────────────────────┘
          ↑                              ↑
          │ (Config Commands)           │ (Processed Data)
          │                             │
┌─────────────────────────────────────────────────────────────┐
│         On-Premises Edge / Data Center                      │
├─────────────────────────────────────────────────────────────┤
│  Kubernetes Cluster (K3s)                                   │
│  ┌──────────────────────────────────────────────────┐     │
│  │ MQTT Broker (Port 1883/8883)                      │     │
│  │ ├─ MQTT Client A (Sensor Device)                 │     │
│  │ ├─ MQTT Client B (Industrial Gateway)            │     │
│  │ └─ HTTP Connector → WMS REST API                 │     │
│  │                                                  │     │
│  │ Data Flows                                       │     │
│  │ ├─ Flow 1: Device Data → Fabric                  │     │
│  │ ├─ Flow 2: API Data → Fabric                     │     │
│  │ └─ (Optional: Data Transformation via WASM)      │     │
│  │                                                  │     │
│  │ Local Storage / Message Queue                    │     │
│  │ (Offline buffering for disconnection resilience) │     │
│  └──────────────────────────────────────────────────┘     │
│                                                             │
│  All production data ⬅️ Stays fully local ✅               │
└─────────────────────────────────────────────────────────────┘
```

### Data Sovereignty Compliance

Azure IoT Operations supports these data sovereignty scenarios:

- ✅ **GDPR (EU)**: Personal data processing in EU data centers
- ✅ **CCPA (California)**: Sensitive data localized storage
- ✅ **Oil & Gas**: Core process data encrypted/aggregated before leaving site
- ✅ **Government Projects**: Unclassified info prohibited from cloud, only classified data uploaded
- ✅ **Offshore Operations**: Edge data always in specified geographic location
- ✅ **Network Isolation**: Devices behind firewalls can connect securely via Arc Gateway

---

## 🚀 Quick Start

### System Requirements


| Resource   | Minimum           | Recommended         |
| ---------- | ----------------- | ------------------- |
| **Memory** | 16 GB RAM         | 32 GB RAM           |
| **CPU**    | 4 vCPUs           | 8 vCPUs             |
| **Disk**   | 50 GB SSD         | 100+ GB SSD         |
| **OS**     | WSL2 Ubuntu 24.04 | Ubuntu Server 24.04 |
| **K8s**    | K3s 1.31.1        | Latest K3s          |

### Network Requirements

To connect to Azure Arc and use Azure IoT Operations, your network must allow the following **outbound** connections:

| Port | Target | Description |
|------|--------|-------------|
| **443** | `*.azure.com` | Azure services connectivity (HTTPS) |
| **443** | `management.azure.com` | Azure Resource Manager |
| **443** | `login.microsoftonline.com` | Azure AD authentication |
| **443** | `mcr.microsoft.com` | Pull Azure Arc agent container images |
| **443** | `*.servicebus.windows.net` | Azure Arc Cluster Connect and Custom Locations (WebSockets required) |
| **443** | `guestnotificationservice.azure.com` | Cluster notification service |
| **80** | `dl.k8s.io` | Kubernetes tools download |

**Firewall Configuration Tips**:
- All connections are **outbound** only
- HTTP/HTTPS proxies are supported
- If using an enterprise proxy, ensure it supports HTTPS/TLS interception
- Detailed documentation: [Azure Arc Kubernetes Network Requirements](https://learn.microsoft.com/en-us/azure/azure-arc/kubernetes/network-requirements)

### Deployment Path

```
┌──────────────────────────────────┐
│   Part 1: Infrastructure (3h)    │
│   ✓ K3s cluster deployment       │
│   ✓ Azure Arc enablement         │
│   ✓ IoT Operations initialization│
└──────────────────┬───────────────┘
                   │
                   ↓
┌──────────────────────────────────┐
│   Part 2: Data Flows (3-3.5h)    │
│   ✓ MQTT Broker security config  │
│   ✓ Fabric integration           │
│   ✓ HTTP Connector integration   │
│   ✓ End-to-end testing & monitor │
└──────────────────┬───────────────┘
                   │
                   ↓
        ✨ Production-Ready System ✨
```

---

## 📖 Documentation Structure

```
workshop/
├── README.md (You are here) ⬅️
├── README-zh_CN.md (中文版)
├── README-ja.md (日本語版)
│
├── Part 1: Environment & Infrastructure Setup (3 hours)
│   ├── part1-en.md (English)
│   ├── part1-zh.md (中文)
│   └── part1-ja.md (日本語)
│       ├── Step 1: WSL2 and Azure CLI preparation
│       ├── Step 2: Kubernetes cluster creation
│       ├── Step 3: Azure Arc enablement
│       ├── Step 4: IoT Operations deployment
│       ├── Step 5: Execute deployment commands
│       └── Step 6: Verify deployment
│
├── Part 2: MQTT and Data Flow Configuration (3-3.5 hours)
│   ├── part2-en.md (English)
│   ├── part2-zh.md (中文)
│   └── part2-ja.md (日本語)
│       ├── Step 1: MQTT Broker configuration
│       ├── Step 2: Microsoft Fabric preparation
│       ├── Step 3: Device data flow configuration
│       ├── Step 4: MQTTX client testing
│       ├── Step 5: HTTP Connector integration
│       ├── Step 6: API data flow configuration
│       ├── Step 7: End-to-end testing
│       └── Step 8: Resource cleanup
│
└── Troubleshooting
    ├── troubleshooting-en.md (English)
    ├── troubleshooting-zh.md (中文)
    └── troubleshooting-ja.md (日本語)
        ├── Monitoring (MQTT Broker, Data Flow, HTTP Connector)
        └── Common Issues & Solutions
```

---

## 💡 Key Learning Points

### Architecture Design

- 🎯 **Edge-Cloud Separation**: Why compute at the edge instead of sending all data to cloud
- 🎯 **Multi-Protocol Support**: How MQTT + HTTP/REST + OPC UA coexist on one platform
- 🎯 **Scalability**: DevOps patterns for scaling from single K3s to thousands of edge nodes

### Production Readiness

- 🎯 **Security**: TLS/mTLS encryption, authentication/authorization, secrets management
- 🎯 **Reliability**: Data persistence, failure recovery, multi-tenant isolation
- 🎯 **Observability**: Monitoring, logging, distributed tracing

### Data Integration

- 🎯 **Multi-Source Data Fusion**: Device sensors + Enterprise system APIs + OPC UA industrial equipment
- 🎯 **Real-Time Analytics**: Streaming data directly into Fabric Real-Time Intelligence
- 🎯 **Data Governance**: Versioned schemas, data validation, lineage tracking

---

## 🎓 Recommended Learning Path

### First-Time with IoT Operations?

1. Read this README for the big picture
2. Complete Part 1 (establish cluster) - 3 hours
3. Complete Part 2 (run a full pipeline) - 3-3.5 hours
4. Deep dive into specific areas as needed

### Already Familiar?

Jump directly to:

- **MQTT Broker Configuration** → Part 2, Step 1
- **Fabric Integration** → Part 2, Steps 2-3
- **HTTP Connector** → Part 2, Steps 5-6
- **Troubleshooting** → troubleshooting-en.md

### Post-Workshop Project Ideas

- [ ]  Connect real devices instead of mock API
- [ ]  Configure production-grade TLS certificates (Let's Encrypt/Enterprise CA)
- [ ]  Implement custom WASM data transformation
- [ ]  Build multi-region/multi-cluster federated architecture

---

## 🌐 Related Resources

- 📚 [Azure IoT Operations Official Docs](https://learn.microsoft.com/en-us/azure/iot-operations/)
- 🎯 [Azure Arc Documentation](https://learn.microsoft.com/en-us/azure/azure-arc/)
- 🔧 [MQTT Broker Reference](https://learn.microsoft.com/en-us/azure/iot-operations/manage-mqtt-broker/overview-mqtt-broker)
- 📊 [Microsoft Fabric Real-Time Intelligence](https://learn.microsoft.com/en-us/fabric/real-time-analytics/)
- 🔐 [Azure IoT Operations Security Best Practices](https://learn.microsoft.com/en-us/azure/iot-operations/deploy-iot-ops/concept-production-guidelines)

---

## 🤝 Contributing and Feedback

Found an issue or have improvement suggestions?

- Submit detailed problem descriptions and reproduction steps
- Suggestions should be as detailed and actionable as possible
- PRs welcome for documentation or code example improvements

---

**Ready to start?** 👉 Begin with [Part 1: Environment Setup](./part1-en.md)

---

<div align="center">

**Azure IoT Operations Hands-On Workshop**

From Edge to Cloud | From Zero to One | From Learning to Production

*Version v1.1 | Updated Early 2026*

</div>
- Circuit breaker patterns


- Circuit breaker patterns---
