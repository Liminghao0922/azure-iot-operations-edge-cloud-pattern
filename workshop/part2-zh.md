# # Workshop Part 1: MQTT和数据流配置

本文档继续前面的基础，涵盖MQTT Broker设置、Data Flow构建和端到端测试。

**前置条件**: 完成 [Part 1](./part1-zh.md)

## Step 1: MQTT Broker 配置 (30分钟)

### Step 1.1: 理解MQTT Broker架构

Azure IoT Operations MQTT代理支持多个监听器:

- **Default endpoint**: 集群内部通信
- **External endpoint**: 来自集群外部客户端的通信

### Step 1.2: 获取前端服务信息

首先获取前端服务的信息:

```bash
# 查看MQTT代理服务
kubectl get svc -n azure-iot-operations
```

### Step 1.3: 使用Azure Portal配置BrokerListener用于外部访问

创建一个新的BrokerListener以支持外部连接:

1. 在Azure门户中，导航到您的IoT Operations实例
2. 在左侧菜单的**组件**下，选择**MQTT Broker**
3. 选择**MQTT broker listener for LoadBalancer** > **Create**

   ![MQTT Broker LoadBalancer 创建界面](image/mqtt-broker-loadbalancer-create.png)
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
   >
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
   >
8. 选择**Create listener**完成创建

### Step 1.4: 获取MQTT代理的访问端点

创建LoadBalancer类型的listener后，需要获取外部IP地址:

使用kubectl命令获取LoadBalancer服务的外部IP

```bash
kubectl get svc -n azure-iot-operations
```

查找您的listener服务并记下MQTT代理的端点信息，例如: `<external-ip>:1883` (测试用) 或 `<external-ip>:8883` (生产用，带TLS)

![kubectl 获取服务端点信息](image/service-endpoints-kubectl.png)
----------------------------------------------------------------

## Step 2: 创建 Microsoft Fabric Real-Time Intelligence 数据源 (25分钟)

### Step 2.1: 创建事件流（Event Stream）

1. 登录 [https://fabric.microsoft.com](https://fabric.microsoft.com)
2. 创建或选择一个Workspace
3. 选择 **New Item** →**Eventstream**
   ![Fabric 新建 Eventstream 菜单](image/fabric-new-eventstream.png)
4. 为事件流命名并创建（例如: `aio-eventstream`）
   ![Eventstream 命名配置](image/eventstream-naming.png)
5. 创建完毕后，进入事件流编辑页面

### Step 2.2: 添加自定义终结点

1. 在事件流中，选择 **Add source** → **Custom endpoint**
   ![Eventstream 添加自定义终结点](image/eventstream-add-custom-endpoint.png)
2. 在Custom endpoint配置中:
   - 给源命名（例如: `mqtt-iot-source`）
     ![Custom Endpoint 原始嚊命名](image/custom-endpoint-naming.png)
   - 点击发布 (Publish)
     ![Custom Endpoint 发布配置](image/custom-endpoint-publish.png)

**参考**: [Add a Custom Endpoint or Custom App Source to an Eventstream - Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/add-source-custom-app?pivots=basic-features#add-custom-endpoint-data-as-a-source)

### Step 2.3: 获取与 Kafka 兼容的自定义终结点连接详细信息。

创建自定义终结点源后，在“详细信息”窗格上获取终结点详细信息
![Eventstream 连接详细信息](image/endpoint-connection-details.png)

- Event Hub兼容端点
- 共享访问密钥
- 事件流名称

---

## Step 3: 配置第一个数据流 - MQTT客户端到Fabric (25分钟)

### Step 3.1: 理解数据流架构 - 流程1

```
┌──────────────┐     ┌──────────────┐     ┌────────────┐
│  MQTT Client │────→│  MQTT Broker │────→│ Fabric RTI │
│   (MQTTX)    │     │   Default    │     │ Eventstream│
│              │     │   Endpoint   │     │            │
└──────────────┘     └──────────────┘     └────────────┘
                         (No Transform)
```

### Step 3.2: 创建数据流端点 - Fabric RTI

在Azure IoT Operations门户中创建数据流端点:

1. 创建专门用于 Data Flow 的 Managed Identity

   ```bash
   az identity create \
   --name mi-dataflow-fabric \
   --resource-group rg-demo-aio \
   --location japaneast
   ```
2. 获取 Client ID 和 Tenant ID

   ```bash
   DATAFLOW_MI_CLIENT_ID=$(az identity show \
   --name mi-dataflow-fabric \
   --resource-group rg-demo-aio \
   --query clientId -o tsv)

   TENANT_ID=$(az account show --query tenantId -o tsv)

   echo "Client ID: $DATAFLOW_MI_CLIENT_ID"
   echo "Tenant ID: $TENANT_ID"
   ```
3. 配置 Federated Identity

   ```bash
   # 获取 OIDC Issuer
   OIDC_ISSUER=$(az connectedk8s show \
   --resource-group rg-demo-aio \
   --name aiocluster \
   --query oidcIssuerProfile.issuerUrl \
   --output tsv)

   # 为 Data Flow Service Account 创建联合凭据
   az identity federated-credential create \
   --name "dataflow-fabric-federation" \
   --identity-name mi-dataflow-fabric \
   --resource-group rg-demo-aio \
   --issuer $OIDC_ISSUER \
   --subject system:serviceaccount:azure-iot-operations:aio-dataflow-default \
   --audience api://AzureADTokenExchange
   ```
4. 赋予Managed Identity 访问Fabric的权限。
   ![Fabric managed identity permission](image/fabric-managed-identity-permission.png)
5. 登录 [IoT Operations experience](https://iotoperations.azure.com/)
6. 选择你的实例
7. 导航到 **Data flow endpoints**
8. 新建 **Microsoft Fabric Real-Time Intelligence**
   ![Data Flow Endpoints 创建界面](image/dataflow-endpoint-create-fabric-rti.png)
9. 配置新端点:

- **Name**: `fabric-rti-endpoint`
- **Authentication method**: 选择 **User assigned managed identity**
- **Host**: 从Fabric复制 **Bootstrap server**
  ![Fabric Bootstrap Server 信息](image/fabric-bootstrap-server.png)
- **Client ID**: 从前面的步骤复制
- **Tenant ID**: 从前面的步骤复制

10. 点击  **Apply**
    ![Endpoint 应用配置](image/endpoint-apply.png)

### Step 3.3: 创建数据流 - MQTT到Fabric

1. 在Data Flows页面，点击 **Create new**
   ![Data Flow 创建新流程](image/dataflow-create-new.png)
2. 配置数据流:

   - **Source**: Select **Data flow endpoint** → **Default Endpoint**
   - **Topic**: 例如 `sensors/temperature` 或 `#`（订阅所有主题）
   - **Message Schema**: 点击 **Add** 添加消息架构（重要！）

     > **关键步骤**: 必须配置 Message Schema，否则 Fabric 中会显示空对象 `{}`
     >

     配置 Message Schema:

     1. 点击 **Message Schema** 的 **Add** 按钮
     2. 从下拉列表中选择已有的 Schema，或点击 **Create new** 创建新的 Schema
     3. 如果创建新 Schema，可以使用以下工具生成 Schema：
        - [Schema Generator Helper](https://azure-samples.github.io/explore-iot-operations/schema-gen-helper/) - 根据示例 JSON 自动生成 Schema
        - 输入示例 JSON 消息（如上面的温度传感器数据），工具会生成对应的 Schema
     4. 将生成的 Schema 复制并保存到 Azure IoT Operations Schema Registry
     5. 在 Data Flow 配置中选择该 Schema

     参考文档：[Set Kafka Message Schema](https://learn.microsoft.com/en-us/azure/iot-operations/connect-to-cloud/howto-configure-kafka-endpoint?tabs=portal#set-kafka-message-schema)
   - **Transform**: None（不进行数据转换）
   - **Destination**: Select **fabric-rti-endpoint** (之前创建的Fabric终点)， 设置Topic（从Fabric复制）
     ![Data Flow 配置界面](image/dataflow-configure.png)
3. 点击 **Save** , 配置相关信息，并再次点击 **Save**

   - **Data flow name**:  指定数据流名称，如 **df-sensor-data**
   - **Enable data flow**: 选择 **Yes**
   - **Request data persistence**: 选择 **Yes**
   - **Data flow profile**: 选择 **default**
     ![Data Flow 保存配置](image/dataflow-save-settings.png)

### Step 3.4: 验证数据流配置

```bash
# 查看数据流状态
kubectl get dataflows -n azure-iot-operations

# 获取详细信息
kubectl describe dataflow -n azure-iot-operations
```

---

## Step 4: 使用MQTTX进行测试 - 流程1 (25分钟)

### Step 4.1: 安装MQTTX客户端

1. 下载 [MQTTX - Open source MQTT Client](https://mqttx.app/)
2. 安装该工具

### Step 4.2: 配置MQTTX连接

1. 打开MQTTX
2. 创建新连接:

   - **Name**: `AIO-Cluster`
   - **Host**: 使用之前记录的MQTT代理端点IP/域名
   - **Port**: `1883` (或配置的端口)
   - **Protocol**: `mqtt://`
   - **Client ID**: `mqttx-client-test`
   - **Username**: (如果需要身份验证)
   - **Password**: (如果需要身份验证)
3. 点击 **Connect**

### Step 4.3: 发布测试消息

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

### Step 4.4: 验证Fabric中的数据

1. 回到Fabric Real-Time Intelligence
2. 在Eventstream中查看数据:

   - 查看 **Data preview** 或消息日志
   - 验证收到的JSON对象
3. 如果看到数据，说明流程1测试成功！

**预期结果**: 在Fabric中应该看到通过MQTT发送的消息数据。

**故障排除 - 如果看到空对象 `{}`**:

如果在 Fabric Eventstream 的 Data preview 中看到的是空对象 `{}` 而不是实际的 JSON 数据：

- **原因**: Data Flow 的 Source 配置中缺少 **Message Schema**
- **解决方案**:
  1. 返回 Data Flow 配置页面
  2. 编辑 Source 配置
  3. 添加 **Message Schema**（参考 Step 3.3 中的配置步骤）
  4. 保存并重新发送测试消息
  5. 刷新 Fabric Eventstream 的 Data preview，应该可以看到完整的 JSON 数据

> **说明**: Message Schema 告诉 Data Flow 如何解析 MQTT 消息的 payload。没有 Schema，Data Flow 无法正确解析 JSON 格式，导致 Fabric 接收到空对象。

---

## Step 5: 使用HTTP Connector从REST API拉取数据 (30分钟)

### Step 5.1: 理解HTTP Connector的作用

Azure IoT Operations内置的HTTP/REST Connector可以:

- 定期从WMS系统(或其他REST API)拉取库存数据
- 自动将数据转换为MQTT消息
- 发送到MQTT代理，无需编写自定义代码

相比于构建容器镜像，使用connector更简单快捷，且内置支持认证、数据转换等功能。

### Step 5.2: 部署模拟WMS API (到Kubernetes集群)

为了避免网络问题，我们将模拟WMS API部署为**Kubernetes Deployment和Service**，这样HTTP Connector可以通过集群内部DNS直接访问。

#### 前置条件：安装Docker

在WSL中验证Docker是否已安装：

```bash
docker --version
```

**如果Docker未安装，按以下步骤安装：**

对于Ubuntu WSL，运行以下命令：

```bash
# 更新包管理器
sudo apt-get update

# 安装Docker依赖
sudo apt-get install -y \
  apt-transport-https \
  ca-certificates \
  curl \
  gnupg \
  lsb-release

# 添加Docker官方GPG密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 配置Docker官方仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# 启动Docker服务
sudo service docker start

# 验证安装
docker --version
```

**为当前用户配置Docker权限（可选，避免每次都需要sudo）：**

```bash
# 将当前用户添加到docker组
sudo usermod -aG docker $USER

# 应用新的组成员身份（注销并重新登录，或运行）
newgrp docker

# 验证是否可以不用sudo运行docker
docker ps
```

#### 部署步骤：

1. **构建模拟API的Docker镜像**

   首先，在WSL中进入项目目录：

   ```bash
   cd ~/projects/azure-iot-operations-edge-cloud-pattern
   ```

   使用项目中的 `Dockerfile` 构建Docker镜像（如果没有Dockerfile，参考Step 5.2末尾）：

   ```bash
   # 构建镜像
   docker build -t mock-wms-api:latest -f app/Dockerfile app/

   # 验证镜像
   docker images | grep mock-wms-api
   ```
2. **将镜像导入到K3s**

   K3s使用containerd运行时，需要将Docker镜像导入到K3s中：

   ```bash
   # 将Docker镜像保存为tar文件
   docker save mock-wms-api:latest -o /tmp/mock-wms-api.tar

   # 导入到K3s的containerd（使用k3s ctr命令）
   sudo k3s ctr images import /tmp/mock-wms-api.tar

   # 验证镜像已导入到K3s
   sudo k3s ctr images ls | grep mock-wms-api

   # 清理临时文件
   rm /tmp/mock-wms-api.tar
   ```

   > **说明**: K3s使用containerd作为容器运行时，而不是Docker。Docker构建的镜像需要手动导入到K3s的镜像仓库中。
   >
3. **创建Namespace（如果不存在）**

   首先创建专门的namespace用于部署模拟API：

   ```bash
   # 创建app namespace（如果已存在会提示错误，可忽略）
   kubectl create namespace app

   # 验证namespace
   kubectl get namespace app
   ```
4. **创建Kubernetes Deployment**

   在WSL Terminal中使用YAML创建Deployment（设置imagePullPolicy为Never以使用本地镜像）：

   ```bash
   # 使用YAML创建Deployment
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

   # 验证Deployment
   kubectl get deployment -n app | grep mock-wms-api

   # 查看Pod启动状态（应该从Pending → ContainerCreating → Running）
   kubectl get pods -n app -w
   ```

   > **关键配置**: `imagePullPolicy: Never` 确保Kubernetes只使用本地已导入的镜像，不会尝试从远程仓库拉取。
   >
5. **暴露为Kubernetes Service**

   创建ClusterIP类型的Service，用于内部通信：

   ```bash
   # 创建Service
   kubectl expose deployment mock-wms-api \
     --port=8080 \
     --target-port=8080 \
     --type=ClusterIP \
     -n app

   # 验证Service
   kubectl get svc -n app | grep mock-wms-api

   # 查看Service详细信息
   kubectl describe svc mock-wms-api -n app
   ```
6. **验证模拟API是否工作**

   从集群内部测试API连接：

   ```bash
   # 方法1: 使用curl镜像测试（推荐）
   kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n azure-iot-operations -- \
     curl http://mock-wms-api.app.svc.cluster.local:8080/api/inventory

   # 方法2: 使用busybox测试
   kubectl run -it --rm debug --image=busybox --restart=Never -n azure-iot-operations -- \
     wget -qO- http://mock-wms-api.app.svc.cluster.local:8080/api/inventory
   ```

   预期响应 (JSON格式):

   ```json
   [
     {"item_id": "ITEM-001", "name": "Product 1", "quantity": 45, "last_updated": "2026-03-05T10:30:00.123456"},
     {"item_id": "ITEM-002", "name": "Product 2", "quantity": 78, "last_updated": "2026-03-05T10:30:00.123456"},
     {"item_id": "ITEM-003", "name": "Product 3", "quantity": 32, "last_updated": "2026-03-05T10:30:00.123456"}
   ]
   ```

   > **提示**: 如果Pod创建后立即被删除但未显示输出，可能是镜像拉取中。等待几秒后重试，或使用 `kubectl get pods -n azure-iot-operations -w` 观察Pod状态。
   >
7. **模拟API代码位置**

   - **源代码**: `app/src/mock_wms_api.py`
   - **Namespace**: `app`
   - **服务地址**: `0.0.0.0:8080` (Pod内监听)
   - **API端点**: `/api/inventory` (GET请求)
   - **Kubernetes Service DNS**:
     - 同namespace内访问: `mock-wms-api:8080`
     - 跨namespace访问: `mock-wms-api.app.svc.cluster.local:8080`
   - **返回数据**: 包含3个商品的库存列表（item_id, name, quantity, last_updated）

> **说明**: 模拟API Pod运行在 `app` namespace中。HTTP Connector（运行在 `azure-iot-operations` namespace）需要使用完整的Service DNS名称 `mock-wms-api.app.svc.cluster.local` 进行跨namespace访问。

### Step 5.3: 部署HTTP Connector模板

首先，在Azure IoT Operations中部署HTTP/REST connector模板:

1. 在Azure门户，导航到您的IoT Operations实例
2. 选择 **Connector templates**
3. 点击 **Create a connector template**
   ![Create connector template](image/http-connector-template-create.png)
4. 选择以下配置:

   - **Connector name**: `Azure IoT Operations connector for REST/HTTP`
     ![Select REST HTTP connector template](image/http-connector-template-select.png)
5. 在后续向导中按默认值继续，最后点击 **Create**
   ![Confirm connector template creation](image/http-connector-template-review-create.png)

> **说明**: 此步骤仅需执行一次，connector模板将被添加到您的IoT Operations实例中。

### Step 5.4: 验证模拟API Deployment状态

部署完成后，检查所有组件是否正常运行：

```bash
# 查看Pod状态
kubectl get pods -n app -o wide | grep mock-wms-api

# 查看Pod日志
kubectl logs -n app -l app=mock-wms-api -f

# 查看Service状态
kubectl get svc -n app | grep mock-wms-api
```

**预期状态**:

- Pod: `Running` (1/1 Ready)
- Service: ClusterIP 类型，有内部 IP 地址

### Step 5.5: 使用Operations Experience创建设备

1. 登录 [IoT Operations Experience](https://iotoperations.azure.com/)
2. 选择您的实例
3. 在左侧导航中选择 **Devices**，点击 **Create device** 或者 **Create new** -> **Device**
   ![Create device](image/device-create.png)
4. 输入设备名称，例如 `wms-api-device`
5. 在 **Microsoft.Http** 下选择 **New** 添加HTTP端点
6. 配置HTTP端点:

   - **Endpoint name**: `wms-endpoint`
   - **Endpoint URL**: `http://mock-wms-api.app.svc.cluster.local:8080`
     - 使用完整的Service DNS名称进行跨namespace访问
     - HTTP Connector在 `azure-iot-operations` namespace，模拟API在 `app` namespace
     - 此方式避免了网络隔离问题
   - **Authentication mode**:
     - `Anonymous` (如果API无需认证，仅用于测试)
     - `Username password` (如需用户名/密码认证)
     - `X509 certificate` (如需证书认证)
       ![HTTP endpoint configuration](image/http-endpoint-config.png)

   > **网络说明**: HTTP Connector运行在 `azure-iot-operations` namespace，模拟API运行在 `app` namespace。通过使用完整的Service DNS名称（`mock-wms-api.app.svc.cluster.local`），可以实现跨namespace通信，无需处理宿主机网络问题。
   >
7. 点击 **Save** 保存端点配置
8. 点击 **Next** 继续，在后续步骤中可添加自定义属性
9. 最后点击 **Create** 完成设备创建
   ![Create device confirmation](image/device-create-confirm.png)

### Step 5.6: 创建资产和数据集

1. 在 **Assets** 部分选择 **Create asset** 或者 **Create new** -> **Asset**
   ![Create asset](image/asset-create.png)
2. 选择刚创建的HTTP端点 `wms-endpoint`
3. 输入资产名称，例如 `wms`
   ![Asset name](image/asset-name.png)
4. 点击 **Next** 继续
5. **创建数据集** - 点击 **Create dataset** 添加数据集:

   - **Dataset name**: `inventory`
   - **Data source**: `/api/inventory` (REST API路径)
   - **Sampling interval**: `10000` (每10秒拉取一次，必填)
   - **Destination**: `aio/data/wms/inventory` (MQTT主题)
   - **Transform**: 留空（暂不使用数据转换，如需转换可使用WASM模块）

   > **重要**: 必须设置 **Sampling interval**，否则会触发 `Failed to parse dataset configuration`。
   > ![Dataset configuration](image/dataset-config.png)  （Sampling interval 必填）
   >
6. 点击 **Next**
7. 在Review页面，检查配置后点击 **Create** 完成资产创建
   ![Asset review create](image/asset-review-create.png)

### Step 5.7: 验证数据流

等待几分钟后，HTTP Connector开始定期拉取数据:

```bash
# 查看连接器Pod状态
kubectl get pods -n azure-iot-operations | grep httpconnector

# 查看HTTP连接器日志（查看最新100行）
kubectl logs -n azure-iot-operations $(kubectl get pods -n azure-iot-operations -o name | grep httpconnector) --tail=100

# 实时查看HTTP连接器日志
kubectl logs -n azure-iot-operations $(kubectl get pods -n azure-iot-operations -o name | grep httpconnector) -f

# 查看Asset配置
kubectl get assets.namespaces.deviceregistry.microsoft.com wms  -n azure-iot-operations -o json
```

**预期结果**: 每10秒应该看到来自WMS API的库存数据消息。

---

## Step 6: 配置第二个数据流 - HTTP Connector到Fabric (35分钟)

### Step 6.1: 理解数据流架构 - 流程2

```
┌──────────────┐     ┌──────────────┐     ┌────────────────┐
│  WMS System  │     │   HTTP/REST  │     │ MQTT Broker    │     ┌─────────────────────┐
│   REST API   │────→│   Connector  │────→│ (MQTT topics)  │────→│ Fabric RTI          │
│              │     │  (Built-in)  │     │                │     │ Eventstream (WMS)   │
└──────────────┘     └──────────────┘     └────────────────┘     └─────────────────────┘
```

### Step 6.2: 创建第二个Fabric Event Stream（用于WMS数据）

为了实现数据源隔离和独立管理，我们为WMS数据创建一个独立的Event Stream：

1. 登录 [https://fabric.microsoft.com](https://fabric.microsoft.com)
2. 创建或选择一个Workspace
3. 选择 **New Item** → **Eventstream**
4. 为事件流命名（例如: `aio-wms-eventstream`）
5. 创建完毕后，进入事件流编辑页面
6. 在事件流中，选择 **Add source** → **Custom endpoint**
   - 给源命名（例如: `mqtt-iot-wms`）
   - 点击发布 (Publish)

### Step 6.3: 获取第二个Event Stream的连接详细信息

创建自定义终结点源后，在"详细信息"窗格上获取终结点详细信息：
**Details** -> **Kafka**  -> **Entra ID Authentication**

- Bootstrap server
- Topic name

**参考**: [Add a Custom Endpoint to an Eventstream - Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/add-source-custom-app?pivots=basic-features#add-custom-endpoint-data-as-a-source)

### Step 6.4: 创建第二个Data Flow Endpoint - Fabric RTI (用于WMS数据)

在Azure IoT Operations门户中创建第二个数据流端点：

1. 登录 [IoT Operations experience](https://iotoperations.azure.com/)
2. 选择你的实例
3. 导航到 **Data flow endpoints**
4. 新建 **Microsoft Fabric Real-Time Intelligence**
5. 配置新端点:

   - **Name**: `fabric-rti-wms-endpoint`
   - **Authentication method**: 选择 **User assigned managed identity**
   - **Host**: 从新创建的Fabric Event Stream复制 **Bootstrap server**
   - **Client ID**: 使用前面创建的Managed Identity (`mi-dataflow-fabric`) 的Client ID
   - **Tenant ID**: 使用相同的Tenant ID
6. 点击 **Apply**
   ![Fabric RTI endpoint for WMS](image/dataflow-endpoint-wms.png)

> **注意**: 两个Data Flow Endpoint都使用相同的Managed Identity (`mi-dataflow-fabric`)，只是连接到不同的Fabric Event Stream。

### Step 6.5: 创建HTTP Connector数据到Fabric的数据流

HTTP Connector已经将数据发送到MQTT主题 `aio/data/wms/inventory`。现在需要创建数据流将这些数据转发到Fabric：

1. 登录 [IoT Operations Experience](https://iotoperations.azure.com/)
2. 导航到 **Data Flows**
3. 点击 **Create new**
4. 配置数据流2:

   - **Source**: Select **Asset** → 之前步骤创建的Asset，如 **wms**
   - **Source Details**: **Dataset** 之前创建的`inventory`
     ![Dataflow source asset selection](image/dataflow-wms-source-asset.png)
   - **Transform**: None（不进行数据转换）
   - **Destination**: Select **fabric-rti-wms-endpoint** (新创建的WMS专用Fabric终点)
   - 从新创建的WMS Event Stream中复制 Topic 信息
     ![Dataflow destination topic](image/dataflow-wms-destination-topic.png)
5. 点击 **Save** , 配置相关信息，并再次点击 **Save**

   - **Data flow name**:  指定数据流名称，如 **df-wms-inventory**
   - **Enable data flow**: 选择 **Yes**
   - **Request data persistence**: 选择 **Yes**
   - **Data flow profile**: 选择 **default**
     ![Dataflow save settings](image/dataflow-wms-save-settings.png)

## Step 7: 测试端到端流程2 - HTTP Connector (25分钟)

### Step 7.1: 验证Fabric中的WMS数据

1. 回到Fabric Real-Time Intelligence
2. 在Eventstream中查看:

   - **Data preview** 应该显示来自HTTP Connector的WMS库存数据
3. 确认收到正确的库存数据结构

**预期结果**: HTTP Connector每10秒从WMS API拉取库存数据，经过MQTT Broker转发到Fabric，全过程自动化完成。
![Fabric WMS data preview](image/fabric-wms-data-preview.png)
-------------------------------------------------------------

## 预计总时间 (下半部分)

- MQTT Broker配置: 30分钟
- Fabric设置: 25分钟
- 数据流配置（流程1）: 25分钟
- MQTTX测试: 25分钟
- HTTP Connector配置: 30分钟
- 数据流配置（流程2）: 35分钟
- 端到端测试: 25分钟
- 清理: 5分钟

**下半部分总计: 约3-3.5小时**

---

## 完整端到端流程总结

```
🔵 数据流1 (客户端场景 - Step 3-4):
MQTTX Client → MQTT Broker (external) → Data Flow → Fabric RTI

✅ 验证: 通过MQTTX发送的消息出现在Fabric中

🟢 数据流2 (集成场景 - Step 5-7 - 使用HTTP Connector):
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

## Step 8: 清理 (5分钟)

当不再需要资源时，运行以下命令清理环境:

```powershell
# 卸载Ubuntu WSL
wsl --unregister Ubuntu
```

如果只想删除Azure资源而保留WSL:

```bash
# 删除资源组（删除所有Azure资源）
az group delete --name rg-demo-aio --yes

# 删除Arc连接
az connectedk8s delete --name aiocluster --resource-group rg-demo-aio --yes
```

---

**最后更新**: 2026年3月6日
