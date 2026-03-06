# Workshop Part 1: 基本デプロイ

## 🎯 学習目標

本パートの完了後、以下ができるようになります。

- [ ] 本ソリューションのアーキテクチャを理解する
- [ ] 開発環境を準備する
- [ ] インフラをデプロイする
- [ ] コアサービスを構成する

## ⏱ 予定時間：3時間

## 📋 前提条件

- **Azure サブスクリプション**
  - ない場合は [Azure 無料アカウント](https://azure.microsoft.com/free/) を作成（12か月無料 + $200 クレジット）
  - 必要権限：迅速に進めるため **Owner** を推奨。最小権限は [Azure IoT Operations の必要権限](https://learn.microsoft.com/azure/iot-operations/deploy-iot-ops/overview-deploy#required-permissions) を参照
- Kubernetes の基本知識

> **💡 補足**
> 本ガイドは WSL2（Ubuntu）を前提としています。すでに Ubuntu 環境がある場合、Step 1 の「WSL2 のインストールと構成」「Ubuntu のインストール」はスキップできます。
> 対応環境は [Azure IoT Operations のサポート環境](https://learn.microsoft.com/azure/iot-operations/deploy-iot-ops/overview-deploy#supported-environments) を参照してください。

## 🚀 手順

### Step 1: 環境準備 (30分)

1. WSL2 のインストールと構成

- WSL2 を最新に更新
- WSL2 のバージョン確認

```powershell
wsl --update
wsl --version
```

2. DNS Tuning の有効化

- WSL2 推奨の DNS Tuning を有効にして DNS クエリ性能を改善
- 設定アプリで以下を実施：

> 💡 **手順**：
>
> - Settings → System → WSL Settings
> - DNS Tuning を有効化
>   ![DNS Tuning 設定](image/dns-tuning-settings.png)

3. Ubuntu のインストール

```powershell
wsl --install Ubuntu
```

![Ubuntu インストール](image/ubuntu-installation.png)

4. 必要ツールのインストール

- Azure CLI をインストール
  ```bash
  curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
  ```
- connectedk8s 拡張をインストール
  ```bash
  az extension add --upgrade --name connectedk8s
  ```
- kubectl（K3s により自動インストール）
- Helm
  ```bash
  sudo apt-get install curl gpg apt-transport-https --yes
  curl -fsSL https://packages.buildkite.com/helm-linux/helm-debian/gpgkey | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null
  echo "deb [signed-by=/usr/share/keyrings/helm.gpg] https://packages.buildkite.com/helm-linux/helm-debian/any/ any main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
  sudo apt-get update
  sudo apt-get install helm
  ```

### Step 2: Kubernetes クラスタの作成と構成 (30分)

1. K3s クラスタを作成

```bash
curl -sfL https://get.k3s.io | sh -
```

2. kubectl のアクセス設定

```bash
mkdir ~/.kube
sudo KUBECONFIG=~/.kube/config:/etc/rancher/k3s/k3s.yaml kubectl config view --flatten > ~/.kube/merged
mv ~/.kube/merged ~/.kube/config
chmod 0600 ~/.kube/config
export KUBECONFIG=~/.kube/config
kubectl config use-context default
sudo chmod 644 /etc/rancher/k3s/k3s.yaml
```

3. kubectl の確認

```bash
kubectl version --client
```

4. システムパラメータの最適化

- inotify 制限を増加
  ```bash
  echo fs.inotify.max_user_instances=8192 | sudo tee -a /etc/sysctl.conf
  echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
  sudo sysctl -p
  ```
- ファイルディスクリプタ上限を増加
  ```bash
  echo fs.file-max = 100000 | sudo tee -a /etc/sysctl.conf
  sudo sysctl -p
  ```

5. クラスタ状態の確認

```bash
kubectl get pods --all-namespaces
```

期待結果：kube-system の Pod が Running または Completed。
![Kubernetes Pod 状態](image/cluster-pods-status.png)

6. プロジェクトディレクトリ作成、GitHub リポジトリのクローン、VS Code で開く

```bash
cd ~
mkdir projects
git clone https://github.com/Liminghao0922/azure-iot-operations-edge-cloud-pattern
cd azure-iot-operations-edge-cloud-pattern/
code .
```

- VS Code Python 拡張: [Python - Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- VS Code Kubernetes 拡張: [Kubernetes - Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=ms-kubernetes-tools.vscode-kubernetes-tools)（任意だが推奨）

インストール後、左側に Kubernetes アイコンが表示され、クラスタ状態とリソースを確認できます。
![VS Code Kubernetes 拡張](image/vscode-kubernetes-extension.png)

### Step 3: Azure Arc の有効化 (30分)

1. Azure にログイン

   ```
   az login
   ```
2. Azure リソースプロバイダーの登録（1回のみ）

```bash
az provider register -n "Microsoft.ExtendedLocation"
az provider register -n "Microsoft.Kubernetes"
az provider register -n "Microsoft.KubernetesConfiguration"
az provider register -n "Microsoft.IoTOperations"
az provider register -n "Microsoft.DeviceRegistry"
az provider register -n "Microsoft.SecretSyncController"
```

3. リソースグループを作成

```bash
az group create --location japaneast --name rg-demo-aio
```

期待結果：作成の JSON 応答が返る。

4. Arc でクラスタを接続

```bash
az connectedk8s connect \
  --name aiocluster \
  -l eastus \
  --resource-group rg-demo-aio\
  --enable-oidc-issuer \
  --enable-workload-identity \
  --disable-auto-upgrade
```

期待結果：数分でコマンドが完了。

5. Arc エージェントの確認

```bash
kubectl get deployments,pods -n azure-arc
```

すべての Pod が Running。
![Azure Arc エージェント](image/arc-agents-verification.png)

6. OIDC Issuer URL を取得

```bash
az connectedk8s show \
  --resource-group rg-demo-aio\
  --name aiocluster \
  --query oidcIssuerProfile.issuerUrl \
  --output tsv
```

この URL を後続で使用します。

7. K3s API サーバー設定

```bash
sudo nano /etc/rancher/k3s/config.yaml
```

以下を追加（<SERVICE_ACCOUNT_ISSUER> は上記 URL に置換）：

```
kube-apiserver-arg:
  - service-account-issuer=<SERVICE_ACCOUNT_ISSUER>
  - service-account-max-token-expiration=24h
```

保存して終了（Ctrl+X, Y, Enter）。

8. カスタムロケーション機能を有効化

```bash
export OBJECT_ID=$(az ad sp show --id bc313c14-388c-4e7d-a58e-70017303ee3b --query id -o tsv)
az connectedk8s enable-features \
  -n aiocluster \
  -g rg-demo-aio \
  --custom-locations-oid $OBJECT_ID \
  --features cluster-connect custom-locations
```

K3s を再起動：

```bash
sudo systemctl restart k3s
```

1-2分待機。

### Step 4: Azure ポータルで Azure IoT Operations をデプロイ (30分)

1. Azure ポータルで IoT Operations インスタンスを作成

- [Azure Portal](https://portal.azure.com/) にアクセス
- Azure IoT Operations を検索
- Create を選択

2. Basics タブ

   | 項目                    | 値           |
   | ----------------------- | ------------ |
   | Subscription            | 選択         |
   | Resource group          | rg-demo-aio  |
   | Cluster name            | aiocluster   |
   | Custom location name    | 既定/任意     |
   | Deployment version      | 1.2 (latest) |
   | Next: Configuration     |              |

   ![Basics](image/basics-configuration.png)
3. Configuration タブ

   | 項目                              | 説明         |
   | --------------------------------- | ------------ |
   | Azure IoT Operations name         | 既定/任意    |
   | MQTT broker configuration         | 既定（テスト） |
   | Data flow profile configuration   | 既定（テスト） |
   | Next: Dependency management       |              |

   ![Configuration](image/configuration-settings.png)
4. 依存関係管理 - Schema Registry

- Create new を選択
- 名前と名前空間を入力
- ストレージアカウントとコンテナを選択/作成
  ![Schema Registry 作成](image/schema-registry-create.png)
  ![Schema Registry コンテナ](image/schema-registry-container.png)
- Apply をクリック
  ![Schema Registry 適用](image/schema-registry-apply.png)

5. 依存関係管理 - Device Registry

- Create new を選択
- 基本情報（サブスクリプション、リソースグループ、名前、リージョン）を入力
- 作成完了後に新しい名前空間を選択
  ![Device Registry 作成](image/device-registry-create.png)

6. セキュリティ設定

- **Secure settings** を選択
- **Key Vault 設定**

  - 既存 Key Vault を選択するか新規作成
  - Key Vault で RBAC を有効化し、作業ユーザーに `Key Vault Secrets Officer` を付与
    ![Key Vault 設定](image/keyvault-configuration.png)
- **Managed Identity 設定**

  - シークレット同期用のマネージド ID を作成
    ![Managed Identity key sync](image/managed-identity-key-sync.png)
  - クラウドリンク用のマネージド ID を作成
    ![Managed Identity cloud link](image/managed-identity-cloud-link.png)
- **Automation >** をクリック
  ![Automation タブ](image/automation-tab.png)

> **💡 ヒント**：
>
> - 本番環境では Secure settings を推奨
> - Managed Identity を使用し、資格情報のハードコードを回避
> - Key Vault はソフト削除とパージ保護を有効化
> - [Enable secure settings in Azure IoT Operations](https://learn.microsoft.com/en-us/azure/iot-operations/deploy-iot-ops/howto-enable-secure-settings?tabs=bash) を参照

### Step 5: デプロイコマンドを実行 (30-60分)

1. ポータルの Automation タブから Azure CLI コマンドを取得して実行
   ![Automation init command](image/automation-init-command.png)
2. 順に実行：

- 対話的に Azure へログイン

  ```bash
  az login
  ```
- Azure IoT Operations CLI 拡張をインストール

  ```bash
  az extension add --upgrade --name azure-iot-ops
  ```
- Schema Registry を作成。自動生成のスクリプトに location が含まれない場合があるため `--location eastus` を明示。

  ```bash
  az iot ops schema registry create  \
   --subscription <subscription-id>  \
   -g rg-demo-aio  \
   -n my-iot-reg  \
   --registry-namespace my-iot-reg-ns  \
   --sa-resource-id /subscriptions/<subscription-id>/resourceGroups/rg-demo-aio/providers/Microsoft.Storage/storageAccounts/saiot   \
   --sa-container iotconfig  \
   --location eastus
  ```
- クラスタ初期化（10分以上） # ポータルの `az iot ops init` を使用
- Azure IoT Operations デプロイ（30分） # ポータルの `az iot ops create` を使用
  ![Automation deploy command](image/automation-create-command.png)
- Secret Sync を有効化 # ポータルの `az iot ops secretsync enable` を使用
- 長時間コマンドはターミナルで進捗を確認

3. 全コマンド完了後、ポータルのウィザードを閉じる

### Step 6: デプロイの検証 (10分)

1. デプロイのヘルスチェック

```bash
az iot ops check
```

期待結果：
![IoT Operations ヘルスチェック](image/health-check-result.png)
2. Broker の詳細ヘルスチェック

```bash
az iot ops check --svc broker --detail-level 1
```

3. Operations UI へアクセス

- [IoT Operations UI](https://iotoperations.azure.com/) を開く
- Microsoft Entra ID でサインイン
- 未割り当てインスタンスを確認し、クラスタ作成を確認

## ✅ 検証チェックリスト

- [ ] クラスタが稼働
- [ ] すべての Pod が Running
- [ ] サービスに IP が割り当てられている
- [ ] ヘルスエンドポイントにアクセス可能
- [ ] ログが収集されている
- [ ] メトリクスが収集されている

## 🔗 参考リンク

- [Azure IoT Operations ドキュメント](https://learn.microsoft.com/en-us/azure/iot-operations/)
- [Kubernetes インストールガイド](https://kubernetes.io/docs/)
- [K3s ドキュメント](https://docs.k3s.io/)
- [Azure Arc ドキュメント](https://learn.microsoft.com/en-us/azure/azure-arc/)
- [Azure CLI リファレンス](https://learn.microsoft.com/en-us/cli/azure/)

## 🆘 よくある問題

**問題: デバイスを管理対象にしないとリソースにアクセスできない**

- 対処: `az login` を再実行し、ブラウザでの対話ログインを確認

**問題: kubectl がクラスタにアクセスできない**

- 対処: 環境変数の設定を確認
  ```bash
  export KUBECONFIG=~/.kube/config
  ```

**問題: Arc 接続に失敗する**

- 対処:
  1. Azure アカウント権限を確認（Owner または Contributor + User Access Administrator）
  2. リソースプロバイダーの登録を確認
  3. ネットワーク接続を確認

**問題: デプロイコマンドがタイムアウトする**

- 対処: 10-15 分かかる場合があるため、失敗時は `az iot ops check` で状態確認

---

## 予定合計時間

- 環境準備 (Step 1)：30分
- Kubernetes クラスタ作成 (Step 2)：30分
- Azure Arc 有効化 (Step 3)：30分
- ポータルデプロイ (Step 4)：30分
- デプロイコマンド実行 (Step 5)：30-60分
- 検証 (Step 6)：10分

**合計：おおよそ3時間**

---

## 🎉 Part 1 完了！次のステップ

Part 1 の全手順が完了しました。続いて [Part 2: MQTT とデータフロー構成](./part2-ja.md) に進んでください。

---

**最終更新**：2026年3月4日
