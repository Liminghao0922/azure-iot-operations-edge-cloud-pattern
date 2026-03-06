# トラブルシューティング（参考）

用途：監視、ログ、よくある問題のクイック参照。

## 監視とログ

### MQTT Broker

```bash
# MQTT ブローカー統計を確認
kubectl exec -it -n azure-iot-operations pod/aio-broker-frontend-0 -- \
   mosquitto_sub -h localhost -t '$SYS/#'
```

### Data Flow

```bash
# データフローの状態
kubectl describe dataflow -n azure-iot-operations

# エンドポイント接続状態
kubectl get dataendpoint -n azure-iot-operations

# dataflow 関連 Pod 一覧
kubectl get pods -n azure-iot-operations | grep dataflow

# dataflow ログ（リアルタイム）
kubectl logs -n azure-iot-operations aio-dataflow-default-0 -f

# dataflow 直近ログ
kubectl logs -n azure-iot-operations aio-dataflow-default-0 --tail=100

# dataflow 全 Pod ログ
kubectl logs -n azure-iot-operations -l app.kubernetes.io/name=aio-dataflow --tail=50

# dataflow Service Account（認証確認）
kubectl get sa aio-dataflow -n azure-iot-operations -o yaml

# dataflow 詳細設定
kubectl get dataflow -n azure-iot-operations -o yaml
```

**ログの目安**:

- `Average msg/min: X/Y/Z` - メッセージスループット
- `AADSTS70025` - Federated Identity Credential 設定ミス
- `No matching federated identity record found` - Service Account の subject 不一致
- `Connection refused` - 送信先に到達不可

### HTTP Connector と MQTT

```bash
# HTTP Connector ログ（MQTT 接続診断）
kubectl logs -n azure-iot-operations $(kubectl get pods -n azure-iot-operations -o name | grep httpconnector) --tail=200 | grep -i mqtt

# MQTT Broker Default Endpoint サービス確認
kubectl get svc -n azure-iot-operations | grep aio-broker

# MQTT Broker サービス詳細
kubectl get svc -n azure-iot-operations aio-broker -o yaml

# クラスタ内から MQTT Broker ポートを確認
kubectl run -it --rm debug --image=busybox --restart=Never -n azure-iot-operations -- \
   nc -zv aio-broker 18883

# HTTP Connector が WMS API に到達できるか確認
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n azure-iot-operations -- \
  curl http://mock-wms-api.app.svc.cluster.local:8080/api/inventory
```

**クイック診断**:

`Failed to connect MQTT session` が出る場合、次の順で確認：

1. **MQTT Broker 状態**

   ```bash
   kubectl get pods -n azure-iot-operations | grep aio-broker
   kubectl get svc -n azure-iot-operations | grep mqtt
   ```
2. **DNS 解決**

   ```bash
   kubectl run -it --rm debug --image=busybox --restart=Never -n azure-iot-operations -- \
     nslookup aio-broker
   ```
3. **NetworkPolicy**

   ```bash
   kubectl get networkpolicies -n azure-iot-operations
   ```
4. **MQTT Broker ログ**

   ```bash
   kubectl logs -n azure-iot-operations -l app.kubernetes.io/name=aio-broker --tail=100
   ```

## よくある問題

| 問題 | 症状 | 対処 |
| --- | --- | --- |
| Fabric が `{}` を表示 | Data preview に `{}` だけが出る | Data Flow の Source に Message Schema を追加（Step 3.3 参照）。Schema Generator Helper で schema 作成 |
| Federated Identity 認証失敗 | ログに `AADSTS70025` または `AADSTS70021` | Federated Credential を作成し、subject を `system:serviceaccount:azure-iot-operations:aio-dataflow` に設定。OIDC issuer を確認 |
| Data Flow が Fabric に接続できない | 接続/認証エラーが出る | Managed Identity の Client ID と Tenant ID を確認。Fabric endpoint の bootstrap server を確認 |
| HTTP Connector が MQTT に接続できない | `Failed to connect MQTT session` が出る | MQTT Broker サービス確認：`kubectl get pods -l app.kubernetes.io/name=aio-broker`。DNS 確認：`nslookup aio-broker`。NetworkPolicy を確認。必要なら `aio-broker-frontend-0` を再起動 |
| HTTP Connector がデータを取得できない | Connector ログに接続エラー | WMS API の URL と到達性を確認。mock API が稼働中か確認。localhost は避ける（Step 5.4 参照） |
| Dataset 設定の解析失敗 | `Failed to parse dataset configuration` | Dataset 作成時に **Sampling interval** を必須設定（`samplingIntervalInMilliseconds` が書き込まれる）。未設定なら再作成 |
| HTTP Endpoint が localhost | Connector がホスト API に接続不可 | localhost をホスト IP に変更。`ip addr show eth0` で IP を取得。Pod 内の localhost は自分自身を指す |
| MQTT にデータが来ない | MQTTX の購読でメッセージがない | Connector ログと HTTP 端点設定を確認。HTTP Connector Pod 稼働を確認 |
| Fabric に届かない | Eventstream に新規メッセージなし | Data Flow 設定と MQTT ソーストピックを確認。dataflow ログを確認 |
| Fabric Event Hub 接続失敗 | Connector ログに Event Hub エラー | Fabric からコピーした接続文字列を確認。Event Hub 名前空間の権限を確認 |
| Data Flow スループット 0 | `Average msg/min: 0/0/0` | Source topic を確認。MQTT Broker にメッセージが届いているか確認。dataflow が有効か確認 |
| 変換失敗 | WASM モジュールエラー | WASM モジュール URL を確認。コンテナレジストリ資格情報を確認。transform ログを確認 |
| 認証失敗 | Connector ログに 401/403 | HTTP 端点の認証情報（ユーザー名/パスワード、証明書）を確認 |
