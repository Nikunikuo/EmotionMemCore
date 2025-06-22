"""
ChromaDB クライアント実装
"""

import os
from typing import List, Dict, Any, Optional
from uuid import UUID

import chromadb
from chromadb.config import Settings

from infrastructure.config.logger import get_logger


class ChromaDBClient:
    """ChromaDB クライアント"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.logger = get_logger(__name__)
        self.persist_directory = persist_directory
        
        # ChromaDB設定
        settings = Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False  # テレメトリ無効化
        )
        
        try:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=settings
            )
            
            self.logger.info(
                "chromadb_initialized",
                persist_directory=persist_directory
            )
            
        except Exception as e:
            self.logger.error("chromadb_init_failed", error=str(e))
            raise
    
    def get_or_create_collection(
        self, 
        name: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> chromadb.Collection:
        """コレクションを取得または作成"""
        try:
            # デフォルトメタデータ
            default_metadata = {
                "description": "感情付き記憶データベース",
                "version": "1.0.0"
            }
            
            if metadata:
                default_metadata.update(metadata)
            
            collection = self.client.get_or_create_collection(
                name=name,
                metadata=default_metadata
            )
            
            self.logger.info(
                "collection_created_or_retrieved",
                collection_name=name,
                count=collection.count()
            )
            
            return collection
            
        except Exception as e:
            self.logger.error(
                "collection_creation_failed",
                collection_name=name,
                error=str(e)
            )
            raise
    
    def add_memory(
        self,
        collection: chromadb.Collection,
        memory_id: str,
        summary: str,
        emotions: List[str],
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """記憶をコレクションに追加"""
        try:
            # メタデータの準備
            memory_metadata = {
                "emotions": ",".join(emotions),
                "summary": summary,
                **metadata
            }
            
            collection.add(
                ids=[memory_id],
                documents=[summary],  # 検索用テキスト
                embeddings=[embedding],
                metadatas=[memory_metadata]
            )
            
            self.logger.info(
                "memory_added",
                memory_id=memory_id,
                emotions_count=len(emotions),
                metadata_keys=list(metadata.keys())
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "memory_add_failed",
                memory_id=memory_id,
                error=str(e)
            )
            return False
    
    def search_memories(
        self,
        collection: chromadb.Collection,
        query_embedding: List[float],
        top_k: int = 5,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """記憶を検索"""
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            self.logger.info(
                "memories_searched",
                results_count=len(results["ids"][0]) if results["ids"] else 0,
                top_k=top_k,
                has_filter=where_filter is not None
            )
            
            return results
            
        except Exception as e:
            self.logger.error(
                "memory_search_failed",
                error=str(e),
                top_k=top_k
            )
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
    
    def get_memory_by_id(
        self,
        collection: chromadb.Collection,
        memory_id: str
    ) -> Optional[Dict[str, Any]]:
        """IDで記憶を取得"""
        try:
            results = collection.get(
                ids=[memory_id],
                include=["documents", "metadatas"]
            )
            
            if results["ids"] and len(results["ids"]) > 0:
                return {
                    "id": results["ids"][0],
                    "document": results["documents"][0],
                    "metadata": results["metadatas"][0]
                }
            
            return None
            
        except Exception as e:
            self.logger.error(
                "memory_get_failed",
                memory_id=memory_id,
                error=str(e)
            )
            return None
    
    def delete_memory(
        self,
        collection: chromadb.Collection,
        memory_id: str
    ) -> bool:
        """記憶を削除"""
        try:
            collection.delete(ids=[memory_id])
            
            self.logger.info(
                "memory_deleted",
                memory_id=memory_id
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "memory_delete_failed",
                memory_id=memory_id,
                error=str(e)
            )
            return False
    
    def get_collection_stats(self, collection: chromadb.Collection) -> Dict[str, Any]:
        """コレクションの統計情報を取得"""
        try:
            count = collection.count()
            
            # 最近の記憶をサンプリング
            sample_results = collection.peek(limit=10)
            
            # 感情統計の計算
            emotion_counts = {}
            if sample_results["metadatas"]:
                for metadata in sample_results["metadatas"]:
                    if "emotions" in metadata:
                        emotions = metadata["emotions"].split(",")
                        for emotion in emotions:
                            emotion = emotion.strip()
                            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            stats = {
                "total_memories": count,
                "recent_emotions": emotion_counts,
                "sample_count": len(sample_results["ids"]) if sample_results["ids"] else 0
            }
            
            self.logger.info("collection_stats_retrieved", **stats)
            
            return stats
            
        except Exception as e:
            self.logger.error("collection_stats_failed", error=str(e))
            return {"total_memories": 0, "recent_emotions": {}, "sample_count": 0}
    
    def health_check(self) -> bool:
        """ChromaDBヘルスチェック"""
        try:
            # テストコレクション作成
            test_collection = self.client.get_or_create_collection("health_check")
            
            # 簡単なテスト
            test_id = "health_test"
            test_collection.add(
                ids=[test_id],
                documents=["health check test"],
                embeddings=[[0.1, 0.2, 0.3]]
            )
            
            # 削除
            test_collection.delete(ids=[test_id])
            
            self.logger.info("chromadb_health_check_passed")
            return True
            
        except Exception as e:
            self.logger.error("chromadb_health_check_failed", error=str(e))
            return False