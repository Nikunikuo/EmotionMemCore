"""
DB層の単体テスト
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from uuid import uuid4

from infrastructure.db.chroma_client import ChromaDBClient
from infrastructure.db.memory_store import ChromaMemoryStore, BaseMemoryStore
from infrastructure.db.collection_manager import CollectionManager
from core.embedding.openai_client import OpenAIEmbeddingClient
from api.schemas import Memory, SearchRequest
from api.schemas.emotion import Emotion


@pytest.mark.unit
class TestChromaDBClient:
    """ChromaDBClientテスト"""
    
    def test_init(self):
        """初期化テスト"""
        with patch('chromadb.PersistentClient') as mock_client:
            client = ChromaDBClient(persist_directory="./test_db")
            
            assert client.persist_directory == "./test_db"
            mock_client.assert_called_once()
    
    def test_get_or_create_collection(self):
        """コレクション作成テスト"""
        with patch('chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.count.return_value = 0
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            client = ChromaDBClient()
            collection = client.get_or_create_collection("test_collection")
            
            assert collection == mock_collection
            mock_client.return_value.get_or_create_collection.assert_called_once()
    
    def test_add_memory(self):
        """記憶追加テスト"""
        with patch('chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            
            client = ChromaDBClient()
            
            result = client.add_memory(
                collection=mock_collection,
                memory_id="test_id",
                summary="テスト要約",
                emotions=["喜び", "期待"],
                embedding=[0.1] * 10,
                metadata={"test": "data"}
            )
            
            assert result is True
            mock_collection.add.assert_called_once()
    
    def test_search_memories(self):
        """記憶検索テスト"""
        with patch('chromadb.PersistentClient'):
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "ids": [["id1", "id2"]],
                "documents": [["doc1", "doc2"]],
                "metadatas": [[{"meta1": "data1"}, {"meta2": "data2"}]],
                "distances": [[0.1, 0.2]]
            }
            
            client = ChromaDBClient()
            
            results = client.search_memories(
                collection=mock_collection,
                query_embedding=[0.1] * 10,
                top_k=5
            )
            
            assert "ids" in results
            assert len(results["ids"][0]) == 2
            mock_collection.query.assert_called_once()
    
    def test_get_memory_by_id(self):
        """ID検索テスト"""
        with patch('chromadb.PersistentClient'):
            mock_collection = Mock()
            mock_collection.get.return_value = {
                "ids": ["test_id"],
                "documents": ["test_doc"],
                "metadatas": [{"test": "meta"}]
            }
            
            client = ChromaDBClient()
            result = client.get_memory_by_id(mock_collection, "test_id")
            
            assert result is not None
            assert result["id"] == "test_id"
            mock_collection.get.assert_called_once()
    
    def test_delete_memory(self):
        """記憶削除テスト"""
        with patch('chromadb.PersistentClient'):
            mock_collection = Mock()
            
            client = ChromaDBClient()
            result = client.delete_memory(mock_collection, "test_id")
            
            assert result is True
            mock_collection.delete.assert_called_once_with(ids=["test_id"])
    
    def test_health_check(self):
        """ヘルスチェックテスト"""
        with patch('chromadb.PersistentClient') as mock_client:
            mock_test_collection = Mock()
            mock_client.return_value.get_or_create_collection.return_value = mock_test_collection
            
            client = ChromaDBClient()
            result = client.health_check()
            
            assert result is True
            mock_test_collection.add.assert_called_once()
            mock_test_collection.delete.assert_called_once()


@pytest.mark.unit
class TestChromeMemoryStore:
    """ChromaMemoryStoreテスト"""
    
    @pytest.fixture
    def mock_chroma_client(self):
        """モックChromaクライアント"""
        mock = Mock()
        mock_collection = Mock()
        mock_collection.count.return_value = 0
        mock.get_or_create_collection.return_value = mock_collection
        return mock
    
    @pytest.fixture
    def mock_embedding_client(self):
        """モックEmbeddingクライアント"""
        mock = Mock()
        mock.get_embedding = AsyncMock(return_value=[0.1] * 1536)
        return mock
    
    def test_init(self, mock_chroma_client, mock_embedding_client):
        """初期化テスト"""
        store = ChromaMemoryStore(
            chroma_client=mock_chroma_client,
            embedding_client=mock_embedding_client,
            collection_name="test_collection"
        )
        
        assert store.chroma_client == mock_chroma_client
        assert store.embedding_client == mock_embedding_client
        assert store.collection_name == "test_collection"
    
    @pytest.mark.asyncio
    async def test_save_memory(self, mock_chroma_client, mock_embedding_client):
        """記憶保存テスト"""
        mock_chroma_client.add_memory.return_value = True
        
        store = ChromaMemoryStore(
            chroma_client=mock_chroma_client,
            embedding_client=mock_embedding_client
        )
        
        memory = Memory(
            id=uuid4(),
            summary="テスト要約",
            emotions=[Emotion.JOY],
            original_user="ユーザーメッセージ",
            original_ai="AI回答",
            embedding=[0.1] * 1536
        )
        
        result = await store.save_memory(memory)
        
        assert result is True
        mock_chroma_client.add_memory.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_memory_without_embedding(self, mock_chroma_client, mock_embedding_client):
        """埋め込みなし記憶保存テスト"""
        mock_chroma_client.add_memory.return_value = True
        
        store = ChromaMemoryStore(
            chroma_client=mock_chroma_client,
            embedding_client=mock_embedding_client
        )
        
        memory = Memory(
            id=uuid4(),
            summary="テスト要約",
            emotions=[Emotion.JOY],
            original_user="ユーザーメッセージ",
            original_ai="AI回答"
            # embedding なし
        )
        
        result = await store.save_memory(memory)
        
        assert result is True
        mock_embedding_client.get_embedding.assert_called_once()
        mock_chroma_client.add_memory.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_memories(self, mock_chroma_client, mock_embedding_client):
        """記憶検索テスト"""
        mock_chroma_client.search_memories.return_value = {
            "ids": [["id1"]],
            "metadatas": [[{
                "summary": "テスト要約",
                "emotions": "喜び,期待",
                "created_at": datetime.utcnow().isoformat()
            }]],
            "distances": [[0.1]]
        }
        
        store = ChromaMemoryStore(
            chroma_client=mock_chroma_client,
            embedding_client=mock_embedding_client
        )
        
        request = SearchRequest(
            query="テスト検索",
            top_k=5
        )
        
        results = await store.search_memories([0.1] * 1536, request)
        
        assert len(results) == 1
        assert results[0]["id"] == "id1"
        assert results[0]["score"] == 0.9  # 1.0 - 0.1
    
    @pytest.mark.asyncio
    async def test_search_memories_with_emotion_filter(self, mock_chroma_client, mock_embedding_client):
        """感情フィルター付き検索テスト"""
        mock_chroma_client.search_memories.return_value = {
            "ids": [["id1", "id2"]],
            "metadatas": [[
                {
                    "summary": "喜びの記憶",
                    "emotions": "喜び,期待",
                    "created_at": datetime.utcnow().isoformat()
                },
                {
                    "summary": "悲しみの記憶",
                    "emotions": "悲しみ",
                    "created_at": datetime.utcnow().isoformat()
                }
            ]],
            "distances": [[0.1, 0.2]]
        }
        
        store = ChromaMemoryStore(
            chroma_client=mock_chroma_client,
            embedding_client=mock_embedding_client
        )
        
        request = SearchRequest(
            query="テスト検索",
            top_k=5,
            emotion_filter=[Emotion.JOY]  # 喜びのみ
        )
        
        results = await store.search_memories([0.1] * 1536, request)
        
        # 喜びを含む記憶のみフィルターされる
        assert len(results) == 1
        assert results[0]["id"] == "id1"
    
    @pytest.mark.asyncio
    async def test_get_memory_by_id(self, mock_chroma_client, mock_embedding_client):
        """ID取得テスト"""
        test_id = uuid4()
        mock_chroma_client.get_memory_by_id.return_value = {
            "id": str(test_id),
            "metadata": {
                "summary": "テスト要約",
                "emotions": "喜び,期待",
                "original_user": "ユーザーメッセージ",
                "original_ai": "AI回答",
                "created_at": datetime.utcnow().isoformat()
            }
        }
        
        store = ChromaMemoryStore(
            chroma_client=mock_chroma_client,
            embedding_client=mock_embedding_client
        )
        
        result = await store.get_memory_by_id(test_id)
        
        assert result is not None
        assert result.id == test_id
        assert result.summary == "テスト要約"
        assert len(result.emotions) == 2
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, mock_chroma_client, mock_embedding_client):
        """削除テスト"""
        mock_chroma_client.delete_memory.return_value = True
        
        store = ChromaMemoryStore(
            chroma_client=mock_chroma_client,
            embedding_client=mock_embedding_client
        )
        
        test_id = uuid4()
        result = await store.delete_memory(test_id)
        
        assert result is True
        mock_chroma_client.delete_memory.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_chroma_client, mock_embedding_client):
        """ヘルスチェックテスト"""
        mock_chroma_client.health_check.return_value = True
        
        store = ChromaMemoryStore(
            chroma_client=mock_chroma_client,
            embedding_client=mock_embedding_client
        )
        
        result = await store.health_check()
        
        assert result is True
        mock_chroma_client.health_check.assert_called_once()


@pytest.mark.unit
class TestCollectionManager:
    """CollectionManagerテスト"""
    
    @pytest.fixture
    def mock_chroma_client(self):
        """モックChromaクライアント"""
        mock = Mock()
        mock.client = Mock()
        return mock
    
    def test_init(self, mock_chroma_client):
        """初期化テスト"""
        with patch('pathlib.Path.mkdir'):
            manager = CollectionManager(
                chroma_client=mock_chroma_client,
                persist_directory="./test_db"
            )
            
            assert manager.chroma_client == mock_chroma_client
            assert manager.persist_directory == "./test_db"
    
    def test_create_collection(self, mock_chroma_client):
        """コレクション作成テスト"""
        with patch('pathlib.Path.mkdir'):
            manager = CollectionManager(mock_chroma_client)
            
            result = manager.create_collection("test_collection")
            
            assert result is True
    
    def test_delete_collection(self, mock_chroma_client):
        """コレクション削除テスト"""
        with patch('pathlib.Path.mkdir'):
            manager = CollectionManager(mock_chroma_client)
            
            # バックアップ作成をモック
            with patch.object(manager, 'backup_collection', return_value=True):
                result = manager.delete_collection("test_collection")
                
                assert result is True
                mock_chroma_client.client.delete_collection.assert_called_once()
    
    def test_list_collections(self, mock_chroma_client):
        """コレクション一覧テスト"""
        mock_collection = Mock()
        mock_collection.name = "test_collection"
        mock_collection.count.return_value = 10
        mock_collection.metadata = {"version": "1.0"}
        
        mock_chroma_client.client.list_collections.return_value = [mock_collection]
        mock_chroma_client.get_collection_stats.return_value = {"total_memories": 10}
        
        with patch('pathlib.Path.mkdir'):
            manager = CollectionManager(mock_chroma_client)
            
            collections = manager.list_collections()
            
            assert len(collections) == 1
            assert collections[0]["name"] == "test_collection"
            assert collections[0]["count"] == 10
    
    @patch('json.dump')
    @patch('builtins.open')
    @patch('pathlib.Path.mkdir')
    def test_backup_collection(self, mock_mkdir, mock_open, mock_json_dump, mock_chroma_client):
        """バックアップ作成テスト"""
        mock_collection = Mock()
        mock_collection.metadata = {"version": "1.0"}
        mock_collection.count.return_value = 5
        mock_collection.get.return_value = {
            "ids": ["id1", "id2"],
            "documents": ["doc1", "doc2"],
            "metadatas": [{"meta1": "data1"}, {"meta2": "data2"}],
            "embeddings": [[0.1], [0.2]]
        }
        
        mock_chroma_client.client.get_collection.return_value = mock_collection
        
        manager = CollectionManager(mock_chroma_client)
        
        with patch('os.path.getsize', return_value=1024):
            result = manager.backup_collection("test_collection")
            
            assert result is True
            mock_json_dump.assert_called()
    
    def test_get_storage_info(self, mock_chroma_client):
        """ストレージ情報テスト"""
        with patch('pathlib.Path.mkdir'), \
             patch('os.path.exists', return_value=True), \
             patch('os.walk', return_value=[("./", [], ["file1.db"])]), \
             patch('os.path.getsize', return_value=1024), \
             patch('os.listdir', return_value=["backup1"]), \
             patch('os.path.isdir', return_value=True):
            
            manager = CollectionManager(mock_chroma_client)
            
            # コレクション一覧をモック
            with patch.object(manager, 'list_collections', return_value=[{"count": 10}]):
                info = manager.get_storage_info()
                
                assert "database_size_mb" in info
                assert "backup_size_mb" in info
                assert "total_memories" in info
                assert info["total_memories"] == 10