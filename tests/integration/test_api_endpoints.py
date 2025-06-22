"""
APIエンドポイントの統合テスト
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from uuid import uuid4

from api.schemas import SaveResponse, SearchResponse
from api.schemas.emotion import Emotion


@pytest.mark.integration
class TestSaveEndpoint:
    """保存エンドポイントテスト"""
    
    def test_save_success(self, test_client: TestClient, mock_memory_service, sample_save_request):
        """正常保存テスト"""
        # モックレスポンス設定
        mock_response = SaveResponse(
            success=True,
            memory_id=uuid4(),
            summary="ユーザーが天気について話した",
            emotions=[Emotion.JOY, Emotion.ANTICIPATION],
            processing_time_ms=150.5
        )
        mock_memory_service.save_memory.return_value = mock_response
        
        response = test_client.post("/save", json=sample_save_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "memory_id" in data
        assert "summary" in data
        assert "emotions" in data
        assert data["processing_time_ms"] == 150.5
    
    def test_save_empty_user_message(self, test_client: TestClient, sample_save_request):
        """空ユーザーメッセージテスト"""
        sample_save_request["user_message"] = ""
        
        response = test_client.post("/save", json=sample_save_request)
        
        assert response.status_code == 400
        assert "user_messageが空です" in response.json()["detail"]
    
    def test_save_empty_ai_message(self, test_client: TestClient, sample_save_request):
        """空AIメッセージテスト"""
        sample_save_request["ai_message"] = ""
        
        response = test_client.post("/save", json=sample_save_request)
        
        assert response.status_code == 400
        assert "ai_messageが空です" in response.json()["detail"]
    
    def test_save_too_long_message(self, test_client: TestClient, sample_save_request):
        """長すぎるメッセージテスト"""
        sample_save_request["user_message"] = "x" * 10001  # 10,001文字
        
        response = test_client.post("/save", json=sample_save_request)
        
        assert response.status_code == 400
        assert "長すぎます" in response.json()["detail"]
    
    def test_save_service_error(self, test_client: TestClient, mock_memory_service, sample_save_request):
        """サービスエラーテスト"""
        # エラーレスポンス設定
        mock_response = SaveResponse(
            success=False,
            error="LLM処理エラー: API key invalid",
            memory_id=uuid4()
        )
        mock_memory_service.save_memory.return_value = mock_response
        
        response = test_client.post("/save", json=sample_save_request)
        
        assert response.status_code == 500
        assert "LLM処理エラー" in response.json()["detail"]
    
    def test_save_invalid_json(self, test_client: TestClient):
        """不正JSONテスト"""
        response = test_client.post("/save", data="invalid json")
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_save_missing_required_fields(self, test_client: TestClient):
        """必須フィールド不足テスト"""
        incomplete_request = {
            "user_message": "こんにちは"
            # ai_message が不足
        }
        
        response = test_client.post("/save", json=incomplete_request)
        
        assert response.status_code == 422
    
    def test_save_with_context_window(self, test_client: TestClient, mock_memory_service):
        """文脈付き保存テスト"""
        request_with_context = {
            "user_message": "ありがとう！",
            "ai_message": "どういたしまして！",
            "context_window": [
                {"role": "user", "content": "手伝ってください"},
                {"role": "assistant", "content": "喜んでお手伝いします"}
            ],
            "user_id": "test_user",
            "session_id": "test_session"
        }
        
        mock_response = SaveResponse(
            success=True,
            memory_id=uuid4(),
            summary="ユーザーが感謝を示した",
            emotions=[Emotion.GRATITUDE],
            processing_time_ms=120.0
        )
        mock_memory_service.save_memory.return_value = mock_response
        
        response = test_client.post("/save", json=request_with_context)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # サービスが正しい引数で呼ばれたかチェック
        mock_memory_service.save_memory.assert_called_once()
        call_args = mock_memory_service.save_memory.call_args[0][0]
        assert call_args.context_window is not None
        assert len(call_args.context_window) == 2


@pytest.mark.integration
class TestSearchEndpoint:
    """検索エンドポイントテスト"""
    
    def test_search_success(self, test_client: TestClient, mock_memory_service, sample_search_request):
        """正常検索テスト"""
        # モックレスポンス設定
        mock_response = SearchResponse(
            success=True,
            results=[
                {
                    "id": "memory_1",
                    "score": 0.95,
                    "summary": "天気について話した記憶",
                    "emotions": ["喜び", "期待"],
                    "metadata": {
                        "created_at": "2024-01-01T12:00:00",
                        "user_id": "test_user"
                    }
                }
            ],
            total_count=1,
            processing_time_ms=80.3
        )
        mock_memory_service.search_memories.return_value = mock_response
        
        response = test_client.post("/search", json=sample_search_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_count"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["score"] == 0.95
    
    def test_search_empty_query(self, test_client: TestClient):
        """空クエリテスト"""
        empty_request = {
            "query": "",
            "top_k": 5
        }
        
        response = test_client.post("/search", json=empty_request)
        
        assert response.status_code == 400
        assert "検索クエリが空です" in response.json()["detail"]
    
    def test_search_invalid_top_k(self, test_client: TestClient):
        """不正top_kテスト"""
        invalid_request = {
            "query": "テスト検索",
            "top_k": 0  # 無効な値
        }
        
        response = test_client.post("/search", json=invalid_request)
        
        assert response.status_code == 400
        assert "1から100の間" in response.json()["detail"]
    
    def test_search_too_large_top_k(self, test_client: TestClient):
        """過大top_kテスト"""
        invalid_request = {
            "query": "テスト検索",
            "top_k": 150  # 上限超過
        }
        
        response = test_client.post("/search", json=invalid_request)
        
        assert response.status_code == 400
        assert "1から100の間" in response.json()["detail"]
    
    def test_search_long_query(self, test_client: TestClient):
        """長すぎるクエリテスト"""
        long_request = {
            "query": "x" * 1001,  # 1,001文字
            "top_k": 5
        }
        
        response = test_client.post("/search", json=long_request)
        
        assert response.status_code == 400
        assert "クエリが長すぎます" in response.json()["detail"]
    
    def test_search_with_filters(self, test_client: TestClient, mock_memory_service):
        """フィルター付き検索テスト"""
        filtered_request = {
            "query": "楽しい思い出",
            "top_k": 10,
            "user_id": "specific_user",
            "emotion_filter": ["喜び", "楽しさ"],
            "date_from": "2024-01-01T00:00:00",
            "date_to": "2024-12-31T23:59:59"
        }
        
        mock_response = SearchResponse(
            success=True,
            results=[],
            total_count=0,
            processing_time_ms=45.2
        )
        mock_memory_service.search_memories.return_value = mock_response
        
        response = test_client.post("/search", json=filtered_request)
        
        assert response.status_code == 200
        
        # サービスが正しい引数で呼ばれたかチェック
        mock_memory_service.search_memories.assert_called_once()
        call_args = mock_memory_service.search_memories.call_args[0][0]
        assert call_args.user_id == "specific_user"
        assert call_args.emotion_filter is not None
        assert len(call_args.emotion_filter) == 2
    
    def test_search_invalid_date_format(self, test_client: TestClient):
        """不正日付フォーマットテスト"""
        invalid_date_request = {
            "query": "テスト検索",
            "date_from": "2024/01/01",  # 不正フォーマット
            "top_k": 5
        }
        
        response = test_client.post("/search", json=invalid_date_request)
        
        assert response.status_code == 400
        assert "フォーマットが正しくありません" in response.json()["detail"]
    
    def test_search_service_error(self, test_client: TestClient, mock_memory_service, sample_search_request):
        """検索サービスエラーテスト"""
        # エラーレスポンス設定
        mock_response = SearchResponse(
            success=False,
            error="検索エラー: Database connection failed",
            results=[],
            total_count=0
        )
        mock_memory_service.search_memories.return_value = mock_response
        
        response = test_client.post("/search", json=sample_search_request)
        
        assert response.status_code == 500
        assert "検索エラー" in response.json()["detail"]


@pytest.mark.integration
class TestMemoriesEndpoint:
    """記憶一覧エンドポイントテスト"""
    
    def test_get_memories_basic(self, test_client: TestClient, mock_memory_service):
        """基本記憶一覧テスト"""
        # モックメモリデータ
        from api.schemas import Memory
        from datetime import datetime
        
        mock_memories = [
            Memory(
                id=uuid4(),
                summary="テスト記憶1",
                emotions=[Emotion.JOY],
                original_user="ユーザー1",
                original_ai="AI1",
                created_at=datetime.utcnow()
            ),
            Memory(
                id=uuid4(),
                summary="テスト記憶2",
                emotions=[Emotion.SADNESS],
                original_user="ユーザー2",
                original_ai="AI2",
                created_at=datetime.utcnow()
            )
        ]
        mock_memory_service.get_memories_by_filter.return_value = mock_memories
        
        response = test_client.get("/memories")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert "id" in data[0]
        assert "summary" in data[0]
        assert "emotions" in data[0]
    
    def test_get_memories_with_pagination(self, test_client: TestClient, mock_memory_service):
        """ページネーション付き記憶一覧テスト"""
        mock_memory_service.get_memories_by_filter.return_value = []
        
        response = test_client.get("/memories?limit=10&offset=20")
        
        assert response.status_code == 200
        
        # サービスが正しい引数で呼ばれたかチェック
        mock_memory_service.get_memories_by_filter.assert_called_once()
        call_kwargs = mock_memory_service.get_memories_by_filter.call_args[1]
        assert call_kwargs["limit"] == 10
        assert call_kwargs["offset"] == 20
    
    def test_get_memories_with_filters(self, test_client: TestClient, mock_memory_service):
        """フィルター付き記憶一覧テスト"""
        mock_memory_service.get_memories_by_filter.return_value = []
        
        response = test_client.get(
            "/memories"
            "?user_id=test_user"
            "&emotions=喜び&emotions=楽しさ"
            "&date_from=2024-01-01T00:00:00"
            "&date_to=2024-12-31T23:59:59"
        )
        
        assert response.status_code == 200
        
        # フィルター引数確認
        call_kwargs = mock_memory_service.get_memories_by_filter.call_args[1]
        assert call_kwargs["user_id"] == "test_user"
        assert call_kwargs["emotions"] == ["喜び", "楽しさ"]
        assert call_kwargs["date_from"] == "2024-01-01T00:00:00"
        assert call_kwargs["date_to"] == "2024-12-31T23:59:59"
    
    def test_get_memories_invalid_limit(self, test_client: TestClient):
        """不正limit値テスト"""
        response = test_client.get("/memories?limit=0")
        
        assert response.status_code == 422  # Validation error
    
    def test_get_memories_too_large_limit(self, test_client: TestClient):
        """過大limit値テスト"""
        response = test_client.get("/memories?limit=1000")
        
        assert response.status_code == 422  # Validation error


@pytest.mark.integration
class TestHealthEndpoint:
    """ヘルスチェックエンドポイントテスト"""
    
    def test_health_check_success(self, test_client: TestClient, mock_memory_service):
        """正常ヘルスチェックテスト"""
        mock_health_status = {
            "healthy": True,
            "timestamp": 1234567890.0,
            "components": {
                "memory_store": {"healthy": True},
                "embedding_client": {"healthy": True},
                "llm_client": {"healthy": True}
            }
        }
        mock_memory_service.health_check.return_value = mock_health_status
        
        response = test_client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["healthy"] is True
        assert "components" in data
        assert len(data["components"]) == 3
    
    def test_health_check_unhealthy(self, test_client: TestClient, mock_memory_service):
        """異常ヘルスチェックテスト"""
        mock_health_status = {
            "healthy": False,
            "timestamp": 1234567890.0,
            "components": {
                "memory_store": {"healthy": False},
                "embedding_client": {"healthy": True},
                "llm_client": {"healthy": True}
            },
            "error": "Database connection failed"
        }
        mock_memory_service.health_check.return_value = mock_health_status
        
        response = test_client.get("/health/")
        
        assert response.status_code == 200  # ヘルスチェックは200で返すが、内容で判断
        data = response.json()
        assert data["healthy"] is False
        assert "error" in data
    
    def test_stats_endpoint(self, test_client: TestClient, mock_memory_service):
        """統計エンドポイントテスト"""
        mock_stats = {
            "total_memories": 100,
            "recent_emotions": {"喜び": 30, "悲しみ": 20},
            "service_status": "active",
            "llm_provider": "MockLLM",
            "embedding_model": "text-embedding-3-small"
        }
        mock_memory_service.get_stats.return_value = mock_stats
        
        response = test_client.get("/health/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_memories"] == 100
        assert "recent_emotions" in data
        assert data["service_status"] == "active"


@pytest.mark.integration
class TestRootEndpoint:
    """ルートエンドポイントテスト"""
    
    def test_root_endpoint(self, test_client: TestClient):
        """ルートエンドポイントテスト"""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "EmotionMemCore API"
        assert "version" in data
        assert "endpoints" in data
        assert "debug_mode" in data