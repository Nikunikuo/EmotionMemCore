"""
記憶検索エンドポイント
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional

from api.schemas import SearchRequest, SearchResponse
from api.dependencies import memory_service_dependency
from services.memory_service import MemoryService
from infrastructure.config.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/search", response_model=SearchResponse)
async def search_memories(
    request: SearchRequest,
    memory_service: MemoryService = Depends(memory_service_dependency)
):
    """
    記憶検索エンドポイント
    
    自然言語クエリで過去の記憶を検索します。
    
    - **query**: 検索クエリ（自然言語）
    - **top_k**: 取得する結果数（デフォルト: 5）
    - **user_id**: 特定ユーザーの記憶に限定（オプション）
    - **emotion_filter**: 感情フィルター（オプション）
    - **date_from**: 開始日時（ISO 8601形式、オプション）
    - **date_to**: 終了日時（ISO 8601形式、オプション）
    
    レスポンスには以下が含まれます：
    - **success**: 検索成功フラグ
    - **results**: 検索結果リスト（スコア順）
    - **total_count**: 検索結果総数
    - **processing_time_ms**: 処理時間
    - **error**: エラーメッセージ（失敗時のみ）
    
    検索結果の各項目：
    - **id**: 記憶ID
    - **score**: 類似度スコア（0-1）
    - **summary**: 記憶の要約
    - **emotions**: 検出された感情
    - **metadata**: メタデータ（作成日時、ユーザーID等）
    """
    
    logger.info(
        "search_request_received",
        query=request.query,
        top_k=request.top_k,
        user_id=request.user_id,
        has_emotion_filter=bool(request.emotion_filter),
        has_date_filter=bool(request.date_from or request.date_to)
    )
    
    try:
        # 入力バリデーション
        if not request.query.strip():
            raise HTTPException(
                status_code=400,
                detail="検索クエリが空です"
            )
        
        if request.top_k <= 0 or request.top_k > 100:
            raise HTTPException(
                status_code=400,
                detail="top_kは1から100の間で指定してください"
            )
        
        # クエリ長チェック
        max_query_length = 1000
        if len(request.query) > max_query_length:
            raise HTTPException(
                status_code=400,
                detail=f"クエリが長すぎます（最大{max_query_length}文字）"
            )
        
        # 日付フォーマットチェック
        if request.date_from:
            try:
                from datetime import datetime
                datetime.fromisoformat(request.date_from)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="date_fromのフォーマットが正しくありません（ISO 8601形式で入力してください）"
                )
        
        if request.date_to:
            try:
                from datetime import datetime
                datetime.fromisoformat(request.date_to)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="date_toのフォーマットが正しくありません（ISO 8601形式で入力してください）"
                )
        
        # 記憶検索実行
        response = await memory_service.search_memories(request)
        
        # 成功・失敗に応じたログ出力
        if response.success:
            logger.info(
                "search_request_success",
                query=request.query,
                results_count=response.total_count,
                processing_time_ms=response.processing_time_ms
            )
        else:
            logger.warning(
                "search_request_failed",
                query=request.query,
                error=response.error
            )
            # 失敗時はHTTPエラーとして返す
            raise HTTPException(
                status_code=500,
                detail=response.error or "記憶検索に失敗しました"
            )
        
        return response
        
    except HTTPException:
        # HTTPExceptionはそのまま再発生
        raise
        
    except Exception as e:
        logger.error(
            "search_endpoint_error",
            query=request.query,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=500,
            detail=f"サーバーエラー: {str(e)}"
        )


@router.get("/memories", response_model=List[Dict[str, Any]])
async def get_memories(
    user_id: Optional[str] = Query(None, description="ユーザーID"),
    emotions: Optional[List[str]] = Query(None, description="感情フィルター"),
    date_from: Optional[str] = Query(None, description="開始日時（ISO 8601）"),
    date_to: Optional[str] = Query(None, description="終了日時（ISO 8601）"),
    limit: int = Query(50, ge=1, le=500, description="取得件数"),
    offset: int = Query(0, ge=0, description="オフセット"),
    memory_service: MemoryService = Depends(memory_service_dependency)
):
    """
    記憶一覧取得エンドポイント
    
    フィルター条件に基づいて記憶を取得します（ページネーション対応）
    
    クエリパラメータ：
    - **user_id**: 特定ユーザーの記憶に限定
    - **emotions**: 感情フィルター（複数指定可）
    - **date_from**: 開始日時（ISO 8601形式）
    - **date_to**: 終了日時（ISO 8601形式）
    - **limit**: 取得件数（1-500、デフォルト: 50）
    - **offset**: オフセット（デフォルト: 0）
    """
    
    logger.info(
        "memories_list_request",
        user_id=user_id,
        emotions=emotions,
        date_range=f"{date_from} - {date_to}" if date_from or date_to else None,
        limit=limit,
        offset=offset
    )
    
    try:
        # 記憶取得実行
        memories = await memory_service.get_memories_by_filter(
            user_id=user_id,
            emotions=emotions,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset
        )
        
        # Memory オブジェクトを辞書に変換
        result = []
        for memory in memories:
            result.append({
                "id": str(memory.id),
                "summary": memory.summary,
                "emotions": [e.value for e in memory.emotions],
                "user_id": memory.user_id,
                "session_id": memory.session_id,
                "app_name": memory.app_name,
                "created_at": memory.created_at.isoformat(),
                "original_user": memory.original_user,
                "original_ai": memory.original_ai
            })
        
        logger.info(
            "memories_list_success",
            retrieved_count=len(result),
            limit=limit,
            offset=offset
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "memories_list_error",
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=500,
            detail=f"記憶取得エラー: {str(e)}"
        )