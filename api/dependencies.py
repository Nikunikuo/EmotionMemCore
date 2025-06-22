"""
依存性注入設定
"""

import os
from typing import Optional, Union

from core.llm import ClaudeLLM, MockLLM
from core.embedding.openai_client import OpenAIEmbeddingClient
from core.embedding.mock_client import MockEmbeddingClient
from infrastructure.db import ChromaDBClient, ChromaMemoryStore, CollectionManager
from services.memory_service import MemoryService
from infrastructure.config.logger import get_logger

logger = get_logger(__name__)

# シングルトンインスタンス
_memory_service: Optional[MemoryService] = None
_chroma_client: Optional[ChromaDBClient] = None
_embedding_client: Optional[Union[OpenAIEmbeddingClient, MockEmbeddingClient]] = None
_collection_manager: Optional[CollectionManager] = None


async def get_chroma_client() -> ChromaDBClient:
    """ChromaDBクライアント取得"""
    global _chroma_client
    
    if _chroma_client is None:
        persist_directory = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
        _chroma_client = ChromaDBClient(persist_directory=persist_directory)
        
        logger.info("chroma_client_initialized", persist_directory=persist_directory)
    
    return _chroma_client


async def get_embedding_client():
    """Embeddingクライアント取得"""
    global _embedding_client
    
    if _embedding_client is None:
        # OpenAI API Key チェック
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if openai_api_key:
            # OpenAI Embedding Client を使用
            model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            try:
                _embedding_client = OpenAIEmbeddingClient(model=model)
                logger.info("embedding_client_initialized", model=model)
            except Exception as e:
                logger.warning("openai_embedding_failed_fallback_to_mock", error=str(e))
                _embedding_client = MockEmbeddingClient(model="mock-embedding")
        else:
            # Mock Embedding Client にフォールバック
            logger.warning("openai_api_key_missing_using_mock_embedding")
            _embedding_client = MockEmbeddingClient(model="mock-embedding")
    
    return _embedding_client


async def get_collection_manager() -> CollectionManager:
    """コレクション管理取得"""
    global _collection_manager
    
    if _collection_manager is None:
        chroma_client = await get_chroma_client()
        persist_directory = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
        _collection_manager = CollectionManager(
            chroma_client=chroma_client,
            persist_directory=persist_directory
        )
        
        logger.info("collection_manager_initialized")
    
    return _collection_manager


async def get_llm_client():
    """LLMクライアント取得"""
    
    # モックモードチェック
    if os.getenv("LLM_MOCK_MODE", "false").lower() == "true":
        logger.info("llm_mock_mode_enabled")
        return MockLLM()
    
    # LLMプロバイダー選択
    llm_provider = os.getenv("LLM_PROVIDER", "claude").lower()
    
    if llm_provider == "claude":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("anthropic_api_key_missing_fallback_to_mock")
            mock_config = {"model": "mock-claude", "max_tokens": 1000}
            return MockLLM(model_config=mock_config)
        
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        model_config = {
            "model": model,
            "max_tokens": 1000,
            "temperature": 0.3
        }
        return ClaudeLLM(model_config=model_config)
    
    else:
        logger.warning(
            "unsupported_llm_provider_fallback_to_mock",
            provider=llm_provider
        )
        mock_config = {"model": "mock-unknown", "max_tokens": 1000}
        return MockLLM(model_config=mock_config)


async def get_memory_service() -> MemoryService:
    """メモリサービス取得"""
    global _memory_service
    
    if _memory_service is None:
        # 依存関係取得
        chroma_client = await get_chroma_client()
        embedding_client = await get_embedding_client()
        llm_client = await get_llm_client()
        
        # メモリストア作成
        collection_name = os.getenv("MEMORY_COLLECTION_NAME", "emotion_memories")
        memory_store = ChromaMemoryStore(
            chroma_client=chroma_client,
            embedding_client=embedding_client,
            collection_name=collection_name
        )
        
        # メモリサービス作成
        _memory_service = MemoryService(
            memory_store=memory_store,
            llm_client=llm_client,
            embedding_client=embedding_client
        )
        
        logger.info(
            "memory_service_initialized",
            collection_name=collection_name,
            llm_provider=os.getenv("LLM_PROVIDER", "claude"),
            embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        )
    
    return _memory_service


# FastAPI Depends用のファクトリ関数
def memory_service_dependency():
    """FastAPI Depends用メモリサービス取得"""
    return get_memory_service


def collection_manager_dependency():
    """FastAPI Depends用コレクション管理取得"""
    return get_collection_manager