"""
記憶ストア抽象化層
将来的なDB切り替えを考慮した設計
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from api.schemas import Memory, SearchRequest, Emotion


class BaseMemoryStore(ABC):
    """記憶ストア基底クラス"""
    
    @abstractmethod
    async def save_memory(self, memory: Memory) -> bool:
        """記憶を保存"""
        pass
    
    @abstractmethod
    async def search_memories(
        self, 
        query_embedding: List[float], 
        request: SearchRequest
    ) -> List[Dict[str, Any]]:
        """記憶を検索"""
        pass
    
    @abstractmethod
    async def get_memory_by_id(self, memory_id: UUID) -> Optional[Memory]:
        """IDで記憶を取得"""
        pass
    
    @abstractmethod
    async def delete_memory(self, memory_id: UUID) -> bool:
        """記憶を削除"""
        pass
    
    @abstractmethod
    async def get_memories_by_filter(
        self, 
        user_id: Optional[str] = None,
        emotions: Optional[List[Emotion]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Memory]:
        """フィルターで記憶を取得"""
        pass
    
    @abstractmethod
    async def get_collection_stats(self) -> Dict[str, Any]:
        """コレクション統計を取得"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """ヘルスチェック"""
        pass


class ChromaMemoryStore(BaseMemoryStore):
    """ChromaDB を使用した記憶ストア"""
    
    def __init__(self, chroma_client, embedding_client, collection_name: str = "emotion_memories"):
        self.chroma_client = chroma_client
        self.embedding_client = embedding_client
        self.collection_name = collection_name
        
        # コレクション初期化
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={
                "description": "感情付き記憶データベース",
                "version": "1.0.0",
                "created_at": datetime.utcnow().isoformat()
            }
        )
    
    async def save_memory(self, memory: Memory) -> bool:
        """記憶をChromaDBに保存"""
        try:
            # メタデータ準備
            metadata = {
                "summary": memory.summary,
                "emotions": ",".join([e.value for e in memory.emotions]),
                "user_id": memory.user_id or "",
                "session_id": memory.session_id or "",
                "app_name": memory.app_name or "",
                "created_at": memory.created_at.isoformat(),
                "original_user": memory.original_user,
                "original_ai": memory.original_ai
            }
            
            # 埋め込みベクトルの準備
            if not memory.embedding:
                # 要約からベクトル生成
                memory.embedding = await self.embedding_client.get_embedding(memory.summary)
            
            # ChromaDBに保存
            return self.chroma_client.add_memory(
                collection=self.collection,
                memory_id=str(memory.id),
                summary=memory.summary,
                emotions=[e.value for e in memory.emotions],
                embedding=memory.embedding,
                metadata=metadata
            )
            
        except Exception as e:
            from infrastructure.config.logger import get_logger
            logger = get_logger(__name__)
            logger.error("memory_save_failed", memory_id=str(memory.id), error=str(e))
            return False
    
    async def search_memories(
        self, 
        query_embedding: List[float], 
        request: SearchRequest
    ) -> List[Dict[str, Any]]:
        """記憶を検索"""
        try:
            # フィルター構築
            where_filter = {}
            
            if request.user_id:
                where_filter["user_id"] = request.user_id
            
            if request.emotion_filter:
                # OR条件での感情フィルター（部分マッチ）
                emotion_values = [e.value for e in request.emotion_filter]
                # ChromaDBの場合、メタデータでの複雑な検索は制限があるため、
                # 後でフィルタリングする
            
            # 検索実行
            results = self.chroma_client.search_memories(
                collection=self.collection,
                query_embedding=query_embedding,
                top_k=request.top_k,
                where_filter=where_filter if where_filter else None
            )
            
            # 結果を変換
            search_results = []
            if results["ids"] and results["ids"][0]:
                for i, memory_id in enumerate(results["ids"][0]):
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i]
                    
                    # 感情フィルターの後処理
                    if request.emotion_filter:
                        memory_emotions = metadata.get("emotions", "").split(",")
                        emotion_values = [e.value for e in request.emotion_filter]
                        if not any(emotion in memory_emotions for emotion in emotion_values):
                            continue
                    
                    # 日付フィルター
                    if request.date_from or request.date_to:
                        created_at = datetime.fromisoformat(metadata.get("created_at", ""))
                        if request.date_from and created_at < request.date_from:
                            continue
                        if request.date_to and created_at > request.date_to:
                            continue
                    
                    search_results.append({
                        "id": memory_id,
                        "score": 1.0 - distance,  # 距離をスコアに変換
                        "metadata": metadata,
                        "summary": metadata.get("summary", ""),
                        "emotions": metadata.get("emotions", "").split(",")
                    })
            
            return search_results
            
        except Exception as e:
            from infrastructure.config.logger import get_logger
            logger = get_logger(__name__)
            logger.error("memory_search_failed", error=str(e))
            return []
    
    async def get_memory_by_id(self, memory_id: UUID) -> Optional[Memory]:
        """IDで記憶を取得"""
        try:
            result = self.chroma_client.get_memory_by_id(
                collection=self.collection,
                memory_id=str(memory_id)
            )
            
            if not result:
                return None
            
            # Memoryオブジェクトに変換
            metadata = result["metadata"]
            
            return Memory(
                id=UUID(result["id"]),
                summary=metadata["summary"],
                emotions=[Emotion.from_japanese(e.strip()) for e in metadata["emotions"].split(",") if e.strip()],
                original_user=metadata["original_user"],
                original_ai=metadata["original_ai"],
                user_id=metadata.get("user_id") or None,
                session_id=metadata.get("session_id") or None,
                app_name=metadata.get("app_name") or None,
                created_at=datetime.fromisoformat(metadata["created_at"])
            )
            
        except Exception as e:
            from infrastructure.config.logger import get_logger
            logger = get_logger(__name__)
            logger.error("memory_get_failed", memory_id=str(memory_id), error=str(e))
            return None
    
    async def delete_memory(self, memory_id: UUID) -> bool:
        """記憶を削除"""
        try:
            return self.chroma_client.delete_memory(
                collection=self.collection,
                memory_id=str(memory_id)
            )
        except Exception as e:
            from infrastructure.config.logger import get_logger
            logger = get_logger(__name__)
            logger.error("memory_delete_failed", memory_id=str(memory_id), error=str(e))
            return False
    
    async def get_memories_by_filter(
        self, 
        user_id: Optional[str] = None,
        emotions: Optional[List[Emotion]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Memory]:
        """フィルターで記憶を取得（ページネーション対応）"""
        # ChromaDBでは複雑なフィルターとページネーションの組み合わせが困難なため、
        # 簡易実装として全件取得後にフィルター
        # 本格的な実装では専用のクエリエンジンが必要
        
        try:
            # 基本フィルター
            where_filter = {}
            if user_id:
                where_filter["user_id"] = user_id
            
            # 大量データ取得（ChromaDBの制限内で）
            results = self.chroma_client.search_memories(
                collection=self.collection,
                query_embedding=[0.0] * 1536,  # ダミーベクトル
                top_k=min(1000, limit * 10),  # 余裕を持った取得
                where_filter=where_filter if where_filter else None
            )
            
            memories = []
            if results["ids"] and results["ids"][0]:
                for i, memory_id in enumerate(results["ids"][0]):
                    metadata = results["metadatas"][0][i]
                    
                    # 感情フィルター
                    if emotions:
                        memory_emotions = metadata.get("emotions", "").split(",")
                        emotion_values = [e.value for e in emotions]
                        if not any(emotion in memory_emotions for emotion in emotion_values):
                            continue
                    
                    # 日付フィルター
                    if date_from or date_to:
                        created_at = datetime.fromisoformat(metadata.get("created_at", ""))
                        if date_from and created_at < date_from:
                            continue
                        if date_to and created_at > date_to:
                            continue
                    
                    # Memoryオブジェクト作成
                    memory = Memory(
                        id=UUID(memory_id),
                        summary=metadata["summary"],
                        emotions=[Emotion.from_japanese(e.strip()) for e in metadata["emotions"].split(",") if e.strip()],
                        original_user=metadata["original_user"],
                        original_ai=metadata["original_ai"],
                        user_id=metadata.get("user_id") or None,
                        session_id=metadata.get("session_id") or None,
                        app_name=metadata.get("app_name") or None,
                        created_at=datetime.fromisoformat(metadata["created_at"])
                    )
                    
                    memories.append(memory)
            
            # ページネーション
            return memories[offset:offset + limit]
            
        except Exception as e:
            from infrastructure.config.logger import get_logger
            logger = get_logger(__name__)
            logger.error("memories_filter_failed", error=str(e))
            return []
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """コレクション統計を取得"""
        try:
            return self.chroma_client.get_collection_stats(self.collection)
        except Exception as e:
            from infrastructure.config.logger import get_logger
            logger = get_logger(__name__)
            logger.error("collection_stats_failed", error=str(e))
            return {"total_memories": 0, "recent_emotions": {}}
    
    async def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            return self.chroma_client.health_check()
        except Exception as e:
            from infrastructure.config.logger import get_logger
            logger = get_logger(__name__)
            logger.error("memory_store_health_check_failed", error=str(e))
            return False