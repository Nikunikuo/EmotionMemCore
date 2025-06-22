# 🔌 EmotionMemCore 統合ガイド

> **EmotionMemCoreを様々なアプリケーションに統合するための詳細ガイド**

EmotionMemCoreは、AI Vtuberや対話型AIシステムと簡単に統合できるよう設計されています。このガイドでは、実際のプロジェクトでの統合方法を詳しく説明します。

---

## 📋 目次

1. [🏗️ 基本統合](#️-基本統合)
2. [🎭 AI Vtuber統合](#-ai-vtuber統合)
3. [🤖 Discord Bot統合](#-discord-bot統合)
4. [🌐 Web アプリケーション統合](#-web-アプリケーション統合)
5. [📱 モバイルアプリ統合](#-モバイルアプリ統合)
6. [⚡ パフォーマンス最適化](#-パフォーマンス最適化)
7. [🐛 エラーハンドリング](#-エラーハンドリング)
8. [🔒 セキュリティ考慮事項](#-セキュリティ考慮事項)

---

## 🏗️ 基本統合

### EmotionMemCore クライアント

まず、共通して使用するPythonクライアントクラスを作成します。

```python
# emotion_mem_client.py
import httpx
import asyncio
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class EmotionMemCoreClient:
    """EmotionMemCore API クライアント"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            self.headers["X-API-Key"] = api_key
        
        # HTTPクライアント設定
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers=self.headers
        )
    
    async def save_memory(
        self, 
        user_message: str, 
        ai_message: str,
        user_id: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """会話を記憶として保存"""
        
        payload = {
            "user_message": user_message,
            "ai_message": ai_message,
            "user_id": user_id
        }
        
        if session_id:
            payload["session_id"] = session_id
        if metadata:
            payload["metadata"] = metadata
        
        try:
            response = await self.client.post(f"{self.base_url}/save", json=payload)
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Memory save failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Memory save error: {str(e)}")
            raise
    
    async def search_memories(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        emotions: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """記憶を検索"""
        
        payload = {
            "query": query,
            "user_id": user_id,
            "top_k": top_k
        }
        
        if emotions:
            payload["emotions"] = emotions
        if start_date:
            payload["start_date"] = start_date
        if end_date:
            payload["end_date"] = end_date
        
        try:
            response = await self.client.post(f"{self.base_url}/search", json=payload)
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Memory search failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Memory search error: {str(e)}")
            raise
    
    async def get_memories(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0,
        emotions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """記憶一覧を取得"""
        
        params = {
            "user_id": user_id,
            "limit": limit,
            "offset": offset
        }
        
        if emotions:
            params["emotions"] = ",".join(emotions)
        
        try:
            response = await self.client.get(f"{self.base_url}/memories", params=params)
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Memory list failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Memory list error: {str(e)}")
            raise
    
    async def batch_save_memories(
        self,
        conversations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """複数の会話を一括保存"""
        
        try:
            response = await self.client.post(f"{self.base_url}/batch-save", json=conversations)
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Batch save failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Batch save error: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        
        try:
            response = await self.client.get(f"{self.base_url}/health/")
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            raise
    
    async def close(self):
        """クライアント終了"""
        await self.client.aclose()
```

---

## 🎭 AI Vtuber統合

### Vtuber記憶システムの実装

```python
# vtuber_memory_system.py
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from emotion_mem_client import EmotionMemCoreClient

class VtuberMemorySystem:
    """AI Vtuber向け記憶システム"""
    
    def __init__(self, emotion_core_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.emotion_core = EmotionMemCoreClient(emotion_core_url, api_key)
        self.current_session_id = None
        self.user_contexts = {}  # ユーザーごとのコンテキスト
    
    def start_session(self, user_id: str) -> str:
        """新しいセッションを開始"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session_id = f"session_{user_id}_{timestamp}"
        
        # ユーザーコンテキスト初期化
        self.user_contexts[user_id] = {
            "session_id": self.current_session_id,
            "recent_emotions": [],
            "conversation_count": 0
        }
        
        return self.current_session_id
    
    async def chat_with_memory(
        self, 
        user_message: str, 
        user_id: str,
        character_name: str = "VtuberAI"
    ) -> Dict[str, Any]:
        """記憶を活用した会話処理"""
        
        # 1. 過去の記憶を検索
        relevant_memories = await self._search_relevant_memories(user_message, user_id)
        
        # 2. 記憶を踏まえてAI応答生成
        context = self._build_conversation_context(relevant_memories, user_id)
        ai_response = await self._generate_response(user_message, context, character_name)
        
        # 3. 会話を記憶として保存（バックグラウンド）
        asyncio.create_task(self._save_conversation_async(
            user_message=user_message,
            ai_message=ai_response["message"],
            user_id=user_id,
            session_id=self.user_contexts.get(user_id, {}).get("session_id"),
            metadata={
                "character_name": character_name,
                "response_time_ms": ai_response.get("processing_time_ms"),
                "used_memories": len(relevant_memories)
            }
        ))
        
        # 4. ユーザーコンテキスト更新
        self._update_user_context(user_id, ai_response.get("detected_emotions", []))
        
        return {
            "message": ai_response["message"],
            "emotions": ai_response.get("detected_emotions", []),
            "used_memories": len(relevant_memories),
            "session_id": self.current_session_id
        }
    
    async def _search_relevant_memories(
        self, 
        user_message: str, 
        user_id: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """関連する記憶を検索"""
        
        try:
            # 感情コンテキストも考慮
            user_context = self.user_contexts.get(user_id, {})
            recent_emotions = user_context.get("recent_emotions", [])
            
            result = await self.emotion_core.search_memories(
                query=user_message,
                user_id=user_id,
                top_k=limit,
                emotions=recent_emotions if recent_emotions else None
            )
            
            return result.get("results", [])
            
        except Exception as e:
            print(f"Memory search failed: {e}")
            return []
    
    def _build_conversation_context(
        self, 
        memories: List[Dict[str, Any]], 
        user_id: str
    ) -> str:
        """会話コンテキストを構築"""
        
        if not memories:
            return "このユーザーとの会話履歴は見つかりませんでした。"
        
        context_parts = ["過去の会話記憶:"]
        
        for i, memory in enumerate(memories, 1):
            summary = memory.get("summary", "")
            emotions = ", ".join(memory.get("emotions", []))
            context_parts.append(f"{i}. {summary} (感情: {emotions})")
        
        user_context = self.user_contexts.get(user_id, {})
        if user_context.get("recent_emotions"):
            recent_emotions = ", ".join(user_context["recent_emotions"])
            context_parts.append(f"最近の感情傾向: {recent_emotions}")
        
        return "\n".join(context_parts)
    
    async def _generate_response(
        self, 
        user_message: str, 
        context: str, 
        character_name: str
    ) -> Dict[str, Any]:
        """AI応答を生成（お客様のLLMクライアントと連携）"""
        
        # この部分は実際のLLM（ChatGPT, Claude等）クライアントと連携
        prompt = f"""
あなたは{character_name}です。以下の記憶と現在のメッセージを踏まえて、自然で感情豊かな応答をしてください。

{context}

現在のメッセージ: {user_message}

過去の記憶を自然に活用し、ユーザーとの関係性を感じられる応答を心がけてください。
"""
        
        # 実際のLLM API呼び出し（例）
        # response = await your_llm_client.generate(prompt)
        
        # デモ用のモック応答
        return {
            "message": f"そのお話、覚えています！{user_message}について、また聞かせてくださいね✨",
            "detected_emotions": ["喜び", "興味"],
            "processing_time_ms": 150
        }
    
    async def _save_conversation_async(
        self,
        user_message: str,
        ai_message: str, 
        user_id: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """非同期での会話保存"""
        
        try:
            result = await self.emotion_core.save_memory(
                user_message=user_message,
                ai_message=ai_message,
                user_id=user_id,
                session_id=session_id,
                metadata=metadata
            )
            print(f"Memory saved: {result.get('memory_id')}")
            
        except Exception as e:
            print(f"Failed to save memory: {e}")
    
    def _update_user_context(self, user_id: str, new_emotions: List[str]):
        """ユーザーコンテキストを更新"""
        
        if user_id not in self.user_contexts:
            return
        
        context = self.user_contexts[user_id]
        context["conversation_count"] += 1
        
        # 最近の感情傾向を追跡（最大5つまで）
        context["recent_emotions"].extend(new_emotions)
        context["recent_emotions"] = context["recent_emotions"][-5:]
    
    async def get_user_memory_summary(self, user_id: str) -> Dict[str, Any]:
        """ユーザーの記憶サマリーを取得"""
        
        try:
            memories = await self.emotion_core.get_memories(user_id, limit=20)
            
            # 感情分析
            all_emotions = []
            for memory in memories.get("memories", []):
                all_emotions.extend(memory.get("emotions", []))
            
            # 感情頻度計算
            emotion_counts = {}
            for emotion in all_emotions:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            # 最頻感情トップ5
            top_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                "total_memories": len(memories.get("memories", [])),
                "top_emotions": [{"emotion": emotion, "count": count} for emotion, count in top_emotions],
                "recent_activity": memories.get("memories", [])[:5],
                "user_context": self.user_contexts.get(user_id, {})
            }
            
        except Exception as e:
            print(f"Failed to get memory summary: {e}")
            return {"error": str(e)}

# 使用例
async def vtuber_example():
    """Vtuber統合の使用例"""
    
    vtuber = VtuberMemorySystem()
    user_id = "user_12345"
    
    # セッション開始
    session_id = vtuber.start_session(user_id)
    print(f"Started session: {session_id}")
    
    # 会話例
    conversations = [
        "おはよう！今日はいい天気だね",
        "昨日見た映画がとても面白かったよ", 
        "最近ゲームにハマってるんだ"
    ]
    
    for user_msg in conversations:
        response = await vtuber.chat_with_memory(user_msg, user_id, "ココロちゃん")
        print(f"User: {user_msg}")
        print(f"VtuberAI: {response['message']}")
        print(f"Emotions: {response['emotions']}\n")
        
        # 少し待機（リアルな会話間隔をシミュレート）
        await asyncio.sleep(1)
    
    # ユーザーサマリー表示
    summary = await vtuber.get_user_memory_summary(user_id)
    print("User Memory Summary:", summary)
    
    await vtuber.emotion_core.close()

if __name__ == "__main__":
    asyncio.run(vtuber_example())
```

---

## 🤖 Discord Bot統合

### Discord.py との統合

```python
# discord_memory_bot.py
import discord
from discord.ext import commands
import asyncio
from emotion_mem_client import EmotionMemCoreClient
from typing import Optional, Dict, Any

class MemoryBot(commands.Bot):
    """記憶機能付きDiscord Bot"""
    
    def __init__(self, command_prefix='!', emotion_core_url="http://localhost:8000"):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=command_prefix, intents=intents)
        
        self.emotion_core = EmotionMemCoreClient(emotion_core_url)
        self.user_sessions = {}  # ユーザーセッション管理
    
    async def on_ready(self):
        """Bot起動時の処理"""
        print(f'{self.user.name} has connected to Discord!')
        
        # EmotionMemCore接続確認
        try:
            health = await self.emotion_core.health_check()
            print(f"EmotionMemCore connected: {health}")
        except Exception as e:
            print(f"Failed to connect to EmotionMemCore: {e}")
    
    async def on_message(self, message):
        """メッセージ受信時の処理"""
        
        # Bot自身のメッセージは無視
        if message.author == self.user:
            return
        
        # コマンドでない場合、記憶学習
        if not message.content.startswith(self.command_prefix):
            await self._learn_from_message(message)
        
        # コマンド処理
        await self.process_commands(message)
    
    async def _learn_from_message(self, message):
        """メッセージから学習"""
        
        user_id = str(message.author.id)
        channel_id = str(message.channel.id)
        
        # セッション管理
        session_key = f"{user_id}_{channel_id}"
        if session_key not in self.user_sessions:
            self.user_sessions[session_key] = {
                "message_count": 0,
                "last_bot_response": None
            }
        
        session = self.user_sessions[session_key]
        session["message_count"] += 1
        
        # 前回のBot応答がある場合、会話ペアとして保存
        if session.get("last_bot_response"):
            try:
                await self.emotion_core.save_memory(
                    user_message=message.content,
                    ai_message=session["last_bot_response"],
                    user_id=user_id,
                    session_id=session_key,
                    metadata={
                        "platform": "discord",
                        "channel_id": channel_id,
                        "guild_id": str(message.guild.id) if message.guild else None,
                        "message_count": session["message_count"]
                    }
                )
                
                # Bot応答をリセット
                session["last_bot_response"] = None
                
            except Exception as e:
                print(f"Failed to save memory: {e}")

    @commands.command(name='remember')
    async def remember_command(self, ctx, *, query: str):
        """記憶検索コマンド"""
        
        user_id = str(ctx.author.id)
        
        try:
            # 記憶検索
            result = await self.emotion_core.search_memories(
                query=query,
                user_id=user_id,
                top_k=5
            )
            
            memories = result.get("results", [])
            
            if not memories:
                await ctx.send("関連する記憶が見つかりませんでした。")
                return
            
            # 検索結果を整形
            embed = discord.Embed(
                title="🧠 記憶検索結果",
                description=f"クエリ: `{query}`",
                color=0x00ff00
            )
            
            for i, memory in enumerate(memories[:3], 1):
                emotions = "、".join(memory.get("emotions", []))
                score = memory.get("score", 0)
                timestamp = memory.get("timestamp", "")
                
                embed.add_field(
                    name=f"記憶 {i} (類似度: {score:.2f})",
                    value=f"**要約**: {memory.get('summary', '')}\n"
                           f"**感情**: {emotions}\n"
                           f"**日時**: {timestamp[:10]}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"記憶検索中にエラーが発生しました: {str(e)}")
    
    @commands.command(name='memories')
    async def memories_command(self, ctx, limit: Optional[int] = 5):
        """記憶一覧表示コマンド"""
        
        user_id = str(ctx.author.id)
        limit = max(1, min(limit, 10))  # 1-10の範囲に制限
        
        try:
            result = await self.emotion_core.get_memories(
                user_id=user_id,
                limit=limit
            )
            
            memories = result.get("memories", [])
            
            if not memories:
                await ctx.send("まだ記憶がありません。")
                return
            
            embed = discord.Embed(
                title="📚 あなたの記憶一覧",
                description=f"最新 {len(memories)} 件の記憶",
                color=0x0099ff
            )
            
            for i, memory in enumerate(memories, 1):
                emotions = "、".join(memory.get("emotions", []))
                timestamp = memory.get("timestamp", "")
                
                embed.add_field(
                    name=f"記憶 {i}",
                    value=f"**要約**: {memory.get('summary', '')}\n"
                           f"**感情**: {emotions}\n"
                           f"**日時**: {timestamp[:10]}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"記憶取得中にエラーが発生しました: {str(e)}")
    
    @commands.command(name='emotions')
    async def emotions_command(self, ctx):
        """感情統計表示コマンド"""
        
        user_id = str(ctx.author.id)
        
        try:
            # 最近の記憶を取得
            result = await self.emotion_core.get_memories(
                user_id=user_id,
                limit=50
            )
            
            memories = result.get("memories", [])
            
            if not memories:
                await ctx.send("感情データがありません。")
                return
            
            # 感情統計計算
            emotion_counts = {}
            for memory in memories:
                for emotion in memory.get("emotions", []):
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            # 上位5つの感情
            top_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            embed = discord.Embed(
                title="📊 あなたの感情統計",
                description=f"最近の {len(memories)} 件の記憶から分析",
                color=0xff6b6b
            )
            
            for i, (emotion, count) in enumerate(top_emotions, 1):
                percentage = (count / len(memories)) * 100
                embed.add_field(
                    name=f"{i}. {emotion}",
                    value=f"{count}回 ({percentage:.1f}%)",
                    inline=True
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"感情統計取得中にエラーが発生しました: {str(e)}")
    
    @commands.command(name='chat')
    async def chat_command(self, ctx, *, message: str):
        """記憶を活用したチャットコマンド"""
        
        user_id = str(ctx.author.id)
        
        try:
            # 関連記憶を検索
            memories_result = await self.emotion_core.search_memories(
                query=message,
                user_id=user_id,
                top_k=3
            )
            
            memories = memories_result.get("results", [])
            
            # コンテキスト構築
            if memories:
                context = "過去の記憶:\n"
                for memory in memories:
                    context += f"- {memory.get('summary', '')}\n"
            else:
                context = "初回の会話です。"
            
            # AI応答生成（実際のLLM APIと連携する部分）
            # response = await your_llm_api.generate(message, context)
            
            # デモ用応答
            bot_response = f"『{message}』について、{len(memories)}件の関連記憶があります！過去のお話を思い出しながらお返事しますね✨"
            
            await ctx.send(bot_response)
            
            # セッションに応答を記録（次回の学習用）
            session_key = f"{user_id}_{ctx.channel.id}"
            if session_key in self.user_sessions:
                self.user_sessions[session_key]["last_bot_response"] = bot_response
            
        except Exception as e:
            await ctx.send(f"チャット処理中にエラーが発生しました: {str(e)}")
    
    async def close(self):
        """Bot終了時の処理"""
        await self.emotion_core.close()
        await super().close()

# Bot起動関数
async def run_discord_bot(token: str):
    """Discord Bot起動"""
    
    bot = MemoryBot(command_prefix='!')
    
    try:
        await bot.start(token)
    finally:
        await bot.close()

# 使用例
if __name__ == "__main__":
    import os
    
    # 環境変数からDiscord Botトークンを取得
    DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    
    if not DISCORD_TOKEN:
        print("DISCORD_BOT_TOKEN environment variable is required")
        exit(1)
    
    # Bot起動
    asyncio.run(run_discord_bot(DISCORD_TOKEN))
```

---

## 🌐 Web アプリケーション統合

### FastAPI + React 統合例

#### バックエンド（FastAPI）

```python
# web_app_backend.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
from emotion_mem_client import EmotionMemCoreClient

app = FastAPI(title="EmotionMemCore Web App")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React開発サーバー
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# EmotionMemCore クライアント
emotion_client = EmotionMemCoreClient()

# Pydanticモデル
class ChatMessage(BaseModel):
    message: str
    user_id: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    emotions: List[str]
    used_memories: int
    memory_id: Optional[str] = None

class MemoryQuery(BaseModel):
    query: str
    user_id: str
    emotions: Optional[List[str]] = None
    limit: int = 5

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """チャットエンドポイント"""
    
    try:
        # 関連記憶を検索
        memories_result = await emotion_client.search_memories(
            query=message.message,
            user_id=message.user_id,
            top_k=3
        )
        
        memories = memories_result.get("results", [])
        
        # AI応答生成（実際のLLM APIと連携）
        bot_response = await generate_ai_response(message.message, memories)
        
        # 会話を保存
        save_result = await emotion_client.save_memory(
            user_message=message.message,
            ai_message=bot_response["response"],
            user_id=message.user_id,
            session_id=message.session_id
        )
        
        return ChatResponse(
            response=bot_response["response"],
            emotions=bot_response["emotions"],
            used_memories=len(memories),
            memory_id=save_result.get("memory_id")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search-memories")
async def search_memories_endpoint(query: MemoryQuery):
    """記憶検索エンドポイント"""
    
    try:
        result = await emotion_client.search_memories(
            query=query.query,
            user_id=query.user_id,
            top_k=query.limit,
            emotions=query.emotions
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memories/{user_id}")
async def get_user_memories(user_id: str, limit: int = 10, offset: int = 0):
    """ユーザー記憶一覧"""
    
    try:
        result = await emotion_client.get_memories(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/emotions/{user_id}")
async def get_user_emotions(user_id: str):
    """ユーザー感情統計"""
    
    try:
        memories_result = await emotion_client.get_memories(
            user_id=user_id,
            limit=100
        )
        
        memories = memories_result.get("memories", [])
        
        # 感情統計計算
        emotion_counts = {}
        for memory in memories:
            for emotion in memory.get("emotions", []):
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # 時系列データ作成（月別）
        monthly_emotions = {}  # 実装は省略
        
        return {
            "total_memories": len(memories),
            "emotion_distribution": emotion_counts,
            "monthly_trend": monthly_emotions,
            "top_emotions": sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def generate_ai_response(message: str, memories: List[Dict]) -> Dict[str, Any]:
    """AI応答生成（モック）"""
    
    # 実際のLLM APIと連携する部分
    context = ""
    if memories:
        context = "関連記憶: " + ", ".join([m.get("summary", "") for m in memories])
    
    # デモ用応答
    return {
        "response": f"『{message}』についてお答えします！{context}",
        "emotions": ["喜び", "親しみ"],
        "processing_time_ms": 120
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

#### フロントエンド（React）

```typescript
// EmotionMemoryChat.tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface ChatMessage {
  id: string;
  message: string;
  response: string;
  emotions: string[];
  timestamp: Date;
  usedMemories: number;
}

interface Memory {
  memory_id: string;
  summary: string;
  emotions: string[];
  timestamp: string;
  score?: number;
}

const EmotionMemoryChat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [userId, setUserId] = useState('user_demo');
  const [loading, setLoading] = useState(false);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  const API_BASE = 'http://localhost:8001/api';

  // チャット送信
  const sendMessage = async () => {
    if (!currentMessage.trim()) return;

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/chat`, {
        message: currentMessage,
        user_id: userId,
        session_id: `session_${Date.now()}`
      });

      const newMessage: ChatMessage = {
        id: Date.now().toString(),
        message: currentMessage,
        response: response.data.response,
        emotions: response.data.emotions,
        timestamp: new Date(),
        usedMemories: response.data.used_memories
      };

      setMessages(prev => [...prev, newMessage]);
      setCurrentMessage('');
      
      // 記憶一覧を更新
      loadMemories();

    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setLoading(false);
    }
  };

  // 記憶一覧読み込み
  const loadMemories = async () => {
    try {
      const response = await axios.get(`${API_BASE}/memories/${userId}?limit=10`);
      setMemories(response.data.memories || []);
    } catch (error) {
      console.error('Failed to load memories:', error);
    }
  };

  // 記憶検索
  const searchMemories = async () => {
    if (!searchQuery.trim()) return;

    try {
      const response = await axios.post(`${API_BASE}/search-memories`, {
        query: searchQuery,
        user_id: userId,
        limit: 10
      });
      
      setMemories(response.data.results || []);
    } catch (error) {
      console.error('Memory search error:', error);
    }
  };

  useEffect(() => {
    loadMemories();
  }, [userId]);

  return (
    <div className="emotion-memory-chat">
      <div className="chat-container">
        {/* チャット履歴 */}
        <div className="chat-history">
          {messages.map((msg) => (
            <div key={msg.id} className="chat-message">
              <div className="user-message">
                <strong>あなた:</strong> {msg.message}
              </div>
              <div className="ai-response">
                <strong>AI:</strong> {msg.response}
                <div className="emotions">
                  感情: {msg.emotions.join(', ')} | 使用記憶: {msg.usedMemories}件
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* メッセージ入力 */}
        <div className="chat-input">
          <input
            type="text"
            value={currentMessage}
            onChange={(e) => setCurrentMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="メッセージを入力..."
            disabled={loading}
          />
          <button onClick={sendMessage} disabled={loading || !currentMessage.trim()}>
            {loading ? '送信中...' : '送信'}
          </button>
        </div>
      </div>

      {/* 記憶パネル */}
      <div className="memory-panel">
        <h3>記憶管理</h3>
        
        {/* 記憶検索 */}
        <div className="memory-search">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="記憶を検索..."
          />
          <button onClick={searchMemories}>検索</button>
          <button onClick={loadMemories}>全て表示</button>
        </div>

        {/* 記憶一覧 */}
        <div className="memory-list">
          {memories.map((memory) => (
            <div key={memory.memory_id} className="memory-item">
              <div className="memory-summary">{memory.summary}</div>
              <div className="memory-meta">
                <span className="emotions">{memory.emotions.join(', ')}</span>
                <span className="timestamp">{new Date(memory.timestamp).toLocaleDateString()}</span>
                {memory.score && (
                  <span className="score">類似度: {(memory.score * 100).toFixed(1)}%</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <style jsx>{`
        .emotion-memory-chat {
          display: flex;
          height: 100vh;
          font-family: 'Helvetica', sans-serif;
        }

        .chat-container {
          flex: 2;
          display: flex;
          flex-direction: column;
          border-right: 1px solid #e0e0e0;
        }

        .chat-history {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
          background: #f9f9f9;
        }

        .chat-message {
          margin-bottom: 20px;
          padding: 15px;
          background: white;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .user-message {
          margin-bottom: 10px;
          color: #333;
        }

        .ai-response {
          color: #2196F3;
        }

        .emotions {
          font-size: 12px;
          color: #666;
          margin-top: 5px;
        }

        .chat-input {
          display: flex;
          padding: 20px;
          background: white;
          border-top: 1px solid #e0e0e0;
        }

        .chat-input input {
          flex: 1;
          padding: 10px;
          border: 1px solid #ddd;
          border-radius: 4px;
          margin-right: 10px;
        }

        .chat-input button {
          padding: 10px 20px;
          background: #2196F3;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        }

        .chat-input button:disabled {
          background: #ccc;
          cursor: not-allowed;
        }

        .memory-panel {
          flex: 1;
          padding: 20px;
          background: #f5f5f5;
          overflow-y: auto;
        }

        .memory-search {
          margin-bottom: 20px;
        }

        .memory-search input {
          width: 100%;
          padding: 8px;
          margin-bottom: 10px;
          border: 1px solid #ddd;
          border-radius: 4px;
        }

        .memory-search button {
          margin-right: 10px;
          padding: 6px 12px;
          background: #4CAF50;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        }

        .memory-item {
          background: white;
          padding: 12px;
          margin-bottom: 10px;
          border-radius: 6px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .memory-summary {
          font-size: 14px;
          margin-bottom: 8px;
          line-height: 1.4;
        }

        .memory-meta {
          font-size: 12px;
          color: #666;
        }

        .memory-meta span {
          margin-right: 10px;
        }

        .emotions {
          color: #FF9800;
        }

        .score {
          color: #4CAF50;
          font-weight: bold;
        }
      `}</style>
    </div>
  );
};

export default EmotionMemoryChat;
```

---

## 📱 モバイルアプリ統合

### React Native 統合例

```typescript
// EmotionMemoryService.ts
import axios, { AxiosInstance } from 'axios';

interface MemoryResult {
  memory_id: string;
  summary: string;
  emotions: string[];
  timestamp: string;
  score?: number;
}

interface SaveMemoryParams {
  user_message: string;
  ai_message: string;
  user_id: string;
  session_id?: string;
  metadata?: Record<string, any>;
}

interface SearchMemoryParams {
  query: string;
  user_id: string;
  top_k?: number;
  emotions?: string[];
}

export class EmotionMemoryService {
  private client: AxiosInstance;

  constructor(baseURL: string = 'http://localhost:8000', apiKey?: string) {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        ...(apiKey && { 'X-API-Key': apiKey })
      }
    });
  }

  async saveMemory(params: SaveMemoryParams): Promise<any> {
    try {
      const response = await this.client.post('/save', params);
      return response.data;
    } catch (error) {
      console.error('Failed to save memory:', error);
      throw error;
    }
  }

  async searchMemories(params: SearchMemoryParams): Promise<MemoryResult[]> {
    try {
      const response = await this.client.post('/search', {
        ...params,
        top_k: params.top_k || 5
      });
      return response.data.results || [];
    } catch (error) {
      console.error('Failed to search memories:', error);
      throw error;
    }
  }

  async getMemories(
    userId: string, 
    limit: number = 10, 
    offset: number = 0
  ): Promise<MemoryResult[]> {
    try {
      const response = await this.client.get('/memories', {
        params: { user_id: userId, limit, offset }
      });
      return response.data.memories || [];
    } catch (error) {
      console.error('Failed to get memories:', error);
      throw error;
    }
  }

  async healthCheck(): Promise<any> {
    try {
      const response = await this.client.get('/health/');
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }
}

// React Native コンポーネント例
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  Alert
} from 'react-native';

const EmotionMemoryApp: React.FC = () => {
  const [memoryService] = useState(new EmotionMemoryService());
  const [message, setMessage] = useState('');
  const [memories, setMemories] = useState<MemoryResult[]>([]);
  const [loading, setLoading] = useState(false);
  const userId = 'mobile_user_123';

  useEffect(() => {
    loadMemories();
  }, []);

  const loadMemories = async () => {
    try {
      const results = await memoryService.getMemories(userId, 20);
      setMemories(results);
    } catch (error) {
      Alert.alert('エラー', '記憶の読み込みに失敗しました');
    }
  };

  const saveNewMemory = async () => {
    if (!message.trim()) return;

    setLoading(true);
    try {
      await memoryService.saveMemory({
        user_message: message,
        ai_message: `モバイルアプリからの返答: ${message}`,
        user_id: userId,
        metadata: {
          platform: 'react_native',
          device_info: 'mobile_device'
        }
      });

      setMessage('');
      loadMemories();
      Alert.alert('成功', '記憶を保存しました');
    } catch (error) {
      Alert.alert('エラー', '記憶の保存に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const searchMemories = async (query: string) => {
    try {
      const results = await memoryService.searchMemories({
        query,
        user_id: userId,
        top_k: 10
      });
      setMemories(results);
    } catch (error) {
      Alert.alert('エラー', '記憶の検索に失敗しました');
    }
  };

  const renderMemoryItem = ({ item }: { item: MemoryResult }) => (
    <View style={styles.memoryItem}>
      <Text style={styles.summary}>{item.summary}</Text>
      <View style={styles.metaInfo}>
        <Text style={styles.emotions}>
          感情: {item.emotions.join(', ')}
        </Text>
        <Text style={styles.timestamp}>
          {new Date(item.timestamp).toLocaleDateString('ja-JP')}
        </Text>
        {item.score && (
          <Text style={styles.score}>
            類似度: {(item.score * 100).toFixed(1)}%
          </Text>
        )}
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>🤖 EmotionMemCore</Text>
      
      {/* メッセージ入力 */}
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.textInput}
          value={message}
          onChangeText={setMessage}
          placeholder="メッセージを入力..."
          multiline
        />
        <TouchableOpacity
          style={[styles.button, loading && styles.buttonDisabled]}
          onPress={saveNewMemory}
          disabled={loading || !message.trim()}
        >
          <Text style={styles.buttonText}>
            {loading ? '保存中...' : '保存'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* 記憶一覧 */}
      <Text style={styles.sectionTitle}>記憶一覧</Text>
      <FlatList
        data={memories}
        renderItem={renderMemoryItem}
        keyExtractor={(item) => item.memory_id}
        style={styles.memoryList}
        showsVerticalScrollIndicator={false}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#f5f5f5'
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 20,
    color: '#333'
  },
  inputContainer: {
    flexDirection: 'row',
    marginBottom: 20
  },
  textInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    backgroundColor: 'white',
    marginRight: 10,
    minHeight: 50
  },
  button: {
    backgroundColor: '#2196F3',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderRadius: 8,
    justifyContent: 'center'
  },
  buttonDisabled: {
    backgroundColor: '#ccc'
  },
  buttonText: {
    color: 'white',
    fontWeight: 'bold'
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333'
  },
  memoryList: {
    flex: 1
  },
  memoryItem: {
    backgroundColor: 'white',
    padding: 15,
    marginBottom: 10,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 2
  },
  summary: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 8,
    color: '#333'
  },
  metaInfo: {
    flexDirection: 'column'
  },
  emotions: {
    fontSize: 12,
    color: '#FF9800',
    marginBottom: 4
  },
  timestamp: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4
  },
  score: {
    fontSize: 12,
    color: '#4CAF50',
    fontWeight: 'bold'
  }
});

export default EmotionMemoryApp;
```

---

## ⚡ パフォーマンス最適化

### 接続プール最適化

```python
# performance_optimized_client.py
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class CacheEntry:
    data: Any
    timestamp: datetime
    ttl: int  # seconds

class OptimizedEmotionMemClient:
    """パフォーマンス最適化されたEmotionMemCoreクライアント"""
    
    def __init__(
        self, 
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        max_connections: int = 100,
        cache_ttl: int = 300  # 5分
    ):
        self.base_url = base_url.rstrip('/')
        self.cache: Dict[str, CacheEntry] = {}
        self.cache_ttl = cache_ttl
        
        # 接続プール設定
        connector = aiohttp.TCPConnector(
            limit=max_connections,
            limit_per_host=20,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        # HTTPセッション設定
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-API-Key"] = api_key
            
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            headers=headers,
            timeout=timeout
        )
    
    def _get_cache_key(self, method: str, **params) -> str:
        """キャッシュキー生成"""
        key_parts = [method]
        for k, v in sorted(params.items()):
            if isinstance(v, list):
                v = ','.join(str(x) for x in v)
            key_parts.append(f"{k}:{v}")
        return "|".join(key_parts)
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """キャッシュから取得"""
        if cache_key not in self.cache:
            return None
        
        entry = self.cache[cache_key]
        if datetime.now() - entry.timestamp > timedelta(seconds=entry.ttl):
            del self.cache[cache_key]
            return None
        
        return entry.data
    
    def _set_cache(self, cache_key: str, data: Any, ttl: Optional[int] = None):
        """キャッシュに保存"""
        self.cache[cache_key] = CacheEntry(
            data=data,
            timestamp=datetime.now(),
            ttl=ttl or self.cache_ttl
        )
    
    async def search_memories_cached(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        emotions: Optional[List[str]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """キャッシュ付き記憶検索"""
        
        cache_key = self._get_cache_key(
            "search", 
            query=query, 
            user_id=user_id, 
            top_k=top_k, 
            emotions=emotions
        )
        
        # キャッシュチェック
        if use_cache:
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result
        
        # API呼び出し
        payload = {
            "query": query,
            "user_id": user_id,
            "top_k": top_k
        }
        if emotions:
            payload["emotions"] = emotions
        
        try:
            async with self.session.post(f"{self.base_url}/search", json=payload) as response:
                response.raise_for_status()
                result = await response.json()
                
                # キャッシュに保存
                if use_cache:
                    self._set_cache(cache_key, result, ttl=60)  # 検索結果は1分キャッシュ
                
                return result
                
        except Exception as e:
            logging.error(f"Memory search failed: {e}")
            raise
    
    async def batch_save_memories_chunked(
        self,
        conversations: List[Dict[str, Any]],
        chunk_size: int = 10
    ) -> Dict[str, Any]:
        """チャンク分割バッチ保存"""
        
        chunks = [conversations[i:i + chunk_size] for i in range(0, len(conversations), chunk_size)]
        
        results = {
            "total_requested": len(conversations),
            "successful_saves": 0,
            "failed_saves": 0,
            "failed_items": []
        }
        
        # 並行処理でチャンクを送信
        tasks = []
        for chunk_idx, chunk in enumerate(chunks):
            task = self._process_chunk(chunk, chunk_idx * chunk_size)
            tasks.append(task)
        
        chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果集計
        for chunk_result in chunk_results:
            if isinstance(chunk_result, Exception):
                results["failed_saves"] += chunk_size
                continue
            
            results["successful_saves"] += chunk_result.get("successful_saves", 0)
            results["failed_saves"] += chunk_result.get("failed_saves", 0)
            results["failed_items"].extend(chunk_result.get("failed_items", []))
        
        return results
    
    async def _process_chunk(self, chunk: List[Dict[str, Any]], offset: int) -> Dict[str, Any]:
        """チャンク処理"""
        try:
            async with self.session.post(f"{self.base_url}/batch-save", json=chunk) as response:
                response.raise_for_status()
                result = await response.json()
                
                # オフセット調整
                for failed_item in result.get("failed_items", []):
                    failed_item["index"] += offset
                
                return result
                
        except Exception as e:
            logging.error(f"Chunk processing failed: {e}")
            return {
                "successful_saves": 0,
                "failed_saves": len(chunk),
                "failed_items": [
                    {"index": offset + i, "error": str(e)} 
                    for i in range(len(chunk))
                ]
            }
    
    async def save_memory_async(
        self,
        user_message: str,
        ai_message: str,
        user_id: str,
        session_id: Optional[str] = None,
        background: bool = True
    ) -> Optional[Dict[str, Any]]:
        """非同期記憶保存"""
        
        async def _save():
            payload = {
                "user_message": user_message,
                "ai_message": ai_message,
                "user_id": user_id
            }
            if session_id:
                payload["session_id"] = session_id
            
            try:
                async with self.session.post(f"{self.base_url}/save", json=payload) as response:
                    response.raise_for_status()
                    return await response.json()
            except Exception as e:
                logging.error(f"Async memory save failed: {e}")
                return None
        
        if background:
            # バックグラウンドタスクとして実行
            asyncio.create_task(_save())
            return None
        else:
            return await _save()
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """接続統計取得"""
        connector_info = {}
        if hasattr(self.session.connector, '_conns'):
            connector_info = {
                "total_connections": len(self.session.connector._conns),
                "acquired_connections": len([c for c in self.session.connector._conns.values() if c]),
            }
        
        return {
            "cache_size": len(self.cache),
            "connector_info": connector_info,
            "session_closed": self.session.closed
        }
    
    async def cleanup_cache(self, max_age_minutes: int = 60):
        """古いキャッシュエントリを削除"""
        cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
        
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.timestamp < cutoff_time
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return {"cleaned_entries": len(expired_keys), "remaining_entries": len(self.cache)}
    
    async def close(self):
        """リソース解放"""
        await self.session.close()
        self.cache.clear()

# 使用例
async def performance_example():
    """パフォーマンス最適化の使用例"""
    
    client = OptimizedEmotionMemClient(
        max_connections=50,
        cache_ttl=300
    )
    
    try:
        # 並行検索処理
        search_tasks = [
            client.search_memories_cached(f"クエリ{i}", "user123", use_cache=True)
            for i in range(10)
        ]
        
        results = await asyncio.gather(*search_tasks)
        print(f"Processed {len(results)} searches")
        
        # バックグラウンド保存
        await client.save_memory_async(
            "こんにちは", "こんにちは！", "user123", background=True
        )
        
        # 統計確認
        stats = await client.get_connection_stats()
        print(f"Connection stats: {stats}")
        
        # キャッシュクリーンアップ
        cleanup_result = await client.cleanup_cache(max_age_minutes=5)
        print(f"Cache cleanup: {cleanup_result}")
        
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(performance_example())
```

---

## 🐛 エラーハンドリング

### 堅牢なエラーハンドリング実装

```python
# robust_error_handling.py
import asyncio
import logging
from typing import Optional, Dict, Any, Callable, Type
from dataclasses import dataclass
from enum import Enum
import time
import random

class ErrorType(Enum):
    """エラー種別"""
    NETWORK_ERROR = "network_error"
    API_ERROR = "api_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    VALIDATION_ERROR = "validation_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"

@dataclass
class RetryConfig:
    """リトライ設定"""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True

class EmotionMemCoreError(Exception):
    """EmotionMemCore基底例外"""
    def __init__(self, message: str, error_type: ErrorType, details: Optional[Dict] = None):
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}

class RobustEmotionMemClient:
    """エラーハンドリング強化版クライアント"""
    
    def __init__(
        self, 
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        retry_config: Optional[RetryConfig] = None
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.retry_config = retry_config or RetryConfig()
        self.logger = logging.getLogger(__name__)
        
        # エラー統計
        self.error_stats = {
            "total_requests": 0,
            "failed_requests": 0,
            "error_by_type": {},
            "retry_attempts": 0
        }
    
    async def _execute_with_retry(
        self,
        operation: Callable,
        operation_name: str,
        *args,
        **kwargs
    ) -> Any:
        """リトライ機能付き操作実行"""
        
        self.error_stats["total_requests"] += 1
        last_exception = None
        
        for attempt in range(self.retry_config.max_attempts):
            try:
                # 初回以外はディレイ
                if attempt > 0:
                    delay = self._calculate_delay(attempt)
                    self.logger.info(f"Retrying {operation_name} in {delay:.2f}s (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                    self.error_stats["retry_attempts"] += 1
                
                # 操作実行
                result = await operation(*args, **kwargs)
                
                # 成功時はリトライカウンターリセット
                if attempt > 0:
                    self.logger.info(f"{operation_name} succeeded after {attempt + 1} attempts")
                
                return result
                
            except EmotionMemCoreError as e:
                last_exception = e
                self._record_error(e.error_type)
                
                # リトライしないエラー
                if e.error_type in [ErrorType.VALIDATION_ERROR]:
                    self.logger.error(f"{operation_name} failed permanently: {e}")
                    break
                
                # 最後の試行でない場合は続行
                if attempt < self.retry_config.max_attempts - 1:
                    self.logger.warning(f"{operation_name} failed (attempt {attempt + 1}): {e}")
                    continue
                else:
                    self.logger.error(f"{operation_name} failed after {self.retry_config.max_attempts} attempts: {e}")
                    break
                    
            except Exception as e:
                # 予期しないエラー
                last_exception = EmotionMemCoreError(
                    f"Unexpected error in {operation_name}: {str(e)}",
                    ErrorType.UNKNOWN_ERROR,
                    {"original_error": str(e)}
                )
                self._record_error(ErrorType.UNKNOWN_ERROR)
                
                if attempt < self.retry_config.max_attempts - 1:
                    self.logger.warning(f"{operation_name} unexpected error (attempt {attempt + 1}): {e}")
                    continue
                else:
                    self.logger.error(f"{operation_name} failed permanently with unexpected error: {e}")
                    break
        
        # 全ての試行が失敗
        self.error_stats["failed_requests"] += 1
        raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """指数バックオフ計算"""
        delay = self.retry_config.initial_delay * (self.retry_config.exponential_base ** (attempt - 1))
        delay = min(delay, self.retry_config.max_delay)
        
        # ジッター追加
        if self.retry_config.jitter:
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    def _record_error(self, error_type: ErrorType):
        """エラー統計記録"""
        type_key = error_type.value
        self.error_stats["error_by_type"][type_key] = self.error_stats["error_by_type"].get(type_key, 0) + 1
    
    async def _safe_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """安全なHTTPリクエスト"""
        try:
            import httpx
            
            headers = kwargs.get("headers", {})
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            kwargs["headers"] = headers
            
            timeout = kwargs.get("timeout", 30.0)
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(method, url, **kwargs)
                
                # HTTPエラーチェック
                if response.status_code == 429:
                    raise EmotionMemCoreError(
                        "Rate limit exceeded",
                        ErrorType.RATE_LIMIT_ERROR,
                        {"status_code": response.status_code, "response": response.text}
                    )
                elif response.status_code == 422:
                    raise EmotionMemCoreError(
                        "Validation error",
                        ErrorType.VALIDATION_ERROR,
                        {"status_code": response.status_code, "response": response.text}
                    )
                elif response.status_code >= 500:
                    raise EmotionMemCoreError(
                        f"Server error: {response.status_code}",
                        ErrorType.API_ERROR,
                        {"status_code": response.status_code, "response": response.text}
                    )
                elif response.status_code >= 400:
                    raise EmotionMemCoreError(
                        f"Client error: {response.status_code}",
                        ErrorType.API_ERROR,
                        {"status_code": response.status_code, "response": response.text}
                    )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException as e:
            raise EmotionMemCoreError(
                f"Request timeout: {str(e)}",
                ErrorType.TIMEOUT_ERROR,
                {"timeout": timeout}
            )
        except httpx.NetworkError as e:
            raise EmotionMemCoreError(
                f"Network error: {str(e)}",
                ErrorType.NETWORK_ERROR,
                {"url": url}
            )
        except EmotionMemCoreError:
            raise
        except Exception as e:
            raise EmotionMemCoreError(
                f"Unexpected HTTP error: {str(e)}",
                ErrorType.UNKNOWN_ERROR,
                {"url": url}
            )
    
    async def save_memory_safe(
        self,
        user_message: str,
        ai_message: str,
        user_id: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """安全な記憶保存"""
        
        # 入力検証
        if not user_message.strip():
            raise EmotionMemCoreError(
                "user_message cannot be empty",
                ErrorType.VALIDATION_ERROR
            )
        if not ai_message.strip():
            raise EmotionMemCoreError(
                "ai_message cannot be empty", 
                ErrorType.VALIDATION_ERROR
            )
        if not user_id.strip():
            raise EmotionMemCoreError(
                "user_id cannot be empty",
                ErrorType.VALIDATION_ERROR
            )
        
        async def _save_operation():
            payload = {
                "user_message": user_message,
                "ai_message": ai_message,
                "user_id": user_id
            }
            if session_id:
                payload["session_id"] = session_id
            if metadata:
                payload["metadata"] = metadata
            
            return await self._safe_request(
                "POST",
                f"{self.base_url}/save",
                json=payload
            )
        
        try:
            return await self._execute_with_retry(_save_operation, "save_memory")
        except EmotionMemCoreError as e:
            self.logger.error(f"Memory save failed permanently: {e}")
            
            # 重要でない場合はNoneを返す（アプリケーション継続）
            if e.error_type in [ErrorType.RATE_LIMIT_ERROR, ErrorType.NETWORK_ERROR]:
                return None
            else:
                raise
    
    async def search_memories_safe(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        emotions: Optional[list] = None,
        fallback_empty: bool = True
    ) -> Dict[str, Any]:
        """安全な記憶検索"""
        
        # 入力検証
        if not query.strip():
            if fallback_empty:
                return {"results": [], "total_results": 0}
            raise EmotionMemCoreError(
                "query cannot be empty",
                ErrorType.VALIDATION_ERROR
            )
        
        if not user_id.strip():
            raise EmotionMemCoreError(
                "user_id cannot be empty",
                ErrorType.VALIDATION_ERROR
            )
        
        async def _search_operation():
            payload = {
                "query": query,
                "user_id": user_id,
                "top_k": top_k
            }
            if emotions:
                payload["emotions"] = emotions
            
            return await self._safe_request(
                "POST",
                f"{self.base_url}/search",
                json=payload
            )
        
        try:
            return await self._execute_with_retry(_search_operation, "search_memories")
        except EmotionMemCoreError as e:
            self.logger.error(f"Memory search failed: {e}")
            
            # フォールバック: 空の結果を返す
            if fallback_empty and e.error_type in [ErrorType.NETWORK_ERROR, ErrorType.TIMEOUT_ERROR]:
                return {"results": [], "total_results": 0}
            else:
                raise
    
    async def health_check_safe(self) -> Dict[str, Any]:
        """安全なヘルスチェック"""
        
        async def _health_operation():
            return await self._safe_request("GET", f"{self.base_url}/health/")
        
        try:
            return await self._execute_with_retry(_health_operation, "health_check")
        except EmotionMemCoreError as e:
            return {
                "healthy": False,
                "error": str(e),
                "error_type": e.error_type.value
            }
    
    def get_error_stats(self) -> Dict[str, Any]:
        """エラー統計取得"""
        success_rate = 0.0
        if self.error_stats["total_requests"] > 0:
            success_rate = ((self.error_stats["total_requests"] - self.error_stats["failed_requests"]) 
                          / self.error_stats["total_requests"]) * 100
        
        return {
            **self.error_stats,
            "success_rate_percent": round(success_rate, 2),
            "current_retry_config": {
                "max_attempts": self.retry_config.max_attempts,
                "initial_delay": self.retry_config.initial_delay,
                "max_delay": self.retry_config.max_delay
            }
        }
    
    def reset_error_stats(self):
        """エラー統計リセット"""
        self.error_stats = {
            "total_requests": 0,
            "failed_requests": 0,
            "error_by_type": {},
            "retry_attempts": 0
        }

# 使用例とテスト
async def error_handling_example():
    """エラーハンドリングの使用例"""
    
    # カスタムリトライ設定
    retry_config = RetryConfig(
        max_attempts=5,
        initial_delay=0.5,
        max_delay=10.0,
        exponential_base=1.5,
        jitter=True
    )
    
    client = RobustEmotionMemClient(
        base_url="http://localhost:8000",
        retry_config=retry_config
    )
    
    # ヘルスチェック
    health = await client.health_check_safe()
    print(f"Health check: {health}")
    
    try:
        # 正常な記憶保存
        result = await client.save_memory_safe(
            user_message="テストメッセージ",
            ai_message="テスト応答",
            user_id="test_user"
        )
        print(f"Save result: {result}")
        
        # 検索（エラー時フォールバック）
        search_result = await client.search_memories_safe(
            query="テスト",
            user_id="test_user",
            fallback_empty=True
        )
        print(f"Search result: {search_result}")
        
    except EmotionMemCoreError as e:
        print(f"Operation failed: {e.error_type.value} - {e}")
        print(f"Error details: {e.details}")
    
    # エラー統計表示
    stats = client.get_error_stats()
    print(f"Error statistics: {stats}")

if __name__ == "__main__":
    asyncio.run(error_handling_example())
```

---

## 🔒 セキュリティ考慮事項

### セキュアな統合実装

```python
# secure_integration.py
import os
import hashlib
import hmac
import time
import secrets
from typing import Optional, Dict, Any
import jwt
from cryptography.fernet import Fernet
import base64

class SecureEmotionMemClient:
    """セキュリティ強化版クライアント"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        encryption_key: Optional[str] = None,
        jwt_secret: Optional[str] = None
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.jwt_secret = jwt_secret
        
        # 暗号化設定
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode())
        else:
            self.cipher = None
    
    def _encrypt_sensitive_data(self, data: str) -> str:
        """機密データの暗号化"""
        if not self.cipher:
            return data
        
        return self.cipher.encrypt(data.encode()).decode()
    
    def _decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """機密データの復号化"""
        if not self.cipher:
            return encrypted_data
        
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def _generate_request_signature(
        self, 
        method: str, 
        endpoint: str, 
        payload: str, 
        timestamp: str
    ) -> str:
        """リクエスト署名生成"""
        if not self.api_key:
            return ""
        
        message = f"{method.upper()}|{endpoint}|{payload}|{timestamp}"
        signature = hmac.new(
            self.api_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _generate_jwt_token(self, user_id: str, expires_in: int = 3600) -> str:
        """JWT トークン生成"""
        if not self.jwt_secret:
            raise ValueError("JWT secret is required")
        
        payload = {
            "user_id": user_id,
            "iat": int(time.time()),
            "exp": int(time.time()) + expires_in,
            "nonce": secrets.token_hex(16)
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def _validate_jwt_token(self, token: str) -> Dict[str, Any]:
        """JWT トークン検証"""
        if not self.jwt_secret:
            raise ValueError("JWT secret is required")
        
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
    
    def _sanitize_input(self, text: str) -> str:
        """入力データのサニタイゼーション"""
        # HTML/スクリプトタグの除去
        import re
        
        # 危険なパターンを除去
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<iframe[^>]*>.*?</iframe>',
            r'javascript:',
            r'data:text/html',
            r'vbscript:',
        ]
        
        sanitized = text
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # 長さ制限
        max_length = 10000  # 10KB
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    def _validate_user_id(self, user_id: str) -> bool:
        """ユーザーID検証"""
        # 基本的な検証
        if not user_id or len(user_id) < 3 or len(user_id) > 100:
            return False
        
        # 英数字とアンダースコア、ハイフンのみ許可
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', user_id):
            return False
        
        return True
    
    async def save_memory_secure(
        self,
        user_message: str,
        ai_message: str,
        user_id: str,
        session_id: Optional[str] = None,
        encrypt_content: bool = False
    ) -> Dict[str, Any]:
        """セキュアな記憶保存"""
        
        # 入力検証
        if not self._validate_user_id(user_id):
            raise ValueError(f"Invalid user_id: {user_id}")
        
        # サニタイゼーション
        user_message = self._sanitize_input(user_message)
        ai_message = self._sanitize_input(ai_message)
        
        # 機密データの暗号化
        if encrypt_content and self.cipher:
            user_message = self._encrypt_sensitive_data(user_message)
            ai_message = self._encrypt_sensitive_data(ai_message)
        
        # JWTトークン生成（一時的認証用）
        auth_token = None
        if self.jwt_secret:
            auth_token = self._generate_jwt_token(user_id)
        
        # リクエストペイロード
        payload = {
            "user_message": user_message,
            "ai_message": ai_message,
            "user_id": user_id,
            "metadata": {
                "encrypted": encrypt_content,
                "sanitized": True,
                "client_version": "secure_1.0"
            }
        }
        
        if session_id:
            payload["session_id"] = session_id
        
        # セキュリティヘッダー
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "SecureEmotionMemClient/1.0",
            "X-Request-ID": secrets.token_hex(16),
            "X-Timestamp": str(int(time.time()))
        }
        
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        # リクエスト署名
        if self.api_key:
            import json
            payload_str = json.dumps(payload, sort_keys=True)
            signature = self._generate_request_signature(
                "POST", "/save", payload_str, headers["X-Timestamp"]
            )
            headers["X-Signature"] = signature
        
        # API呼び出し
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/save",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()
                
                # 暗号化された結果の復号化
                if encrypt_content and self.cipher and "summary" in result:
                    try:
                        result["summary"] = self._decrypt_sensitive_data(result["summary"])
                    except:
                        pass  # 復号化失敗時は元データを使用
                
                return result
                
        except Exception as e:
            raise RuntimeError(f"Secure save failed: {e}")
    
    def _audit_log(self, action: str, user_id: str, details: Dict[str, Any] = None):
        """監査ログ記録"""
        import logging
        
        audit_logger = logging.getLogger("audit")
        
        log_entry = {
            "timestamp": time.time(),
            "action": action,
            "user_id": user_id,
            "client_ip": "unknown",  # 実際の実装では取得
            "details": details or {}
        }
        
        audit_logger.info(f"AUDIT: {log_entry}")
    
    async def search_memories_secure(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        decrypt_results: bool = False
    ) -> Dict[str, Any]:
        """セキュアな記憶検索"""
        
        # 入力検証
        if not self._validate_user_id(user_id):
            raise ValueError(f"Invalid user_id: {user_id}")
        
        # クエリサニタイゼーション
        query = self._sanitize_input(query)
        
        # 検索範囲制限
        if top_k > 50:
            top_k = 50
        
        # 監査ログ
        self._audit_log("search_memories", user_id, {"query_length": len(query)})
        
        # API呼び出し
        try:
            import httpx
            import json
            
            payload = {
                "query": query,
                "user_id": user_id,
                "top_k": top_k
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-Request-ID": secrets.token_hex(16),
                "X-Timestamp": str(int(time.time()))
            }
            
            if self.api_key:
                headers["X-API-Key"] = self.api_key
                
                # リクエスト署名
                payload_str = json.dumps(payload, sort_keys=True)
                signature = self._generate_request_signature(
                    "POST", "/search", payload_str, headers["X-Timestamp"]
                )
                headers["X-Signature"] = signature
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/search",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()
                
                # 結果の復号化
                if decrypt_results and self.cipher:
                    for memory in result.get("results", []):
                        if "summary" in memory:
                            try:
                                memory["summary"] = self._decrypt_sensitive_data(memory["summary"])
                            except:
                                pass  # 復号化失敗時は元データを使用
                
                return result
                
        except Exception as e:
            # 監査ログ（エラー）
            self._audit_log("search_memories_failed", user_id, {"error": str(e)})
            raise RuntimeError(f"Secure search failed: {e}")

# セキュリティ設定管理
class SecurityConfig:
    """セキュリティ設定管理"""
    
    @staticmethod
    def generate_encryption_key() -> str:
        """暗号化キー生成"""
        return base64.urlsafe_b64encode(Fernet.generate_key()).decode()
    
    @staticmethod
    def generate_jwt_secret() -> str:
        """JWT秘密鍵生成"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_api_key() -> str:
        """APIキー生成"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def load_from_env() -> Dict[str, str]:
        """環境変数からセキュリティ設定読み込み"""
        return {
            "api_key": os.getenv("EMOTION_MEM_API_KEY"),
            "encryption_key": os.getenv("EMOTION_MEM_ENCRYPTION_KEY"),
            "jwt_secret": os.getenv("EMOTION_MEM_JWT_SECRET"),
            "base_url": os.getenv("EMOTION_MEM_BASE_URL", "http://localhost:8000")
        }

# 使用例
async def secure_integration_example():
    """セキュアな統合の使用例"""
    
    # セキュリティ設定読み込み
    config = SecurityConfig.load_from_env()
    
    # または新規生成
    if not config["encryption_key"]:
        config["encryption_key"] = SecurityConfig.generate_encryption_key()
        print(f"Generated encryption key: {config['encryption_key']}")
    
    # セキュアクライアント初期化
    client = SecureEmotionMemClient(
        base_url=config["base_url"],
        api_key=config["api_key"],
        encryption_key=config["encryption_key"],
        jwt_secret=config["jwt_secret"]
    )
    
    try:
        # セキュアな記憶保存（暗号化有効）
        result = await client.save_memory_secure(
            user_message="機密情報を含むメッセージ",
            ai_message="セキュアな応答",
            user_id="secure_user_123",
            encrypt_content=True
        )
        print(f"Secure save result: {result}")
        
        # セキュアな検索（復号化有効）
        search_result = await client.search_memories_secure(
            query="機密情報",
            user_id="secure_user_123",
            decrypt_results=True
        )
        print(f"Secure search result: {search_result}")
        
    except Exception as e:
        print(f"Secure operation failed: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(secure_integration_example())
```

---

## 📝 まとめ

このガイドでは、EmotionMemCoreを様々なアプリケーションに統合する方法を詳しく説明しました。

### 🎯 主要なポイント

1. **共通クライアント**: 再利用可能なクライアントクラスで効率的な統合
2. **AI Vtuber統合**: 感情豊かな記憶システムでより人間らしい対話
3. **Discord Bot統合**: 自然な会話記録と記憶活用
4. **Web/モバイル統合**: リアルタイムな記憶管理インターフェース
5. **パフォーマンス最適化**: 接続プール、キャッシュ、バッチ処理
6. **エラーハンドリング**: 堅牢なリトライ機能とフォールバック
7. **セキュリティ**: 暗号化、認証、監査ログによる安全な運用

### 🚀 次のステップ

統合が完了したら、以下を検討してください：

- **監視設定**: アプリケーションメトリクスの収集
- **パフォーマンスチューニング**: 使用量に応じた最適化
- **セキュリティ監査**: 定期的なセキュリティレビュー
- **スケーリング**: 負荷増加時の拡張計画

---

**技術サポート**: [GitHub Issues](https://github.com/your-username/EmotionMemCore/issues)
**コミュニティ**: [Discussions](https://github.com/your-username/EmotionMemCore/discussions)