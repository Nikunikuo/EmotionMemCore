"""
pytest設定とフィクスチャ
"""

import os
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock

import httpx
from fastapi.testclient import TestClient

# テスト用環境変数設定
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG_MODE"] = "true"
os.environ["LLM_MOCK_MODE"] = "true"
os.environ["CHROMA_PERSIST_DIRECTORY"] = "./test_chroma_db"
os.environ["MEMORY_COLLECTION_NAME"] = "test_emotion_memories"

from api.app import create_app
from api.dependencies import (
    get_memory_service, get_chroma_client, get_embedding_client,
    get_collection_manager
)
from core.llm.mock import MockLLM
from core.embedding.openai_client import OpenAIEmbeddingClient
from infrastructure.db import ChromaDBClient, ChromaMemoryStore, CollectionManager
from services.memory_service import MemoryService


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """テスト用イベントループ"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_llm() -> MockLLM:
    """モックLLMクライアント"""
    return MockLLM()


@pytest.fixture
def mock_embedding_client() -> Mock:
    """モックEmbeddingクライアント"""
    mock = Mock(spec=OpenAIEmbeddingClient)
    mock.model = "text-embedding-3-small"
    mock.dimension = 1536
    
    # get_embeddingメソッドをAsyncMockに設定
    mock.get_embedding = AsyncMock(return_value=[0.1] * 1536)
    mock.get_embeddings_batch = AsyncMock(return_value=[[0.1] * 1536])
    mock.similarity = AsyncMock(return_value=0.8)
    mock.health_check = AsyncMock(return_value=True)
    
    return mock


@pytest.fixture
def mock_chroma_client() -> Mock:
    """モックChromaDBクライアント"""
    mock = Mock(spec=ChromaDBClient)
    
    # コレクション管理
    mock_collection = Mock()
    mock_collection.count.return_value = 0
    mock_collection.metadata = {"description": "test collection"}
    mock.get_or_create_collection.return_value = mock_collection
    
    # データ操作
    mock.add_memory.return_value = True
    mock.search_memories.return_value = {
        "ids": [[]],
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]]
    }
    mock.get_memory_by_id.return_value = None
    mock.delete_memory.return_value = True
    mock.get_collection_stats.return_value = {
        "total_memories": 0,
        "recent_emotions": {}
    }
    mock.health_check.return_value = True
    
    return mock


@pytest.fixture
def mock_memory_store(mock_chroma_client: Mock, mock_embedding_client: Mock) -> Mock:
    """モックメモリストア"""
    mock = Mock(spec=ChromaMemoryStore)
    
    # 基本操作
    mock.save_memory = AsyncMock(return_value=True)
    mock.search_memories = AsyncMock(return_value=[])
    mock.get_memory_by_id = AsyncMock(return_value=None)
    mock.delete_memory = AsyncMock(return_value=True)
    mock.get_memories_by_filter = AsyncMock(return_value=[])
    mock.get_collection_stats = AsyncMock(return_value={
        "total_memories": 0,
        "recent_emotions": {}
    })
    mock.health_check = AsyncMock(return_value=True)
    
    return mock


@pytest.fixture
def mock_collection_manager(mock_chroma_client: Mock) -> Mock:
    """モックコレクション管理"""
    mock = Mock(spec=CollectionManager)
    
    mock.create_collection.return_value = True
    mock.delete_collection.return_value = True
    mock.list_collections.return_value = []
    mock.backup_collection.return_value = True
    mock.restore_collection.return_value = True
    mock.list_backups.return_value = []
    mock.cleanup_old_backups.return_value = 0
    mock.get_storage_info.return_value = {
        "database_size_mb": 0,
        "backup_size_mb": 0,
        "total_size_mb": 0,
        "collection_count": 0,
        "total_memories": 0,
        "backup_count": 0
    }
    
    return mock


@pytest.fixture
def mock_memory_service(
    mock_memory_store: Mock,
    mock_llm: MockLLM,
    mock_embedding_client: Mock
) -> Mock:
    """モックメモリサービス"""
    mock = Mock(spec=MemoryService)
    
    # 非同期メソッドの設定
    mock.save_memory = AsyncMock()
    mock.search_memories = AsyncMock()
    mock.get_memory_by_id = AsyncMock(return_value=None)
    mock.delete_memory = AsyncMock(return_value=True)
    mock.get_memories_by_filter = AsyncMock(return_value=[])
    mock.get_stats = AsyncMock(return_value={
        "total_memories": 0,
        "recent_emotions": {},
        "service_status": "active"
    })
    mock.health_check = AsyncMock(return_value={
        "healthy": True,
        "components": {
            "memory_store": {"healthy": True},
            "embedding_client": {"healthy": True},
            "llm_client": {"healthy": True}
        }
    })
    
    return mock


@pytest.fixture
def app_with_mocks(
    mock_memory_service: Mock,
    mock_collection_manager: Mock
):
    """モック付きFastAPIアプリ"""
    app = create_app()
    
    # 依存性オーバーライド
    app.dependency_overrides[get_memory_service] = lambda: mock_memory_service
    app.dependency_overrides[get_collection_manager] = lambda: mock_collection_manager
    
    yield app
    
    # クリーンアップ
    app.dependency_overrides.clear()


@pytest.fixture
def test_client(app_with_mocks) -> TestClient:
    """テストクライアント"""
    return TestClient(app_with_mocks)


@pytest.fixture
async def async_test_client(app_with_mocks) -> AsyncGenerator[httpx.AsyncClient, None]:
    """非同期テストクライアント"""
    async with httpx.AsyncClient(
        app=app_with_mocks,
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def sample_save_request() -> dict:
    """サンプル保存リクエスト"""
    return {
        "user_message": "今日はいい天気ですね！",
        "ai_message": "そうですね！お散歩日和で気持ちがいいですね。",
        "user_id": "test_user",
        "session_id": "test_session",
        "app_name": "test_app"
    }


@pytest.fixture
def sample_search_request() -> dict:
    """サンプル検索リクエスト"""
    return {
        "query": "天気について",
        "top_k": 5,
        "user_id": "test_user"
    }


@pytest.fixture
def sample_memory_data() -> dict:
    """サンプル記憶データ"""
    return {
        "id": "12345678-1234-1234-1234-123456789abc",
        "summary": "ユーザーが天気について話した",
        "emotions": ["喜び", "期待"],
        "original_user": "今日はいい天気ですね！",
        "original_ai": "そうですね！お散歩日和で気持ちがいいですね。",
        "user_id": "test_user",
        "session_id": "test_session",
        "app_name": "test_app",
        "created_at": "2024-01-01T12:00:00"
    }


# テスト環境のクリーンアップ
@pytest.fixture(autouse=True)
def cleanup_test_env():
    """テスト環境の自動クリーンアップ"""
    yield
    
    # テスト用データベースディレクトリのクリーンアップ
    import shutil
    test_db_path = "./test_chroma_db"
    if os.path.exists(test_db_path):
        try:
            shutil.rmtree(test_db_path)
        except Exception:
            pass  # クリーンアップエラーは無視


# カスタムマーカー
def pytest_configure(config):
    """カスタムマーカー登録"""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests"
    )
    config.addinivalue_line(
        "markers", "requires_api_key: Tests requiring API keys"
    )
    config.addinivalue_line(
        "markers", "requires_internet: Tests requiring internet connection"
    )