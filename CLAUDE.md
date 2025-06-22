# 🤖 CLAUDE.md - EmotionMemCore 完全仕様書

> **感情付き記憶RAGシステム** - AIとの対話を記憶し、感情的な文脈で検索可能なAPIモジュール

**バージョン**: 0.1.0  
**最終更新**: 2024-06-22  
**開発状況**: ✅ 完成 (Phase 1-12 完了)

---

## 📋 プロジェクト概要

### 🎯 目的
AI Vtuberや対話型AIシステム向けの感情付き記憶RAGシステム。ユーザーとAIの会話を38種類の日本語感情タグとともに記憶として保存し、自然言語で過去の記憶を検索可能。

### 🎪 対象ユーザー
- **AI Vtuber開発者** - 感情豊かな記憶システムが欲しい
- **対話AI開発者** - ユーザーとの会話履歴を活用したい  
- **初心者開発者** - コードが苦手でも使いやすいモジュールが欲しい

### ✨ 主要特徴
- 🎭 **38種類の日本語感情タグ** - AI Vtuber向けの豊富な感情表現
- 🧠 **自然言語記憶検索** - 過去の会話を直感的に検索
- 🔌 **簡単統合** - "投げるだけで保存"のシンプルAPI
- 🛡️ **本格的セキュリティ** - 認証・レート制限・CORS対応
- 🐳 **Docker完全対応** - 開発から本番まで一貫した環境
- 🎨 **初心者向けWebUI** - コード不要の直感的操作

---

## 🏗️ システムアーキテクチャ

### 📁 ディレクトリ構造
```
EmotionMemCore/
├── api/                    # FastAPI アプリケーション
│   ├── endpoints/          # API エンドポイント実装
│   │   ├── __init__.py
│   │   ├── save.py         # POST /save - 記憶保存
│   │   ├── search.py       # POST /search - 記憶検索
│   │   ├── memories.py     # GET /memories - 記憶一覧
│   │   ├── health.py       # GET /health - ヘルスチェック
│   │   └── debug.py        # /debug/* - デバッグエンドポイント
│   ├── middleware/         # ミドルウェア
│   │   ├── __init__.py
│   │   ├── auth.py         # API認証
│   │   ├── rate_limit.py   # レート制限
│   │   ├── cors.py         # CORS設定
│   │   └── error_handler.py # エラーハンドリング
│   ├── schemas/            # Pydantic データモデル
│   │   ├── __init__.py
│   │   ├── memory.py       # Memory, SaveRequest, SearchRequest
│   │   ├── emotion.py      # 38種類感情Enum
│   │   └── response.py     # APIレスポンス形式
│   ├── dependencies.py     # FastAPI依存性注入
│   └── app.py             # FastAPIアプリケーション本体
├── core/                   # コアロジック
│   ├── llm/               # LLM抽象化層
│   │   ├── __init__.py
│   │   ├── base.py        # BaseLLM抽象クラス
│   │   ├── claude.py      # Claude実装
│   │   └── mock.py        # モック実装（開発・テスト用）
│   └── embedding/         # Embedding クライアント
│       ├── __init__.py
│       ├── openai_client.py # OpenAI text-embedding-3-small
│       └── base.py        # 抽象化インターフェース
├── infrastructure/        # インフラ層
│   ├── db/               # データベース
│   │   ├── __init__.py
│   │   ├── memory_store.py # ChromaDB実装
│   │   └── base.py       # DB抽象化インターフェース
│   └── config/           # 設定・ログ管理
│       ├── __init__.py
│       ├── settings.py   # 環境設定管理
│       └── logging.py    # 構造化ログ設定
├── services/              # ビジネスロジック
│   ├── __init__.py
│   └── memory_service.py  # 記憶管理サービス
├── ui/                    # 初心者向けWebダッシュボード
│   ├── templates/         # Jinja2 テンプレート
│   │   ├── base.html      # ベーステンプレート
│   │   ├── dashboard.html # メインダッシュボード
│   │   ├── test.html      # 機能テスト
│   │   ├── search.html    # 記憶検索
│   │   ├── memories.html  # 記憶管理
│   │   ├── visualization.html # 記憶可視化
│   │   ├── logs.html      # リアルタイムログ
│   │   └── settings.html  # 設定ガイド
│   ├── static/           # 静的ファイル
│   └── dashboard.py      # ダッシュボードFastAPIアプリ
├── tests/                 # テストスイート
│   ├── unit/             # 単体テスト
│   ├── integration/      # 統合テスト
│   └── e2e/              # E2Eテスト
├── scripts/               # 運用スクリプト
├── docs/                  # ドキュメント
├── configs/               # 環境別設定
├── docker-compose.yml     # 本番用Docker設定
├── docker-compose.dev.yml # 開発用Docker設定
├── Dockerfile            # Dockerイメージ定義
├── pyproject.toml        # Poetry依存関係管理
├── main.py               # メインAPIサーバー起動
├── run_dashboard.py      # ダッシュボード起動
├── README.md             # プロジェクト説明
└── CLAUDE.md             # 本仕様書
```

### 🔧 技術スタック
- **API フレームワーク**: FastAPI + Uvicorn
- **LLM**: Claude 3 Haiku (切り替え可能)
- **Embedding**: OpenAI text-embedding-3-small
- **ベクターDB**: ChromaDB (ローカルファイル)
- **認証**: APIキー + レート制限
- **UI**: Jinja2 + Bootstrap 5 + Chart.js
- **テスト**: pytest + モック環境
- **デプロイ**: Docker + Docker Compose
- **依存管理**: Poetry

---

## 🔌 API エンドポイント仕様

### 🔵 基本エンドポイント

#### `POST /save` - 記憶保存
**概要**: ユーザーとAIの会話を感情付きで記憶として保存

**リクエスト**:
```json
{
  "user_message": "今日はとても良い天気ですね！散歩に行こうかな。",
  "ai_message": "本当にいい天気ですね！散歩は気持ちが良さそうです。",
  "user_id": "user123",
  "session_id": "session456"  // オプション
}
```

**レスポンス**:
```json
{
  "success": true,
  "memory_id": "mem_20240622_123456_abc",
  "summary": "ユーザーが良い天気について話し、散歩を考えている。AIが共感を示した。",
  "emotions": ["喜び", "期待", "安心"],
  "timestamp": "2024-06-22T12:34:56.789Z",
  "processing_time": 1.234
}
```

#### `POST /search` - 記憶検索
**概要**: 自然言語クエリで過去の記憶を検索

**リクエスト**:
```json
{
  "query": "天気の良い日の話",
  "user_id": "user123",  // "all"で全ユーザー検索
  "top_k": 5,
  "emotions": ["喜び", "期待"]  // オプション感情フィルター
}
```

**レスポンス**:
```json
{
  "success": true,
  "results": [
    {
      "memory_id": "mem_20240622_123456_abc",
      "summary": "ユーザーが良い天気について話し、散歩を考えている。",
      "emotions": ["喜び", "期待", "安心"],
      "score": 0.95,
      "timestamp": "2024-06-22T12:34:56.789Z",
      "user_id": "user123"
    }
  ],
  "total": 1,
  "processing_time": 0.456
}
```

#### `GET /memories` - 記憶一覧取得
**概要**: 保存された記憶の一覧を取得（ページネーション対応）

**パラメータ**:
- `user_id`: ユーザーID（オプション）
- `emotions`: 感情フィルター（カンマ区切り、オプション）
- `limit`: 取得件数（デフォルト: 10）
- `offset`: オフセット（デフォルト: 0）

#### `GET /health` - ヘルスチェック
**概要**: システム状態確認

**レスポンス**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development",
  "components": {
    "llm": "healthy",
    "embedding": "healthy",
    "database": "healthy"
  },
  "uptime": "24h 30m 15s",
  "timestamp": "2024-06-22T12:34:56.789Z"
}
```

### 🔷 拡張エンドポイント

#### `GET /memory/{id}` - 個別記憶詳細取得
#### `DELETE /memory/{id}` - 記憶削除
#### `POST /batch-save` - バッチ記憶保存
#### `POST /batch-search` - バッチ記憶検索

### 🟡 デバッグエンドポイント（DEBUG_MODE=true時のみ）

#### `GET /debug/system-info` - システム詳細情報
#### `POST /debug/test-memory` - テストデータ作成
#### `POST /debug/backup/{collection}` - データバックアップ

---

## 🎭 感情タグ仕様

### 📝 38種類の日本語感情タグ

#### ポジティブ感情 (12種類)
- `喜び` `幸せ` `興奮` `愛情` `感謝` `希望`
- `誇り` `安心` `満足` `楽しさ` `自信` `感動`

#### ネガティブ感情 (11種類)  
- `悲しみ` `怒り` `恐れ` `不安` `苛立ち` `失望`
- `孤独` `罪悪感` `恥` `後悔` `嫉妬`

#### ニュートラル感情 (7種類)
- `驚き` `好奇心` `困惑` `懐かしさ` `共感` `同情` `期待`

#### AI Vtuber特有感情 (8種類)
- `いたずら心` `恥ずかしさ` `決意` `再会` `別れ` `励まし` `支え` `信頼`

### 🎨 感情カラーパレット
各感情には専用のカラーコードが割り当てられ、UI表示で使用:
```javascript
const emotionColors = {
  '喜び': '#FF6B35', '幸せ': '#F7931E', '興奮': '#FFB100',
  '愛情': '#FF1744', '感謝': '#E91E63', '希望': '#9C27B0',
  // ... 全38色定義
};
```

---

## 🎨 初心者向けWebダッシュボード

### 🌐 アクセスURL
- **メインAPI**: `http://localhost:8000`
- **ダッシュボード**: `http://localhost:8080`

### 📊 ページ構成

#### 1. メインダッシュボード (`/`)
- **システム統計**: 総記憶数・感情種類・平均応答時間・リクエスト数
- **感情分析グラフ**: Chart.js による上位感情の円グラフ
- **最近の記憶**: 直近の記憶一覧表示
- **クイックアクション**: 各ページへの導線

#### 2. 機能テストページ (`/test`)
- **サンプルデータ生成**: ワンクリックでテストデータ作成
- **記憶保存テスト**: 手動入力でのAPI動作確認
- **システム接続テスト**: 各コンポーネントの稼働状況確認
- **リアルタイム結果表示**: API呼び出し結果の即時表示

#### 3. 記憶検索ページ (`/search`)
- **自然言語検索**: フリーテキストでの記憶検索
- **感情フィルター**: 38種類感情タグでの絞り込み
- **検索履歴**: 過去の検索クエリ管理
- **検索結果表示**: スコア付きランキング表示

#### 4. 記憶管理ページ (`/memories`)
- **表示モード切り替え**: カード・リスト・タイムライン表示
- **フィルタリング**: ユーザー・感情・日付での絞り込み
- **記憶詳細表示**: モーダルでの詳細情報表示
- **削除・エクスポート**: 記憶管理機能

#### 5. 記憶可視化ツール (`/visualization`)
- **感情分布チャート**: 円グラフでの感情分布表示
- **時系列チャート**: 過去30日の記憶数推移
- **感情ヒートマップ**: 日別感情強度のカレンダー表示
- **統計サマリー**: 最頻出感情・アクティブユーザー数
- **関係性ネットワーク**: 感情間の関係性可視化（デモ実装）

#### 6. リアルタイムログ (`/logs`)
- **ログストリーム**: システムログのライブ表示
- **ログフィルタリング**: レベル別・キーワード検索
- **統計情報**: INFO・WARNING・ERROR件数
- **ログエクスポート**: ログファイルダウンロード

#### 7. 設定ガイド (`/settings`)
- **設定完了チェックリスト**: 進捗表示付きステップガイド
- **現在の設定表示**: 環境・認証・レート制限状況
- **設定変更フォーム**: ドロップダウンでの簡単設定
- **APIキー設定ガイド**: OpenAI・Claude設定手順
- **セキュリティガイド**: 本番運用時の必須設定
- **デプロイガイド**: Docker本番環境構築手順
- **トラブルシューティング**: よくある問題の解決方法

### 🎯 UI/UX設計思想
- **初心者ファースト**: コード知識不要で全機能操作可能
- **日本語完全対応**: 説明・ラベル・エラーメッセージ全て日本語
- **レスポンシブデザイン**: PC・タブレット・スマホ対応
- **美しいビジュアル**: Bootstrap 5 + Chart.js による洗練されたデザイン
- **アニメーション**: フェードイン・ホバーエフェクトで滑らかな操作感

---

## ⚙️ 設定・環境変数

### 📋 主要環境変数

#### 基本設定
```bash
ENVIRONMENT=development|staging|production
DEBUG_MODE=true|false
LLM_MOCK_MODE=true|false  # モックモード（APIキー不要）
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR
```

#### API キー
```bash
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-api-your-claude-key
```

#### セキュリティ
```bash
AUTH_ENABLED=true|false
MASTER_API_KEY=your-secure-master-key
RATE_LIMIT_ENABLED=true|false
RATE_LIMIT_RPM=60  # 分間リクエスト数
RATE_LIMIT_RPH=1000  # 時間リクエスト数
```

#### CORS
```bash
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### 🐳 Docker設定

#### 開発環境（APIキー不要）
```bash
docker-compose -f docker-compose.dev.yml up -d
```

#### 本番環境
```bash
# 環境変数設定
export ANTHROPIC_API_KEY="your-api-key"
export OPENAI_API_KEY="your-api-key" 
export MASTER_API_KEY="your-master-key"

# 本番起動
docker-compose up -d
```

---

## 🧪 テスト仕様

### 📊 テストカバレッジ
- **単体テスト**: 各コンポーネントの個別テスト
- **統合テスト**: API エンドポイントのテスト
- **E2Eテスト**: 完全ワークフローテスト

### 🏃‍♂️ テスト実行
```bash
# 高速テスト
python scripts/test_runner.py --fast

# 全テスト + カバレッジ
python scripts/test_runner.py --all --coverage

# CI/CD用全チェック
python scripts/test_runner.py --ci
```

### 🔍 テストシナリオ

#### 記憶保存テスト
1. 正常な会話データでの保存
2. 空メッセージでのエラーハンドリング
3. 長大メッセージでの処理
4. 感情抽出精度の検証

#### 記憶検索テスト
1. 部分一致検索の精度
2. 感情フィルターの動作
3. ユーザー別検索の分離
4. 検索スコアの妥当性

#### セキュリティテスト
1. 認証機能の動作確認
2. レート制限の効果検証
3. CORS設定の妥当性
4. 不正リクエストの排除

---

## 🔒 セキュリティ仕様

### 🛡️ 認証・認可
- **APIキー認証**: `Authorization: Bearer your-api-key`
- **マスターキー**: 管理機能用の特権キー
- **セッション管理**: ユーザー別データ分離

### ⚡ レート制限
- **分間制限**: 60リクエスト/分（デフォルト）
- **時間制限**: 1000リクエスト/時間（デフォルト）
- **バースト制限**: 短時間での集中アクセス制限
- **IPベース**: 送信元IPアドレス単位での制限

### 🌐 CORS設定
- **オリジン制限**: 許可ドメインの明示的指定
- **メソッド制限**: GET, POST, DELETE のみ許可
- **ヘッダー制限**: Content-Type, Authorization のみ許可

### 🔐 データ保護
- **データ暗号化**: 保存時の機密データ暗号化
- **ログ制限**: 個人情報のログ出力制限
- **バックアップ暗号化**: バックアップファイルの暗号化

---

## 📈 パフォーマンス仕様

### ⚡ 応答時間目標
- **記憶保存**: < 500ms（LLM処理込み）
- **記憶検索**: < 100ms（ベクトル検索）
- **記憶一覧**: < 50ms（DB クエリ）
- **ヘルスチェック**: < 10ms

### 🚀 スループット目標
- **記憶保存**: 300 req/min
- **記憶検索**: 1200 req/min  
- **バッチ保存**: 300 req/min（10件バッチ）

### 💾 リソース使用量
- **メモリ**: < 512MB（通常運用時）
- **CPU**: < 50%（通常運用時）
- **ディスク**: 成長率 1GB/月（1万記憶想定）

### 📊 スケーラビリティ
- **最大記憶数**: 100万件（単一インスタンス）
- **最大ユーザー数**: 1万ユーザー
- **最大同時接続**: 100接続

---

## 🚀 デプロイ・運用

### 🐳 Docker デプロイ

#### 環境別設定
- **開発環境**: `docker-compose.dev.yml` - モックモード、認証無効
- **ステージング**: `docker-compose.yml` + `configs/staging.env`
- **本番環境**: `docker-compose.yml` + `configs/production.env`

#### 本番デプロイ手順
1. **環境変数準備**: production.env ファイル作成
2. **イメージビルド**: `docker-compose build`
3. **サービス起動**: `docker-compose up -d`
4. **ヘルスチェック**: `curl http://localhost:8000/health/`

### 📊 監視・ログ
- **構造化ログ**: JSON形式での出力
- **ログローテーション**: 日次ローテーション
- **メトリクス収集**: レスポンス時間・エラー率
- **アラート設定**: エラー閾値での通知

### 💾 バックアップ
- **自動バックアップ**: 日次ChromaDBバックアップ
- **手動バックアップ**: `POST /debug/backup/{collection}`
- **リストア手順**: ドキュメント化済み

---

## 🔧 開発・保守

### 🛠️ 開発環境セットアップ
```bash
# 1. リポジトリクローン
git clone https://github.com/your-username/EmotionMemCore.git
cd EmotionMemCore

# 2. 依存関係インストール  
poetry install

# 3. 開発サーバー起動
python main.py

# 4. ダッシュボード起動
python run_dashboard.py
```

### 📝 コード規約
- **Python**: PEP 8準拠
- **型ヒント**: 全関数・メソッドに必須
- **ドキュメンテーション**: docstring必須
- **テスト**: 新機能は必ずテスト作成

### 🔄 CI/CD
- **テスト自動化**: pytest + coverage
- **コード品質**: flake8 + mypy + black
- **セキュリティチェック**: bandit
- **依存関係チェック**: safety

---

## 🐛 トラブルシューティング

### ❌ よくある問題

#### "Connection Error" が表示される
```bash
# 解決方法
python main.py  # メインAPIサーバー起動
```

#### APIキーエラーが出る
```bash
# 解決方法  
export LLM_MOCK_MODE=true  # モックモード有効化
# または .env ファイルでAPIキー設定
```

#### ポートが使用中エラー
```bash
# 解決方法
lsof -i :8000              # ポート使用状況確認
kill -9 <PID>             # プロセス停止
```

#### Docker起動エラー
```bash
# 解決方法
docker-compose down                    # クリーンアップ
docker-compose build --no-cache       # 再ビルド
```

### 🔍 デバッグ方法
1. **デバッグモード有効化**: `DEBUG_MODE=true`
2. **詳細ログ確認**: `LOG_LEVEL=DEBUG`  
3. **ヘルスチェック**: `curl http://localhost:8000/health/`
4. **コンポーネント個別確認**: ダッシュボードのテストページ活用

---

## 🔮 将来の拡張予定

### Phase 13以降の構想
- [ ] **多言語対応** - 英語・中国語感情タグ
- [ ] **高度な検索** - 時系列・感情グラフ検索
- [ ] **ML強化** - カスタム感情分類モデル
- [ ] **スケーリング** - Redis・PostgreSQL対応
- [ ] **監視強化** - Prometheus・Grafana統合
- [ ] **モバイルアプリ** - React Native対応
- [ ] **プラグインシステム** - カスタムLLM対応

### 🤝 コミュニティ
- **GitHub Issues**: 問題報告・機能要望
- **GitHub Discussions**: 質問・議論
- **Discord**: リアルタイム サポート（予定）

---

## 📄 ライセンス・謝辞

### 📜 ライセンス
MIT License - 商用利用・改変・再配布自由

### 🙏 謝辞
- **FastAPI** - 高性能Web APIフレームワーク
- **ChromaDB** - 優秀なベクターデータベース
- **OpenAI** - 高品質Embeddingサービス  
- **Anthropic** - Claude LLMサービス
- **Bootstrap** - 美しいUIフレームワーク
- **Chart.js** - インタラクティブチャートライブラリ

---

## 📞 サポート・連絡先

- **GitHub**: [EmotionMemCore Repository](https://github.com/your-username/EmotionMemCore)
- **Issues**: [問題報告・機能要望](https://github.com/your-username/EmotionMemCore/issues)
- **Discussions**: [質問・議論](https://github.com/your-username/EmotionMemCore/discussions)
- **Documentation**: [詳細ドキュメント](http://localhost:8000/docs)

---

<div align="center">

**🤖 EmotionMemCore で、感情豊かなAIとの対話を実現しよう！**

Made with ❤️ for AI Vtuber Community

**バージョン 0.1.0 - 2024年6月22日完成**

</div>