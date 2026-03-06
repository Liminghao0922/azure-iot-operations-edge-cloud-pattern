# 故障排除（参考）

适用：监控、日志与常见问题快速定位。

## 监控与日志

### MQTT Broker

```bash
# 查看MQTT代理统计信息
kubectl exec -it -n azure-iot-operations pod/aio-broker-frontend-0 -- \
   mosquitto_sub -h localhost -t '$SYS/#'
```

### Data Flow

```bash
# 获取数据流状态
kubectl describe dataflow -n azure-iot-operations

# 查看端点连接状态
kubectl get dataendpoint -n azure-iot-operations

# 查看所有 dataflow 相关的 pods
kubectl get pods -n azure-iot-operations | grep dataflow

# 查看 dataflow 实时日志（最常用）
kubectl logs -n azure-iot-operations aio-dataflow-default-0 -f

# 查看 dataflow 最近的日志
kubectl logs -n azure-iot-operations aio-dataflow-default-0 --tail=100

# 查看所有 dataflow pods 的日志
kubectl logs -n azure-iot-operations -l app.kubernetes.io/name=aio-dataflow --tail=50

# 查看 dataflow Service Account 配置（用于排查认证问题）
kubectl get sa aio-dataflow -n azure-iot-operations -o yaml

# 检查 dataflow 的详细配置
kubectl get dataflow -n azure-iot-operations -o yaml
```

**常见日志信息解读**:

- `Average msg/min: X/Y/Z` - 消息吞吐量统计
- `AADSTS70025` - Federated Identity Credential 配置错误
- `No matching federated identity record found` - Service Account subject 不匹配
- `Connection refused` - 目标端点无法访问

### HTTP Connector 与 MQTT

```bash
# 查看HTTP Connector的完整日志（诊断MQTT连接问题）
kubectl logs -n azure-iot-operations $(kubectl get pods -n azure-iot-operations -o name | grep httpconnector) --tail=200 | grep -i mqtt

# 检查MQTT Broker Default Endpoint服务是否正常运行
kubectl get svc -n azure-iot-operations | grep aio-broker

# 验证MQTT Broker服务的具体端点信息
kubectl get svc -n azure-iot-operations aio-broker -o yaml

# 从集群内测试MQTT Broker端口（使用busybox调试Pod）
kubectl run -it --rm debug --image=busybox --restart=Never -n azure-iot-operations -- \
   nc -zv aio-broker 18883

# 验证HTTP Connector可以访问WMS API（从azure-iot-operations namespace访问app namespace的服务）
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n azure-iot-operations -- \
  curl http://mock-wms-api.app.svc.cluster.local:8080/api/inventory
```

**快速诊断**:

如果看到 `Failed to connect MQTT session` 错误，按以下顺序诊断：

1. **检查MQTT Broker服务状态**

   ```bash
   kubectl get pods -n azure-iot-operations | grep aio-broker
   kubectl get svc -n azure-iot-operations | grep mqtt
   ```
2. **验证DNS解析是否正常**

   ```bash
   kubectl run -it --rm debug --image=busybox --restart=Never -n azure-iot-operations -- \
     nslookup aio-broker
   ```
3. **检查网络策略是否阻止了连接**

   ```bash
   kubectl get networkpolicies -n azure-iot-operations
   ```
4. **查看MQTT Broker的运行日志**

   ```bash
   kubectl logs -n azure-iot-operations -l app.kubernetes.io/name=aio-broker --tail=100
   ```

## 常见问题

| 问题                       | 症状                                     | 解决方案                                                                                                                                            |
| -------------------------- | ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Fabric显示空对象`{}`       | Data preview中看到`{}` 而非JSON数据      | 在Data Flow Source配置中添加Message Schema（参考Step 3.3）；使用Schema Generator Helper生成schema                                                   |
| Federated Identity认证失败 | 日志显示`AADSTS70025` 或 `AADSTS70021`   | 创建federated credential，确保subject为`system:serviceaccount:azure-iot-operations:aio-dataflow`；验证OIDC issuer                                   |
| Data Flow无法连接Fabric    | 日志显示连接或认证错误                   | 检查Managed Identity的Client ID和Tenant ID；验证Fabric endpoint的bootstrap server地址                                                               |
| HTTP Connector无法连接MQTT | 日志显示`Failed to connect MQTT session` | 检查MQTT Broker服务是否运行：`kubectl get pods -l app.kubernetes.io/name=aio-broker`；验证DNS解析：`nslookup aio-broker`；检查网络策略；必要时重启 `aio-broker-frontend-0` |
| HTTP Connector无法拉取数据 | Connector日志显示连接错误                | 检查WMS API地址，确认URL正确且可访问；验证模拟API仍在运行；确保使用主机IP而非localhost（参考Step 5.4）                                              |
| Dataset配置解析失败        | 日志显示`Failed to parse dataset configuration` | 在门户创建Dataset时必须设置**Sampling interval**，系统会写入`datasetConfiguration`中的`samplingIntervalInMilliseconds`；否则解析失败（可重建Dataset）。 |
| HTTP Endpoint使用localhost | Connector无法连接到宿主机API             | 将localhost替换为宿主机IP地址；使用`ip addr show eth0` 获取IP；Pod内localhost指向Pod自己                                                            |
| MQTT中没有数据             | MQTTX订阅主题无消息                      | 检查Connector日志和HTTP端点配置；确认HTTP Connector Pod正在运行                                                                                     |
| Fabric未收到数据           | Eventstream中没有新消息                  | 检查数据流配置，验证MQTT源主题正确；使用kubectl logs查看dataflow日志                                                                                |
| Fabric Event Hub连接失败   | Connector日志显示Event Hub错误           | 验证Event Hub连接字符串是否从Fabric复制正确；检查Event Hub命名空间权限                                                                              |
| Data Flow吞吐量为0         | 日志显示`Average msg/min: 0/0/0`         | 检查Source topic是否正确；验证MQTT Broker是否收到消息；检查dataflow是否启用                                                                         |
| 数据转换失败               | WASM模块错误                             | 检查WASM模块URL是否正确；验证容器仓库凭据配置；查看transform日志                                                                                    |
| 认证失败                   | Connector日志显示401/403错误             | 检查HTTP端点的认证凭据是否正确；验证用户名/密码或证书配置                                                                                           |
