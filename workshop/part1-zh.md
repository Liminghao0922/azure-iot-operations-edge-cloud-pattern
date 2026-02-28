# Azure IoT Operations - Hands-On Step by Step Guide

本指南将带你完整部署一个Azure IoT Operations实例到本地Kubernetes集群。

---

## Step 1: 环境准备 (30分钟)

### Step 1.1: 安装和配置WSL2

**目标**: 为Ubuntu运行环境做准备

```powershell
# 更新WSL2到最新版本
wsl --update

# 检查版本
wsl --version

# 创建WSL配置文件以启用DNS隧道
@"
[wsl2]
dnsTunneling=true
"@ | Set-Content -Path $HOME\.wslconfig
```

### Step 1.2: 安装Ubuntu

```powershell
wsl --install Ubuntu
```

### Step 1.3: 创建项目目录并在VS Code中打开

```bash
# 在Ubuntu终端中运行
mkdir -p projects/aiodemo
code projects/aiodemo
```

### Step 1.4: 安装必要的工具

#### 安装Azure CLI

```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

#### 安装Kubernetes工具链

**1. 安装connectedk8s扩展:**
```bash
az extension add --upgrade --name connectedk8s
```

**2. 安装kubectl (通过K3s自动安装)**

**3. 安装Helm (可选)**

此步为可选。对于基本的Azure IoT Operations测试部署不是一必需的。如果需要，会使用Helm来安装定制Chart。

如不需要，可跳过此部分直接进行第下一步。

如果需要安装：
```bash
sudo apt-get install curl gpg apt-transport-https --yes

curl -fsSL https://packages.buildkite.com/helm-linux/helm-debian/gpgkey | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null

echo "deb [signed-by=/usr/share/keyrings/helm.gpg] https://packages.buildkite.com/helm-linux/helm-debian/any/ any main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list

sudo apt-get update
sudo apt-get install helm
```

#### 安装VS Code Kubernetes扩展

在VS Code中安装: [Kubernetes - Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=ms-kubernetes-tools.vscode-kubernetes-tools)

### Step 1.5: 登录Azure并创建资源组

```bash
# 登录Azure
az login

# 创建资源组
az group create --location eastus --resource-group rg-demo-aio-eastus
```

**验证步骤**: 你应该看到一个JSON响应，显示资源组已创建。

---

## Step 2: 创建和配置Kubernetes集群 (30分钟)

### Step 2.1: 创建K3s集群

```bash
# 在Ubuntu中运行此命令以创建单节点K3s集群
curl -sfL https://get.k3s.io | sh -
```

### Step 2.2: 配置kubectl访问

```bash
# 创建.kube目录
mkdir ~/.kube

# 配置kubeconfig文件
sudo KUBECONFIG=~/.kube/config:/etc/rancher/k3s/k3s.yaml kubectl config view --flatten > ~/.kube/merged
mv ~/.kube/merged ~/.kube/config
chmod 0600 ~/.kube/config

# 设置环境变量
export KUBECONFIG=~/.kube/config

# 切换到K3s上下文
kubectl config use-context default

# 修复权限
sudo chmod 644 /etc/rancher/k3s/k3s.yaml
```

### Step 2.3: 验证kubectl安装

```bash
kubectl version --client
```

### Step 2.4: 优化系统参数

**增加用户监听限制:**
```bash
echo fs.inotify.max_user_instances=8192 | sudo tee -a /etc/sysctl.conf
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

**增加文件描述符限制:**
```bash
echo fs.file-max = 100000 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Step 2.5: 检查集群状态

```bash
# 查看所有Pod状态
kubectl get pods --all-namespaces
```

**预期结果**: 你应该看到kube-system命名空间中的Pod，状态为Running或Completed。

---

## Step 3: Azure Arc启用 (30分钟)

### Step 3.1: 注册Azure资源提供程序

这些提供程序只需注册一次。

```bash
az provider register -n "Microsoft.ExtendedLocation"
az provider register -n "Microsoft.Kubernetes"
az provider register -n "Microsoft.KubernetesConfiguration"
az provider register -n "Microsoft.IoTOperations"
az provider register -n "Microsoft.DeviceRegistry"
az provider register -n "Microsoft.SecretSyncController"
```

### Step 3.2: Arc启用集群

```bash
az connectedk8s connect \
  --name aiocluster \
  -l eastus \
  --resource-group rg-demo-aio-eastus \
  --enable-oidc-issuer \
  --enable-workload-identity \
  --disable-auto-upgrade
```

**预期结果**: 命令应该成功完成（可能需要几分钟）。

### Step 3.3: 验证Arc代理

```bash
# 查看部署和Pod
kubectl get deployments,pods -n azure-arc

# 验证所有Pod都在Running状态
```

### Step 3.4: 获取OIDC Issuer URL

```bash
# 获取并保存issuer URL（后续步骤需要）
az connectedk8s show \
  --resource-group rg-demo-aio-eastus \
  --name aiocluster \
  --query oidcIssuerProfile.issuerUrl \
  --output tsv
```

**保存这个输出值，你在下一步需要它。**

### Step 3.5: 配置K3s API服务器

配置service account issuer以支持Azure Arc的工作负载身份(此功能需要Step 3.6的自定义位置)。这是使Azure IoT Operations能够在边缘系统上安全运行所必需的:

```bash
# 编辑K3s配置文件
sudo nano /etc/rancher/k3s/config.yaml
```

在文件中添加以下内容（将 `<SERVICE_ACCOUNT_ISSUER>` 替换为上一步获取的URL）:

```yaml
kube-apiserver-arg:
  - service-account-issuer=<SERVICE_ACCOUNT_ISSUER>
  - service-account-max-token-expiration=24h
```

保存并退出（Ctrl+X, Y, Enter）。

### Step 3.6: 启用自定义位置功能

自定义位置是Azure IoT Operations在边缘系统上运行所必需的。此步骤启用cluster-connect和自定义位置功能，这样Azure可以远程管理您集群上的IoT Operations实例:

```bash
# 获取自定义位置对象ID
export OBJECT_ID=$(az ad sp show --id bc313c14-388c-4e7d-a58e-70017303ee3b --query id -o tsv)

# 启用cluster-connect和自定义位置功能
az connectedk8s enable-features \
  -n aiocluster \
  -g rg-demo-aio-eastus \
  --custom-locations-oid $OBJECT_ID \
  --features cluster-connect custom-locations
```

### Step 3.7: 重启K3s

```bash
sudo systemctl restart k3s
```

**等待1-2分钟让K3s重启完成。**

---

## Step 4: 通过Azure门户部署Azure IoT Operations (30分钟)

### Step 4.1: 在Azure门户中创建IoT Operations实例

1. 访问 [Azure Portal](https://portal.azure.com/)

2. 搜索并选择 **Azure IoT Operations**

3. 点击 **Create**

### Step 4.2: 基础配置 (Basics标签)

填写以下信息:

| 参数 | 值 |
|------|-----|
| **Subscription** | 选择你的订阅 |
| **Resource group** | 选择 `rg-demo-aio-eastus` |
| **Cluster name** | 选择 `aiocluster` |
| **Custom location name** | 保持默认或自定义名称 |
| **Deployment version** | 选择 **1.2 (latest)** |

点击 **Next: Configuration**

### Step 4.3: 配置设置 (Configuration标签)

| 参数 | 说明 |
|------|------|
| **Azure IoT Operations name** | 保持默认或自定义 |
| **MQTT broker configuration** | 保持默认（用于测试） |
| **Data flow profile configuration** | 保持默认（用于测试） |

点击 **Next: Dependency management**

### Step 4.4: 依赖管理 - Schema Registry (Dependency management标签)

**创建新的Schema Registry:**

1. 选择 **Create new**

2. 提供:
   - **Schema registry name**: `schema-registry-aio`
   - **Schema registry namespace**: `schema-ns`

3. 选择 **Select Azure Storage container**

4. 创建或选择存储账户:
   - 类型: **General purpose v2**
   - **Hierarchical namespace**: Enabled
   - **Public network access**: Enabled

5. 创建或选择容器

6. 点击 **Apply**

### Step 4.5: 依赖管理 - Device Registry (续)

**创建新的Azure Device Registry命名空间:**

1. 选择 **Create new**

2. 基础信息:
   - **Subscription**: 选择你的订阅
   - **Resource group**: 选择 `rg-demo-aio-eastus`
   - **Name**: `device-registry-ns`
   - **Region**: `eastus`

3. 点击 **Next** - 标签步骤

4. 点击 **Next** - Review + create

5. 点击 **Create**

6. 返回门户，在列表中选择新创建的命名空间

### Step 4.6: 测试设置

1. 选择 **Test settings** 部署选项（为测试推荐）

2. 点击 **Next: Automation**

---

## Step 5: 运行部署命令 (30-60分钟)

### Step 5.1: 获取部署命令

在 **Automation** 标签中，你会看到需要运行的Azure CLI命令。

### Step 5.2: 逐个运行命令

**命令1: 交互式登录Azure**

```bash
az login
```

**命令2: 安装Azure IoT Operations CLI扩展**

```bash
az extension add --upgrade --name azure-iot-ops
```

**命令3: 初始化集群 (如果需要)**

复制门户中提供的 `az iot ops init` 命令并运行。这个命令可能需要几分钟。

**命令4: 部署Azure IoT Operations**

复制门户中提供的 `az iot ops create` 命令并运行。这个命令也可能需要几分钟。

**注意**: 在运行这些长运行命令时，你可以在终端中看到进度指示器。

### Step 5.3: 等待部署完成

所有命令成功完成后，关闭门户中的 **Install Azure IoT Operations** 向导。

---

## Step 6: 验证部署 (10分钟)

### Step 6.1: 检查部署健康状况

```bash
# 运行健康检查
az iot ops check
```

**预期**: 你会看到一个关于缺失数据流的警告，这是正常的（尚未创建数据流）。

### Step 6.2: 详细健康检查

```bash
# 运行详细检查（级别2）
az iot ops check --detail-level 2
```

这将显示主题映射、QoS和消息路由的配置。

### Step 6.3: 查看已安装的CLI版本

```bash
az iot ops get-versions
```

### Step 6.4: 访问Operations UI

1. 在浏览器中打开: [IoT Operations UI](https://iotoperations.azure.com/)

2. 使用你的Microsoft Entra ID凭据登录

3. 选择 **View unassigned instances** 查看你的部署

**预期**: 你应该看到在前面步骤中创建的集群。

---

## 故障排除

### 问题: "Your device is required to be managed to access your resource"

**解决方案**: 重新运行 `az login` 并确保使用浏览器进行交互式登录。

### 问题: kubectl 命令无法访问集群

**解决方案**: 确保环境变量已正确设置:
```bash
export KUBECONFIG=~/.kube/config
```

### 问题: Arc连接失败

**解决方案**: 
1. 检查你的Azure账户权限（需要Owner或Contributor + User Access Administrator）
2. 确保所有资源提供程序已注册
3. 检查网络连接

### 问题: 部署命令超时

**解决方案**: 这些命令可能需要10-15分钟。如果失败，运行 `az iot ops check` 查看当前状态。

---

## 关键资源链接

- [Azure IoT Operations文档](https://learn.microsoft.com/en-us/azure/iot-operations/)
- [Kubernetes安装指南](https://kubernetes.io/docs/)
- [K3s官方文档](https://docs.k3s.io/)
- [Azure Arc文档](https://learn.microsoft.com/en-us/azure/azure-arc/)
- [Azure CLI参考](https://learn.microsoft.com/en-us/cli/azure/)

---

## Step 7: 等待IoT Operations部署完成

完成Step 6的验证后，Azure IoT Operations集群已基本就绪。此时应该在Azure Portal中观察部署状态，确保所有组件正常启动（通常需要10-15分钟）。

---

## 预计总时间

- 环境准备 (Step 1): 30分钟
- Kubernetes集群创建 (Step 2): 30分钟
- Azure Arc启用 (Step 3): 30分钟
- 通过门户部署 (Step 4): 30分钟
- 运行部署命令 (Step 5): 30-60分钟
- 验证 (Step 6): 10分钟
- 部署等待 (Step 7): 10-15分钟

**总计: 约3小时**

---

## 🎉 Part 1 完成！下一步

恭喜！您已成功完成Part 1的所有步骤。现在可以继续 **[Part 2: MQTT和数据流配置](./hands-on-guide-part2-zh.md)**

Part 2 会从 **Step 8** 开始，指导您：
- 配置MQTT Broker和多端口监听
- 集成Microsoft Fabric Real-Time Intelligence
- 部署HTTP Connector从REST API拉取数据
- 进行端到端测试和故障排除

预计耗时: 4.5小时

---

**最后更新**: 2026年2月28日
