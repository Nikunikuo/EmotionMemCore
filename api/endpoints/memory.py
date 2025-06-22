"""
個別記憶操作エンドポイント
"""

from fastapi import APIRouter, Depends, HTTPException, Path
from typing import Dict, Any

from api.dependencies import memory_service_dependency
from services.memory_service import MemoryService
from infrastructure.config.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/memory/{memory_id}")
async def get_memory(
    memory_id: str = Path(..., description="記憶ID"),
    memory_service: MemoryService = Depends(memory_service_dependency)
):
    """
    個別記憶取得エンドポイント
    
    指定された記憶IDの詳細情報を取得します。
    
    - **memory_id**: 取得する記憶のID（UUID形式）
    
    レスポンス:
    - **id**: 記憶ID
    - **summary**: 記憶の要約
    - **emotions**: 検出された感情タグ
    - **original_user**: 元のユーザーメッセージ
    - **original_ai**: 元のAI回答
    - **user_id**: ユーザーID（設定されている場合）
    - **session_id**: セッションID（設定されている場合）
    - **app_name**: アプリケーション名（設定されている場合）
    - **created_at**: 作成日時
    """
    
    logger.info(
        "memory_get_request",
        memory_id=memory_id
    )
    
    try:
        # UUIDフォーマット検証
        from uuid import UUID
        try:
            UUID(memory_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="無効な記憶ID形式です（UUID形式で指定してください）"
            )
        
        # 記憶取得
        memory = await memory_service.get_memory_by_id(memory_id)
        
        if not memory:
            logger.info(
                "memory_not_found",
                memory_id=memory_id
            )
            raise HTTPException(
                status_code=404,
                detail="指定された記憶が見つかりません"
            )
        
        # レスポンス構築
        response = {
            "id": str(memory.id),
            "summary": memory.summary,
            "emotions": [emotion.value for emotion in memory.emotions],
            "original_user": memory.original_user,
            "original_ai": memory.original_ai,
            "user_id": memory.user_id,
            "session_id": memory.session_id,
            "app_name": memory.app_name,
            "created_at": memory.created_at.isoformat(),
            "embedding_dimension": len(memory.embedding) if memory.embedding else 0
        }
        
        logger.info(
            "memory_get_success",
            memory_id=memory_id,
            emotions_count=len(memory.emotions)
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "memory_get_error",
            memory_id=memory_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=500,
            detail=f"記憶取得エラー: {str(e)}"
        )


@router.delete("/memory/{memory_id}")
async def delete_memory(
    memory_id: str = Path(..., description="記憶ID"),
    memory_service: MemoryService = Depends(memory_service_dependency)
):
    """
    記憶削除エンドポイント
    
    指定された記憶IDの記憶を削除します。
    
    - **memory_id**: 削除する記憶のID（UUID形式）
    
    レスポンス:
    - **success**: 削除成功フラグ
    - **memory_id**: 削除された記憶のID
    - **message**: 結果メッセージ
    - **timestamp**: 削除実行時刻
    """
    
    logger.info(
        "memory_delete_request",
        memory_id=memory_id
    )
    
    try:
        # UUIDフォーマット検証
        from uuid import UUID
        try:
            UUID(memory_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="無効な記憶ID形式です（UUID形式で指定してください）"
            )
        
        # 記憶存在確認
        existing_memory = await memory_service.get_memory_by_id(memory_id)
        if not existing_memory:
            logger.info(
                "memory_delete_not_found",
                memory_id=memory_id
            )
            raise HTTPException(
                status_code=404,
                detail="指定された記憶が見つかりません"
            )
        
        # 記憶削除実行
        success = await memory_service.delete_memory(memory_id)
        
        if not success:
            logger.error(
                "memory_delete_failed",
                memory_id=memory_id
            )
            raise HTTPException(
                status_code=500,
                detail="記憶の削除に失敗しました"
            )
        
        logger.info(
            "memory_delete_success",
            memory_id=memory_id
        )
        
        from datetime import datetime
        return {
            "success": True,
            "memory_id": memory_id,
            "message": "記憶を削除しました",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "memory_delete_error",
            memory_id=memory_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=500,
            detail=f"記憶削除エラー: {str(e)}"
        )


@router.put("/memory/{memory_id}")
async def update_memory_metadata(
    memory_id: str = Path(..., description="記憶ID"),
    update_data: Dict[str, Any] = None,
    memory_service: MemoryService = Depends(memory_service_dependency)
):
    """
    記憶メタデータ更新エンドポイント
    
    指定された記憶のメタデータ（user_id, session_id, app_name等）を更新します。
    記憶の内容（summary, emotions, original_user, original_ai）は変更できません。
    
    - **memory_id**: 更新する記憶のID（UUID形式）
    - **update_data**: 更新データ
      - **user_id**: ユーザーID（オプション）
      - **session_id**: セッションID（オプション）
      - **app_name**: アプリケーション名（オプション）
    
    レスポンス:
    - **success**: 更新成功フラグ
    - **memory_id**: 更新された記憶のID
    - **updated_fields**: 更新されたフィールド一覧
    - **message**: 結果メッセージ
    """
    
    logger.info(
        "memory_update_request",
        memory_id=memory_id,
        update_fields=list(update_data.keys()) if update_data else []
    )
    
    try:
        # UUIDフォーマット検証
        from uuid import UUID
        try:
            UUID(memory_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="無効な記憶ID形式です（UUID形式で指定してください）"
            )
        
        # 更新データ検証
        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="更新データが指定されていません"
            )
        
        # 許可されたフィールドのみ更新
        allowed_fields = {"user_id", "session_id", "app_name"}
        update_fields = set(update_data.keys())
        
        invalid_fields = update_fields - allowed_fields
        if invalid_fields:
            raise HTTPException(
                status_code=400,
                detail=f"更新できないフィールドが含まれています: {', '.join(invalid_fields)}"
            )
        
        # 記憶存在確認
        existing_memory = await memory_service.get_memory_by_id(memory_id)
        if not existing_memory:
            logger.info(
                "memory_update_not_found",
                memory_id=memory_id
            )
            raise HTTPException(
                status_code=404,
                detail="指定された記憶が見つかりません"
            )
        
        # TODO: メタデータ更新機能をサービス層に実装
        # 現在のアーキテクチャでは直接更新は困難なため、
        # 将来的な拡張として実装する
        
        logger.warning(
            "memory_update_not_implemented",
            memory_id=memory_id,
            message="メタデータ更新機能は現在未実装です"
        )
        
        raise HTTPException(
            status_code=501,
            detail="メタデータ更新機能は現在実装中です。将来のバージョンで対応予定です。"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "memory_update_error",
            memory_id=memory_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=500,
            detail=f"記憶更新エラー: {str(e)}"
        )