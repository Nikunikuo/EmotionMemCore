"""
バッチ処理エンドポイント
"""

import asyncio
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException

from api.schemas import SaveRequest, SaveResponse
from api.dependencies import memory_service_dependency
from services.memory_service import MemoryService
from infrastructure.config.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/batch-save")
async def batch_save_memories(
    requests: List[SaveRequest],
    memory_service: MemoryService = Depends(memory_service_dependency)
) -> Dict[str, Any]:
    """
    バッチ記憶保存エンドポイント
    
    複数の会話を一度に保存します。各記憶は個別に処理され、
    一部が失敗しても他の記憶は正常に保存されます。
    
    - **requests**: 保存リクエストのリスト（最大100件）
    
    各リクエストの構造：
    - **user_message**: ユーザーのメッセージ
    - **ai_message**: AIの返答
    - **user_id**: ユーザーID（オプション）
    - **session_id**: セッションID（オプション）
    - **app_name**: アプリケーション名（オプション）
    - **context_window**: 会話の文脈（オプション）
    
    レスポンス：
    - **success**: 全体の成功フラグ
    - **total_requested**: 要求された保存数
    - **successful_saves**: 成功した保存数
    - **failed_saves**: 失敗した保存数
    - **results**: 各保存結果の詳細
    - **processing_time_ms**: 総処理時間
    - **summary**: 処理結果サマリー
    """
    
    import time
    start_time = time.time()
    
    logger.info(
        "batch_save_started",
        batch_size=len(requests)
    )
    
    try:
        # 入力検証
        if not requests:
            raise HTTPException(
                status_code=400,
                detail="保存リクエストが空です"
            )
        
        # バッチサイズ制限
        max_batch_size = 100
        if len(requests) > max_batch_size:
            raise HTTPException(
                status_code=400,
                detail=f"バッチサイズが大きすぎます（最大: {max_batch_size}件）"
            )
        
        # 各リクエストの基本検証
        for i, request in enumerate(requests):
            if not request.user_message.strip():
                raise HTTPException(
                    status_code=400,
                    detail=f"リクエスト{i+1}: user_messageが空です"
                )
            if not request.ai_message.strip():
                raise HTTPException(
                    status_code=400,
                    detail=f"リクエスト{i+1}: ai_messageが空です"
                )
        
        # 並行処理設定
        max_concurrent = min(10, len(requests))  # 最大10並行
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def save_single_memory(index: int, request: SaveRequest) -> Dict[str, Any]:
            """単一記憶保存（セマフォ付き）"""
            async with semaphore:
                try:
                    response = await memory_service.save_memory(request)
                    return {
                        "index": index,
                        "success": response.success,
                        "memory_id": str(response.memory_id) if response.memory_id else None,
                        "summary": response.summary if response.success else None,
                        "emotions": [e.value for e in response.emotions] if response.emotions else [],
                        "processing_time_ms": response.processing_time_ms,
                        "error": response.error if not response.success else None
                    }
                except Exception as e:
                    logger.error(
                        "batch_save_single_error",
                        index=index,
                        error=str(e)
                    )
                    return {
                        "index": index,
                        "success": False,
                        "memory_id": None,
                        "summary": None,
                        "emotions": [],
                        "processing_time_ms": 0,
                        "error": f"予期しないエラー: {str(e)}"
                    }
        
        # 並行保存実行
        tasks = [
            save_single_memory(i, request) 
            for i, request in enumerate(requests)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果集計
        successful_saves = 0
        failed_saves = 0
        processed_results = []
        
        for result in results:
            if isinstance(result, Exception):
                # 例外が発生した場合
                processed_results.append({
                    "index": len(processed_results),
                    "success": False,
                    "error": f"処理例外: {str(result)}"
                })
                failed_saves += 1
            else:
                processed_results.append(result)
                if result["success"]:
                    successful_saves += 1
                else:
                    failed_saves += 1
        
        # 処理時間計算
        total_processing_time = (time.time() - start_time) * 1000
        
        # サマリー生成
        success_rate = (successful_saves / len(requests)) * 100 if requests else 0
        
        summary = {
            "success_rate": round(success_rate, 1),
            "average_processing_time_ms": round(
                sum(r.get("processing_time_ms", 0) for r in processed_results) / len(processed_results)
                if processed_results else 0, 2
            ),
            "total_emotions_detected": sum(
                len(r.get("emotions", [])) for r in processed_results if r.get("success")
            )
        }
        
        # 全体結果
        overall_success = failed_saves == 0
        
        logger.info(
            "batch_save_completed",
            total_requested=len(requests),
            successful_saves=successful_saves,
            failed_saves=failed_saves,
            success_rate=success_rate,
            total_processing_time_ms=round(total_processing_time, 2)
        )
        
        return {
            "success": overall_success,
            "total_requested": len(requests),
            "successful_saves": successful_saves,
            "failed_saves": failed_saves,
            "results": processed_results,
            "processing_time_ms": round(total_processing_time, 2),
            "summary": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(
            "batch_save_error",
            batch_size=len(requests),
            error=str(e),
            error_type=type(e).__name__,
            processing_time_ms=round(processing_time, 2)
        )
        raise HTTPException(
            status_code=500,
            detail=f"バッチ保存エラー: {str(e)}"
        )


@router.post("/batch-search")
async def batch_search_memories(
    queries: List[str],
    top_k: int = 5,
    user_id: str = None,
    memory_service: MemoryService = Depends(memory_service_dependency)
) -> Dict[str, Any]:
    """
    バッチ記憶検索エンドポイント
    
    複数のクエリで同時に記憶を検索します。
    
    - **queries**: 検索クエリのリスト（最大50件）
    - **top_k**: 各クエリで取得する結果数（デフォルト: 5）
    - **user_id**: 特定ユーザーの記憶に限定（オプション）
    
    レスポンス：
    - **success**: 全体の成功フラグ
    - **total_queries**: 要求されたクエリ数
    - **successful_searches**: 成功した検索数
    - **failed_searches**: 失敗した検索数
    - **results**: 各検索結果の詳細
    - **processing_time_ms**: 総処理時間
    """
    
    import time
    start_time = time.time()
    
    logger.info(
        "batch_search_started",
        batch_size=len(queries),
        top_k=top_k,
        user_id=user_id
    )
    
    try:
        # 入力検証
        if not queries:
            raise HTTPException(
                status_code=400,
                detail="検索クエリが空です"
            )
        
        # バッチサイズ制限
        max_batch_size = 50
        if len(queries) > max_batch_size:
            raise HTTPException(
                status_code=400,
                detail=f"バッチサイズが大きすぎます（最大: {max_batch_size}件）"
            )
        
        # top_k制限
        if top_k <= 0 or top_k > 20:
            raise HTTPException(
                status_code=400,
                detail="top_kは1から20の間で指定してください"
            )
        
        # クエリ検証
        for i, query in enumerate(queries):
            if not query.strip():
                raise HTTPException(
                    status_code=400,
                    detail=f"クエリ{i+1}が空です"
                )
            if len(query) > 1000:
                raise HTTPException(
                    status_code=400,
                    detail=f"クエリ{i+1}が長すぎます（最大1000文字）"
                )
        
        # 並行処理設定
        max_concurrent = min(5, len(queries))  # 検索は最大5並行
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def search_single_query(index: int, query: str) -> Dict[str, Any]:
            """単一クエリ検索（セマフォ付き）"""
            async with semaphore:
                try:
                    from api.schemas import SearchRequest
                    
                    search_request = SearchRequest(
                        query=query,
                        top_k=top_k,
                        user_id=user_id
                    )
                    
                    response = await memory_service.search_memories(search_request)
                    
                    return {
                        "index": index,
                        "query": query,
                        "success": response.success,
                        "results": response.results if response.success else [],
                        "total_count": response.total_count if response.success else 0,
                        "processing_time_ms": response.processing_time_ms,
                        "error": response.error if not response.success else None
                    }
                except Exception as e:
                    logger.error(
                        "batch_search_single_error",
                        index=index,
                        query=query,
                        error=str(e)
                    )
                    return {
                        "index": index,
                        "query": query,
                        "success": False,
                        "results": [],
                        "total_count": 0,
                        "processing_time_ms": 0,
                        "error": f"予期しないエラー: {str(e)}"
                    }
        
        # 並行検索実行
        tasks = [
            search_single_query(i, query) 
            for i, query in enumerate(queries)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果集計
        successful_searches = 0
        failed_searches = 0
        processed_results = []
        
        for result in results:
            if isinstance(result, Exception):
                # 例外が発生した場合
                processed_results.append({
                    "index": len(processed_results),
                    "query": queries[len(processed_results)] if len(processed_results) < len(queries) else "unknown",
                    "success": False,
                    "error": f"処理例外: {str(result)}"
                })
                failed_searches += 1
            else:
                processed_results.append(result)
                if result["success"]:
                    successful_searches += 1
                else:
                    failed_searches += 1
        
        # 処理時間計算
        total_processing_time = (time.time() - start_time) * 1000
        
        # 全体結果
        overall_success = failed_searches == 0
        
        logger.info(
            "batch_search_completed",
            total_queries=len(queries),
            successful_searches=successful_searches,
            failed_searches=failed_searches,
            total_processing_time_ms=round(total_processing_time, 2)
        )
        
        return {
            "success": overall_success,
            "total_queries": len(queries),
            "successful_searches": successful_searches,
            "failed_searches": failed_searches,
            "results": processed_results,
            "processing_time_ms": round(total_processing_time, 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(
            "batch_search_error",
            batch_size=len(queries),
            error=str(e),
            error_type=type(e).__name__,
            processing_time_ms=round(processing_time, 2)
        )
        raise HTTPException(
            status_code=500,
            detail=f"バッチ検索エラー: {str(e)}"
        )