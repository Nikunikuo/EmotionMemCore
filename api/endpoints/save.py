"""
記憶保存エンドポイント
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from api.schemas import SaveRequest, SaveResponse
from api.dependencies import memory_service_dependency
from services.memory_service import MemoryService
from infrastructure.config.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/save", response_model=SaveResponse)
async def save_memory(
    request: SaveRequest,
    memory_service: MemoryService = Depends(memory_service_dependency)
):
    """
    記憶保存エンドポイント
    
    ユーザーとAIの会話を分析し、感情付きの記憶として保存します。
    
    - **user_message**: ユーザーのメッセージ
    - **ai_message**: AIの返答
    - **user_id**: ユーザーID（オプション、同じユーザーの記憶をまとめる際に使用）
    - **session_id**: セッションID（オプション、会話セッションをまとめる際に使用）
    - **app_name**: アプリケーション名（オプション、どのアプリからの記憶かを識別）
    - **context_window**: 会話の文脈（オプション、直近の会話履歴）
    
    レスポンスには以下が含まれます：
    - **success**: 保存成功フラグ
    - **memory_id**: 保存された記憶のID
    - **summary**: LLMが生成した会話の要約
    - **emotions**: 検出された感情タグ
    - **processing_time_ms**: 処理時間
    - **error**: エラーメッセージ（失敗時のみ）
    """
    
    logger.info(
        "save_request_received",
        user_id=request.user_id,
        session_id=request.session_id,
        app_name=request.app_name,
        user_message_length=len(request.user_message),
        ai_message_length=len(request.ai_message)
    )
    
    try:
        # 入力バリデーション
        if not request.user_message.strip():
            raise HTTPException(
                status_code=400,
                detail="user_messageが空です"
            )
        
        if not request.ai_message.strip():
            raise HTTPException(
                status_code=400,
                detail="ai_messageが空です"
            )
        
        # メッセージ長チェック（過度に長いメッセージを制限）
        max_message_length = 10000  # 10,000文字制限
        if len(request.user_message) > max_message_length:
            raise HTTPException(
                status_code=400,
                detail=f"user_messageが長すぎます（最大{max_message_length}文字）"
            )
        
        if len(request.ai_message) > max_message_length:
            raise HTTPException(
                status_code=400,
                detail=f"ai_messageが長すぎます（最大{max_message_length}文字）"
            )
        
        # 記憶保存実行
        response = await memory_service.save_memory(request)
        
        # 成功・失敗に応じたログ出力
        if response.success:
            logger.info(
                "save_request_success",
                memory_id=str(response.memory_id),
                emotions_count=len(response.emotions) if response.emotions else 0,
                processing_time_ms=response.processing_time_ms
            )
        else:
            logger.warning(
                "save_request_failed",
                memory_id=str(response.memory_id),
                error=response.error
            )
            # 失敗時はHTTPエラーとして返す
            raise HTTPException(
                status_code=500,
                detail=response.error or "記憶保存に失敗しました"
            )
        
        return response
        
    except HTTPException:
        # HTTPExceptionはそのまま再発生
        raise
        
    except Exception as e:
        logger.error(
            "save_endpoint_error",
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=500,
            detail=f"サーバーエラー: {str(e)}"
        )