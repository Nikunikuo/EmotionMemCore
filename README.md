# 🤖 EmotionMemCore

> **感情付き記憶RAGシステム** - AIとの対話を記憶し、感情的な文脈で検索可能なAPIモジュール

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 概要

EmotionMemCoreは、AI Vtuberや対話型AIシステム向けの**感情付き記憶RAGシステム**です。ユーザーとAIの会話を分析し、38種類の日本語感情タグとともに記憶として保存。自然言語で過去の記憶を検索できます。

### ✨ 主な特徴

- 🎭 **38種類の日本語感情タグ** - AI Vtuber向けの豊富な感情表現
- 🧠 **自然言語記憶検索** - 過去の会話を直感的に検索
- 🔌 **簡単統合** - "投げるだけで保存"のシンプルAPI
- 🛡️ **本格的セキュリティ** - 認証・レート制限・CORS対応
- 🐳 **Docker完全対応** - 開発から本番まで一貫した環境
- 📊 **包括的テスト** - 単体・統合・E2Eテスト完備

### 🎯 対象ユーザー

- **AI Vtuber開発者** - 感情豊かな記憶システムが欲しい
- **対話AI開発者** - ユーザーとの会話履歴を活用したい
- **初心者開発者** - コードが苦手でも使いやすいモジュールが欲しい

---

## 🚀 クイックスタート

### 📋 必要環境

- Python 3.11+
- Docker & Docker Compose
- OpenAI API キー（Embedding用）
- Anthropic API キー（Claude用、オプション）

### ⚡ 即座に試す（Docker）

```bash
# 1. リポジトリクローン
git clone https://github.com/Nikunikuo/EmotionMemCore.git
cd EmotionMemCore

# 2. 開発環境起動（APIキー不要）
docker-compose -f docker-compose.dev.yml up -d

# 3. ブラウザでアクセス
open http://localhost:8000/docs
```

### 🔧 ローカル開発環境

#### 🪟 Windows の場合

**最も簡単な方法:**
```powershell
# quick_setup.bat をダブルクリック
# または
.\quick_setup.bat
```

**手動セットアップ:**
```powershell
# 1. Poetry インストール（PowerShell）
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# または pip でインストール
pip install poetry

# 2. 依存関係インストール
poetry install

# 3. 環境変数設定
copy .env.example .env
# .envファイルを編集してAPIキーを設定

# 4. 開発サーバー起動
poetry run python main.py
```

#### 🐧 Mac/Linux の場合

```bash
# 1. Poetry インストール
curl -sSL https://install.python-poetry.org | python3 -

# 2. 依存関係インストール
poetry install

# 3. 環境変数設定
cp .env.example .env
# .envファイルを編集してAPIキーを設定

# 4. 開発サーバー起動
poetry run python main.py
```

### 🎨 初心者向けWebダッシュボード

**コードが苦手な方でも安心！** 直感的なWebインターフェースを用意しました。

```bash
# 1. メインAPIサーバー起動
python main.py

# 2. 別ターミナルでダッシュボード起動
python run_dashboard.py

# 3. ブラウザでアクセス
open http://localhost:8080
```

**✨ ダッシュボード機能:**
- 📊 **システム統計**: 記憶数・感情分析・パフォーマンス表示
- 🧪 **機能テスト**: サンプルデータで簡単に動作確認
- 🔍 **記憶検索**: 自然言語での直感的な検索
- 📋 **記憶管理**: 保存された記憶の一覧・管理
- 📈 **記憶可視化**: Chart.jsによる美しい感情分析グラフ
- 📟 **リアルタイムログ**: システムログのライブ監視
- ⚙️ **設定ガイド**: ステップバイステップの初心者向け設定画面

---

## 📖 API使用例

### 基本的な使い方

```python
import requests

# 1. 記憶を保存
save_data = {
    "user_message": "今日はとても良い天気ですね！散歩に行こうかな。",
    "ai_message": "本当にいい天気ですね！散歩は気持ちが良さそうです。どちらに行かれますか？",
    "user_id": "user123",
    "session_id": "session456"
}

response = requests.post("http://localhost:8000/save", json=save_data)
result = response.json()

print(f"保存成功: {result['memory_id']}")
print(f"要約: {result['summary']}")
print(f"感情: {', '.join(result['emotions'])}")

# 2. 記憶を検索
search_data = {
    "query": "天気の良い日の話",
    "top_k": 5,
    "user_id": "user123"
}

response = requests.post("http://localhost:8000/search", json=search_data)
results = response.json()

for memory in results['results']:
    print(f"スコア: {memory['score']:.2f}")
    print(f"要約: {memory['summary']}")
    print(f"感情: {', '.join(memory['emotions'])}")
```

### バッチ処理

```python
# 複数の記憶を一度に保存
batch_data = [
    {
        "user_message": "新しいゲームを買いました！",
        "ai_message": "わあ、新しいゲームですね！どんなジャンルですか？",
        "user_id": "user123"
    },
    {
        "user_message": "最近仕事が忙しくて疲れています...",
        "ai_message": "お疲れ様です。無理をしないでくださいね。",
        "user_id": "user123"
    }
]

response = requests.post("http://localhost:8000/batch-save", json=batch_data)
result = response.json()

print(f"成功: {result['successful_saves']}/{result['total_requested']}")
```

---

## 🛠️ API エンドポイント

### 基本エンドポイント

| エンドポイント | メソッド | 説明 |
|---------------|----------|------|
| `/save` | POST | 会話を記憶として保存 |
| `/search` | POST | 自然言語で記憶を検索 |
| `/memories` | GET | 記憶一覧取得（フィルター対応） |
| `/health` | GET | システムヘルスチェック |

### 拡張エンドポイント

| エンドポイント | メソッド | 説明 |
|---------------|----------|------|
| `/memory/{id}` | GET | 個別記憶詳細取得 |
| `/memory/{id}` | DELETE | 記憶削除 |
| `/batch-save` | POST | バッチ記憶保存 |
| `/batch-search` | POST | バッチ記憶検索 |

### デバッグエンドポイント（DEBUG_MODE=true）

| エンドポイント | メソッド | 説明 |
|---------------|----------|------|
| `/debug/system-info` | GET | システム詳細情報 |
| `/debug/test-memory` | POST | テストデータ作成 |
| `/debug/backup/{collection}` | POST | データバックアップ |

詳細な仕様は [API ドキュメント](http://localhost:8000/docs) をご覧ください。

---

## 🎭 感情タグ一覧

EmotionMemCoreは38種類の日本語感情タグに対応：

### ポジティブ感情
`喜び` `幸せ` `興奮` `愛情` `感謝` `希望` `誇り` `安心` `満足` `楽しさ` `自信` `感動`

### ネガティブ感情  
`悲しみ` `怒り` `恐れ` `不安` `苛立ち` `失望` `孤独` `罪悪感` `恥` `後悔` `嫉妬`

### ニュートラル感情
`驚き` `好奇心` `困惑` `懐かしさ` `共感` `同情` `期待`

### AI Vtuber特有感情
`いたずら心` `恥ずかしさ` `決意` `再会` `別れ` `励まし` `支え` `信頼`

---

## 🐳 Docker デプロイ

### 開発環境

```bash
# モックモード（APIキー不要）
docker-compose -f docker-compose.dev.yml up -d
```

### 本番環境

```bash
# 1. 環境変数設定
export ANTHROPIC_API_KEY="your-api-key"
export OPENAI_API_KEY="your-api-key"
export MASTER_API_KEY="your-master-key"

# 2. 本番デプロイ
./scripts/deploy.sh -e production

# 3. ヘルスチェック
curl http://localhost:8000/health/
```

### 環境別設定

- **開発環境**: `docker-compose.dev.yml` - モックモード、認証無効
- **ステージング**: `docker-compose.yml` + `configs/staging.env`
- **本番環境**: `docker-compose.yml` + `configs/production.env`

---

## ⚙️ 設定

### 環境変数

```bash
# 基本設定
ENVIRONMENT=production
DEBUG_MODE=false
LLM_MOCK_MODE=false

# API キー
ANTHROPIC_API_KEY=your-claude-api-key
OPENAI_API_KEY=your-openai-api-key

# セキュリティ
AUTH_ENABLED=true
MASTER_API_KEY=your-secure-master-key
RATE_LIMIT_ENABLED=true
RATE_LIMIT_RPM=60

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

### レート制限設定

```bash
# 全体制限
RATE_LIMIT_RPM=60        # 分間リクエスト数
RATE_LIMIT_RPH=1000      # 時間リクエスト数
RATE_LIMIT_BURST=10      # バースト制限

# エンドポイント別制限
SAVE_RATE_LIMIT_RPM=30      # 保存エンドポイント
SEARCH_RATE_LIMIT_RPM=60    # 検索エンドポイント
MEMORIES_RATE_LIMIT_RPM=30  # 一覧エンドポイント
```

---

## 🧪 テスト

### テスト実行

```bash
# 高速テスト
python scripts/test_runner.py --fast

# 全テスト + カバレッジ
python scripts/test_runner.py --all --coverage

# CI/CD用全チェック
python scripts/test_runner.py --ci
```

### テスト種別

- **単体テスト**: 各コンポーネントの個別テスト
- **統合テスト**: API エンドポイントのテスト
- **E2Eテスト**: 完全ワークフローテスト

---

## 🏗️ アーキテクチャ

```
EmotionMemCore/
├── api/                 # FastAPI アプリケーション
│   ├── endpoints/       # API エンドポイント
│   ├── middleware/      # 認証・レート制限・CORS
│   └── schemas/         # Pydantic データモデル
├── core/                # コアロジック
│   ├── llm/            # LLM抽象化（Claude/Mock）
│   └── embedding/      # Embedding クライアント
├── infrastructure/     # インフラ層
│   ├── db/             # ChromaDB クライアント
│   └── config/         # 設定・ログ管理
├── services/           # ビジネスロジック
└── tests/              # テストスイート
```

### 技術スタック

- **API**: FastAPI + Uvicorn
- **LLM**: Claude 3 Haiku (切り替え可能)
- **Embedding**: OpenAI text-embedding-3-small
- **DB**: ChromaDB (ローカルファイル)
- **認証**: APIキー + JWT準拠
- **テスト**: pytest + モック環境完備

---

## 🔧 開発ガイド

### 開発環境セットアップ

```bash
# 1. Poetry インストール
curl -sSL https://install.python-poetry.org | python3 -

# 2. プロジェクトセットアップ
git clone https://github.com/your-username/EmotionMemCore.git
cd EmotionMemCore
poetry install

# 3. 開発用環境変数
cp .env.example .env.dev
# .env.dev を編集

# 4. 開発サーバー起動
poetry run python main.py
```

### コードスタイル

```bash
# フォーマット
black .
isort .

# リンティング
flake8 .
mypy .

# すべて実行
python scripts/test_runner.py --ci
```

### コントリビューション

1. フォークしてブランチ作成
2. 機能追加・バグ修正
3. テスト追加・実行
4. プルリクエスト作成

---

## 📊 監視・運用

### ヘルスチェック

```bash
# システム状態確認
curl http://localhost:8000/health/

# 詳細統計
curl http://localhost:8000/health/stats
```

### ログ監視

```bash
# リアルタイムログ
docker-compose logs -f

# 構造化ログ出力（JSON）
tail -f logs/app.log | jq .
```

### バックアップ

```bash
# 手動バックアップ
curl -X POST http://localhost:8000/debug/backup/emotion_memories

# 自動バックアップ（Cron例）
0 2 * * * curl -X POST http://localhost:8000/debug/backup/emotion_memories
```

---

## 🤝 統合例

### AI Vtuber との統合

```python
class VtuberMemorySystem:
    def __init__(self):
        self.emotion_core = EmotionMemCoreClient("http://localhost:8000")
    
    async def chat_with_memory(self, user_message: str, user_id: str):
        # 1. 過去の記憶を検索
        memories = await self.emotion_core.search({
            "query": user_message,
            "user_id": user_id,
            "top_k": 3
        })
        
        # 2. 記憶を踏まえてAI応答生成
        context = self.build_context(memories)
        ai_response = await self.generate_response(user_message, context)
        
        # 3. 会話を記憶として保存
        await self.emotion_core.save({
            "user_message": user_message,
            "ai_message": ai_response,
            "user_id": user_id,
            "session_id": self.current_session_id
        })
        
        return ai_response
```

### Discord Bot との統合

```python
import discord
from discord.ext import commands

class MemoryBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!')
        self.memory_api = EmotionMemCoreClient("http://localhost:8000")
    
    @commands.command()
    async def remember(self, ctx, *, query):
        memories = await self.memory_api.search({
            "query": query,
            "user_id": str(ctx.author.id),
            "top_k": 5
        })
        
        if memories['results']:
            response = "こんなことを覚えています：\n"
            for memory in memories['results']:
                response += f"• {memory['summary']} ({', '.join(memory['emotions'])})\n"
        else:
            response = "関連する記憶が見つかりませんでした。"
        
        await ctx.send(response)
```

---

## 🐛 トラブルシューティング

### よくある問題

**Q: APIキーエラーが出る**
```bash
# A: 環境変数を確認
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

# または開発時はモックモードを使用
export LLM_MOCK_MODE=true
```

**Q: ChromaDB接続エラー**
```bash
# A: データディレクトリの権限確認
ls -la chroma_db/
chmod 755 chroma_db/
```

**Q: Docker起動エラー**
```bash
# A: ポートの確認
lsof -i :8000
docker-compose down

# クリーンビルド
docker-compose build --no-cache
```

**Q: レート制限に引っかかる**
```bash
# A: 設定を緩和
export RATE_LIMIT_ENABLED=false
# または
export RATE_LIMIT_RPM=120
```

### ログデバッグ

```bash
# 詳細ログ有効化
export DEBUG_MODE=true
export LOG_LEVEL=DEBUG

# 特定エラーの調査
docker-compose logs | grep ERROR
```

---

## 📈 パフォーマンス

### ベンチマーク

| 操作 | 平均応答時間 | スループット |
|------|-------------|-------------|
| 記憶保存 | ~200ms | 300 req/min |
| 記憶検索 | ~50ms | 1200 req/min |
| バッチ保存 | ~2s (10件) | 300 req/min |

### 最適化のヒント

- **バッチ処理**: 大量データは `/batch-save` を使用
- **キャッシュ**: よく検索される内容は結果をキャッシュ
- **並行処理**: 複数のリクエストを並行実行
- **インデックス**: 大量データ時はChromaDBのインデックス最適化

---

## 🔮 今後の予定

### Phase 12: 初心者向けUI（✅ 完成）
- [x] Webダッシュボード
- [x] リアルタイムログ表示  
- [x] 記憶可視化ツール
- [x] 設定ガイドUI

### 将来の機能拡張
- [ ] **多言語対応** - 英語・中国語感情タグ
- [ ] **高度な検索** - 時系列・感情グラフ検索  
- [ ] **ML強化** - カスタム感情分類モデル
- [ ] **スケーリング** - Redis・PostgreSQL対応
- [ ] **監視強化** - Prometheus・Grafana統合

---

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) をご覧ください。

---

## 🙏 謝辞

- **FastAPI** - 高性能Web APIフレームワーク
- **ChromaDB** - 優秀なベクターデータベース  
- **OpenAI** - 高品質Embeddingサービス
- **Anthropic** - Claude LLMサービス

---

## 📞 サポート

- **GitHub Issues**: [問題報告・機能要望](https://github.com/your-username/EmotionMemCore/issues)
- **Discussions**: [質問・議論](https://github.com/your-username/EmotionMemCore/discussions)
- **Documentation**: [詳細ドキュメント](http://localhost:8000/docs)

---

<div align="center">

**🤖 EmotionMemCore で、感情豊かなAIとの対話を実現しよう！**

Made with ❤️ for AI Vtuber Community

</div>