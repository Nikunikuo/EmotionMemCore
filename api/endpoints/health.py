"""
ヘルスチェックエンドポイント
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from api.dependencies import memory_service_dependency
from services.memory_service import MemoryService

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def health_check(
    memory_service: MemoryService = Depends(memory_service_dependency)
):
    """
    システムヘルスチェック
    
    各コンポーネントの動作状況を確認
    """
    return await memory_service.health_check()


@router.get("/stats", response_model=Dict[str, Any])
async def get_stats(
    memory_service: MemoryService = Depends(memory_service_dependency)
):
    """
    システム統計情報取得
    
    記憶データの統計情報を取得
    """
    return await memory_service.get_stats()