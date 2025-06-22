"""
記憶サービス実装
ビジネスロジックとLLM連携
"""

import time
from typing import List, Dict, Any, Optional
from uuid import uuid4

from api.schemas import Memory, SaveRequest, SearchRequest, SearchResponse, SaveResponse
from core.llm.base import BaseLLM, LLMRequest, LLMError
from core.llm.prompts import PromptTemplate
from core.embedding.openai_client import OpenAIEmbeddingClient
from infrastructure.db.memory_store import BaseMemoryStore
from infrastructure.config.logger import get_logger


class MemoryService:
    """記憶サービス"""
    
    def __init__(
        self, 
        memory_store: BaseMemoryStore,
        llm_client: BaseLLM,
        embedding_client: OpenAIEmbeddingClient
    ):
        self.logger = get_logger(__name__)
        self.memory_store = memory_store
        self.llm_client = llm_client
        self.embedding_client = embedding_client
        self.prompt_template = PromptTemplate()
        
        self.logger.info("memory_service_initialized")
    
    async def save_memory(self, request: SaveRequest) -> SaveResponse:
        """記憶を保存"""
        start_time = time.time()
        memory_id = uuid4()
        
        try:
            self.logger.info(
                "memory_save_started",
                memory_id=str(memory_id),
                user_id=request.user_id,
                session_id=request.session_id
            )
            
            # LLMで要約と感情抽出
            llm_request = LLMRequest(
                user_message=request.user_message,
                ai_message=request.ai_message,
                context_window=request.context_window,
                user_id=request.user_id,
                session_id=request.session_id
            )
            
            llm_response = await self.llm_client.process_memory(llm_request)
            
            # Embeddingベクトル生成
            embedding_text = f"{llm_response.summary} {request.user_message} {request.ai_message}"
            embedding = await self.embedding_client.get_embedding(embedding_text)
            
            # Memoryオブジェクト作成
            memory = Memory(
                id=memory_id,
                summary=llm_response.summary,
                emotions=llm_response.emotions,
                original_user=request.user_message,
                original_ai=request.ai_message,
                user_id=request.user_id,
                session_id=request.session_id,
                app_name=request.app_name,
                embedding=embedding
            )
            
            # データベースに保存
            save_success = await self.memory_store.save_memory(memory)
            
            if not save_success:
                raise RuntimeError("記憶の保存に失敗しました")
            
            processing_time = (time.time() - start_time) * 1000
            
            self.logger.info(
                "memory_save_completed",
                memory_id=str(memory_id),
                summary=llm_response.summary,
                emotions=[e.value for e in llm_response.emotions],
                processing_time_ms=round(processing_time, 2)
            )
            
            return SaveResponse(
                success=True,
                memory_id=memory_id,
                summary=llm_response.summary,
                emotions=llm_response.emotions,
                processing_time_ms=round(processing_time, 2)
            )
            
        except LLMError as e:
            self.logger.error(
                "memory_save_llm_failed",
                memory_id=str(memory_id),
                error=str(e),
                error_type=type(e).__name__
            )
            return SaveResponse(
                success=False,
                error=f"LLM処理エラー: {str(e)}",
                memory_id=memory_id
            )
            
        except Exception as e:
            self.logger.error(
                "memory_save_failed",
                memory_id=str(memory_id),
                error=str(e),
                error_type=type(e).__name__
            )
            return SaveResponse(
                success=False,
                error=f"記憶保存エラー: {str(e)}",
                memory_id=memory_id
            )
    
    async def search_memories(self, request: SearchRequest) -> SearchResponse:
        """記憶を検索"""
        start_time = time.time()
        
        try:
            self.logger.info(
                "memory_search_started",
                query=request.query,
                top_k=request.top_k,
                user_id=request.user_id
            )
            
            # クエリのEmbedding生成
            query_embedding = await self.embedding_client.get_embedding(request.query)
            
            # データベース検索
            search_results = await self.memory_store.search_memories(
                query_embedding=query_embedding,
                request=request
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            self.logger.info(
                "memory_search_completed",
                query=request.query,
                results_count=len(search_results),
                processing_time_ms=round(processing_time, 2)
            )
            
            return SearchResponse(
                success=True,
                results=search_results,
                total_count=len(search_results),
                processing_time_ms=round(processing_time, 2)
            )
            
        except Exception as e:
            self.logger.error(
                "memory_search_failed",
                query=request.query,
                error=str(e),
                error_type=type(e).__name__
            )
            return SearchResponse(
                success=False,
                error=f"検索エラー: {str(e)}",
                results=[],
                total_count=0
            )
    
    async def get_memory_by_id(self, memory_id: str) -> Optional[Memory]:
        """IDで記憶を取得"""
        try:
            from uuid import UUID
            memory_uuid = UUID(memory_id)
            return await self.memory_store.get_memory_by_id(memory_uuid)
        except Exception as e:
            self.logger.error(
                "memory_get_by_id_failed",
                memory_id=memory_id,
                error=str(e)
            )
            return None
    
    async def delete_memory(self, memory_id: str) -> bool:
        """記憶を削除"""
        try:
            from uuid import UUID
            memory_uuid = UUID(memory_id)
            success = await self.memory_store.delete_memory(memory_uuid)
            
            if success:
                self.logger.info("memory_deleted", memory_id=memory_id)
            else:
                self.logger.warning("memory_deletion_failed", memory_id=memory_id)
            
            return success
        except Exception as e:
            self.logger.error(
                "memory_delete_failed",
                memory_id=memory_id,
                error=str(e)
            )
            return False
    
    async def get_memories_by_filter(
        self,
        user_id: Optional[str] = None,
        emotions: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Memory]:
        """フィルターで記憶を取得"""
        try:
            from datetime import datetime
            from api.schemas.emotion import Emotion
            
            # 日付変換
            date_from_dt = None
            date_to_dt = None
            if date_from:
                date_from_dt = datetime.fromisoformat(date_from)
            if date_to:
                date_to_dt = datetime.fromisoformat(date_to)
            
            # 感情変換
            emotion_list = None
            if emotions:
                emotion_list = [Emotion.from_japanese(e) for e in emotions if e]
            
            return await self.memory_store.get_memories_by_filter(
                user_id=user_id,
                emotions=emotion_list,
                date_from=date_from_dt,
                date_to=date_to_dt,
                limit=limit,
                offset=offset
            )
            
        except Exception as e:
            self.logger.error(
                "memory_filter_failed",
                user_id=user_id,
                emotions=emotions,
                error=str(e)
            )
            return []
    
    async def get_stats(self) -> Dict[str, Any]:
        """統計情報取得"""
        try:
            stats = await self.memory_store.get_collection_stats()
            
            # 追加統計情報
            stats.update({
                "service_status": "active",
                "llm_provider": type(self.llm_client).__name__,
                "embedding_model": self.embedding_client.model,
                "embedding_dimension": self.embedding_client.dimension
            })
            
            return stats
            
        except Exception as e:
            self.logger.error("stats_retrieval_failed", error=str(e))
            return {
                "total_memories": 0,
                "recent_emotions": {},
                "service_status": "error",
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        health_status = {
            "healthy": True,
            "timestamp": time.time(),
            "components": {}
        }
        
        try:
            # メモリストアチェック
            memory_store_healthy = await self.memory_store.health_check()
            health_status["components"]["memory_store"] = {
                "healthy": memory_store_healthy,
                "type": type(self.memory_store).__name__
            }
            
            # Embeddingクライアントチェック
            embedding_healthy = await self.embedding_client.health_check()
            health_status["components"]["embedding_client"] = {
                "healthy": embedding_healthy,
                "model": self.embedding_client.model,
                "dimension": self.embedding_client.dimension
            }
            
            # LLMクライアントチェック（簡易）
            llm_healthy = True
            llm_info = {"type": type(self.llm_client).__name__}
            try:
                if hasattr(self.llm_client, 'health_check'):
                    llm_healthy = await self.llm_client.health_check()
                elif hasattr(self.llm_client, 'model'):
                    llm_info["model"] = self.llm_client.model
            except Exception:
                llm_healthy = False
            
            health_status["components"]["llm_client"] = {
                "healthy": llm_healthy,
                **llm_info
            }
            
            # 全体ステータス
            health_status["healthy"] = all(
                comp["healthy"] for comp in health_status["components"].values()
            )
            
            self.logger.info("health_check_completed", status=health_status)
            
        except Exception as e:
            self.logger.error("health_check_failed", error=str(e))
            health_status.update({
                "healthy": False,
                "error": str(e)
            })
        
        return health_status