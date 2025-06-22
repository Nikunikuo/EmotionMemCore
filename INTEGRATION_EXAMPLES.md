# 🔗 EmotionMemCore 実装例集

> **実際のソフトウェアとの連携コード集**  
> コピペして使える実装例

---

## 📋 目次

1. [AITuberKit との連携](#aituberkit)
2. [Discord Bot との連携](#discord-bot)
3. [Unity (C#) との連携](#unity)
4. [VRChat OSC との連携](#vrchat)
5. [OBS Studio プラグイン](#obs-studio)
6. [Node.js/Electron アプリ](#nodejs-electron)
7. [Python GUI アプリ](#python-gui)
8. [Web アプリ (React)](#react)

---

## 🎭 AITuberKit

### 完全実装例

```python
# aituberkit_memory_extension.py

import requests
from typing import List, Dict, Optional
import asyncio
import json

class MemoryEnabledAITuber:
    """
    AITuberKit に記憶機能を追加する拡張クラス
    """
    
    def __init__(self, base_aituber, memory_api_url="http://localhost:8000"):
        self.aituber = base_aituber  # 既存のAITuberインスタンス
        self.memory_api = memory_api_url
        self.memory_enabled = self._check_memory_api()
        
    def _check_memory_api(self) -> bool:
        """EmotionMemCore が起動しているか確認"""
        try:
            response = requests.get(f"{self.memory_api}/health")
            return response.status_code == 200
        except:
            print("⚠️ EmotionMemCore が起動していません。記憶機能は無効です。")
            return False
    
    async def process_chat(self, username: str, message: str) -> str:
        """
        チャットメッセージを処理（記憶機能付き）
        """
        if not self.memory_enabled:
            # 記憶機能なしで通常処理
            return await self.aituber.generate_response(message)
        
        try:
            # 1. 過去の記憶を検索
            memories = await self._search_memories(username, message)
            
            # 2. コンテキストを構築
            context = self._build_context(memories, username)
            
            # 3. AIの応答を生成
            response = await self.aituber.generate_response_with_context(
                message, 
                context
            )
            
            # 4. 会話を記憶として保存（非同期）
            asyncio.create_task(
                self._save_memory(username, message, response)
            )
            
            return response
            
        except Exception as e:
            print(f"記憶処理エラー: {e}")
            # エラー時は通常処理
            return await self.aituber.generate_response(message)
    
    async def _search_memories(self, username: str, query: str) -> List[Dict]:
        """記憶を検索"""
        try:
            response = await asyncio.to_thread(
                requests.post,
                f"{self.memory_api}/search",
                json={
                    "query": query,
                    "user_id": username,
                    "top_k": 3
                }
            )
            return response.json().get("results", [])
        except:
            return []
    
    async def _save_memory(self, username: str, user_msg: str, ai_msg: str):
        """会話を記憶として保存"""
        try:
            await asyncio.to_thread(
                requests.post,
                f"{self.memory_api}/save",
                json={
                    "user_message": user_msg,
                    "ai_message": ai_msg,
                    "user_id": username,
                    "session_id": f"aituber_{self.aituber.channel_id}"
                }
            )
        except:
            pass  # 保存エラーは無視
    
    def _build_context(self, memories: List[Dict], username: str) -> str:
        """記憶からコンテキストを構築"""
        if not memories:
            return ""
        
        context = f"【{username}さんとの過去の会話】\n"
        for memory in memories:
            context += f"・{memory['summary']}\n"
            if memory.get('emotions'):
                context += f"  感情: {', '.join(memory['emotions'])}\n"
        
        return context

# 使用例
from aituberkit import AITuber  # 既存のAITuberKitインポート

# 通常のAITuber初期化
base_aituber = AITuber(
    model="gpt-3.5-turbo",
    character_prompt="元気で明るいAITuber"
)

# 記憶機能を追加
aituber_with_memory = MemoryEnabledAITuber(base_aituber)

# チャット処理
async def on_chat_received(username, message):
    response = await aituber_with_memory.process_chat(username, message)
    await base_aituber.speak(response)  # 音声合成して話す
```

---

## 🤖 Discord Bot

### 完全実装例

```python
# discord_bot_with_memory.py

import discord
from discord.ext import commands
import requests
import asyncio

class MemoryBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        self.memory_api = "http://localhost:8000"
        
    async def on_ready(self):
        print(f'{self.user} has connected with memory enabled!')
    
    async def on_message(self, message):
        # 自分のメッセージは無視
        if message.author == self.user:
            return
        
        # コマンド処理
        if message.content.startswith('!'):
            await self.process_commands(message)
            return
        
        # 通常の会話処理
        async with message.channel.typing():
            # 記憶検索
            memories = await self.search_memories(
                str(message.author.id), 
                message.content
            )
            
            # 応答生成
            response = self.generate_response(message.content, memories)
            
            # 送信
            await message.channel.send(response)
            
            # 記憶保存
            await self.save_memory(
                str(message.author.id),
                message.content,
                response
            )
    
    async def search_memories(self, user_id: str, query: str):
        """記憶を検索"""
        try:
            response = await asyncio.to_thread(
                requests.post,
                f"{self.memory_api}/search",
                json={
                    "query": query,
                    "user_id": user_id,
                    "top_k": 2
                }
            )
            return response.json().get("results", [])
        except:
            return []
    
    async def save_memory(self, user_id: str, user_msg: str, bot_msg: str):
        """記憶を保存"""
        try:
            await asyncio.to_thread(
                requests.post,
                f"{self.memory_api}/save",
                json={
                    "user_message": user_msg,
                    "ai_message": bot_msg,
                    "user_id": user_id
                }
            )
        except:
            pass
    
    def generate_response(self, message: str, memories: list) -> str:
        """記憶を考慮して応答生成"""
        if memories:
            memory_context = memories[0]['summary']
            return f"以前「{memory_context}」とお話しましたね。{message}について..."
        else:
            return f"{message}について、初めてお聞きしました！"
    
    @commands.command(name='memories')
    async def show_memories(self, ctx):
        """ユーザーの記憶を表示"""
        user_id = str(ctx.author.id)
        
        response = requests.get(
            f"{self.memory_api}/memories",
            params={"user_id": user_id, "limit": 5}
        )
        
        memories = response.json().get("memories", [])
        
        if memories:
            embed = discord.Embed(
                title="あなたとの思い出",
                color=discord.Color.blue()
            )
            for memory in memories:
                embed.add_field(
                    name=f"📝 {memory['timestamp']}",
                    value=memory['summary'][:100],
                    inline=False
                )
            await ctx.send(embed=embed)
        else:
            await ctx.send("まだ思い出がありません。会話しましょう！")

# Bot起動
bot = MemoryBot()
bot.run('YOUR_DISCORD_TOKEN')
```

---

## 🎮 Unity (C#)

### UnityWebRequest を使った実装

```csharp
// EmotionMemoryManager.cs

using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

[Serializable]
public class MemorySaveRequest
{
    public string user_message;
    public string ai_message;
    public string user_id;
}

[Serializable]
public class MemorySearchRequest
{
    public string query;
    public string user_id;
    public int top_k = 3;
}

[Serializable]
public class MemorySearchResponse
{
    public bool success;
    public List<MemoryResult> results;
}

[Serializable]
public class MemoryResult
{
    public string memory_id;
    public string summary;
    public List<string> emotions;
    public float score;
}

public class EmotionMemoryManager : MonoBehaviour
{
    private string apiUrl = "http://localhost:8000";
    private string currentUserId = "unity_player";
    
    // 記憶保存
    public void SaveMemory(string userMessage, string aiMessage, Action<bool> callback = null)
    {
        StartCoroutine(SaveMemoryCoroutine(userMessage, aiMessage, callback));
    }
    
    private IEnumerator SaveMemoryCoroutine(string userMessage, string aiMessage, Action<bool> callback)
    {
        var request = new MemorySaveRequest
        {
            user_message = userMessage,
            ai_message = aiMessage,
            user_id = currentUserId
        };
        
        string json = JsonUtility.ToJson(request);
        byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(json);
        
        using (UnityWebRequest www = UnityWebRequest.Post($"{apiUrl}/save", ""))
        {
            www.uploadHandler = new UploadHandlerRaw(bodyRaw);
            www.downloadHandler = new DownloadHandlerBuffer();
            www.SetRequestHeader("Content-Type", "application/json");
            
            yield return www.SendWebRequest();
            
            bool success = www.result == UnityWebRequest.Result.Success;
            callback?.Invoke(success);
            
            if (!success)
            {
                Debug.LogError($"Memory save failed: {www.error}");
            }
        }
    }
    
    // 記憶検索
    public void SearchMemories(string query, Action<List<MemoryResult>> callback)
    {
        StartCoroutine(SearchMemoriesCoroutine(query, callback));
    }
    
    private IEnumerator SearchMemoriesCoroutine(string query, Action<List<MemoryResult>> callback)
    {
        var request = new MemorySearchRequest
        {
            query = query,
            user_id = currentUserId,
            top_k = 3
        };
        
        string json = JsonUtility.ToJson(request);
        byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(json);
        
        using (UnityWebRequest www = UnityWebRequest.Post($"{apiUrl}/search", ""))
        {
            www.uploadHandler = new UploadHandlerRaw(bodyRaw);
            www.downloadHandler = new DownloadHandlerBuffer();
            www.SetRequestHeader("Content-Type", "application/json");
            
            yield return www.SendWebRequest();
            
            if (www.result == UnityWebRequest.Result.Success)
            {
                var response = JsonUtility.FromJson<MemorySearchResponse>(www.downloadHandler.text);
                callback?.Invoke(response.results);
            }
            else
            {
                Debug.LogError($"Memory search failed: {www.error}");
                callback?.Invoke(new List<MemoryResult>());
            }
        }
    }
}

// 使用例
public class AICharacterController : MonoBehaviour
{
    private EmotionMemoryManager memoryManager;
    
    void Start()
    {
        memoryManager = GetComponent<EmotionMemoryManager>();
    }
    
    public void OnPlayerSpeak(string playerMessage)
    {
        // 記憶を検索
        memoryManager.SearchMemories(playerMessage, (memories) =>
        {
            string aiResponse;
            
            if (memories.Count > 0)
            {
                // 過去の記憶を考慮した返答
                var memory = memories[0];
                aiResponse = $"以前{memory.summary}とお話しましたね。";
            }
            else
            {
                // 通常の返答
                aiResponse = "なるほど、それは興味深いですね。";
            }
            
            // AIキャラクターが話す
            SpeakResponse(aiResponse);
            
            // 会話を記憶として保存
            memoryManager.SaveMemory(playerMessage, aiResponse);
        });
    }
    
    void SpeakResponse(string response)
    {
        // AIキャラクターのアニメーションや音声合成
        Debug.Log($"AI: {response}");
    }
}
```

---

## 🌐 VRChat OSC

### OSC経由での連携

```python
# vrchat_osc_memory.py

from pythonosc import udp_client, osc_server, dispatcher
import requests
import threading
import time

class VRChatMemoryBridge:
    """
    VRChat OSC と EmotionMemCore を繋ぐブリッジ
    """
    
    def __init__(self):
        self.memory_api = "http://localhost:8000"
        self.vrc_ip = "127.0.0.1"
        self.vrc_port = 9000  # VRChat OSC入力ポート
        self.listen_port = 9001  # VRChatからの受信ポート
        
        # OSCクライアント（VRChatへ送信）
        self.client = udp_client.SimpleUDPClient(self.vrc_ip, self.vrc_port)
        
        # 最後の会話記録
        self.last_chat = {"user": "", "ai": "", "time": 0}
        
    def on_chatbox_input(self, address, *args):
        """VRChatのチャットボックス入力を処理"""
        if len(args) > 0:
            message = args[0]
            user_id = args[1] if len(args) > 1 else "vrc_user"
            
            # 記憶検索
            memories = self.search_memories(user_id, message)
            
            # 応答生成
            if memories:
                response = f"[Memory] {memories[0]['summary'][:50]}..."
            else:
                response = "[New] Saved to memory!"
            
            # VRChatに応答を送信
            self.send_to_vrchat(response)
            
            # 記憶保存（5秒後）
            self.last_chat = {
                "user": message,
                "ai": response,
                "time": time.time()
            }
    
    def search_memories(self, user_id: str, query: str):
        """記憶検索"""
        try:
            response = requests.post(
                f"{self.memory_api}/search",
                json={
                    "query": query,
                    "user_id": user_id,
                    "top_k": 1
                }
            )
            return response.json().get("results", [])
        except:
            return []
    
    def send_to_vrchat(self, message: str):
        """VRChatにOSCメッセージ送信"""
        # チャットボックスに表示
        self.client.send_message("/chatbox/input", [message, True])
        
        # パラメータとして感情値を送信（例）
        self.client.send_message("/avatar/parameters/Emotion_Happy", 1.0)
    
    def save_memory_loop(self):
        """定期的に記憶を保存"""
        while True:
            time.sleep(5)
            
            if self.last_chat["time"] > 0 and \
               time.time() - self.last_chat["time"] < 10:
                try:
                    requests.post(
                        f"{self.memory_api}/save",
                        json={
                            "user_message": self.last_chat["user"],
                            "ai_message": self.last_chat["ai"],
                            "user_id": "vrc_user"
                        }
                    )
                    self.last_chat["time"] = 0  # 保存済みマーク
                except:
                    pass
    
    def start(self):
        """ブリッジ開始"""
        # OSCサーバー設定
        disp = dispatcher.Dispatcher()
        disp.map("/chatbox/input", self.on_chatbox_input)
        
        server = osc_server.ThreadingOSCUDPServer(
            ("127.0.0.1", self.listen_port), disp
        )
        
        # 保存スレッド開始
        save_thread = threading.Thread(target=self.save_memory_loop)
        save_thread.daemon = True
        save_thread.start()
        
        print(f"VRChat Memory Bridge started on port {self.listen_port}")
        server.serve_forever()

# 起動
if __name__ == "__main__":
    bridge = VRChatMemoryBridge()
    bridge.start()
```

---

## 🎥 OBS Studio

### OBS Python スクリプト

```python
# obs_memory_plugin.py

import obspython as obs
import requests
import json
from datetime import datetime

# グローバル設定
memory_api_url = "http://localhost:8000"
enabled = True
save_interval = 300  # 5分ごとに保存

def save_stream_memory(stream_title, viewer_count, chat_summary):
    """配信の記憶を保存"""
    try:
        response = requests.post(
            f"{memory_api_url}/save",
            json={
                "user_message": f"配信: {stream_title} (視聴者数: {viewer_count})",
                "ai_message": f"配信内容: {chat_summary}",
                "user_id": "obs_stream",
                "session_id": f"stream_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
        )
        obs.script_log(obs.LOG_INFO, f"Memory saved: {response.status_code}")
    except Exception as e:
        obs.script_log(obs.LOG_ERROR, f"Failed to save memory: {e}")

def on_event(event):
    """OBSイベントハンドラ"""
    if event == obs.OBS_FRONTEND_EVENT_STREAMING_STARTED:
        obs.script_log(obs.LOG_INFO, "Streaming started - Memory recording enabled")
    elif event == obs.OBS_FRONTEND_EVENT_STREAMING_STOPPED:
        # 配信終了時に要約を保存
        save_stream_memory(
            "配信終了",
            0,
            "本日の配信が終了しました"
        )

def script_description():
    return """EmotionMemCore OBS連携
    配信の記憶を自動保存します。
    - 配信開始/終了を記録
    - チャット内容を定期保存
    - 視聴者数の推移を記録"""

def script_properties():
    """設定UI"""
    props = obs.obs_properties_create()
    
    obs.obs_properties_add_text(
        props, "api_url", "EmotionMemCore API URL", obs.OBS_TEXT_DEFAULT
    )
    obs.obs_properties_add_bool(props, "enabled", "記憶機能を有効化")
    obs.obs_properties_add_int(
        props, "save_interval", "保存間隔（秒）", 60, 3600, 60
    )
    
    return props

def script_defaults(settings):
    """デフォルト設定"""
    obs.obs_data_set_default_string(settings, "api_url", memory_api_url)
    obs.obs_data_set_default_bool(settings, "enabled", True)
    obs.obs_data_set_default_int(settings, "save_interval", 300)

def script_load(settings):
    """スクリプト読み込み時"""
    obs.obs_frontend_add_event_callback(on_event)

def script_unload():
    """スクリプトアンロード時"""
    obs.obs_frontend_remove_event_callback(on_event)
```

---

## 🌐 Web アプリ (React)

### React Hook での実装

```javascript
// useEmotionMemory.js

import { useState, useCallback } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_MEMORY_API || 'http://localhost:8000';

export const useEmotionMemory = (userId = 'web_user') => {
  const [memories, setMemories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 記憶を保存
  const saveMemory = useCallback(async (userMessage, aiMessage) => {
    try {
      const response = await axios.post(`${API_URL}/save`, {
        user_message: userMessage,
        ai_message: aiMessage,
        user_id: userId
      });
      return response.data;
    } catch (err) {
      setError(err.message);
      return null;
    }
  }, [userId]);

  // 記憶を検索
  const searchMemories = useCallback(async (query, options = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(`${API_URL}/search`, {
        query,
        user_id: userId,
        top_k: options.topK || 5,
        emotions: options.emotions || []
      });
      
      setMemories(response.data.results || []);
      return response.data.results;
    } catch (err) {
      setError(err.message);
      return [];
    } finally {
      setLoading(false);
    }
  }, [userId]);

  // 全記憶を取得
  const fetchAllMemories = useCallback(async (limit = 50) => {
    setLoading(true);
    
    try {
      const response = await axios.get(`${API_URL}/memories`, {
        params: { user_id: userId, limit }
      });
      
      setMemories(response.data.memories || []);
      return response.data.memories;
    } catch (err) {
      setError(err.message);
      return [];
    } finally {
      setLoading(false);
    }
  }, [userId]);

  return {
    memories,
    loading,
    error,
    saveMemory,
    searchMemories,
    fetchAllMemories
  };
};

// 使用例: ChatComponent.jsx
import React, { useState, useEffect } from 'react';
import { useEmotionMemory } from './useEmotionMemory';

export const ChatWithMemory = () => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const { saveMemory, searchMemories, memories } = useEmotionMemory('user123');

  const handleSend = async () => {
    if (!input.trim()) return;

    // 関連する記憶を検索
    const relatedMemories = await searchMemories(input);
    
    // AI応答生成（実際はAPIを呼ぶ）
    let aiResponse = 'なるほど、それは興味深いですね。';
    
    if (relatedMemories.length > 0) {
      const memory = relatedMemories[0];
      aiResponse = `以前「${memory.summary}」とお話しましたね。${input}について...`;
    }

    // メッセージ追加
    setMessages(prev => [
      ...prev,
      { type: 'user', text: input },
      { type: 'ai', text: aiResponse }
    ]);

    // 記憶保存
    await saveMemory(input, aiResponse);
    
    setInput('');
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.type}`}>
            {msg.text}
          </div>
        ))}
      </div>
      
      {memories.length > 0 && (
        <div className="memory-hints">
          <h4>関連する記憶:</h4>
          {memories.map(memory => (
            <div key={memory.memory_id} className="memory-item">
              <span>{memory.summary}</span>
              <span className="emotions">
                {memory.emotions.join(', ')}
              </span>
            </div>
          ))}
        </div>
      )}
      
      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="メッセージを入力..."
        />
        <button onClick={handleSend}>送信</button>
      </div>
    </div>
  );
};
```

---

## 🎯 まとめ

どのプラットフォームでも基本は同じ：

1. **記憶保存**: POST `/save` に会話データを送信
2. **記憶検索**: POST `/search` でキーワード検索
3. **エラー処理**: API接続失敗時も動作継続

これらのコードをコピペして、あなたのプロジェクトに組み込むだけで、AIに記憶機能を追加できます！ 🚀