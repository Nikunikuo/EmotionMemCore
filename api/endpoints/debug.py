"""
デバッグエンドポイント（DEBUG_MODE=trueの時のみ有効）
"""

import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional

from api.dependencies import memory_service_dependency, collection_manager_dependency
from services.memory_service import MemoryService
from infrastructure.db.collection_manager import CollectionManager
from infrastructure.config.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# デバッグモードチェック用デコレータ
def debug_mode_required():
    """デバッグモードが有効かチェック"""
    if os.getenv("DEBUG_MODE", "false").lower() != "true":
        raise HTTPException(
            status_code=404,
            detail="Debug endpoints are not available"
        )


@router.get("/system-info")
async def get_system_info(
    memory_service: MemoryService = Depends(memory_service_dependency),
    collection_manager: CollectionManager = Depends(collection_manager_dependency)
):
    """システム情報を取得"""
    debug_mode_required()
    
    try:
        # システム統計
        stats = await memory_service.get_stats()
        
        # ストレージ情報
        storage_info = collection_manager.get_storage_info()
        
        # コレクション情報
        collections = collection_manager.list_collections()
        
        # 環境変数情報（センシティブな情報は除外）
        env_info = {
            "DEBUG_MODE": os.getenv("DEBUG_MODE", "false"),
            "ENVIRONMENT": os.getenv("ENVIRONMENT", "development"),
            "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "claude"),
            "LLM_MOCK_MODE": os.getenv("LLM_MOCK_MODE", "false"),
            "OPENAI_EMBEDDING_MODEL": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            "MEMORY_COLLECTION_NAME": os.getenv("MEMORY_COLLECTION_NAME", "emotion_memories"),
            "CHROMA_PERSIST_DIRECTORY": os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db"),
            "PORT": os.getenv("PORT", "8000")
        }
        
        return {
            "system_stats": stats,
            "storage_info": storage_info,
            "collections": collections,
            "environment": env_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("debug_system_info_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/last-memories")
async def get_last_memories(
    count: int = Query(10, ge=1, le=100, description="取得件数"),
    memory_service: MemoryService = Depends(memory_service_dependency)
):
    """最新の記憶を取得（デバッグ用）"""
    debug_mode_required()
    
    try:
        # 最新の記憶を取得
        memories = await memory_service.get_memories_by_filter(
            limit=count,
            offset=0
        )
        
        result = []
        for memory in memories:
            result.append({
                "id": str(memory.id),
                "summary": memory.summary,
                "emotions": [e.value for e in memory.emotions],
                "created_at": memory.created_at.isoformat(),
                "user_id": memory.user_id,
                "session_id": memory.session_id,
                "app_name": memory.app_name,
                "original_user": memory.original_user[:100] + "..." if len(memory.original_user) > 100 else memory.original_user,
                "original_ai": memory.original_ai[:100] + "..." if len(memory.original_ai) > 100 else memory.original_ai
            })
        
        logger.info("debug_last_memories_retrieved", count=len(result))
        
        return {
            "memories": result,
            "total_retrieved": len(result),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("debug_last_memories_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/{memory_id}")
async def get_memory_detail(
    memory_id: str,
    memory_service: MemoryService = Depends(memory_service_dependency)
):
    """特定の記憶の詳細を取得"""
    debug_mode_required()
    
    try:
        memory = await memory_service.get_memory_by_id(memory_id)
        
        if not memory:
            raise HTTPException(status_code=404, detail="記憶が見つかりません")
        
        result = {
            "id": str(memory.id),
            "summary": memory.summary,
            "emotions": [e.value for e in memory.emotions],
            "created_at": memory.created_at.isoformat(),
            "user_id": memory.user_id,
            "session_id": memory.session_id,
            "app_name": memory.app_name,
            "original_user": memory.original_user,
            "original_ai": memory.original_ai,
            "embedding_dimension": len(memory.embedding) if memory.embedding else 0
        }
        
        logger.info("debug_memory_detail_retrieved", memory_id=memory_id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("debug_memory_detail_failed", memory_id=memory_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memory/{memory_id}")
async def delete_memory(
    memory_id: str,
    memory_service: MemoryService = Depends(memory_service_dependency)
):
    """記憶を削除（デバッグ用）"""
    debug_mode_required()
    
    try:
        success = await memory_service.delete_memory(memory_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="記憶の削除に失敗しました")
        
        logger.info("debug_memory_deleted", memory_id=memory_id)
        
        return {
            "success": True,
            "memory_id": memory_id,
            "message": "記憶を削除しました",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("debug_memory_deletion_failed", memory_id=memory_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections")
async def get_collections(
    collection_manager: CollectionManager = Depends(collection_manager_dependency)
):
    """コレクション一覧を取得"""
    debug_mode_required()
    
    try:
        collections = collection_manager.list_collections()
        storage_info = collection_manager.get_storage_info()
        
        return {
            "collections": collections,
            "storage_info": storage_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("debug_collections_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backups")
async def get_backups(
    collection_manager: CollectionManager = Depends(collection_manager_dependency)
):
    """バックアップ一覧を取得"""
    debug_mode_required()
    
    try:
        backups = collection_manager.list_backups()
        
        return {
            "backups": backups,
            "backup_count": len(backups),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("debug_backups_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup/{collection_name}")
async def create_backup(
    collection_name: str,
    collection_manager: CollectionManager = Depends(collection_manager_dependency)
):
    """コレクションのバックアップを作成"""
    debug_mode_required()
    
    try:
        success = collection_manager.backup_collection(collection_name)
        
        if not success:
            raise HTTPException(status_code=500, detail="バックアップの作成に失敗しました")
        
        logger.info("debug_backup_created", collection_name=collection_name)
        
        return {
            "success": True,
            "collection_name": collection_name,
            "message": "バックアップを作成しました",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("debug_backup_creation_failed", collection_name=collection_name, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-memory")
async def create_test_memory(
    count: int = Query(1, ge=1, le=10, description="作成するテスト記憶数"),
    memory_service: MemoryService = Depends(memory_service_dependency)
):
    """テスト用記憶を作成"""
    debug_mode_required()
    
    try:
        from api.schemas import SaveRequest
        
        test_memories = []
        test_scenarios = [
            {
                "user": "今日はいい天気ですね！",
                "ai": "そうですね！お散歩日和で気持ちがいいですね。どこか出かける予定はありますか？",
                "context": "weather"
            },
            {
                "user": "最近仕事が忙しくて疲れています...",
                "ai": "お疲れ様です。無理をしないでくださいね。少しでも休息を取ることが大切です。",
                "context": "work_stress"
            },
            {
                "user": "新しいゲームを買いました！",
                "ai": "わあ、素敵ですね！どんなゲームですか？楽しそうで私もワクワクします♪",
                "context": "entertainment"
            },
            {
                "user": "今度の休みに旅行に行こうと思うんです",
                "ai": "いいですね！旅行はリフレッシュできて素晴らしいですね。どちらに行かれる予定ですか？",
                "context": "travel"
            },
            {
                "user": "ちょっと体調が悪くて...",
                "ai": "大丈夫ですか？無理をしないで、ゆっくり休んでくださいね。お大事にしてください。",
                "context": "health"
            }
        ]
        
        for i in range(count):
            scenario = test_scenarios[i % len(test_scenarios)]
            
            request = SaveRequest(
                user_message=scenario["user"],
                ai_message=scenario["ai"],
                user_id=f"test_user_{i+1}",
                session_id=f"debug_session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                app_name="debug_test"
            )
            
            response = await memory_service.save_memory(request)
            
            if response.success:
                test_memories.append({
                    "memory_id": str(response.memory_id),
                    "summary": response.summary,
                    "emotions": [e.value for e in response.emotions] if response.emotions else [],
                    "context": scenario["context"]
                })
        
        logger.info("debug_test_memories_created", count=len(test_memories))
        
        return {
            "success": True,
            "created_memories": test_memories,
            "count": len(test_memories),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("debug_test_memory_creation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))