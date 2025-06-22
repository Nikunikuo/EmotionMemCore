# 🎭 AITuberKit 連携ガイド

> **EmotionMemCore を AITuberKit と連携する手順**  
> YouTube見るだけ層でも3分で設定完了！

---

## 🎯 **この連携でできること**

### ✨ **AITuber が記憶を持つ！**
- **視聴者との過去の会話を覚える**
- **感情に応じた自然な反応**
- **「この前話した○○の件」が通じる**
- **長期的な関係性構築**

### 📊 **具体例**
```
視聴者: 「おはよう！」
AITuber: 「おはようございます！昨日話していた映画、見ましたか？」
          ↑ 過去の会話を EmotionMemCore から検索して返答
```

---

## 🚀 **超簡単！3ステップ連携**

### 📋 **必要なもの**
- ✅ AITuberKit（既にお使いのもの）
- ✅ EmotionMemCore（この記事で設定）
- ✅ 3分の設定時間

### ⚡ **ステップ1: EmotionMemCore 起動**

#### **最も簡単な方法（推奨）**
```
1. EmotionMemCore フォルダの「start_emotionmemcore.bat」をダブルクリック
2. 自動でブラウザが開く
3. 「機能テスト」で動作確認
```

#### **手動起動する場合**
```bash
# コマンドプロンプトで実行
cd EmotionMemCore
python main.py

# 別のコマンドプロンプトで
python run_dashboard.py
```

### ⚡ **ステップ2: AITuberKit 設定**

#### **config.json に追加**
```json
{
  "emotion_memory": {
    "enabled": true,
    "api_url": "http://localhost:8000",
    "user_id": "aituber_viewer",
    "auto_save": true,
    "auto_search": true
  }
}
```

#### **main.py に記憶機能追加**
```python
import requests

class AITuberWithMemory:
    def __init__(self):
        self.memory_api = "http://localhost:8000"
        self.user_id = "aituber_viewer"
    
    def chat_with_memory(self, user_message):
        # 1. 過去の記憶を検索
        memories = self.search_memory(user_message)
        
        # 2. 記憶を踏まえて返答生成
        context = self.build_context(memories)
        ai_response = self.generate_response(user_message, context)
        
        # 3. 会話を記憶として保存
        self.save_memory(user_message, ai_response)
        
        return ai_response
    
    def search_memory(self, query):
        """過去の記憶を検索"""
        try:
            response = requests.post(f"{self.memory_api}/search", json={
                "query": query,
                "user_id": self.user_id,
                "top_k": 3
            })
            return response.json().get("results", [])
        except:
            return []  # エラー時は空リスト
    
    def save_memory(self, user_msg, ai_msg):
        """会話を記憶として保存"""
        try:
            requests.post(f"{self.memory_api}/save", json={
                "user_message": user_msg,
                "ai_message": ai_msg,
                "user_id": self.user_id
            })
        except:
            pass  # エラー時は無視
    
    def build_context(self, memories):
        """記憶から文脈を構築"""
        if not memories:
            return ""
        
        context = "過去の会話: "
        for memory in memories:
            context += f"「{memory['summary']}」 "
        return context
```

### ⚡ **ステップ3: 動作確認**

#### **テスト会話**
```
1. AITuberKit を起動
2. 「今日は映画を見ました」と入力
3. AITuber が返答
4. EmotionMemCore のダッシュボードで記憶が保存されているか確認
5. 「映画の話」と検索して、記憶が見つかるか確認
```

---

## 🎨 **レベル別カスタマイズ**

### 👶 **初心者レベル（コピペでOK）**

#### **chat_function.py** （新規作成）
```python
import requests

# EmotionMemCore 連携関数
def chat_with_emotion_memory(user_message, user_id="viewer"):
    """記憶機能付きチャット"""
    api_url = "http://localhost:8000"
    
    # 過去の記憶を検索
    try:
        search_response = requests.post(f"{api_url}/search", json={
            "query": user_message,
            "user_id": user_id,
            "top_k": 2
        })
        memories = search_response.json().get("results", [])
    except:
        memories = []
    
    # 記憶を踏まえてプロンプト作成
    context = ""
    if memories:
        context = f"過去の会話: {memories[0]['summary']} "
    
    # AI返答生成（既存のコードを使用）
    prompt = f"{context}ユーザー: {user_message}\nAI:"
    ai_response = generate_ai_response(prompt)  # 既存の関数
    
    # 会話を記憶として保存
    try:
        requests.post(f"{api_url}/save", json={
            "user_message": user_message,
            "ai_message": ai_response,
            "user_id": user_id
        })
    except:
        pass
    
    return ai_response

# 既存のチャット処理を置き換え
def on_user_message(message):
    response = chat_with_emotion_memory(message)
    send_to_chat(response)
```

### 🧑‍💻 **中級者レベル（感情考慮）**

```python
def advanced_chat_with_memory(user_message, user_id="viewer"):
    """感情を考慮した高度なチャット"""
    api_url = "http://localhost:8000"
    
    # 感情フィルター付きで記憶検索
    emotions = detect_user_emotion(user_message)  # 既存の感情検出
    
    search_response = requests.post(f"{api_url}/search", json={
        "query": user_message,
        "user_id": user_id,
        "emotions": emotions,
        "top_k": 3
    })
    
    memories = search_response.json().get("results", [])
    
    # 感情に応じたトーン調整
    tone = get_response_tone(emotions, memories)
    
    # プロンプト生成
    prompt = build_contextual_prompt(user_message, memories, tone)
    ai_response = generate_ai_response(prompt)
    
    # 保存
    requests.post(f"{api_url}/save", json={
        "user_message": user_message,
        "ai_message": ai_response,
        "user_id": user_id,
        "session_id": get_current_session()
    })
    
    return ai_response
```

### 🚀 **上級者レベル（完全統合）**

```python
class EmotionMemoryAITuber:
    """EmotionMemCore 完全統合 AITuber"""
    
    def __init__(self, config):
        self.memory_api = config.get("memory_api_url", "http://localhost:8000")
        self.emotion_threshold = config.get("emotion_threshold", 0.7)
        self.memory_context_limit = config.get("context_limit", 3)
    
    async def process_message(self, user_message, user_id, session_id):
        """非同期メッセージ処理"""
        # 並行処理で記憶検索と感情分析
        memory_task = self.search_memories(user_message, user_id)
        emotion_task = self.analyze_emotion(user_message)
        
        memories, emotions = await asyncio.gather(memory_task, emotion_task)
        
        # 文脈構築
        context = self.build_rich_context(memories, emotions)
        
        # AI応答生成
        response = await self.generate_response(user_message, context)
        
        # バックグラウンドで保存
        asyncio.create_task(self.save_memory(
            user_message, response, user_id, session_id
        ))
        
        return response
    
    def get_memory_statistics(self, user_id):
        """ユーザーの記憶統計取得"""
        response = requests.get(f"{self.memory_api}/memories", params={
            "user_id": user_id,
            "limit": 100
        })
        return self.analyze_memory_patterns(response.json())
```

---

## 📊 **実際の使用例**

### 🎪 **配信での活用シーン**

#### **シーン1: 常連視聴者との会話**
```
視聴者A: 「おはよう！」
AITuber: 「おはようございます！昨日お話しした資格試験の勉強、進んでますか？」
         ↑ 前日の「勉強頑張ってる」記憶から自動生成

視聴者A: 「実は合格しました！」
AITuber: 「えー！おめでとうございます！頑張っていらっしゃったので、
         本当に嬉しいです！」
         ↑ 過去の「頑張ってる」記憶 + 現在の「合格」で感情豊かに反応
```

#### **シーン2: 初見視聴者への対応**
```
視聴者B: 「初めまして！」
AITuber: 「初めまして！ようこそいらっしゃいました。
         どちらからいらしたんですか？」
         ↑ 記憶なしでも自然な初見対応

視聴者B: 「YouTubeのおすすめから来ました」
AITuber: 「おすすめに出てきてくださったんですね！ありがとうございます」
         ↑ この会話が記憶され、次回は「おすすめから来てくださった方」として認識
```

### 🎮 **ゲーム配信での活用**
```
視聴者C: 「このゲーム難しそう」
AITuber: 「確かに難しいですね。でも前回一緒に攻略した○○ステージより
         は簡単だと思います！」
         ↑ 過去のゲーム記憶から比較コメント

視聴者C: 「あー、あのステージね！懐かしい」
AITuber: 「覚えててくださったんですね！嬉しいです」
         ↑ 共通記憶での親近感演出
```

---

## 🛠️ **トラブルシューティング**

### ❌ **よくある問題**

#### **「記憶機能が働かない」**
```bash
# 解決手順
1. EmotionMemCore が起動しているか確認
   → http://localhost:8080 にアクセス

2. APIエンドポイントが正しいか確認
   → http://localhost:8000/docs で仕様確認

3. コードのリクエスト部分をデバッグ
   → print文でレスポンスを確認
```

#### **「エラーで落ちる」**
```python
# エラー対策コード
def safe_memory_request(url, data):
    """安全な記憶API呼び出し"""
    try:
        response = requests.post(url, json=data, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"記憶API エラー: {e}")
    return None  # エラー時は None を返す
```

#### **「記憶が多すぎて重い」**
```python
# パフォーマンス最適化
search_params = {
    "query": user_message,
    "user_id": user_id,
    "top_k": 2,  # 結果数を制限
    "emotions": ["喜び", "興奮"]  # 関連感情のみ
}
```

### 🎯 **動作確認手順**

#### **手動テスト**
```
1. EmotionMemCore ダッシュボードを開く
2. 「機能テスト」でサンプルデータ作成
3. 「記憶検索」で検索動作確認
4. AITuberKit でテスト会話
5. ダッシュボードで新しい記憶が追加されているか確認
```

#### **自動テスト**
```python
def test_memory_integration():
    """記憶連携テスト"""
    # テストメッセージ
    test_msg = "テスト会話です"
    
    # 保存テスト
    save_result = save_memory(test_msg, "テスト返答")
    assert save_result is not None
    
    # 検索テスト
    search_result = search_memory("テスト")
    assert len(search_result) > 0
    
    print("✅ 記憶連携テスト成功")
```

---

## 🎉 **おめでとうございます！**

これで AITuberKit と EmotionMemCore の連携が完了しました！

### 🌟 **これで実現できること**
- ✅ **記憶を持つAITuber** - 視聴者との継続的関係
- ✅ **感情豊かな反応** - 38種類の感情分析
- ✅ **自然な会話** - 過去の文脈を踏まえた返答
- ✅ **長期的成長** - 時間と共に記憶が蓄積

### 📈 **さらなる改善アイデア**
- **定期配信での「今週の思い出」コーナー**
- **視聴者別の「記憶アルバム」機能**
- **感情グラフでの「今日の配信の盛り上がり」分析**
- **記念日の自動リマインド**

AITuber と視聴者の、より深い絆を育んでください！ 🤖💕