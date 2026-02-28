# Azure IoT Operations Implementation Guide

## 📋 Generated Files Summary

本项目包含了根据 Azure IoT Operations hands-on guide 生成的完整实现文件。以下是所有生成的文件及其用途。

---

## 📁 File Structure & Purpose

### 1. **Application Code** (`app/src/`)

#### `mqtt_client.py` - MQTT 测试客户端
**用途**: 模拟IoT设备向MQTT Broker发送数据
**特性**:
- 发布传感器数据（温度、湿度）
- 订阅MQTT主题
- 支持TLS/认证
- 命令行界面

**使用示例**:
```bash
# 发布数据
python app/src/mqtt_client.py --host <broker-ip> pub --count 10

# 监听数据
python app/src/mqtt_client.py --host <broker-ip> sub
```

**相关 Guide**: Step 11 - MQTTX客户端测试

---

#### `mock_wms_api.py` - 模拟WMS REST API
**用途**: 模拟企业库存管理系统的REST API
**特性**:
- 提供仓库库存数据
- 多个查询端点
- 库存预警
- 实时库存变化（随机化）

**端点**:
- `GET /api/inventory` - 全部库存
- `GET /api/inventory/<warehouse_id>` - 特定仓库
- `GET /api/inventory/<wh>/low-stock` - 低库存
- `GET /api/inventory/sku/<sku>` - SKU查询

**启动**:
```bash
pip install flask
python app/src/mock_wms_api.py
# 访问: http://localhost:8080/api/inventory
```

**相关 Guide**: Step 12 - HTTP Connector配置

---

#### `requirements.txt` - 依赖包
**包含**:
- `paho-mqtt` - MQTT客户端库
- `flask` - Web框架
- `python-dotenv` - 环境变量
- 其他工具包

**安装**:
```bash
pip install -r app/requirements.txt
```

---

### 2. **Kubernetes Configurations** (`deployment/k8s/`)

#### `mqtt-broker-config.yaml` - MQTT Broker配置
**用途**: 部署和配置MQTT Broker
**包含**:
- BrokerListener配置（外部LoadBalancer访问）
- 端口配置：
  - 1883: 测试（无身份验证、无TLS）
  - 8883: 生产（支持认证、TLS）
- 自动证书管理
- 主题订阅配置

**部署**:
```bash
kubectl apply -f deployment/k8s/mqtt-broker-config.yaml -n azure-iot-operations
```

**验证**:
```bash
kubectl get brokerlistener -n azure-iot-operations
kubectl get svc -n azure-iot-operations | grep listener
```

**相关 Guide**: Step 8 - MQTT Broker配置

---

#### `dataflow-config.yaml` - 数据流配置
**用途**: 定义从MQTT到Azure Event Hub的数据流
**包含**:
- **Data Flow 1**: 设备数据 → Fabric RTI
- **Data Flow 2**: HTTP Connector数据 → Fabric RTI
- 事件中心连接配置
- 数据转换（可选WASM）
- 消息批处理设置

**部署步骤**:
```bash
# 1. 获取Event Hub连接字符串（从Fabric或Key Vault）
# 2. 编辑dataflow-config.yaml，更新Event Hub参数
# 3. 部署配置
kubectl apply -f deployment/k8s/dataflow-config.yaml -n azure-iot-operations
```

**验证**:
```bash
kubectl get dataflow -n azure-iot-operations
kubectl describe dataflow mqtt-to-fabric -n azure-iot-operations
```

**相关 Guide**: Step 10, 13 - 数据流配置

---

#### `apply-configs.sh` - 自动化部署脚本
**用途**: 批量应用所有Kubernetes配置
**功能**:
- 创建命名空间（如需要）
- 应用MQTT Broker配置
- 应用Data Flow配置
- 验证部署状态
- 显示外部端点信息

**使用**:
```bash
chmod +x deployment/k8s/apply-configs.sh
./deployment/k8s/apply-configs.sh azure-iot-operations
```

---

### 3. **Bicep Infrastructure Templates** (`deployment/bicep/`)

#### `main.bicep` - Azure资源IaC模板
**用途**: 通过Infrastructure as Code (IaC)部署所有必需的Azure资源
**部署的资源**:
- Storage Account (Schema Registry用)
- Event Hub Namespace & Event Hub
- IoT Device Registry
- Key Vault (存储连接字符串)
- 诊断设置

**参数**:
```bicep
location = "eastus"
environment = "dev"
resourceGroupPrefix = "rg-aio"
```

**部署**:
```bash
az deployment group create \
  --resource-group rg-demo-aio-eastus \
  --template-file deployment/bicep/main.bicep \
  --parameters location=eastus environment=dev
```

**输出**:
- Storage Account名称
- Event Hub命名空间和名称
- 存储在Key Vault中的连接字符串

**相关 Guide**: Step 4 - 依赖资源管理

---

#### `deploy.sh` - Bicep部署脚本
**用途**: 简化Bicep模板的部署过程
**功能**:
- 前置条件检查（Azure CLI、kubectl）
- Azure登录
- 自动创建资源组
- 执行Bicep部署
- 提取Event Hub连接字符串
- 保存配置到环境文件

**使用**:
```bash
chmod +x deployment/bicep/deploy.sh
./deployment/bicep/deploy.sh dev eastus
```

**输出**:
- `deployment-config.env` - 包含所有部署信息和连接字符串

---

### 4. **Architecture & Documentation** (`architecture/` & `docs/`)

#### `dataflow-architecture.md` - 完整架构文档
**内容**:
- 整体架构图
- 数据流组件说明
- MQTT Broker详解
- Data Flow工作流程
- 数据变换（WASM）说明
- 数据驻留和主权说明
- 性能特性
- 监控指标
- 故障排除表

**详细段落**:
- 3000+ 字详细说明
- 5个架构图解
- 实际使用场景
- 性能数据表

**针对内容**:
- 架构基础知识
- 数据处理流程
- 云集成方案

---

#### `mqtt-broker-setup.md` - MQTT Broker详细指南
**内容**:
- MQTT Broker概述
- 端口配置详解
- 连接测试步骤
- 主题设计最佳实践
- 认证和授权配置
- 监控和健康检查
- TLS证书管理
- 性能调优建议
- 安全最佳实践
- 故障排除表

**实用命令**: 30+ kubectl/MQTT命令

**针对内容**:
- 从Step 8详细展开
- 生产就绪配置

---

### 5. **Workshop & Validation** (`workshop/`)

#### `part1.md` - Part 1: 基础设施准备(英文版)
**内容** (来自 hands-on-guide-part1-zh.md):
- Step 1: 环境准备（WSL2、Azure CLI）
- Step 2: Kubernetes集群创建（K3s）
- Step 3: Azure Arc启用
- Step 4: IoT Operations通过门户部署
- Step 5: 执行部署命令
- Step 6: 验证部署
- Step 7: 等待部署完成

**时长**: 3小时
**输出**: 完全部署的Azure IoT Operations实例

**后继**:
- 需要完成才能开始Step 8
- 创建baseline环境

---

#### `validation-checklist.md` - 部署验证清单
**内容**: 12个阶段的验证检查点
**每个阶段包括**:
- ✓ 步骤验证项
- 预期结果
- 故障排除提示

**阶段**:
1. 环境准备检查
2. Kubernetes集群检查
3. Azure Arc集成检查
4. IoT Operations部署检查
5. MQTT Broker配置检查
6. 数据流设置检查
7. MQTT客户端测试检查
8. Fabric集成检查
9. API集成检查
10. 监控检查
11. 生产就绪检查
12. 清理检查

**使用方法**:
- 打印或在电子设备上打开
- 部署后逐项勾选
- 记录问题和时间戳

---

## 🎯 使用流程

### 流程1: 从零开始部署（推荐）

```
1. 阅读 README.md (此项目根目录)
   ↓
2. 按照 workshop/part1.md 完成基础设施部署
   ├─ Step 1-6: 基础设施 (3小时)
   └─ Step 7: 等待部署 (10-15分钟)
   ↓
3. 执行 deployment/bicep/deploy.sh
   └─ 创建Event Hub和Key Vault
   ↓
4. 应用 deployment/k8s/apply-configs.sh
   ├─ 部署MQTT Broker
   └─ 配置Data Flow
   ↓
5. 使用 app/src/mqtt_client.py 测试
   ├─ 发布测试数据
   └─ 监控Fabric接收
   ↓
6. 运行 app/src/mock_wms_api.py 测试API集成
   ↓
7. 使用 workshop/validation-checklist.md 验证
   └─ 确认所有组件正常work
```

**总时间**: ~7-8小时

---

### 流程2: 现有环境升级

```
1. 检查现有K3s集群和Arc连接
   ↓
2. 确认Azure IoT Operations已部署
   ↓
3. 直接执行:
   - deployment/bicep/deploy.sh (创建Event Hub)
   - deployment/k8s/apply-configs.sh (配置Broker和DataFlow)
   ↓
4. 跳过 hands-on-guide 的基础步骤
   ↓
5. 测试数据流: mqtt_client.py → Fabric
```

**总时间**: ~1小时

---

### 流程3: 只测试特定功能

```
想测试MQTT?
  → 使用 app/src/mqtt_client.py
  → 参考 docs/mqtt-broker-setup.md

想测试API集成?
  → 启动 app/src/mock_wms_api.py
  → 参考 deployment/k8s/dataflow-config.yaml 的Flow 2

想了解架构?
  → 阅读 architecture/dataflow-architecture.md
  → 查看完整数据流图
```

---

## 📚 文件关系图

```
hands-on-guide-part1/part2-zh.md (参考资料)
        ↓
    ├─→ workshop/part1.md (部署步骤)
    ├─→ app/src/ (应用代码)
    ├─→ deployment/k8s/ (K8s配置)
    ├─→ deployment/bicep/ (Azure资源)
    └─→ architecture/ (架构文档)
            ↓
        ├─→ docs/mqtt-broker-setup.md (MQTT指南)
        └─→ workshop/validation-checklist.md (验证清单)
```

---

## 🔑 关键参数

在部署时需要收集/填入的关键信息：

| 参数 | 来源 | 示例 |
|------|------|------|
| `MQTT_BROKER_IP` | kubectl get svc | `20.x.x.x` |
| `EVENT_HUB_NAMESPACE` | Bicep输出 | `aio-eventhub-xxx` |
| `EVENT_HUB_NAME` | Bicep输出 | `aio-events` |
| `EVENT_HUB_CONNECTION_STRING` | Key Vault | `Endpoint=sb://...` |
| `KEY_VAULT_NAME` | Bicep输出 | `kv-aio-dev-xxx` |
| `DEVICE_REGISTRY_ID` | Bicep输出 | `/subscriptions/.../registries/xxx` |

**重点**: Event Hub连接字符串必须填入 `dataflow-config.yaml` 的5处位置

---

## 🚀 快速开始命令

```bash
# 1. 克隆项目并进入目录
cd /path/to/azure-iot-operations-edge-cloud-pattern

# 2. 部署Azure资源
chmod +x deployment/bicep/deploy.sh
./deployment/bicep/deploy.sh dev eastus

# 3. 获取Event Hub连接字符串
EVENT_HUB_CONN=$(az keyvault secret show \
  --vault-name $(grep KEY_VAULT deployment-config.env | cut -d= -f2) \
  --name event-hub-connection-string \
  --query value -o tsv)

# 4. 更新Data Flow配置（编辑dataflow-config.yaml中的5处<event-hub-xxx>）

# 5. 应用K8s配置
chmod +x deployment/k8s/apply-configs.sh
./deployment/k8s/apply-configs.sh azure-iot-operations

# 6. 等待Broker启动（1-2分钟）
kubectl get brokerlistener -n azure-iot-operations -w

# 7. 获取Broker IP
BROKER_IP=$(kubectl get svc loadbalancer-listener \
  -n azure-iot-operations \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)

# 8. 测试MQTT连接
python app/src/mqtt_client.py --host $BROKER_IP pub

# 9. 验证Fabric接收数据
# 登陆 https://fabric.microsoft.com 查看Eventstream
```

---

## 📖 学习路径

### 初学者
```
1. 阅读 README.md (了解完整概况)
2. 通读 architecture/dataflow-architecture.md (理解设计)
3. 逐步执行 workshop/part1.md (构建环境)
4. 运行脚本和应用代码 (动手体验)
5. 参考 docs/mqtt-broker-setup.md (深入某个组件)
```

### 有经验的开发者
```
1. 快速浏览 architecture/dataflow-architecture.md
2. 执行 deployment/bicep/deploy.sh 和 apply-configs.sh
3. 集成到现有项目并定制
```

### DevOps/运维
```
1. 研究 deployment/ 目录下的所有脚本和模板
2. 定制参数和资源大小
3. 集成到CI/CD流程
4. 使用 workshop/validation-checklist.md 验证
```

---

## ✅ 完成信号

成功完成本项目的标志:

- ✅ `kubectl get pods -n azure-iot-operations` 显示所有pods Running
- ✅ MQTT Broker外部IP可访问 (1883和8883端口)
- ✅ `python app/src/mqtt_client.py pub` 成功发布消息
- ✅ Fabric Real-Time Intelligence中看到数据流入
- ✅ `az iot ops check` 显示所有组件Healthy
- ✅ 完成 workshop/validation-checklist.md 所有检查项

---

## 🤝 后续步骤

1. **生产部署** - 配置完整TLS、RBAC、监控告警
2. **扩展功能** - 添加更多connectors、自定义WASM变换
3. **集成现有系统** - 连接真实WMS/ERP系统
4. **高可用性** - 多节点集群、备份策略、灾难恢复
5. **性能优化** - 基于监控数据调整资源

---

**最后更新**: 2026年2月28日
**生成基于**: Azure IoT Operations Hands-On Guide v1.1 (中文版，已优化)
