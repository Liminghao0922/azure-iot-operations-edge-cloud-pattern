# 🚀 快速参考 - 常用命令

快速查找你需要的命令。详细文档请参考 `IMPLEMENTATION_GUIDE.md`。

---

## 📋 完整部署流程

```bash
# 1. 部署Azure资源
cd deployment/bicep
./deploy.sh dev eastus

# 2. 应用Kubernetes配置
cd ../k8s
./apply-configs.sh azure-iot-operations

# 3. 等待Broker启动
kubectl get brokerlistener -n azure-iot-operations -w

# 4. 获取外部IP
kubectl get svc loadbalancer-listener -n azure-iot-operations -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

# 5. 测试数据发布
export BROKER_IP=<上一步得到的IP>
python app/src/mqtt_client.py --host $BROKER_IP pub --count 5
```

---

## 🔍 诊断与检查

```bash
# MQTT Broker状态
kubectl get pods -n azure-iot-operations -l app=mq-broker
kubectl logs -n azure-iot-operations -l app=mq-broker -f

# 数据流状态
kubectl get dataflow -n azure-iot-operations
kubectl describe dataflow mqtt-to-fabric -n azure-iot-operations

# 外部Listener状态
kubectl get brokerlistener -n azure-iot-operations
kubectl describe brokerlistener loadbalancer-listener -n azure-iot-operations

# 所有资源概览
kubectl get all -n azure-iot-operations
```

---

## 📡 MQTT测试命令

```bash
# 发布单条消息
python app/src/mqtt_client.py \
  --host <broker-ip> \
  pub \
  --topic sensors/temperature \
  --temperature 22.5 \
  --count 1

# 连续发布（模拟实时流）
python app/src/mqtt_client.py \
  --host <broker-ip> \
  pub \
  --count 100 \
  --interval 1

# 订阅所有消息
python app/src/mqtt_client.py \
  --host <broker-ip> \
  sub

# 订阅特定主题
python app/src/mqtt_client.py \
  --host <broker-ip> \
  sub \
  --topic "sensors/#"

# 使用TLS和认证连接
python app/src/mqtt_client.py \
  --host <broker-ip> \
  --port 8883 \
  --tls \
  --username <user> \
  --password <pass> \
  pub --count 5
```

---

## 🏭 WMS API测试

```bash
# 启动模拟API
python app/src/mock_wms_api.py
# 访问: http://localhost:8080

# 获取所有库存
curl http://localhost:8080/api/inventory | jq

# 获取特定仓库库存
curl http://localhost:8080/api/inventory/WH-001 | jq

# 获取低库存项目
curl http://localhost:8080/api/inventory/WH-001/low-stock | jq

# 查询SKU跨仓库情况
curl http://localhost:8080/api/inventory/sku/PROD-2024-001 | jq

# 获取系统状态和指标
curl http://localhost:8080/api/status | jq
```

---

## 🔐 密钥和连接字符串

```bash
# 获取Event Hub连接字符串（部署后立即获取）
az keyvault secret show \
  --vault-name <key-vault-name> \
  --name event-hub-connection-string \
  --query value -o tsv

# 保存到环境变量
export EH_CONN_STR=$(az keyvault secret show \
  --vault-name <kv-name> \
  --name event-hub-connection-string \
  --query value -o tsv)

# 使用环境变量更新dataflow配置
sed -i "s|<event-hub-connection-string>|$EH_CONN_STR|g" \
  deployment/k8s/dataflow-config.yaml
```

---

## 📊 实时监控

```bash
# 监控MQTT Broker性能
watch -n 1 'kubectl top pod -n azure-iot-operations -l app=mq-broker'

# 监听MQTT系统主题（需要在Broker上运行）
mosquitto_sub -h localhost -t '$SYS/#' | head -20

# 实时显示MQTT消息（需要mosquitto-clients）
mosquitto_sub -h <broker-ip> -t '#' -v | tee mqtt-messages.log

# 统计每个主题的消息数
mosquitto_sub -h <broker-ip> -t '#' -v | \
  awk -F' ' '{print $1}' | sort | uniq -c | sort -rn
```

---

## 🐛 故障排除

```bash
# 检查IoT Operations整体状态
az iot ops check

# 详细健康检查
az iot ops check --detail-level 2

# 查看部署日志
kubectl get events -n azure-iot-operations --sort-by='.lastTimestamp'

# 检查连接到Arc的K8s集群
az connectedk8s show -n aiocluster -g rg-demo-aio-eastus

# 查看OIDC状态
az connectedk8s show \
  -n aiocluster \
  -g rg-demo-aio-eastus \
  --query oidcIssuerProfile

# 检查mTLS证书
kubectl get certificates -n azure-iot-operations

# 查看证书详情
kubectl describe certificate -n azure-iot-operations <cert-name>

# 检查Event Hub连接
az eventhubs namespace list --query "[].name"
```

---

## 🗑️ 清理资源

```bash
# 删除Kubernetes配置
kubectl delete -f deployment/k8s/mqtt-broker-config.yaml -n azure-iot-operations
kubectl delete -f deployment/k8s/dataflow-config.yaml -n azure-iot-operations

# 删除整个Azure资源组（包含所有资源）
az group delete --name rg-demo-aio-eastus --yes

# 断开Arc连接
az connectedk8s delete --name aiocluster --resource-group rg-demo-aio-eastus --yes

# 卸载WSL Ubuntu（可选）
wsl --unregister Ubuntu
```

---

## 📈 性能测试

```bash
# 发送高频消息（每10ms一条）
for i in {1..1000}; do
  python app/src/mqtt_client.py --host $BROKER_IP pub --count 1 --interval 0 &
  sleep 0.01
done

# 监控Broker资源使用
kubectl top pod -n azure-iot-operations

# 查看消息吞吐量
mosquitto_pub -h $BROKER_IP -t test -m "msg" -c 1000

# 监控Event Hub 入站消息
az eventhubs eventhub stats -n aio-events \
  --namespace-name <ns-name> \
  --resource-group rg-demo-aio-eastus
```

---

## 🎯 验证检查表

```bash
# 完整验证脚本
echo "=== 验证部署 ==="

# 1. 检查Broker
echo "1. MQTT Broker: $(kubectl get pod -n azure-iot-operations -l app=mq-broker --no-headers | wc -l) pods"

# 2. 检查监听器
echo "2. 监听器: $(kubectl get brokerlistener -n azure-iot-operations --no-headers | wc -l) listeners"

# 3. 检查数据流
echo "3. 数据流: $(kubectl get dataflow -n azure-iot-operations --no-headers | wc -l) flows"

# 4. 检查事件中心
echo "4. Event Hub:"
az eventhubs namespace list --query "[].name" -o tsv

# 5. MQTT连接测试
echo "5. MQTT连接测试..."
python app/src/mqtt_client.py --host $(kubectl get svc loadbalancer-listener \
  -n azure-iot-operations -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null) \
  pub --count 1 && echo "✓ 成功" || echo "✗ 失败"

echo "=== 验证完成 ==="
```

---

## 📦 环境设置

```bash
# Python环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r app/requirements.txt

# 设置环境变量
export MQTT_BROKER_HOST=<your-broker-ip>
export MQTT_BROKER_PORT=1883
export EVENT_HUB_NAMESPACE=<your-namespace>
export RESOURCE_GROUP=rg-demo-aio-eastus
```

---

## 🔗 有用的URL和工具

```bash
# 本地Web服务
http://localhost:8080/api/inventory          # Mock WMS API
http://localhost:8080/api/status             # API健康状态

# Azure Portal
https://portal.azure.com                      # Azure门户
# 搜索: IoT Operations

# Microsoft Fabric
https://fabric.microsoft.com                  # Fabric主界面
# 导航到: Real-Time Intelligence → Eventstream

# IoT Operations UI
https://iotoperations.azure.com               # IoT Ops管理界面

# 工具下载
https://mqttx.app/                            # MQTTX客户端
https://www.mosquitto.org/                    # Mosquitto CLI工具
```

---

## ⏱️ 时间参考

| 操作 | 预期时间 |
|------|---------|
| `./deploy.sh dev eastus` | 3-5分钟 |
| `./apply-configs.sh` | 1-2分钟 |
| Broker启动就绪 | 2-3分钟 |
| Event Hub连接活跃 | 1-2分钟 |
| 第一条消息进入Fabric | 5-10秒 |
| 完整部署验证 | 10-15分钟 |

---

## 💡 提示

- **保存BROKER_IP**: `export BROKER_IP=$(kubectl get svc loadbalancer-listener -n azure-iot-operations -o jsonpath='{.status.loadBalancer.ingress[0].ip}')`
- **监视日志**: 在新终端运行 `kubectl logs ... -f` 实时查看
- **不确定什么使用**: 查看 `workshop/validation-checklist.md` 中的错误排查部分
- **想看详情**: 查看 `IMPLEMENTATION_GUIDE.md`
- **需要帮助**: 检查 `docs/mqtt-broker-setup.md` 和 `architecture/dataflow-architecture.md`

---

**最后更新**: 2026年2月28日
