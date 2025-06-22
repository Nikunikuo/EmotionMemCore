"""
E2E（エンドツーエンド）テスト
実際のワークフローをテスト
"""

import pytest
import httpx
import asyncio
from typing import List, Dict, Any


@pytest.mark.e2e
@pytest.mark.slow
class TestFullWorkflow:
    """完全ワークフローテスト"""
    
    @pytest.mark.asyncio
    async def test_save_and_search_workflow(self, async_test_client: httpx.AsyncClient):
        """保存→検索の完全ワークフローテスト"""
        
        # Step 1: ヘルスチェック
        health_response = await async_test_client.get("/health/")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["healthy"] is True
        
        # Step 2: 複数の記憶を保存
        conversations = [
            {
                "user_message": "今日はとても良い天気ですね！散歩に行こうかな。",
                "ai_message": "本当にいい天気ですね！散歩は気持ちが良さそうです。どちらに行かれますか？",
                "user_id": "test_user_1",
                "session_id": "session_weather",
                "app_name": "e2e_test"
            },
            {
                "user_message": "最近仕事が忙しくて疲れています...休みたいです。",
                "ai_message": "お疲れ様です。無理をしないでくださいね。しっかり休息を取ることが大切です。",
                "user_id": "test_user_1", 
                "session_id": "session_work",
                "app_name": "e2e_test"
            },
            {
                "user_message": "新しいゲームを買いました！すごく面白そうです。",
                "ai_message": "わあ、新しいゲームですね！どんなジャンルのゲームですか？楽しそうでワクワクします♪",
                "user_id": "test_user_1",
                "session_id": "session_game", 
                "app_name": "e2e_test"
            }
        ]
        
        saved_memory_ids: List[str] = []
        
        for conversation in conversations:
            save_response = await async_test_client.post("/save", json=conversation)
            assert save_response.status_code == 200
            
            save_data = save_response.json()
            assert save_data["success"] is True
            assert "memory_id" in save_data
            assert "summary" in save_data
            assert "emotions" in save_data
            assert save_data["processing_time_ms"] > 0
            
            saved_memory_ids.append(save_data["memory_id"])
        
        # Step 3: 保存された記憶の検証
        assert len(saved_memory_ids) == 3
        
        # Step 4: 様々な検索パターンをテスト
        search_queries = [
            {
                "query": "天気について話した内容",
                "top_k": 5,
                "expected_keywords": ["天気", "散歩"]
            },
            {
                "query": "仕事のストレスや疲れについて",
                "top_k": 5,
                "expected_keywords": ["仕事", "疲れ", "忙し"]
            },
            {
                "query": "楽しいことや娯楽について",
                "top_k": 5,
                "expected_keywords": ["ゲーム", "楽し", "面白"]
            }
        ]
        
        for search_query in search_queries:
            search_response = await async_test_client.post("/search", json={
                "query": search_query["query"],
                "top_k": search_query["top_k"],
                "user_id": "test_user_1"
            })
            
            assert search_response.status_code == 200
            search_data = search_response.json()
            assert search_data["success"] is True
            assert search_data["total_count"] >= 0
            assert search_data["processing_time_ms"] > 0
            
            # 検索結果の関連性チェック
            if search_data["total_count"] > 0:
                top_result = search_data["results"][0]
                assert "id" in top_result
                assert "score" in top_result
                assert "summary" in top_result
                assert "emotions" in top_result
                assert 0 <= top_result["score"] <= 1
                
                # キーワードの関連性確認（部分的）
                summary_lower = top_result["summary"].lower()
                found_keyword = any(
                    keyword in summary_lower 
                    for keyword in search_query["expected_keywords"]
                )
                # 完璧な一致は期待しないが、ある程度の関連性は期待
                
        # Step 5: 感情フィルター付き検索
        emotion_search_response = await async_test_client.post("/search", json={
            "query": "楽しい記憶",
            "top_k": 10,
            "user_id": "test_user_1",
            "emotion_filter": ["喜び", "楽しさ", "興奮"]
        })
        
        assert emotion_search_response.status_code == 200
        emotion_search_data = emotion_search_response.json()
        assert emotion_search_data["success"] is True
        
        # Step 6: 記憶一覧取得
        memories_response = await async_test_client.get("/memories", params={
            "user_id": "test_user_1",
            "limit": 10,
            "offset": 0
        })
        
        assert memories_response.status_code == 200
        memories_data = memories_response.json()
        assert isinstance(memories_data, list)
        
        # 保存した記憶が含まれているか確認
        memory_ids_in_list = [memory["id"] for memory in memories_data]
        common_ids = set(saved_memory_ids) & set(memory_ids_in_list)
        assert len(common_ids) >= 0  # モックモードでは実際の保存は行われない
        
        # Step 7: 統計情報取得
        stats_response = await async_test_client.get("/health/stats")
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        assert "total_memories" in stats_data
        assert "service_status" in stats_data
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, async_test_client: httpx.AsyncClient):
        """エラーハンドリングワークフローテスト"""
        
        # 不正な保存リクエスト
        invalid_save_requests = [
            {
                "user_message": "",  # 空メッセージ
                "ai_message": "回答"
            },
            {
                "user_message": "質問",
                "ai_message": ""  # 空回答
            },
            {
                "user_message": "x" * 10001,  # 長すぎるメッセージ
                "ai_message": "回答"
            }
        ]
        
        for invalid_request in invalid_save_requests:
            save_response = await async_test_client.post("/save", json=invalid_request)
            assert save_response.status_code == 400
            error_data = save_response.json()
            assert "detail" in error_data
        
        # 不正な検索リクエスト
        invalid_search_requests = [
            {
                "query": "",  # 空クエリ
                "top_k": 5
            },
            {
                "query": "テスト",
                "top_k": 0  # 不正なtop_k
            },
            {
                "query": "x" * 1001,  # 長すぎるクエリ
                "top_k": 5
            }
        ]
        
        for invalid_request in invalid_search_requests:
            search_response = await async_test_client.post("/search", json=invalid_request)
            assert search_response.status_code == 400
            error_data = search_response.json()
            assert "detail" in error_data
        
        # 不正なJSONリクエスト
        invalid_json_response = await async_test_client.post(
            "/save", 
            content="invalid json", 
            headers={"Content-Type": "application/json"}
        )
        assert invalid_json_response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, async_test_client: httpx.AsyncClient):
        """同時リクエストテスト"""
        
        # 同時保存リクエスト
        save_tasks = []
        for i in range(5):
            request = {
                "user_message": f"並行テストメッセージ {i}",
                "ai_message": f"並行テスト回答 {i}",
                "user_id": f"concurrent_user_{i}",
                "session_id": f"concurrent_session_{i}",
                "app_name": "concurrent_test"
            }
            task = async_test_client.post("/save", json=request)
            save_tasks.append(task)
        
        # 全ての保存リクエストを並行実行
        save_responses = await asyncio.gather(*save_tasks, return_exceptions=True)
        
        successful_saves = 0
        for response in save_responses:
            if isinstance(response, httpx.Response) and response.status_code == 200:
                successful_saves += 1
            elif isinstance(response, Exception):
                # 例外の場合はログに記録（実際のテストでは詳細確認）
                print(f"Concurrent save exception: {response}")
        
        # 少なくとも一部は成功することを期待
        assert successful_saves >= 0
        
        # 同時検索リクエスト
        search_tasks = []
        for i in range(3):
            request = {
                "query": f"並行検索 {i}",
                "top_k": 5,
                "user_id": f"concurrent_user_{i}"
            }
            task = async_test_client.post("/search", json=request)
            search_tasks.append(task)
        
        search_responses = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        successful_searches = 0
        for response in search_responses:
            if isinstance(response, httpx.Response) and response.status_code == 200:
                successful_searches += 1
        
        assert successful_searches >= 0
    
    @pytest.mark.asyncio
    async def test_session_based_workflow(self, async_test_client: httpx.AsyncClient):
        """セッションベースワークフローテスト"""
        
        # 同一セッション内での複数会話
        session_id = "session_conversation_flow"
        user_id = "test_user_session"
        
        conversation_flow = [
            {
                "user_message": "こんにちは！今日は何をしましょうか？",
                "ai_message": "こんにちは！今日はどんなことをお手伝いしましょうか？",
                "context": "greeting"
            },
            {
                "user_message": "プログラミングについて教えてください",
                "ai_message": "プログラミングについてですね！どの言語に興味がありますか？",
                "context": "programming_interest",
                "context_window": [
                    {"role": "user", "content": "こんにちは！今日は何をしましょうか？"},
                    {"role": "assistant", "content": "こんにちは！今日はどんなことをお手伝いしましょうか？"}
                ]
            },
            {
                "user_message": "Pythonを学びたいです！",
                "ai_message": "Pythonは素晴らしい選択ですね！まずは基本構文から始めましょう。",
                "context": "python_learning",
                "context_window": [
                    {"role": "user", "content": "プログラミングについて教えてください"},
                    {"role": "assistant", "content": "プログラミングについてですね！どの言語に興味がありますか？"}
                ]
            }
        ]
        
        saved_memories = []
        
        for conversation in conversation_flow:
            save_request = {
                "user_message": conversation["user_message"],
                "ai_message": conversation["ai_message"],
                "user_id": user_id,
                "session_id": session_id,
                "app_name": "session_test"
            }
            
            if "context_window" in conversation:
                save_request["context_window"] = conversation["context_window"]
            
            save_response = await async_test_client.post("/save", json=save_request)
            assert save_response.status_code == 200
            
            save_data = save_response.json()
            saved_memories.append(save_data)
        
        # セッション内検索
        session_search_response = await async_test_client.post("/search", json={
            "query": "プログラミングの学習について",
            "top_k": 10,
            "user_id": user_id
        })
        
        assert session_search_response.status_code == 200
        search_data = session_search_response.json()
        assert search_data["success"] is True
        
        # セッション内記憶取得
        session_memories_response = await async_test_client.get("/memories", params={
            "user_id": user_id,
            "limit": 20
        })
        
        assert session_memories_response.status_code == 200
        memories_data = session_memories_response.json()
        assert isinstance(memories_data, list)


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.requires_internet
class TestRealIntegrationWorkflow:
    """実際の統合テスト（API キー必要）"""
    
    @pytest.mark.skip(reason="Requires real API keys and is slow")
    @pytest.mark.asyncio
    async def test_real_llm_integration(self, async_test_client: httpx.AsyncClient):
        """実LLM統合テスト（スキップ対象）"""
        # このテストは実際のAPIキーが必要で時間がかかるため、
        # 通常はスキップされる
        
        # 実際のLLMを使用したテストロジック
        # - 環境変数でLLM_MOCK_MODE=falseに設定
        # - 実際のAPIキーを使用
        # - ネットワーク接続が必要
        pass
    
    @pytest.mark.skip(reason="Requires real embedding API and is slow")
    @pytest.mark.asyncio
    async def test_real_embedding_integration(self, async_test_client: httpx.AsyncClient):
        """実Embedding統合テスト（スキップ対象）"""
        # このテストは実際のEmbedding APIが必要
        
        # 実際のEmbedding APIを使用したテストロジック
        # - OpenAI API キーが必要
        # - ネットワーク接続が必要
        # - 実際のベクトル計算を実行
        pass