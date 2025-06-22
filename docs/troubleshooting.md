# 🐛 EmotionMemCore トラブルシューティングガイド

> **EmotionMemCoreの問題を素早く解決するための完全ガイド**

このガイドでは、EmotionMemCoreの使用中に発生する可能性のある問題と、その解決方法を詳しく説明します。

---

## 📋 目次

1. [🏥 ヘルスチェックと診断](#-ヘルスチェックと診断)
2. [🚀 起動時の問題](#-起動時の問題)
3. [🔑 認証・API キーの問題](#-認証api-キーの問題)
4. [💾 データベース（ChromaDB）の問題](#-データベースchromadbの問題)
5. [🤖 LLM 接続の問題](#-llm-接続の問題)
6. [🌐 ネットワークと接続の問題](#-ネットワークと接続の問題)
7. [⚡ パフォーマンスの問題](#-パフォーマンスの問題)
8. [🐳 Docker 関連の問題](#-docker-関連の問題)
9. [📊 ログとデバッグ](#-ログとデバッグ)
10. [🔧 よくある設定ミス](#-よくある設定ミス)
11. [🆘 緊急時の対処法](#-緊急時の対処法)

---

## 🏥 ヘルスチェックと診断

### 基本ヘルスチェック

まず、システムの基本状態を確認しましょう。

```bash
# APIヘルスチェック
curl http://localhost:8000/health/

# 詳細ヘルスチェック
curl http://localhost:8000/health/stats

# デバッグモード時のシステム情報
curl http://localhost:8000/debug/system-info
```

**正常な応答例**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "0.1.0",
  "dependencies": {
    "chroma_db": "connected",
    "llm_service": "available",
    "embedding_service": "available"
  }
}
```

### 診断スクリプト

```python
# diagnosis_tool.py
import asyncio
import httpx
import json
from datetime import datetime

async def comprehensive_diagnosis(base_url="http://localhost:8000"):
    """包括的な診断を実行"""
    
    print("🔍 EmotionMemCore 診断開始...")
    print(f"📍 対象URL: {base_url}")
    print(f"🕐 実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    results = {}
    
    # 1. 基本接続テスト
    print("1️⃣ 基本接続テスト...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{base_url}/")
            if response.status_code == 200:
                print("   ✅ API サーバー: 接続成功")
                results["api_connection"] = "success"
            else:
                print(f"   ❌ API サーバー: HTTP {response.status_code}")
                results["api_connection"] = f"http_error_{response.status_code}"
    except Exception as e:
        print(f"   ❌ API サーバー: 接続失敗 - {e}")
        results["api_connection"] = f"connection_failed_{type(e).__name__}"
    
    # 2. ヘルスチェック
    print("2️⃣ ヘルスチェック...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{base_url}/health/")
            if response.status_code == 200:
                health_data = response.json()
                print(f"   ✅ ヘルス: {health_data.get('status', 'unknown')}")
                results["health_check"] = health_data
                
                # 依存関係チェック
                deps = health_data.get("dependencies", {})
                for service, status in deps.items():
                    icon = "✅" if status in ["connected", "available", "healthy"] else "❌"
                    print(f"   {icon} {service}: {status}")
            else:
                print(f"   ❌ ヘルス: HTTP {response.status_code}")
                results["health_check"] = {"error": f"http_{response.status_code}"}
    except Exception as e:
        print(f"   ❌ ヘルス: {e}")
        results["health_check"] = {"error": str(e)}
    
    # 3. API エンドポイントテスト
    print("3️⃣ API エンドポイントテスト...")
    endpoints = ["/", "/health/", "/health/stats"]
    
    for endpoint in endpoints:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{base_url}{endpoint}")
                if response.status_code == 200:
                    print(f"   ✅ {endpoint}: OK")
                    results[f"endpoint_{endpoint.replace('/', '_')}"] = "success"
                else:
                    print(f"   ❌ {endpoint}: HTTP {response.status_code}")
                    results[f"endpoint_{endpoint.replace('/', '_')}"] = f"http_{response.status_code}"
        except Exception as e:
            print(f"   ❌ {endpoint}: {e}")
            results[f"endpoint_{endpoint.replace('/', '_')}"] = f"error_{type(e).__name__}"
    
    # 4. 記憶保存テスト（簡単なテスト）
    print("4️⃣ 記憶保存テスト...")
    try:
        test_payload = {
            "user_message": "診断テストメッセージ",
            "ai_message": "診断テスト応答",
            "user_id": "diagnosis_test_user",
            "metadata": {"test": True}
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{base_url}/save", json=test_payload)
            if response.status_code == 200:
                print("   ✅ 記憶保存: 成功")
                results["memory_save"] = "success"
            else:
                print(f"   ❌ 記憶保存: HTTP {response.status_code}")
                print(f"      応答: {response.text[:200]}")
                results["memory_save"] = f"http_{response.status_code}"
    except Exception as e:
        print(f"   ❌ 記憶保存: {e}")
        results["memory_save"] = f"error_{type(e).__name__}"
    
    # 5. 記憶検索テスト
    print("5️⃣ 記憶検索テスト...")
    try:
        search_payload = {
            "query": "診断テスト",
            "user_id": "diagnosis_test_user",
            "top_k": 1
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{base_url}/search", json=search_payload)
            if response.status_code == 200:
                search_data = response.json()
                result_count = len(search_data.get("results", []))
                print(f"   ✅ 記憶検索: 成功 ({result_count}件の結果)")
                results["memory_search"] = "success"
            else:
                print(f"   ❌ 記憶検索: HTTP {response.status_code}")
                results["memory_search"] = f"http_{response.status_code}"
    except Exception as e:
        print(f"   ❌ 記憶検索: {e}")
        results["memory_search"] = f"error_{type(e).__name__}"
    
    # 6. 診断結果サマリー
    print("\n" + "=" * 50)
    print("📊 診断結果サマリー")
    print("=" * 50)
    
    success_count = sum(1 for v in results.values() if v == "success" or (isinstance(v, dict) and v.get("status") == "healthy"))
    total_count = len(results)
    
    print(f"✅ 成功: {success_count}/{total_count}")
    print(f"❌ 失敗: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n🎉 全ての診断項目が正常です！")
    else:
        print(f"\n⚠️  {total_count - success_count}個の問題が見つかりました。下記を確認してください:")
        for key, value in results.items():
            if value != "success" and not (isinstance(value, dict) and value.get("status") == "healthy"):
                print(f"   - {key}: {value}")
    
    # 診断結果を保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"diagnosis_report_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "target_url": base_url,
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 詳細レポート: diagnosis_report_{timestamp}.json")
    return results

# 実行
if __name__ == "__main__":
    asyncio.run(comprehensive_diagnosis())
```

---

## 🚀 起動時の問題

### 問題: サーバーが起動しない

**症状**: `python main.py` 実行時にエラーが発生

**一般的な原因と解決法**:

#### 1. ポートが既に使用されている
```bash
# 問題確認
lsof -i :8000
netstat -tulpn | grep :8000

# 解決法
# プロセスを終了
kill -9 <PID>

# または別ポートを使用
export PORT=8001
python main.py
```

#### 2. 依存関係のインストール不足
```bash
# Poetry を使用している場合
poetry install

# pip を使用している場合
pip install -r requirements.txt
```

#### 3. Python バージョンの問題
```bash
# Python バージョン確認
python --version

# 3.11+ が必要
# pyenv などで適切なバージョンに切り替え
pyenv install 3.11
pyenv local 3.11
```

#### 4. 環境変数の設定不足
```bash
# 最小限の環境変数設定
export ENVIRONMENT=development
export DEBUG_MODE=true
export LLM_MOCK_MODE=true

# 設定確認
python -c "import os; print('ENV:', os.getenv('ENVIRONMENT')); print('DEBUG:', os.getenv('DEBUG_MODE'))"
```

### 問題: アプリケーション初期化エラー

**エラーメッセージ例**:
```
RuntimeError: システム初期化に失敗しました
```

**解決法**:

1. **ログ詳細確認**:
```bash
# ログレベルを DEBUG に設定
export LOG_LEVEL=DEBUG
python main.py
```

2. **依存サービス確認**:
```bash
# ChromaDB ディレクトリの権限確認
ls -la chroma_db/
chmod 755 chroma_db/

# API キー設定確認（本番モード時）
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY
```

3. **モックモードでの起動**:
```bash
# 外部依存を無効にして起動テスト
export LLM_MOCK_MODE=true
export EMBEDDING_MOCK_MODE=true
python main.py
```

---

## 🔑 認証・API キーの問題

### 問題: APIキー認証エラー

**エラーメッセージ例**:
```json
{
  "error": "authentication_failed",
  "message": "Invalid or missing API key"
}
```

**解決法**:

1. **環境変数の確認**:
```bash
# API キー設定確認
echo "Anthropic: ${ANTHROPIC_API_KEY:0:10}..."
echo "OpenAI: ${OPENAI_API_KEY:0:10}..."
echo "Master: ${MASTER_API_KEY:0:10}..."
```

2. **設定ファイルの確認**:
```bash
# .env ファイルの確認
cat .env | grep -E "(ANTHROPIC|OPENAI|MASTER)_API_KEY"

# 設定の読み込み確認
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Anthropic:', bool(os.getenv('ANTHROPIC_API_KEY')))
print('OpenAI:', bool(os.getenv('OPENAI_API_KEY')))
"
```

3. **認証の無効化（開発時）**:
```bash
# 認証を無効にして一時的に回避
export AUTH_ENABLED=false
export LLM_MOCK_MODE=true
```

4. **APIキーの検証**:
```python
# api_key_test.py
import os
import asyncio
import httpx

async def test_anthropic_key():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return False
    
    try:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Simple test request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "Hi"}]
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                print("✅ Anthropic API key is valid")
                return True
            else:
                print(f"❌ Anthropic API error: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Anthropic API test failed: {e}")
        return False

async def test_openai_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers=headers,
                json={
                    "model": "text-embedding-3-small",
                    "input": "test"
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                print("✅ OpenAI API key is valid")
                return True
            else:
                print(f"❌ OpenAI API error: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        return False

async def main():
    print("🔑 API キー検証テスト")
    print("-" * 30)
    
    anthropic_ok = await test_anthropic_key()
    openai_ok = await test_openai_key()
    
    if anthropic_ok and openai_ok:
        print("\n🎉 全ての API キーが有効です")
    else:
        print("\n⚠️  無効な API キーがあります")
        print("   モックモードでの起動を検討してください:")
        print("   export LLM_MOCK_MODE=true")

if __name__ == "__main__":
    asyncio.run(main())
```

### 問題: レート制限エラー

**エラーメッセージ例**:
```json
{
  "error": "rate_limit_exceeded",
  "message": "レート制限に達しました"
}
```

**解決法**:

1. **レート制限の緩和**:
```bash
# 設定を緩和
export RATE_LIMIT_ENABLED=false
# または
export RATE_LIMIT_RPM=120
export RATE_LIMIT_RPH=2000
```

2. **API使用量の確認**:
```bash
# 現在のレート制限状況確認
curl -H "X-API-Key: your-key" http://localhost:8000/health/stats
```

---

## 💾 データベース（ChromaDB）の問題

### 問題: ChromaDB 接続エラー

**エラーメッセージ例**:
```
chromadb.errors.ConnectionError: Unable to connect to database
```

**解決法**:

1. **ディレクトリ権限の確認**:
```bash
# データディレクトリの確認
ls -la chroma_db/
ls -la dev_chroma_db/

# 権限修正
chmod -R 755 chroma_db/
chmod -R 755 dev_chroma_db/

# オーナー確認
whoami
chown -R $(whoami) chroma_db/
```

2. **ディスク容量の確認**:
```bash
# ディスク使用量確認
df -h .
du -sh chroma_db/

# 不要なファイル削除
rm -rf test_chroma_db/
```

3. **ChromaDB の再初期化**:
```bash
# 開発環境のデータベースリセット
rm -rf dev_chroma_db/
mkdir dev_chroma_db

# アプリケーション再起動
python main.py
```

4. **ChromaDB バージョン確認**:
```python
# chroma_version_check.py
import chromadb
print(f"ChromaDB version: {chromadb.__version__}")

# クライアント接続テスト
try:
    client = chromadb.PersistentClient(path="./test_chroma_connection")
    collection = client.get_or_create_collection("test")
    print("✅ ChromaDB connection successful")
    
    # クリーンアップ
    client.delete_collection("test")
    import shutil
    shutil.rmtree("./test_chroma_connection")
    
except Exception as e:
    print(f"❌ ChromaDB connection failed: {e}")
```

### 問題: データ破損・不整合

**症状**: 検索結果が返らない、保存に失敗する

**解決法**:

1. **データベース整合性チェック**:
```python
# db_integrity_check.py
import chromadb
import os

def check_db_integrity(db_path):
    print(f"🔍 Checking database integrity: {db_path}")
    
    try:
        client = chromadb.PersistentClient(path=db_path)
        collections = client.list_collections()
        
        print(f"📂 Found {len(collections)} collections:")
        
        total_memories = 0
        for collection in collections:
            count = collection.count()
            total_memories += count
            print(f"   - {collection.name}: {count} items")
            
            # サンプルデータ確認
            if count > 0:
                try:
                    results = collection.peek(limit=1)
                    print(f"     Sample data keys: {list(results.keys())}")
                except Exception as e:
                    print(f"     ❌ Error reading sample: {e}")
        
        print(f"📊 Total memories: {total_memories}")
        return True
        
    except Exception as e:
        print(f"❌ Database integrity check failed: {e}")
        return False

# チェック実行
if __name__ == "__main__":
    db_paths = ["./chroma_db", "./dev_chroma_db", "./staging_chroma_db"]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            check_db_integrity(db_path)
            print("-" * 40)
```

2. **バックアップからの復元**:
```bash
# バックアップが存在する場合
cp -r backups/20240115_103000/chroma_db ./chroma_db_restored

# 設定で復元されたDBを使用
export CHROMA_PERSIST_DIRECTORY=./chroma_db_restored
```

3. **データベース再構築**:
```bash
# 既存データをバックアップ
mv chroma_db chroma_db_backup_$(date +%Y%m%d_%H%M%S)

# 新しいデータベース作成
mkdir chroma_db

# アプリケーション再起動（自動でコレクション作成）
python main.py
```

---

## 🤖 LLM 接続の問題

### 問題: Claude API 接続エラー

**エラーメッセージ例**:
```
anthropic.APIError: Error communicating with Anthropic API
```

**解決法**:

1. **ネットワーク接続確認**:
```bash
# Anthropic API への接続確認
curl -I https://api.anthropic.com/

# DNS 解決確認
nslookup api.anthropic.com
```

2. **API キー再確認**:
```bash
# キーの形式確認（sk-ant-api で始まる）
echo $ANTHROPIC_API_KEY | head -c 20

# 新しいキーでテスト
export ANTHROPIC_API_KEY="your-new-key"
```

3. **モデル名確認**:
```bash
# 正しいモデル名を使用
export ANTHROPIC_MODEL="claude-3-haiku-20240307"
```

4. **タイムアウト調整**:
```python
# LLM timeout configuration
export LLM_TIMEOUT=60  # seconds
```

### 問題: OpenAI Embedding エラー

**エラーメッセージ例**:
```
openai.error.RateLimitError: Rate limit exceeded
```

**解決法**:

1. **レート制限の確認**:
```python
# embedding_test.py
import openai
import os

async def test_embedding():
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    try:
        response = openai.Embedding.create(
            model="text-embedding-3-small",
            input="test embedding"
        )
        print("✅ OpenAI Embedding test successful")
        print(f"   Dimensions: {len(response['data'][0]['embedding'])}")
        return True
    except Exception as e:
        print(f"❌ OpenAI Embedding test failed: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_embedding())
```

2. **バックオフ戦略の有効化**:
```bash
# Retry settings
export OPENAI_MAX_RETRIES=5
export OPENAI_RETRY_DELAY=1.0
```

### 問題: LLM 応答が遅い

**解決法**:

1. **タイムアウト設定の調整**:
```bash
export LLM_TIMEOUT=30
export EMBEDDING_TIMEOUT=10
```

2. **非同期処理の確認**:
```python
# 非同期記憶保存でレスポンス時間短縮
await emotion_core.save_memory_async(
    user_message="test",
    ai_message="test",
    user_id="user123",
    background=True  # バックグラウンド処理
)
```

3. **バッチ処理の活用**:
```python
# 複数の記憶を一括処理
await emotion_core.batch_save_memories(conversations_list)
```

---

## 🌐 ネットワークと接続の問題

### 問題: 接続タイムアウト

**エラーメッセージ例**:
```
httpx.ConnectTimeout: Connection timeout
```

**解決法**:

1. **ファイアウォール確認**:
```bash
# ポート 8000 の確認
sudo netstat -tulpn | grep :8000

# ファイアウォール設定確認
sudo ufw status
sudo iptables -L
```

2. **タイムアウト設定調整**:
```bash
# クライアント側
export HTTP_TIMEOUT=60

# サーバー側
export UVICORN_TIMEOUT_KEEP_ALIVE=65
```

3. **プロキシ設定**:
```bash
# プロキシ環境での設定
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
export NO_PROXY=localhost,127.0.0.1
```

### 問題: CORS エラー

**エラーメッセージ例**:
```
Access to fetch at 'http://localhost:8000/save' from origin 'http://localhost:3000' 
has been blocked by CORS policy
```

**解決法**:

1. **CORS 設定の確認**:
```bash
# 許可オリジンの設定
export CORS_ALLOWED_ORIGINS="http://localhost:3000,https://yourdomain.com"

# すべてのオリジンを許可（開発時のみ）
export CORS_ALLOWED_ORIGINS="*"
```

2. **ブラウザでの確認**:
```javascript
// ブラウザコンソールでテスト
fetch('http://localhost:8000/health/', {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

---

## ⚡ パフォーマンスの問題

### 問題: 応答が遅い

**症状**: API レスポンス時間が 5 秒以上

**解決法**:

1. **パフォーマンス監視の有効化**:
```bash
# デバッグモードでパフォーマンス詳細を表示
export DEBUG_MODE=true
export LOG_LEVEL=DEBUG
```

2. **ボトルネック特定**:
```python
# performance_profiler.py
import time
import asyncio
from emotion_mem_client import EmotionMemCoreClient

async def performance_test():
    client = EmotionMemCoreClient()
    
    # 保存テスト
    start_time = time.time()
    result = await client.save_memory(
        "パフォーマンステスト",
        "テスト応答",
        "perf_test_user"
    )
    save_time = time.time() - start_time
    print(f"💾 保存時間: {save_time:.2f}秒")
    
    # 検索テスト
    start_time = time.time()
    results = await client.search_memories(
        "パフォーマンス",
        "perf_test_user"
    )
    search_time = time.time() - start_time
    print(f"🔍 検索時間: {search_time:.2f}秒")
    
    # バッチテスト
    conversations = [
        {"user_message": f"メッセージ{i}", "ai_message": f"応答{i}", "user_id": "perf_test_user"}
        for i in range(10)
    ]
    
    start_time = time.time()
    batch_result = await client.batch_save_memories(conversations)
    batch_time = time.time() - start_time
    print(f"📦 バッチ保存時間: {batch_time:.2f}秒 (10件)")
    print(f"   平均: {batch_time/10:.2f}秒/件")

if __name__ == "__main__":
    asyncio.run(performance_test())
```

3. **最適化設定**:
```bash
# 接続プール最適化
export HTTP_MAX_CONNECTIONS=100
export HTTP_MAX_KEEPALIVE_CONNECTIONS=20

# LLM 並行処理制限
export LLM_MAX_CONCURRENT_REQUESTS=5

# キャッシュ有効化
export ENABLE_MEMORY_CACHE=true
export CACHE_TTL_SECONDS=300
```

### 問題: メモリ使用量が多い

**解決法**:

1. **メモリ使用量監視**:
```python
# memory_monitor.py
import psutil
import os

def monitor_memory():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    print(f"📊 メモリ使用量:")
    print(f"   RSS: {memory_info.rss / 1024 / 1024:.1f} MB")
    print(f"   VMS: {memory_info.vms / 1024 / 1024:.1f} MB")
    print(f"   使用率: {process.memory_percent():.1f}%")

if __name__ == "__main__":
    monitor_memory()
```

2. **メモリ最適化設定**:
```bash
# バッチサイズ制限
export BATCH_SIZE_LIMIT=50

# ChromaDB メモリ制限
export CHROMA_MAX_MEMORY_MB=1024

# ガベージコレクション調整
export PYTHONHASHSEED=0
```

---

## 🐳 Docker 関連の問題

### 問題: Docker イメージビルドエラー

**解決法**:

1. **キャッシュクリア**:
```bash
# Docker キャッシュクリア
docker system prune -a

# 強制リビルド
docker-compose build --no-cache
```

2. **ビルドログ確認**:
```bash
# 詳細ログでビルド
docker-compose build --progress=plain

# 特定サービスのみビルド
docker-compose build emotionmemcore-api
```

3. **Dockerfile の修正確認**:
```dockerfile
# Base image の確認
FROM python:3.11-slim

# 依存関係の確認
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev --no-interaction --no-ansi
```

### 問題: コンテナが起動しない

**解決法**:

1. **ログ確認**:
```bash
# コンテナログ確認
docker-compose logs emotionmemcore-api

# リアルタイムログ
docker-compose logs -f
```

2. **環境変数確認**:
```bash
# コンテナ内環境変数確認
docker-compose exec emotionmemcore-api env | grep -E "(ANTHROPIC|OPENAI|DEBUG)"
```

3. **ヘルスチェック確認**:
```bash
# コンテナヘルスチェック
docker-compose ps
docker inspect <container_id> | grep Health -A 10
```

### 問題: ボリュームマウントエラー

**エラーメッセージ例**:
```
Error: Bind mount failed: no such file or directory
```

**解決法**:

1. **パス確認**:
```bash
# ホスト側ディレクトリ作成
mkdir -p ./chroma_db
mkdir -p ./logs

# 権限設定
chmod 755 ./chroma_db
chmod 755 ./logs
```

2. **docker-compose.yml 確認**:
```yaml
volumes:
  - ./chroma_db:/app/data/chroma_db
  - ./logs:/app/logs
```

---

## 📊 ログとデバッグ

### ログレベル設定

```bash
# 詳細ログ有効化
export LOG_LEVEL=DEBUG
export DEBUG_MODE=true

# 構造化ログ（JSON形式）
export LOG_FORMAT=json

# ログファイル出力
export LOG_FILE=./logs/emotionmemcore.log
```

### デバッグエンドポイント活用

```bash
# システム情報取得
curl http://localhost:8000/debug/system-info

# 最後の保存操作確認
curl http://localhost:8000/debug/last-save

# テストデータ作成
curl -X POST http://localhost:8000/debug/test-memory \
  -H "Content-Type: application/json" \
  -d '{"count": 5, "user_id": "debug_user"}'
```

### ログ解析ツール

```python
# log_analyzer.py
import json
import re
from datetime import datetime
from collections import defaultdict

def analyze_logs(log_file_path):
    """ログファイル解析"""
    
    error_counts = defaultdict(int)
    response_times = []
    endpoints = defaultdict(int)
    
    with open(log_file_path, 'r') as f:
        for line in f:
            try:
                if line.strip().startswith('{'):
                    # JSON 形式ログ
                    log_entry = json.loads(line)
                    
                    # エラー集計
                    if log_entry.get('level') == 'ERROR':
                        error_type = log_entry.get('event', 'unknown_error')
                        error_counts[error_type] += 1
                    
                    # レスポンス時間集計
                    if 'processing_time_ms' in log_entry:
                        response_times.append(log_entry['processing_time_ms'])
                    
                    # エンドポイント使用量
                    if 'endpoint' in log_entry:
                        endpoints[log_entry['endpoint']] += 1
                        
                else:
                    # テキスト形式ログの解析
                    if 'ERROR' in line:
                        error_counts['text_error'] += 1
                    
                    # レスポンス時間抽出
                    time_match = re.search(r'(\d+\.?\d*)ms', line)
                    if time_match:
                        response_times.append(float(time_match.group(1)))
                        
            except json.JSONDecodeError:
                continue
    
    # 結果表示
    print("📊 ログ解析結果")
    print("=" * 40)
    
    if error_counts:
        print("❌ エラー統計:")
        for error_type, count in error_counts.items():
            print(f"   {error_type}: {count}回")
    
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        print(f"\n⏱️  レスポンス時間統計:")
        print(f"   平均: {avg_time:.2f}ms")
        print(f"   最大: {max_time:.2f}ms") 
        print(f"   最小: {min_time:.2f}ms")
        print(f"   サンプル数: {len(response_times)}")
    
    if endpoints:
        print(f"\n🔗 エンドポイント使用統計:")
        for endpoint, count in sorted(endpoints.items(), key=lambda x: x[1], reverse=True):
            print(f"   {endpoint}: {count}回")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        analyze_logs(sys.argv[1])
    else:
        print("使用法: python log_analyzer.py <log_file_path>")
```

---

## 🔧 よくある設定ミス

### 1. 環境変数の設定ミス

**問題**: 設定が反映されない

**確認方法**:
```bash
# 環境変数一覧表示
printenv | grep -E "(ANTHROPIC|OPENAI|DEBUG|ENVIRONMENT)"

# .env ファイル読み込み確認
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('Environment:', os.getenv('ENVIRONMENT'))
print('Debug Mode:', os.getenv('DEBUG_MODE'))
print('LLM Mock:', os.getenv('LLM_MOCK_MODE'))
"
```

### 2. データベースパス設定ミス

**問題**: データが保存されない

**確認方法**:
```bash
# 実際の保存先確認
python -c "
import os
from infrastructure.config.settings import get_settings
settings = get_settings()
print('ChromaDB Path:', settings.chroma_persist_directory)
print('Exists:', os.path.exists(settings.chroma_persist_directory))
"
```

### 3. ポート番号の競合

**問題**: 他のサービスとポートが競合

**確認・解決**:
```bash
# ポート使用状況確認
netstat -tulpn | grep :8000

# 代替ポート使用
export PORT=8001
```

---

## 🆘 緊急時の対処法

### システム完全停止時

1. **すべてのプロセス強制終了**:
```bash
# EmotionMemCore 関連プロセス確認
ps aux | grep -i emotion

# 強制終了
pkill -f emotionmemcore
pkill -f uvicorn

# Docker コンテナ停止
docker-compose down -v
```

2. **最小構成での再起動**:
```bash
# 最小設定で起動
export ENVIRONMENT=development
export DEBUG_MODE=true
export LLM_MOCK_MODE=true
export AUTH_ENABLED=false
export RATE_LIMIT_ENABLED=false

python main.py
```

### データ復旧

1. **バックアップからの復元**:
```bash
# 最新バックアップ確認
ls -la backups/

# 復元実行
cp -r backups/latest/chroma_db ./chroma_db_restored
export CHROMA_PERSIST_DIRECTORY=./chroma_db_restored
```

2. **部分的データ復旧**:
```python
# data_recovery.py
import chromadb
import os
import shutil

def recover_data():
    """データ復旧スクリプト"""
    
    backup_paths = [
        "./chroma_db_backup",
        "./backups/latest/chroma_db",
        "./dev_chroma_db"
    ]
    
    recovered_data = []
    
    for backup_path in backup_paths:
        if os.path.exists(backup_path):
            try:
                client = chromadb.PersistentClient(path=backup_path)
                collections = client.list_collections()
                
                for collection in collections:
                    count = collection.count()
                    if count > 0:
                        print(f"✅ Found {count} items in {collection.name} at {backup_path}")
                        recovered_data.append((backup_path, collection.name, count))
                        
            except Exception as e:
                print(f"❌ Failed to read {backup_path}: {e}")
    
    if recovered_data:
        print("\n📋 復旧可能なデータ:")
        for path, collection, count in recovered_data:
            print(f"   {path}/{collection}: {count} items")
        
        # 最大のデータソースを推奨
        best_backup = max(recovered_data, key=lambda x: x[2])
        print(f"\n💡 推奨復元先: {best_backup[0]}")
        print(f"   復元コマンド: cp -r {best_backup[0]} ./chroma_db_recovered")
    else:
        print("❌ 復旧可能なデータが見つかりませんでした")

if __name__ == "__main__":
    recover_data()
```

### サポート情報収集

問題報告時に必要な情報を収集するスクリプト:

```python
# collect_support_info.py
import os
import sys
import json
import subprocess
from datetime import datetime

def collect_support_info():
    """サポート用システム情報収集"""
    
    info = {
        "timestamp": datetime.now().isoformat(),
        "system": {},
        "environment": {},
        "dependencies": {},
        "logs": {},
        "errors": []
    }
    
    # システム情報
    try:
        info["system"] = {
            "platform": sys.platform,
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "user": os.getenv("USER", "unknown")
        }
    except Exception as e:
        info["errors"].append(f"Failed to collect system info: {e}")
    
    # 環境変数
    env_vars = [
        "ENVIRONMENT", "DEBUG_MODE", "LLM_MOCK_MODE", 
        "AUTH_ENABLED", "RATE_LIMIT_ENABLED",
        "CHROMA_PERSIST_DIRECTORY", "PORT"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            info["environment"][var] = value
    
    # API キー存在確認（値は含めない）
    api_keys = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "MASTER_API_KEY"]
    for key in api_keys:
        info["environment"][f"{key}_set"] = bool(os.getenv(key))
    
    # 依存関係バージョン
    try:
        import chromadb
        info["dependencies"]["chromadb"] = chromadb.__version__
    except:
        info["dependencies"]["chromadb"] = "not_installed"
    
    try:
        import fastapi
        info["dependencies"]["fastapi"] = fastapi.__version__
    except:
        info["dependencies"]["fastapi"] = "not_installed"
    
    # ディレクトリ存在確認
    directories = ["./chroma_db", "./dev_chroma_db", "./logs", "./backups"]
    for dir_path in directories:
        info["environment"][f"{dir_path}_exists"] = os.path.exists(dir_path)
    
    # 最新ログ（エラーのみ）
    log_files = ["./logs/emotionmemcore.log", "./app.log"]
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    error_lines = [line for line in lines[-100:] if 'ERROR' in line]
                    if error_lines:
                        info["logs"][log_file] = error_lines[-10:]  # 最新10個のエラー
            except Exception as e:
                info["errors"].append(f"Failed to read {log_file}: {e}")
    
    # 出力
    output_file = f"support_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    
    print(f"📄 サポート情報を収集しました: {output_file}")
    print("   このファイルを GitHub Issues に添付してください")
    
    return output_file

if __name__ == "__main__":
    collect_support_info()
```

---

## 📞 サポートリソース

### 公式サポート

- **GitHub Issues**: [問題報告・機能要望](https://github.com/your-username/EmotionMemCore/issues)
- **Discussions**: [質問・議論](https://github.com/your-username/EmotionMemCore/discussions)
- **Documentation**: [公式ドキュメント](http://localhost:8000/docs)

### 問題報告時のチェックリスト

- [ ] 診断スクリプトの実行結果
- [ ] エラーメッセージの完全なコピー
- [ ] 環境情報（OS、Pythonバージョン等）
- [ ] 再現手順の詳細
- [ ] 期待する動作と実際の動作
- [ ] ログファイル（エラー部分）
- [ ] 設定ファイル（機密情報は除く）

### コミュニティヘルプ

緊急度に応じて適切なチャンネルを選択してください：

- 🔴 **緊急**: システム全体が動作しない → GitHub Issues
- 🟡 **重要**: 機能が部分的に動作しない → GitHub Issues  
- 🟢 **質問**: 使い方がわからない → GitHub Discussions
- 🔵 **提案**: 新機能や改善案 → GitHub Discussions

---

**このガイドで解決しない問題がある場合は、遠慮なくサポートにお問い合わせください！** 🤝