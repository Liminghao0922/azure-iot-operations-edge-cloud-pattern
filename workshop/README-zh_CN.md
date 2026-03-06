[English](README.md) | [简体中文](README-zh_CN.md) | [日本語](README-ja.md)

---

# Azure IoT Operations 边缘-云端模式

> **工业物联网边缘计算的生产级参考实现**

一个全面的动手指南，演示如何使用 Azure IoT Operations、MQTT Broker、HTTP Connectors 和 Microsoft Fabric Real-Time Intelligence 构建和部署**符合数据主权要求、边缘优先的 IoT 架构**。

[![Azure IoT Operations](https://img.shields.io/badge/Azure-IoT%20Operations-0078D4?logo=microsoft-azure)](https://learn.microsoft.com/azure/iot-operations/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-K3s%201.31-326CE5?logo=kubernetes)](https://k3s.io/)

---

## 📌 本Workshop教程

本研讨会提供**循序渐进、面向生产的实践指南**，用于构建和部署工业物联网解决方案，重点包括：

- **符合数据驻留法规**（GDPR、CCPA、行业特定政策）
- **集成多样化数据源**（MQTT 设备、REST API）
- **通过 Microsoft Fabric 实现实时分析**
- **支持离线操作**，具有本地消息缓冲和自动恢复功能

### 你将构建什么

完成本研讨会后，你将部署：

```
┌─────────────────────────────────────────────┐
│  本地 / 边缘 (你的 K3s 集群)                  │
│  ┌───────────────────────────────────────┐  │
│  │ MQTT Broker (安全、多监听器)            │  │
│  │   ↑         ↑            ↑             │  │
│  │   │         │            │             │  │
│  │ 设备     MQTTX    HTTP Connector       │  │
│  │                   (轮询 WMS API)       │  │
│  │                                        │  │
│  │ Data Flows (转换和路由)                │  │
│  │   ├─ 设备数据 → Fabric                 │  │
│  │   └─ API 数据 → Fabric                 │  │
│  └───────────────────────────────────────┘  │
│  所有生产数据保留在本地 ✅                   │
└─────────────────────────────────────────────┘
                     │
                     ↓ (仅处理后的数据)
┌─────────────────────────────────────────────┐
│  Azure 云端 (管理和分析)                      │
│  • Arc 控制平面 (集群管理)                    │
│  • Fabric Real-Time Intelligence (KQL)      │
│  • Schema Registry (数据治理)               │
└─────────────────────────────────────────────┘
```

**研讨会总时长**：6.5-7 小时（可分多次完成）

---

## 🏗️ Azure IoT Operations 架构概览

Azure IoT Operations采用**边缘-云分离架构**，实现数据主权和低延迟处理的完美平衡：

![Azure IoT Operations Architecture](https://learn.microsoft.com/en-us/azure/iot-operations/media/overview-iot-operations/azure-iot-operations-architecture.png)

### 核心组件解释

#### 🔵 **边缘层** (On-Premises / Edge)

运行在企业本地或边缘数据中心的Kubernetes集群上：

- **MQTT Broker**

  - 角色: 边缘消息中枢
  - 特点: 支持多个监听器、TLS加密、认证授权
  - 连接方式: 内部通信(ClusterIP) + 外部接入(LoadBalancer端口)
  - 处理能力: 可扩展到百万级消息/秒
- **HTTP/REST Connector**

  - 角色: 第三方API集成
  - 功能: 定期轮询REST API、数据格式转换、自动发布到MQTT
  - 支持: 认证、重试、WASM数据转换
  - 场景: WMS系统、ERP接口、IoT网关对接
- **OPC UA Asset Discovery (Akri)**

  - 角色: 工业设备自动发现
  - 功能: 扫描网络中的OPC UA服务器、自动创建数字孪生
  - 优势: 零配置资产注册、实时设备状态同步
- **Data Flows**

  - 角色: 数据管道编排
  - 处理流: MQTT → 数据转换 → 云端数据服务
  - 配置: 声明式主题映射、灵活的目标支持

#### ☁️ **云管理层** (Azure Cloud)

Azure Portal和Azure Resource Manager提供集中式管理和编排：

- **Azure Arc**

  - 角色: 混合云连接运行时
  - 功能: 从Azure Portal远程管理边缘集群
  - 权限: 工作负载身份(Workload Identity)、角色认证
- **Device Registry**

  - 角色: 设备和资产元数据存储库
  - 功能: 设备标签、配置模板、设备分组管理
  - 同步: 与边缘IoT Operations实例同步
- **Schema Registry**

  - 角色: 数据模式版本管理
  - 存储: 基于Azure Blob Storage的模式库
  - 功能: 数据序列化、版本演进、向后兼容

#### 🌊 **数据流向**

```
设备/API → MQTT Broker → Data Flows → Microsoft Fabric / Event Hubs
                ↓
          (可选)数据转换(WASM)
                ↓
          数据丰富(Device Registry)
                ↓
          云端存储/分析
```

**关键特点**:

- 所有实时计算发生在边缘(MQTT、Data Flow)
- 只有经过处理的数据上云
- 支持断网自恢复(local message buffering)

---

## 🌍 数据驻留 & 数据主权

Azure IoT Operations的创新之处在于**解耦管理平面和数据平面**，让企业既能获得云管理便利，又能保证数据不离本地。

![Data Residency Architecture](https://learn.microsoft.com/en-us/azure/iot-operations/deploy-iot-ops/media/overview-deploy/data-residency.png)

### 三层分离模型

#### 第1层: 管理资源 (Management Resources)

- **位置**: Azure Portal所在区域（如US West）
- **内容**: Resource Manager、IoT Operations实例定义、配置元数据
- **特点**: 仅用于编排和监管，不处理生产数据
- **用途**: 通过Azure Portal/CLI远程控制边缘集群

#### 第2层: 边缘运行时 (Edge Runtime)

- **位置**: 企业本地或边缘数据中心
- **内容**: MQTT Broker、Connectors、Data Flows、所有实操工作负载
- **数据**: 生产等级的IoT数据完全存储在本地
- **特点**: **完全在客户控制下**，离线可运行

#### 第3层: 数据目标 (Data Destinations)

- **位置**: 根据企业数据驻留要求灵活选择（如Canada Central）
- **内容**: 数据库、数据仓库、数据湖、Fabric Real-Time Intelligence
- **数据流**: 由边缘的Data Flows直接发送，无需经过WASM平面
- **示例**:
  - 欧盟客户 → Azure EU数据中心
  - 中国运营商 → Azure 中国区域
  - 美国政府 → Azure Government

### 为什么这种设计很重要


| 场景               | 传统IoT平台问题        | Azure IoT Ops方案            |
| ------------------ | ---------------------- | ---------------------------- |
| **GDPR合规**       | 数据被迫上传到特定区域 | 边缘处理，仅汇总结果上云     |
| **低延迟实时反应** | 云端往返高延迟         | 边缘实时处理，毫秒级响应     |
| **网络成本优化**   | 三层分离浪费带宽       | 最小化传输，仅发送有价值数据 |
| **离线鲁棒性**     | 断网即失效             | 边缘自主运行，恢复后同步     |
| **数据敏感性**     | 制造机密难保护         | 核心业务数据永不离厂         |

### 实际部署示例

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
│  │ (Offline buffering, 断网自缓冲)                    │     │
│  └──────────────────────────────────────────────────┘     │
│                                                             │
│  所有生产数据 ⬅️ 完全在本地 ✅                              │
└─────────────────────────────────────────────────────────────┘
```

### 数据主权遵从性

Azure IoT Operations支持以下数据主权场景:

- ✅ **GDPR (欧盟)**: 个人数据处理在EU数据中心
- ✅ **CCPA (加州)**: 敏感数据本地化存储
- ✅ **石油化工**: 核心工艺数据离厂前加密、聚合
- ✅ **政府项目**: 未分类信息禁止云端，只有分类数据上传
- ✅ **离岸运营**: 边缘数据永远在指定地理位置
- ✅ **网络隔离**: Firewall之后的设备可通过Arc Gateway安全连接

---

## 🚀 快速开始

### 系统要求


| 资源     | 最小配置          | 推荐配置            |
| -------- | ----------------- | ------------------- |
| **内存** | 16 GB RAM         | 32 GB RAM           |
| **CPU**  | 4 vCPUs           | 8 vCPUs             |
| **磁盘** | 50 GB SSD         | 100+ GB SSD         |
| **OS**   | WSL2 Ubuntu 24.04 | Ubuntu Server 24.04 |
| **K8s**  | K3s 1.31.1        | Latest K3s          |

### 部署路径

```
┌──────────────────────────────────┐
│   Part 1: 基础设施准备 (3小时)     │
│   ✓ K3s集群部署                  │
│   ✓ Azure Arc启用                │
│   ✓ IoT Operations初始化          │
└──────────────────┬───────────────┘
                   │
                   ↓
┌──────────────────────────────────┐
│   Part 2: 数据流配置 (3-3.5小时)   │
│   ✓ MQTT Broker安全配置           │
│   ✓ Fabric集成                    │
│   ✓ HTTP Connector接入            │
│   ✓ 端到端测试和监控              │
└──────────────────┬───────────────┘
                   │
                   ↓
        ✨ 生产就绪系统 ✨
```

---

## 📖 文档结构

```
workshop/
├── README.md (English version)
├── README-zh_CN.md (你在这里) ⬅️
├── README-ja.md (日本語版)
│
├── Part 1: 环境和基础设施准备 (3小时)
│   ├── part1-en.md (English)
│   ├── part1-zh.md (中文)
│   └── part1-ja.md (日本語)
│       ├── Step 1: WSL2和Azure CLI准备
│       ├── Step 2: Kubernetes集群创建
│       ├── Step 3: Azure Arc启用
│       ├── Step 4: IoT Operations部署
│       ├── Step 5: 执行部署命令
│       └── Step 6: 验证部署
│
├── Part 2: MQTT和数据流配置 (3-3.5小时)
│   ├── part2-en.md (English)
│   ├── part2-zh.md (中文)
│   └── part2-ja.md (日本語)
│       ├── Step 1: MQTT Broker配置
│       ├── Step 2: Microsoft Fabric准备
│       ├── Step 3: 设备数据流配置
│       ├── Step 4: MQTTX客户端测试
│       ├── Step 5: HTTP Connector集成
│       ├── Step 6: API数据流配置
│       ├── Step 7: 端到端测试
│       └── Step 8: 资源清理
│
└── 故障排除
  ├── troubleshooting-en.md (English)
  ├── troubleshooting-zh.md (中文)
  └── troubleshooting-ja.md (日本語)
    ├── 监控 (MQTT Broker, Data Flow, HTTP Connector)
    └── 常见问题和解决方案
```

---

## 💡 关键学习要点

### Architecture Design

- 🎯 **边缘-云分离**: 为什么要在边缘做计算而不是所有数据上云
- 🎯 **多协议支持**: MQTT + HTTP/REST + OPC UA如何在一个平台共存
- 🎯 **可扩展性**: 从单机K3s扩展到千级边缘节点的DevOps模式

### Production Readiness

- 🎯 **安全**: TLS/mTLS加密、认证授权、Secrets管理
- 🎯 **可靠性**: 数据持久化、故障恢复、多租户隔离
- 🎯 **可观测性**: Monitoring、logging、distributed tracing

### Data Integration

- 🎯 **多源数据融合**: 设备传感器 + 企业系统API + OPC UA工业设备
- 🎯 **实时分析**: 流数据直接投入Fabric Real-Time Intelligence
- 🎯 **数据治理**: 版本化schema、数据验证、血缘追踪

---

## 🎓 推荐学习顺序

### 第一次接触IoT Operations？

1. 阅读本README了解全景
2. 完整走一遍Part 1 (建立集群) - 3小时
3. 完整走一遍Part 2 (运行一个完整项目) - 3-3.5小时
4. 根据需要深入特定部分

### 已有经验？

直接跳转到：

- **MQTT Broker配置** → Part 2, Step 1
- **Fabric集成** → Part 2, Steps 2-3
- **HTTP Connector** → Part 2, Steps 5-6
- **故障排除** → troubleshooting-zh.md

### 学习完后的自主项目建议

- [ ]  连接真实设备而不是mock API
- [ ]  配置生产级TLS证书(Let's Encrypt/企业CA)
- [ ]  实现自定义WASM数据转换  构建多区域/多集群的联邦架构

---

## 🌐 相关资源

- 📚 [Azure IoT Operations官方文档](https://learn.microsoft.com/zh-cn/azure/iot-operations/)
- 🎯 [Azure Arc文档](https://learn.microsoft.com/zh-cn/azure/azure-arc/)
- 🔧 [MQTT Broker参考](https://learn.microsoft.com/zh-cn/azure/iot-operations/manage-mqtt-broker/overview-mqtt-broker)
- 📊 [Microsoft Fabric Real-Time Intelligence](https://learn.microsoft.com/zh-cn/fabric/real-time-analytics/)
- 🔐 [Azure IoT Operations安全最佳实践](https://learn.microsoft.com/zh-cn/azure/iot-operations/deploy-iot-ops/concept-production-guidelines)

---

## 🤝 贡献和反馈

发现问题或有改进建议？

- 提交具体问题描述和复现步骤
- 建议尽可能详细和可执行
- 欢迎PR改进文档或代码示例

---

**准备好了吗？** 👉 从[Part 1: 环境和基础设施准备](./part1-zh.md)开始你的Azure IoT Operations之旅！

---

<div align="center">

**Azure IoT Operations 动手研讨会**

从边缘到云端 | 从零到一 | 从学到用

*版本 v1.1 | 2026年初更新*

</div>
