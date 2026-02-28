# Azure IoT Operations - Hands-On 下半部分 (Part 2)

本文档继续前面的基础，涵盖MQTT Broker设置、Data Flow构建和端到端测试。

**前置条件**: 完成 [Part 1](./hands-on-guide-part1-zh.md) 的 Step 1-6，以及 **Step 7: 等待IoT Operations部署完成** (~10-15分钟，部署状态可在Azure Portal查看)

**步骤编号说明**: 本文从 Step 8 开始，因为 Step 1-6 在 Part 1 中完成，Step 7 为部署验证等待期。

---

## Step 8: MQTT Broker 配置 (30分钟)

### Step 8.1: 理解MQTT Broker架构

Azure IoT Operations MQTT代理支持多个监听器:
- **Default endpoint**: 集群内部通信
- **External endpoint**: 来自集群外部客户端的通信

### Step 8.2: 获取前端服务信息

首先获取前端服务的信息:

```bash
# 查看MQTT代理服务
kubectl get svc -n azure-iot-operations

# 获取LoadBalancer或NodePort的外部IP
kubectl get svc aio-mq-dmqtt-frontend -n azure-iot-operations -o wide
```

### Step 8.3: 使用Azure Portal配置BrokerListener用于外部访问

创建一个新的BrokerListener以支持外部连接:

1. 在Azure门户中，导航到您的IoT Operations实例
2. 在左侧菜单的**组件**下，选择**MQTT Broker**
3. 选择**MQTT broker listener for LoadBalancer** > **Create**
4. 输入基本配置:
   - **Name**: 输入listener名称，例如 `loadbalancer-listener`
   - **Service name**: 留空（将使用listener名称作为服务名称）
   - **Service type**: 已选择 **LoadBalancer**

5. 在**Ports**下，配置第一个端口（用于测试）:
   - **Port**: 输入 **1883**
   - **Authentication**: 选择 **None**
   - **Authorization**: 选择 **None**
   - **Protocol**: 选择 **MQTT**
   - **TLS**: 不添加

   > **重要提示**: 此配置仅用于测试。生产环境中必须启用TLS和身份验证。

6. 选择**Add port entry**添加第二个端口（生产配置）:
   - **Port**: 输入 **8883**
   - **Authentication**: 选择 **default**
   - **Authorization**: 选择 **None**
   - **Protocol**: 选择 **MQTT**
   - **TLS**: 选择 **Add**

7. 在**TLS configuration**窗格中，输入以下设置:
   
   **必需参数**:
   - **TLS mode**: 选择 **Automatic** (使用cert-manager自动管理证书)
   - **Issuer name**: 输入 `azure-iot-operations-aio-certificate-issuer`
   - **Issuer kind**: 选择 **ClusterIssuer**
   
   **可选参数** (测试环境可保持默认):
   - **Issuer group**: 默认 `cert-manager.io`
   - **Private key algorithm**: 默认 `Ec256` (椭圆曲线加密)
   - **Private key rotation policy**: 默认 `Always`
   - **DNS names**: 可选，添加证书的DNS主题备用名称
   - **IP addresses**: 可选，添加证书的IP主题备用名称
   - **Duration**: 证书有效期，默认90天
   - **Renew before**: 证书续期时间
   
   对于测试环境，保持其他设置为默认值，然后选择 **Apply**
   
   > **说明**: Automatic模式会使用Azure IoT Operations自带的证书颁发者自动生成和管理TLS证书。生产环境建议配置自定义的证书颁发者。

8. 选择**Create listener**完成创建

### Step 8.4: 获取MQTT代理的访问端点

创建LoadBalancer类型的listener后，需要获取外部IP地址:

**方法1: 使用Azure Portal**
1. 在MQTT Broker页面，查看新创建的listener
2. 记下分配的外部端点信息

**方法2: 使用kubectl命令**
```bash
# 获取LoadBalancer服务的外部IP
kubectl get svc -n azure-iot-operations

# 查找您的listener服务并记下EXTERNAL-IP
# 连接地址为: <EXTERNAL-IP>:1883 或 <EXTERNAL-IP>:8883
```

记下MQTT代理的端点信息，例如: `<external-ip>:1883` (测试用) 或 `<external-ip>:8883` (生产用，带TLS)

---

## Step 9: 创建Microsoft Fabric Real-Time Intelligence数据源 (25分钟)

### Step 9.1: 访问Microsoft Fabric

1. 登录 [https://fabric.microsoft.com](https://fabric.microsoft.com)

2. 创建或选择一个Workspace

3. 创建一个新的**Real-Time Intelligence**项目

### Step 9.2: 创建事件流(Eventstream)

1. 在Real-Time Intelligence中选择 **New** → **Eventstream**

2. 为事件流命名（例如: `aio-eventstream`）

3. 设置完毕后，进入事件流编辑页面

### Step 9.3: 添加自定义应用程序源

1. 在事件流中，选择 **New source** → **Custom App**

2. 在Custom App配置中:
   - 给源命名（例如: `mqtt-client-source` 或 `api-puller-source`）
   - 记下提供的连接字符串和密钥信息

3. 验证源已连接

**参考**: [Add a Custom Endpoint or Custom App Source to an Eventstream - Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/add-source-custom-app?pivots=basic-features#add-custom-endpoint-data-as-a-source)

### Step 9.4: 创建数据源端点

在Fabric中记录以下信息供之后使用:
- Event Hub兼容端点
- 共享访问密钥
- 事件流名称

---

## Step 10: 配置第一个数据流 - MQTT客户端到Fabric (25分钟)

### Step 10.1: 理解数据流架构 - 流程1

```
┌──────────────┐     ┌──────────────┐     ┌────────────┐
│  MQTT Client │────→│  MQTT Broker │────→│ Fabric RTI │
│   (MQTTX)    │     │   Default    │     │ Eventstream│
│              │     │   Endpoint   │     │            │
└──────────────┘     └──────────────┘     └────────────┘
                         (No Transform)
```

### Step 10.2: 创建数据流端点 - Fabric RTI

在Azure IoT Operations门户中创建数据流端点:

1. 登录 [IoT Operations experience](https://iotoperations.azure.com/)

2. 选择你的实例

3. 导航到 **Data Endpoints** 或 **Data Flows**

4. 点击 **Create new endpoint** 或 **Add endpoint**

5. 配置新端点:
   - **Name**: `fabric-rti-endpoint`
   - **Type**: `Azure Event Hubs`
   - **Authentication**: 选择 **Access Key**
   - **Event Hub Name**: 从Fabric复制 (参考下方"获取Fabric Event Hub信息")
   - **Event Hub Namespace**: 从Fabric复制
   - **Shared Access Key Name**: 从Fabric复制
   - **Shared Access Key**: 从Fabric复制

   > **如何获取Fabric Event Hub信息**:
   > 1. 回到Fabric Real-Time Intelligence
   > 2. 打开之前创建的Eventstream
   > 3. 选择 **Custom App** 源
   > 4. 点击 **Connection details** 查看完整连接字符串
   > 5. 从连接字符串中提取: 事件中心名称、命名空间、访问密钥等信息

6. 点击 **Create** 或 **Apply**

### Step 10.3: 创建数据流 - MQTT到Fabric

1. 在Data Flows或Pipeline页面，点击 **Create new** 或 **Add pipeline**

2. 配置数据流:
   - **Source**: Select **MQTT Broker** → **Default Endpoint**
   - **Topic**: 例如 `sensors/temperature` 或 `#`（订阅所有主题）
   - **Transform**: None（不进行数据转换）
   - **Destination**: Select **fabric-rti-endpoint** (之前创建的Fabric终点)

3. 点击 **Create** 或 **Publish**

### Step 10.4: 验证数据流配置

```bash
# 查看数据流状态
kubectl get dataflows -n azure-iot-operations

# 获取详细信息
kubectl describe dataflow -n azure-iot-operations
```

---

## Step 11: 使用MQTTX进行测试 - 流程1 (25分钟)

### Step 11.1: 安装MQTTX客户端

1. 下载 [MQTTX - Open source MQTT Client](https://mqttx.app/)

2. 安装该工具

### Step 11.2: 配置MQTTX连接

1. 打开MQTTX

2. 创建新连接:
   - **Name**: `AIO-Cluster`
   - **Host**: 使用Step 8.4中记录的MQTT代理端点IP/域名
   - **Port**: `1883` (或配置的端口)
   - **Protocol**: `mqtt://`
   - **Client ID**: `mqttx-client-test`
   - **Username**: (如果需要身份验证)
   - **Password**: (如果需要身份验证)

3. 点击 **Connect**

### Step 11.3: 发布测试消息

1. 在MQTTX中，进入 **Publish** 标签

2. 配置发布:
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

3. 点击 **Publish** 按钮

4. 重复发布多条消息，间隔几秒

### Step 11.4: 验证Fabric中的数据

1. 回到Fabric Real-Time Intelligence

2. 在Eventstream中查看数据:
   - 查看 **Data preview** 或消息日志
   - 验证收到的JSON对象

3. 如果看到数据，说明流程1测试成功！

**预期结果**: 在Fabric中应该看到通过MQTT发送的消息数据。

---

## Step 12: 使用HTTP Connector从REST API拉取数据 (30分钟)

### Step 12.1: 理解HTTP Connector的作用

Azure IoT Operations内置的HTTP/REST Connector可以:
- 定期从WMS系统(或其他REST API)拉取库存数据
- 自动将数据转换为MQTT消息
- 发送到MQTT代理，无需编写自定义代码

相比于构建容器镜像，使用connector更简单快捷，且内置支持认证、数据转换等功能。

### Step 12.2: 模拟WMS API (可选但推荐)

如果还没有实际的WMS系统，需要先创建一个简单的模拟API进行测试。这样才能在后续步骤中有数据可以拉取:

```python
# mock_wms_api.py (可选，仅用于测试)
from flask import Flask, jsonify
import random
from datetime import datetime

app = Flask(__name__)

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    """模拟库存数据API"""
    inventory = []
    for i in range(1, 4):
        inventory.append({
            "item_id": f"ITEM-{i:03d}",
            "name": f"Product {i}",
            "quantity": random.randint(10, 100),
            "last_updated": datetime.now().isoformat()
        })
    return jsonify(inventory)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

运行模拟API:
```bash
# 安装Flask
pip install flask

# 运行模拟API服务器
python mock_wms_api.py

# 测试API是否工作
curl http://localhost:8080/api/inventory
```

> **说明**: 此模拟API在localhost:8080上运行。如果HTTP Connector和此API不在同一网络，需要调整IP/域名以便connector可以访问。

### Step 12.3: 部署HTTP Connector模板

首先，在Azure IoT Operations中部署HTTP/REST connector模板:

1. 在Azure门户，导航到您的IoT Operations实例
2. 选择 **Connector templates**
3. 点击 **Create a connector template**
4. 选择以下配置:
   - **Connector type**: `HTTP/REST`
   - **Name**: `http-connector` (或自定义名称)
5. 在后续向导中按默认值继续，最后点击 **Create**

> **说明**: 此步骤仅需执行一次，connector模板将被添加到您的IoT Operations实例中。

### Step 12.4: 使用Operations Experience创建设备

1. 登录 [IoT Operations Experience](https://iotoperations.azure.com/)
2. 选择您的实例
3. 在左侧导航中选择 **Devices**，点击 **Create new**
4. 输入设备名称，例如 `wms-api-device`
5. 在 **Microsoft.Http** 下选择 **New** 添加HTTP端点
6. 配置HTTP端点:
   - **Endpoint name**: `wms-endpoint`
   - **Endpoint URL**: 根据您的设置选择：
     - **本地测试**: `http://localhost:8080/api/inventory` (如果HTTP Connector和模拟API在同一主机)
     - **集群内**: `http://wms-system:8080/api/inventory` (如果WMS系统已部署到集群)
     - **远程API**: `http://<wms-server-ip>:8080/api/inventory` (生产环境)
   - **Authentication mode**: 
     - `Anonymous` (如果API无需认证，仅用于测试)
     - `Username password` (如需用户名/密码认证)
     - `X509 certificate` (如需证书认证)

   ![HTTP Endpoint Configuration](https://learn.microsoft.com/en-us/azure/iot-operations/discover-manage-assets/media/howto-use-http-connector/add-http-connector-endpoint.png)

7. 点击 **Apply** 保存端点配置
8. 点击 **Next** 继续，在后续步骤中可添加自定义属性
9. 最后点击 **Create** 完成设备创建

### Step 12.5: 创建资产和数据集

1. 在 **Assets** 部分选择 **Create asset**
2. 选择刚创建的HTTP端点 `wms-endpoint`
3. 输入资产名称，例如 `wms-inventory-asset`
4. 点击 **Next** 继续
5. **创建数据集** - 点击 **Create dataset** 添加数据集:
   - **Dataset name**: `inventory-data`
   - **Data source**: `/inventory` (REST API路径)
   - **Sampling interval**: `30` (每30秒拉取一次)
   - **Destination**: `wms/inventory/data` (MQTT主题)
   - **Transform**: 留空（暂不使用数据转换，如需转换可使用WASM模块）

   ![Dataset Configuration](https://learn.microsoft.com/en-us/azure/iot-operations/discover-manage-assets/media/howto-use-http-connector/create-dataset.png)

6. 点击 **Create** 创建数据集
7. 在Review页面，检查配置后点击 **Create** 完成资产创建

### Step 12.6: 验证数据流

等待几分钟后，HTTP Connector开始定期拉取数据:

```bash
# 查看连接器Pod状态
kubectl get pods -n azure-iot-operations | grep http-connector

# 查看HTTP连接器日志
kubectl logs -n azure-iot-operations -l app=http-connector

# 订阅MQTT主题验证数据
mosquitto_sub -h <MQTT_BROKER_IP> -p 1883 -t "wms/inventory/#"
```

**预期结果**: 每30秒应该看到来自WMS API的库存数据消息。

---

## Step 13: 配置第二个数据流 - HTTP Connector到Fabric (35分钟)

### Step 13.1: 理解数据流架构 - 流程2

```
┌──────────────┐     ┌──────────────┐     ┌────────────┐
│  WMS System  │     │   HTTP/REST  │     │ MQTT Broker│     ┌────────────┐
│   REST API   │────→│   Connector  │────→│ (MQTT      │────→│ Fabric RTI │
│              │     │  (Built-in)  │     │  topics)   │     │ Eventstream│
└──────────────┘     └──────────────┘     └────────────┘     └────────────┘
```

### Step 13.2: 创建HTTP Connector数据到Fabric的数据流

HTTP Connector已经将数据发送到MQTT主题 `wms/inventory/data`。现在需要创建数据流将这些数据转发到Fabric:

1. 登录 [IoT Operations Experience](https://iotoperations.azure.com/)

2. 导航到 **Data Flows**

3. 点击 **Create new** 或 **Add pipeline**

4. 配置数据流2:
   - **Name**: `http-connector-to-fabric`
   - **Source**: Select **MQTT Broker** → **Default Endpoint**
   - **Topic**: `wms/inventory/#` (订阅所有WMS库存主题)
   - **Transform**: None (暂不转换，或可添加WASM模块进行数据转换)
   - **Destination**: Select **fabric-rti-endpoint** (之前创建的Fabric端点)

5. 点击 **Create** 或 **Publish** 完成配置

---

## Step 14: 测试端到端流程2 - HTTP Connector (25分钟)

### Step 14.1: 验证模拟WMS API是否运行

确认您在Step 12.2中启动的模拟API仍在运行:

```bash
# 测试API是否仍然可访问
curl http://localhost:8080/api/inventory

# 预期看到库存数据的JSON响应
```

如果需要重新启动API:
```bash
python mock_wms_api.py
```

### Step 14.2: 验证HTTP Connector状态

HTTP Connector应该已经开始定期拉取WMS API数据:

```bash
# 查看HTTP Connector Pod状态
kubectl get pods -n azure-iot-operations -l app=http-connector

# 查看连接器日志
kubectl logs -n azure-iot-operations -l app=http-connector -f

# 预期看到connector定期拉取数据的信息
```

### Step 14.3: 使用MQTTX订阅WMS数据

1. 打开MQTTX (之前连接仍然活跃)

2. 在 **Subscribe** 标签中:
   - **Topic**: `wms/inventory/#`
   - **QoS**: 1

3. 点击 **Subscribe**

4. 应该每30秒看到来自HTTP Connector的库存数据消息 (消息格式为JSON)

### Step 14.4: 验证Fabric中的WMS数据

1. 回到Fabric Real-Time Intelligence

2. 在Eventstream中查看:
   - **Data preview** 应该显示来自HTTP Connector的WMS库存数据
   - 这些消息应该有主题 `wms/inventory/data`

3. 确认收到正确的库存数据结构

**预期结果**: HTTP Connector每30秒从WMS API拉取库存数据，经过MQTT Broker转发到Fabric，全过程自动化完成。

---

## Step 15: 监控和故障排除 (20分钟)

### Step 15.1: 监控MQTT代理

```bash
# 查看MQTT代理统计信息
kubectl exec -it -n azure-iot-operations deployment/aio-mq-broker -- \
  mosquitto_sub -h localhost -t '$SYS/#'
```

### Step 15.2: 查看数据流指标

```bash
# 获取数据流状态
kubectl describe dataflow -n azure-iot-operations

# 查看端点连接状态
kubectl get dataendpoint -n azure-iot-operations
```

### Step 15.3: 检查HTTP Connector连接

```bash
# 验证HTTP Connector可以访问WMS API
kubectl run -it --rm debug --image=alpine --restart=Never -- \
  wget -O - http://wms-system:8080/api/inventory
```

### Step 15.4: 常见问题排查

| 问题 | 症状 | 解决方案 |
|------|------|---------|
| HTTP Connector无法拉取数据 | Connector日志显示连接错误 | 检查WMS API地址，确认URL正确且可访问；验证模拟API仍在运行 |
| MQTT中没有数据 | MQTTX订阅主题无消息 | 检查Connector日志和HTTP端点配置；确认HTTP Connector Pod正在运行 |
| Fabric未收到数据 | Eventstream中没有新消息 | 检查数据流配置，验证MQTT源主题正确；确认Fabric Event Hub连接字符串有效 |
| Fabric Event Hub连接失败 | Connector日志显示Event Hub错误 | 验证Event Hub连接字符串是否从Fabric复制正确；检查Event Hub命名空间权限 |
| 数据转换失败 | WASM模块错误 | 检查WASM模块URL是否正确；验证容器仓库凭据配置；查看transform日志 |
| 认证失败 | Connector日志显示401/403错误 | 检查HTTP端点的认证凭据是否正确；验证用户名/密码或证书配置 |

---

## 预计总时间 (下半部分)

- MQTT Broker配置: 30分钟
- Fabric设置: 25分钟
- Step 10: 数据流配置: 25分钟
- MQTTX测试: 25分钟
- HTTP Connector配置: 30分钟
- Step 13: 第二个数据流配置: 35分钟
- 端到端测试: 25分钟
- 监控和故障排除: 20分钟
- 清理: 5分钟

**下半部分总计: 约3.5-4小时** (相比API Puller方式节省了约1小时)

---

## 完整端到端流程总结

```
🔵 数据流1 (客户端场景 - Step 11):
MQTTX Client → MQTT Broker (external) → Data Flow → Fabric RTI

✅ 验证: 通过MQTTX发送的消息出现在Fabric中

🟢 数据流2 (集成场景 - Step 12-14 - 使用HTTP Connector):
WMS API → HTTP Connector → MQTT Broker → Data Flow → Fabric RTI

✅ 验证: 通过HTTP Connector自动拉取的WMS数据出现在Fabric中
```

---

## 关键资源链接

- [Azure IoT Operations - HTTP/REST Connector](https://learn.microsoft.com/en-us/azure/iot-operations/discover-manage-assets/howto-use-http-connector)
- [Azure IoT Operations - Data Flows](https://learn.microsoft.com/en-us/azure/iot-operations/connect-to-cloud/overview-dataflow)
- [Microsoft Fabric Real-Time Intelligence](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/overview)
- [MQTTX Documentation](https://docs.mqttx.app/)
- [Kubernetes Deployment Guide](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)

---

## Step 16: 清理 (5分钟)

当不再需要资源时，运行以下命令清理环境:

```bash
# 卸载Ubuntu WSL
wsl --unregister Ubuntu
```

如果只想删除Azure资源而保留WSL:

```bash
# 删除资源组（删除所有Azure资源）
az group delete --name rg-demo-aio-eastus --yes

# 删除Arc连接
az connectedk8s delete --name aiocluster --resource-group rg-demo-aio-eastus --yes
```

---

**最后更新**: 2026年2月28日
