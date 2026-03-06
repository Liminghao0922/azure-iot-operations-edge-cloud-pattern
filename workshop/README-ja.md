[English](README.md) | [简体中文](README-zh_CN.md) | [日本語](README-ja.md)

---

# Azure IoT Operations エッジ-クラウドパターン

> **産業用IoTエッジコンピューティングのプロダクションレディなリファレンス実装**

Azure IoT Operations、MQTTブローカー、HTTPコネクタ、Microsoft Fabric Real-Time Intelligenceを使用して、**データ主権に準拠したエッジファーストのIoTアーキテクチャ**を構築およびデプロイする方法を示す包括的なハンズオンガイド。

[![Azure IoT Operations](https://img.shields.io/badge/Azure-IoT%20Operations-0078D4?logo=microsoft-azure)](https://learn.microsoft.com/azure/iot-operations/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-K3s%201.31-326CE5?logo=kubernetes)](https://k3s.io/)

---

## 📌 本ワークショップについて

このワークショップは、産業用IoTソリューションの構築とデプロイのための**ステップバイステップでプロダクション指向の実践ガイド**を提供し、以下に重点を置いています：

- **データ居住性規制に準拠**（GDPR、CCPA、業界固有のポリシー）
- **多様なデータソースを統合**（MQTTデバイス、REST API）
- Microsoft Fabricを通じて**リアルタイム分析を可能に**
- ローカルメッセージバッファリングと自動回復による**オフライン運用をサポート**

### 構築するもの

このワークショップを完了すると、次のものをデプロイします：

```
┌─────────────────────────────────────────────┐
│  オンプレミス / エッジ (K3sクラスター)         │
│  ┌───────────────────────────────────────┐  │
│  │ MQTT Broker (セキュア、マルチリスナー)  │  │
│  │   ↑         ↑            ↑             │  │
│  │   │         │            │             │  │
│  │ デバイス  MQTTX    HTTP Connector      │  │
│  │                   (WMS APIポーリング)  │  │
│  │                                        │  │
│  │ Data Flows (変換とルーティング)        │  │
│  │   ├─ デバイスデータ → Fabric           │  │
│  │   └─ APIデータ → Fabric                │  │
│  └───────────────────────────────────────┘  │
│  すべての本番データはローカルに保存 ✅       │
└─────────────────────────────────────────────┘
                     │
                     ↓ (処理済みデータのみ)
┌─────────────────────────────────────────────┐
│  Azure クラウド (管理と分析)                  │
│  • Arc コントロールプレーン (クラスター管理)  │
│  • Fabric Real-Time Intelligence (KQL)      │
│  • Schema Registry (データガバナンス)        │
└─────────────────────────────────────────────┘
```

**ワークショップ総時間**: 6.5〜7時間（複数のセッションに分割可能）

---

## 🏗️ Azure IoT Operations アーキテクチャ概要

Azure IoT Operationsは、**エッジ-クラウド分離アーキテクチャ**を使用して、データ主権と低レイテンシー処理の完璧なバランスを実現します：

![Azure IoT Operations Architecture](https://learn.microsoft.com/en-us/azure/iot-operations/media/overview-iot-operations/azure-iot-operations-architecture.png)

### コアコンポーネントの説明

#### 🔵 **エッジレイヤー** (オンプレミス / エッジデータセンター)

Kubernetesクラスター（K3s/AKS/Arc対応）で実行：

- **MQTT Broker**
  - 役割: エッジメッセージハブ
  - 機能: 複数のリスナー、TLS暗号化、認証/認可
  - 接続性: 内部通信（ClusterIP）+ 外部アクセス（LoadBalancer）
  - 容量: 毎秒数百万メッセージまでスケール

- **HTTP/REST Connector**
  - 役割: サードパーティAPI統合
  - 機能: 定期的なREST APIポーリング、データ変換、MQTTへの自動公開
  - サポート: 認証、再試行ロジック、WASMデータ変換
  - ユースケース: WMSシステム、ERPインターフェース、IoTゲートウェイ統合

- **OPC UA Asset Discovery (Akri)**
  - 役割: 産業機器の自動検出
  - 機能: OPC UAサーバーのネットワークスキャン、デジタルツインの自動作成
  - 利点: ゼロ設定アセット登録、リアルタイムデバイスステータス同期

- **Data Flows**
  - 役割: データパイプラインオーケストレーション
  - 処理: MQTT → 変換 → クラウドデータサービス
  - 設定: 柔軟な宛先サポートを備えた宣言的トピックマッピング

#### ☁️ **クラウド管理レイヤー** (Azure Portal)

Azure PortalとAzure Resource Managerが集中管理を提供：

- **Azure Arc**
  - 役割: ハイブリッドクラウド接続ランタイム
  - 機能: Azure Portalからのリモートクラスター管理
  - 認証: Workload Identity、ロールベース認証

- **Device Registry**
  - 役割: デバイスおよびアセットメタデータリポジトリ
  - 機能: デバイスタグ、構成テンプレート、デバイスグループ化
  - 同期: エッジIoT Operationsインスタンスと同期

- **Schema Registry**
  - 役割: データスキーマバージョン管理
  - ストレージ: Azure Blob Storageベースのスキーマリポジトリ
  - 機能: データシリアライゼーション、バージョン進化、後方互換性

#### 🌊 **データフロー**

```
デバイス/API → MQTT Broker → Data Flows → Microsoft Fabric / Event Hubs
                    ↓
             (オプション) データ変換 (WASM)
                    ↓
             データエンリッチメント (Device Registry)
                    ↓
             クラウドストレージ/分析
```

**主な特性**:
- すべてのリアルタイム処理はエッジで発生（MQTT、Data Flow）
- 処理済みデータのみがクラウドに送信
- ローカルメッセージバッファリングによるオフライン回復をサポート

---

## 🌍 データ居住性とデータ主権

Azure IoT Operationsのイノベーションは、**管理プレーンとデータプレーンを分離**することにあり、企業にクラウド管理の利便性を提供しながら、データをオンプレミスに保持することを保証します。

![Data Residency Architecture](https://learn.microsoft.com/en-us/azure/iot-operations/deploy-iot-ops/media/overview-deploy/data-residency.png)

### 3層分離モデル

#### レイヤー1: 管理リソース

- **場所**: Azure Portalリージョン（例：US West）
- **コンテンツ**: Resource Manager、IoT Operationsインスタンス定義、構成メタデータ
- **特性**: オーケストレーションとガバナンスのみ、本番データなし
- **目的**: Azure Portal/CLI経由でのエッジクラスターのリモート制御

#### レイヤー2: エッジランタイム

- **場所**: 企業のオンプレミスまたはエッジデータセンター
- **コンテンツ**: MQTT Broker、Connectors、Data Flows、すべての運用ワークロード
- **データ**: 本番グレードのIoTデータが完全にオンプレミスに保存
- **特性**: **完全に顧客の管理下**、オフラインで実行可能

#### レイヤー3: データ宛先

- **場所**: データ居住性要件に基づいて柔軟に選択（例：Canada Central）
- **コンテンツ**: データベース、データウェアハウス、データレイク、Fabric Real-Time Intelligence
- **データフロー**: エッジのData Flowsから直接送信、中間WASMプレーンなし
- **例**:
  - EUの顧客 → Azure EUデータセンター
  - 中国の事業者 → Azure中国リージョン
  - 米国政府 → Azure Government

### この設計が重要な理由

| シナリオ | 従来のIoTの問題 | Azure IoT Opsソリューション |
|---------|----------------|---------------------------|
| **GDPRコンプライアンス** | データが特定リージョンに強制される | エッジ処理、集約結果のみクラウドへ |
| **低レイテンシーリアルタイム** | クラウドラウンドトリップの高レイテンシー | エッジリアルタイム処理、ミリ秒応答 |
| **ネットワークコスト最適化** | 3層分離が帯域幅を浪費 | 転送を最小化、価値あるデータのみ送信 |
| **オフライン堅牢性** | 切断時に失敗 | エッジ自律運用、回復後に同期 |
| **データ機密性** | 製造秘密の保護が困難 | コアビジネスデータは工場外に出ない |

### 実世界のデプロイ例

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
│  すべての本番データ ⬅️ 完全にローカルに保存 ✅             │
└─────────────────────────────────────────────────────────────┘
```

### データ主権コンプライアンス

Azure IoT Operationsは、これらのデータ主権シナリオをサポートします：

- ✅ **GDPR (EU)**: EUデータセンターでの個人データ処理
- ✅ **CCPA (カリフォルニア)**: 機密データのローカライズドストレージ
- ✅ **石油・ガス**: コアプロセスデータをサイト外に出る前に暗号化/集約
- ✅ **政府プロジェクト**: 未分類情報のクラウド禁止、分類データのみアップロード
- ✅ **オフショア運用**: エッジデータは常に指定された地理的位置に
- ✅ **ネットワーク分離**: ファイアウォールの背後にあるデバイスはArc Gateway経由で安全に接続

---

## 🚀 クイックスタート

### システム要件

| リソース | 最小 | 推奨 |
|---------|------|------|
| **メモリ** | 16 GB RAM | 32 GB RAM |
| **CPU** | 4 vCPUs | 8 vCPUs |
| **ディスク** | 50 GB SSD | 100+ GB SSD |
| **OS** | WSL2 Ubuntu 24.04 | Ubuntu Server 24.04 |
| **K8s** | K3s 1.31.1 | Latest K3s |

### デプロイパス

```
┌──────────────────────────────────┐
│   Part 1: インフラストラクチャ (3h)│
│   ✓ K3sクラスターデプロイ          │
│   ✓ Azure Arc有効化               │
│   ✓ IoT Operations初期化          │
└──────────────────┬───────────────┘
                   │
                   ↓
┌──────────────────────────────────┐
│   Part 2: データフロー (3-3.5h)    │
│   ✓ MQTT Brokerセキュリティ設定   │
│   ✓ Fabric統合                    │
│   ✓ HTTP Connector統合            │
│   ✓ エンドツーエンドテスト＆監視  │
└──────────────────┬───────────────┘
                   │
                   ↓
        ✨ プロダクションレディシステム ✨
```

---

## 📖 ドキュメント構造

```
workshop/
├── README.md (English version)
├── README-zh_CN.md (中文版)
├── README-ja.md (ここにいます) ⬅️
│
├── Part 1: 環境とインフラストラクチャセットアップ (3時間)
│   ├── part1-en.md (English)
│   ├── part1-zh.md (中文)
│   └── part1-ja.md (日本語)
│       ├── Step 1: WSL2とAzure CLIの準備
│       ├── Step 2: Kubernetesクラスター作成
│       ├── Step 3: Azure Arc有効化
│       ├── Step 4: IoT Operationsデプロイ
│       ├── Step 5: デプロイコマンド実行
│       └── Step 6: デプロイ検証
│
├── Part 2: MQTTとデータフロー設定 (3-3.5時間)
│   ├── part2-en.md (English)
│   ├── part2-zh.md (中文)
│   └── part2-ja.md (日本語)
│       ├── Step 1: MQTT Broker設定
│       ├── Step 2: Microsoft Fabric準備
│       ├── Step 3: デバイスデータフロー設定
│       ├── Step 4: MQTTXクライアントテスト
│       ├── Step 5: HTTP Connector統合
│       ├── Step 6: APIデータフロー設定
│       ├── Step 7: エンドツーエンドテスト
│       └── Step 8: リソースクリーンアップ
│
└── トラブルシューティング
    ├── troubleshooting-en.md (English)
    ├── troubleshooting-zh.md (中文)
    └── troubleshooting-ja.md (日本語)
        ├── 監視 (MQTT Broker, Data Flow, HTTP Connector)
        └── 一般的な問題と解決策
```

---

## 💡 主な学習ポイント

### アーキテクチャ設計

- 🎯 **エッジ-クラウド分離**: すべてのデータをクラウドに送信するのではなく、エッジで計算する理由
- 🎯 **マルチプロトコルサポート**: MQTT + HTTP/REST + OPC UAが1つのプラットフォームでどのように共存するか
- 🎯 **スケーラビリティ**: 単一のK3sから数千のエッジノードへのスケーリングのためのDevOpsパターン

### プロダクションレディネス

- 🎯 **セキュリティ**: TLS/mTLS暗号化、認証/認可、シークレット管理
- 🎯 **信頼性**: データ永続化、障害回復、マルチテナント分離
- 🎯 **可観測性**: 監視、ロギング、分散トレーシング

### データ統合

- 🎯 **マルチソースデータ融合**: デバイスセンサー + エンタープライズシステムAPI + OPC UA産業機器
- 🎯 **リアルタイム分析**: ストリーミングデータを直接Fabric Real-Time Intelligenceに
- 🎯 **データガバナンス**: バージョン管理されたスキーマ、データ検証、系統追跡

---

## 🎓 推奨学習パス

### IoT Operationsが初めての場合？

1. このREADMEを読んで全体像を把握
2. Part 1を完了（クラスター確立） - 3時間
3. Part 2を完了（完全なパイプライン実行） - 3〜3.5時間
4. 必要に応じて特定の領域を深掘り

### すでに精通している場合？

直接ジャンプ：
- **MQTT Broker設定** → Part 2, Step 1
- **Fabric統合** → Part 2, Steps 2-3
- **HTTP Connector** → Part 2, Steps 5-6
- **トラブルシューティング** → troubleshooting-ja.md

### ワークショップ後のプロジェクトアイデア

- [ ] モックAPIの代わりに実際のデバイスを接続
- [ ] プロダクショングレードのTLS証明書を設定（Let's Encrypt/エンタープライズCA）
- [ ] カスタムWASMデータ変換を実装
- [ ] エンタープライズActive Directory認証と統合
- [ ] マルチリージョン/マルチクラスターフェデレーテッドアーキテクチャの構築

---

## 🌐 関連リソース

- 📚 [Azure IoT Operations公式ドキュメント](https://learn.microsoft.com/ja-jp/azure/iot-operations/)
- 🎯 [Azure Arcドキュメント](https://learn.microsoft.com/ja-jp/azure/azure-arc/)
- 🔧 [MQTT Brokerリファレンス](https://learn.microsoft.com/ja-jp/azure/iot-operations/manage-mqtt-broker/overview-mqtt-broker)
- 📊 [Microsoft Fabric Real-Time Intelligence](https://learn.microsoft.com/ja-jp/fabric/real-time-analytics/)
- 🔐 [Azure IoT Operationsセキュリティベストプラクティス](https://learn.microsoft.com/ja-jp/azure/iot-operations/deploy-iot-ops/concept-production-guidelines)

---

## 🤝 コントリビューションとフィードバック

問題を発見したり、改善提案がありますか？

- 詳細な問題説明と再現手順を提出
- 提案はできるだけ詳細で実行可能なものに
- ドキュメントやコード例の改善のためのPRを歓迎

---

**始める準備はできましたか？** 👉 [Part 1: 環境セットアップ](./part1-ja.md)から始めましょう

---

<div align="center">

**Azure IoT Operations ハンズオンワークショップ**

エッジからクラウドへ | ゼロからイチへ | 学習から本番へ

*バージョン v1.1 | 2026年初頭更新*

</div>
