# 🔌 EmotionMemCore 連携方法 - 超わかりやすい説明

> **「起動したけど、どうやって使うの？」という方へ**

---

## 🤔 EmotionMemCore の仕組み

### 📡 APIサーバーとして動作

EmotionMemCore を起動すると、あなたのパソコンで **APIサーバー** が動きます。

```
あなたのPC
├── EmotionMemCore (ポート8000で待機中)
│   └── 「データください！」と待っている状態
│
└── あなたのAIソフト（AITuberKit等）
    └── EmotionMemCore にデータを送る必要がある
```

### 🎯 つまり何が必要？

**他のソフトから EmotionMemCore に「会話データを送る」コードが必要です！**

---

## 🚀 超簡単！3つの連携方法

### 方法1: コピペで使える Python コード

#### 📋 最小限のコード（これだけでOK！）

```python
import requests

# 記憶を保存する関数
def save_memory(user_msg, ai_msg):
    try:
        requests.post("http://localhost:8000/save", json={
            "user_message": user_msg,
            "ai_message": ai_msg,
            "user_id": "test_user"
        })
    except:
        pass  # エラーは無視

# 使い方
save_memory("こんにちは", "こんにちは！元気ですか？")
```

#### 🔍 記憶を検索する関数

```python
# 記憶を検索する関数
def search_memory(keyword):
    try:
        response = requests.post("http://localhost:8000/search", json={
            "query": keyword,
            "user_id": "test_user"
        })
        return response.json().get("results", [])
    except:
        return []

# 使い方
memories = search_memory("こんにちは")
print(memories)  # 過去の「こんにちは」に関する記憶
```

### 方法2: JavaScript (Node.js) での連携

```javascript
// 記憶を保存
async function saveMemory(userMsg, aiMsg) {
    try {
        await fetch('http://localhost:8000/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                user_message: userMsg,
                ai_message: aiMsg,
                user_id: "test_user"
            })
        });
    } catch (e) {
        // エラーは無視
    }
}

// 記憶を検索
async function searchMemory(keyword) {
    try {
        const response = await fetch('http://localhost:8000/search', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                query: keyword,
                user_id: "test_user"
            })
        });
        const data = await response.json();
        return data.results || [];
    } catch (e) {
        return [];
    }
}
```

### 方法3: cURL コマンド（テスト用）

```bash
# 記憶を保存
curl -X POST http://localhost:8000/save \
  -H "Content-Type: application/json" \
  -d '{
    "user_message": "今日は楽しかった",
    "ai_message": "それは良かったですね！",
    "user_id": "test_user"
  }'

# 記憶を検索
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "楽しかった",
    "user_id": "test_user"
  }'
```

---

## 🎮 具体的な使用例

### 例1: シンプルなチャットボット

```python
import requests

class SimpleBot:
    def __init__(self):
        self.api_url = "http://localhost:8000"
        self.user_id = "chat_user"
    
    def chat(self, user_input):
        # 1. 関連する過去の記憶を検索
        memories = self.search_memories(user_input)
        
        # 2. AIの返答を生成（ここは既存のAI処理）
        if memories:
            context = f"過去の会話: {memories[0]['summary']}\n"
            ai_response = f"以前{memories[0]['summary']}とおっしゃってましたね。{user_input}について..."
        else:
            ai_response = f"{user_input}について、初めてお聞きしました。"
        
        # 3. 会話を記憶として保存
        self.save_memory(user_input, ai_response)
        
        return ai_response
    
    def save_memory(self, user_msg, ai_msg):
        try:
            requests.post(f"{self.api_url}/save", json={
                "user_message": user_msg,
                "ai_message": ai_msg,
                "user_id": self.user_id
            })
        except:
            pass
    
    def search_memories(self, query):
        try:
            response = requests.post(f"{self.api_url}/search", json={
                "query": query,
                "user_id": self.user_id,
                "top_k": 3
            })
            return response.json().get("results", [])
        except:
            return []

# 使用例
bot = SimpleBot()
response = bot.chat("今日は映画を見ました")
print(response)
```

### 例2: AITuberKit 連携（実践的）

```python
# AITuberKit の既存コードに追加

class AITuberWithMemory:
    def __init__(self, existing_aituber):
        self.aituber = existing_aituber
        self.memory_api = "http://localhost:8000"
    
    def on_chat_message(self, username, message):
        # 1. EmotionMemCore から過去の記憶を取得
        memories = self._get_memories(message, username)
        
        # 2. 記憶を考慮してAITuberが返答
        if memories:
            # 過去の会話を覚えている返答
            context = self._build_context(memories)
            response = self.aituber.generate_response_with_context(message, context)
        else:
            # 通常の返答
            response = self.aituber.generate_response(message)
        
        # 3. 今回の会話を記憶として保存
        self._save_memory(username, message, response)
        
        return response
    
    def _get_memories(self, query, user_id):
        try:
            res = requests.post(f"{self.memory_api}/search", json={
                "query": query,
                "user_id": user_id,
                "top_k": 2
            })
            return res.json().get("results", [])
        except:
            return []
    
    def _save_memory(self, user_id, user_msg, ai_msg):
        try:
            requests.post(f"{self.memory_api}/save", json={
                "user_message": user_msg,
                "ai_message": ai_msg,
                "user_id": user_id
            })
        except:
            pass
    
    def _build_context(self, memories):
        context = "過去の会話:\n"
        for mem in memories:
            context += f"- {mem['summary']}\n"
        return context
```

---

## 🎯 動作確認の手順

### 1️⃣ EmotionMemCore が動いているか確認

ブラウザで以下にアクセス：
- http://localhost:8000/docs （API仕様書）
- http://localhost:8080 （ダッシュボード）

### 2️⃣ テストデータを送信

Python で簡単テスト：
```python
import requests

# テスト保存
response = requests.post("http://localhost:8000/save", json={
    "user_message": "テストです",
    "ai_message": "テスト受信しました",
    "user_id": "test"
})
print(response.json())  # {"success": true, "memory_id": "..."}
```

### 3️⃣ ダッシュボードで確認

http://localhost:8080 の「記憶一覧」で保存されたか確認

---

## 💡 よくある質問

### Q: 「他のPCから使いたい」

A: `localhost` を実際のIPアドレスに変更：
```python
# 例: 192.168.1.100 がEmotionMemCoreが動いているPCのIP
api_url = "http://192.168.1.100:8000"
```

### Q: 「保存されているか分からない」

A: ダッシュボードで確認するか、検索してみる：
```python
# 全ての記憶を取得
response = requests.get("http://localhost:8000/memories?limit=100")
print(response.json())
```

### Q: 「エラーが出る」

A: EmotionMemCore が起動しているか確認：
1. `start_emotionmemcore.bat` が動いている
2. 黒い画面（コンソール）が開いている
3. http://localhost:8000/docs にアクセスできる

---

## 🚀 今すぐ試せる完全サンプル

```python
# test_emotion_memory.py として保存

import requests
import time

def main():
    print("🤖 EmotionMemCore 連携テスト開始")
    
    # 1. 記憶を保存
    print("\n📝 記憶を保存中...")
    save_response = requests.post("http://localhost:8000/save", json={
        "user_message": "今日は天気がいいですね",
        "ai_message": "本当にいい天気ですね！お出かけ日和です",
        "user_id": "demo_user"
    })
    print(f"保存結果: {save_response.json()}")
    
    time.sleep(2)
    
    # 2. 記憶を検索
    print("\n🔍 記憶を検索中...")
    search_response = requests.post("http://localhost:8000/search", json={
        "query": "天気",
        "user_id": "demo_user"
    })
    results = search_response.json().get("results", [])
    
    print(f"\n見つかった記憶: {len(results)}件")
    for i, memory in enumerate(results):
        print(f"\n記憶 {i+1}:")
        print(f"  概要: {memory['summary']}")
        print(f"  感情: {', '.join(memory['emotions'])}")
        print(f"  スコア: {memory['score']}")
    
    print("\n✅ テスト完了！")
    print("📊 ダッシュボード: http://localhost:8080")

if __name__ == "__main__":
    main()
```

実行方法：
```bash
python test_emotion_memory.py
```

---

## 🎉 まとめ

EmotionMemCore は **APIサーバー** なので：

1. **起動する** → localhost:8000 で待機
2. **データを送る** → HTTP POST リクエスト
3. **結果を受け取る** → JSON レスポンス

これだけです！

コピペで使えるコードを、あなたのAIソフトに追加するだけで、記憶機能が使えるようになります！ 🚀