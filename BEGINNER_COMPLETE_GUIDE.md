# 🎯 EmotionMemCore 超初心者完全ガイド

> **YouTube見るだけ層でも3分で使える！**  
> プログラミング知識ゼロでもAIに記憶を持たせられます

---

## 🤔 これは何？

**EmotionMemCore** は、AIとの会話を **感情付きで記憶** するシステムです。

### 🎭 具体的にできること

#### Before（普通のAI）
```
あなた: 「おはよう」
AI: 「おはようございます」

あなた: 「昨日の映画の話だけど...」  
AI: 「すみません、何の映画でしょうか？」← 覚えてない
```

#### After（EmotionMemCore使用）
```
あなた: 「おはよう」
AI: 「おはようございます」

あなた: 「昨日の映画の話だけど...」
AI: 「昨日お話しした○○の映画ですね！」← 覚えてる！
```

### ✨ 特徴
- 🎭 **38種類の感情** を自動分析
- 🔍 **自然な日本語** で記憶を検索
- 📊 **美しいグラフ** で感情変化を可視化
- 🔌 **AITuberKit等** との簡単連携

---

## 🚀 超簡単！3つの使い方

### 🥇 方法1: ワンクリック起動（最も簡単）

#### 準備
1. `quick_setup.bat` をダブルクリック
2. 指示に従って「Y」を押すだけ
3. 完了！

#### 使用
1. `start_emotionmemcore.bat` をダブルクリック
2. ブラウザが自動で開く
3. 「機能テスト」ボタンをクリック

### 🥈 方法2: 実行ファイル版（Python不要）

#### 準備
1. `EmotionMemCore.exe` をダウンロード
2. デスクトップに保存
3. 完了！

#### 使用
1. `EmotionMemCore.exe` をダブルクリック
2. ブラウザが自動で開く
3. 楽しむ！

### 🥉 方法3: 手動セットアップ（上級者向け）

詳細は `README.md` をご覧ください。

---

## 🎮 実際の使い方体験

### 1️⃣ 機能テストで体験

1. ブラウザで「機能テスト」をクリック
2. 以下のような会話を入力:

```
ユーザーメッセージ: 今日はとても楽しかった！映画を見に行きました
AIメッセージ: それは良かったですね！どんな映画でしたか？
```

3. 「保存」ボタンをクリック
4. 自動で感情分析されて記憶に保存！

### 2️⃣ 記憶を検索してみる

1. 「記憶検索」をクリック
2. 検索窓に「映画」と入力
3. さっき保存した記憶が見つかる！

### 3️⃣ 感情グラフを見る

1. 「記憶可視化」をクリック  
2. 美しいグラフで感情の変化を確認
3. 「喜び」「楽しさ」などの感情が可視化される

---

## 🔌 AITuberKit との連携（コピペでOK）

### 🎯 やりたいこと
AITuberが視聴者の過去の会話を覚えて、自然な会話をする

### 📋 手順

#### Step 1: EmotionMemCore を起動
```bash
# start_emotionmemcore.bat をダブルクリック
```

#### Step 2: AITuberKit に以下をコピペ

**chat_function.py** （新規作成）
```python
import requests

def chat_with_memory(user_message, user_id="viewer"):
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
    response = chat_with_memory(message)
    send_to_chat(response)
```

#### Step 3: 動作確認
1. AITuberKit を起動
2. 「映画を見ました」とチャット
3. 別の日に「映画の話」とチャット
4. AITuberが過去の会話を覚えている！

---

## 💡 トラブルシューティング

### ❓ よくある質問

#### 🔌 「起動しない」
**症状**: バッチファイルをダブルクリックしても何も起こらない  
**解決法**:
1. Pythonがインストールされているか確認
2. `quick_setup.bat` で自動セットアップを実行
3. それでもダメなら実行ファイル版(`EmotionMemCore.exe`)を使用

#### 🌐 「ブラウザが開かない」
**症状**: プログラムは起動するがブラウザが開かない  
**解決法**:
1. 手動で http://localhost:8080 にアクセス
2. ブラウザのアドレスバーに直接入力

#### ⚡ 「動作が重い」
**症状**: 反応が遅い、動作がもっさりする  
**解決法**:
1. 他のアプリを閉じる
2. パソコンを再起動
3. メモリ不足の可能性

#### 🛡️ 「Windows Defender の警告」
**症状**: 「Windows によってPCが保護されました」と表示  
**解決法**:
1. 「詳細情報」をクリック
2. 「実行」ボタンをクリック
3. 安全なソフトです（偽陽性）

#### 🔑 「API キーエラー」
**症状**: 「APIキーが設定されていません」エラー  
**解決法**:
1. 「設定」→「モックモード」を有効にする
2. テスト用なので実際のAPIキーは不要
3. 本格利用時のみAPIキーを設定

---

## 🎉 成功事例

### 🎭 AITuber配信での活用

#### ケース1: 常連視聴者との会話
```
視聴者A: 「おはよう！」
AITuber: 「おはようございます！昨日お話しした資格試験、いかがでしたか？」
視聴者A: 「合格しました！」  
AITuber: 「おめでとうございます！頑張ってらっしゃいましたね」
```

#### ケース2: ゲーム配信
```
視聴者B: 「このゲーム難しそう」
AITuber: 「確かに難しいですね。でも前回一緒に攻略した○○ステージより簡単だと思います！」
```

### 🤖 個人AI助手として

#### ケース3: 日記代わり
```
あなた: 「今日は友達とカフェに行きました」
AI: 「楽しそうですね！どちらのカフェでしたか？」

（1週間後）
あなた: 「また同じカフェに行こうかな」
AI: 「先週お友達と行かれたカフェですね！気に入られたんですね」
```

---

## 📊 詳細設定（上級者向け）

### ⚙️ 設定ファイル (.env)

```bash
# 基本設定
ENVIRONMENT=development
DEBUG_MODE=true
LLM_MOCK_MODE=true  # テスト用

# 本格利用時（オプション）
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# セキュリティ（本番環境）
AUTH_ENABLED=false
RATE_LIMIT_ENABLED=false
```

### 🔧 カスタマイズ可能項目

- **感情の種類**: 38種類の日本語感情タグ
- **検索精度**: ベクトル検索のパラメータ調整
- **UI テーマ**: Bootstrap ベースのカスタマイズ
- **API エンドポイント**: REST API の拡張

---

## 🚀 次のステップ

### 🌟 EmotionMemCore を使いこなそう

1. **毎日の会話を記録** - 日記代わりに使用
2. **感情パターンを分析** - 自分の感情の変化を把握
3. **AITuberKit と連携** - より自然な配信を実現
4. **API を活用** - 他のアプリとの連携

### 📚 さらに学ぶ

- **CLAUDE.md**: 完全技術仕様書（開発者向け）
- **GitHub**: https://github.com/Nikunikuo/EmotionMemCore
- **API仕様**: http://localhost:8000/docs
- **AITuberKit連携**: docs/aituberkit-guide.md

---

## 🎯 まとめ

### ✅ EmotionMemCore で実現できること

- 🤖 **AIに記憶を持たせる**
- 🎭 **感情豊かな対話**
- 📊 **美しい可視化**
- 🔌 **簡単な連携**

### 🎉 対象ユーザー

- ✨ **YouTube見るだけ層** - プログラミング知識ゼロ
- 🎮 **AITuber配信者** - 視聴者との関係構築
- 🤖 **AI愛好家** - より自然な対話を求める人
- 💻 **開発者** - カスタマイズして活用

### 💡 始めるなら今すぐ！

1. `quick_setup.bat` をダブルクリック
2. 3分でセットアップ完了
3. すぐに体験開始！

---

**🚀 YouTube見るだけ層でも、今すぐAIに記憶を持たせることができます！**