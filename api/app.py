"""
FastAPIアプリケーション メインファイル
"""

import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from api.endpoints import save, search, health, debug, memory, batch
from api.dependencies import get_memory_service
from api.middleware import (
    error_handler, logging_middleware, performance_middleware,
    auth_middleware, rate_limit_middleware
)
from api.middleware.cors import get_cors_settings, add_security_headers, validate_request_headers
from infrastructure.config.logger import get_logger
from docs.openapi_config import get_custom_openapi

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    
    # 起動時処理
    logger.info(
        "emotionmemcore_starting",
        version="0.1.0",
        environment=os.getenv("ENVIRONMENT", "development")
    )
    
    # 依存関係の初期化チェック
    try:
        memory_service = await get_memory_service()
        health_status = await memory_service.health_check()
        
        if not health_status["healthy"]:
            logger.error("startup_health_check_failed", status=health_status)
            raise RuntimeError("システム初期化に失敗しました")
        
        logger.info("startup_health_check_passed", status=health_status)
        
    except Exception as e:
        logger.error("startup_failed", error=str(e))
        raise
    
    yield
    
    # 終了時処理
    logger.info("emotionmemcore_shutting_down")


def create_app() -> FastAPI:
    """FastAPIアプリケーション作成"""
    
    # FastAPIアプリケーション初期化
    app = FastAPI(
        title="🤖 EmotionMemCore API",
        description="感情付き記憶RAGシステム - AIとの対話を記憶し、感情的な文脈で検索可能なAPIモジュール",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # CORS設定
    cors_settings = get_cors_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_settings["allow_origins"],
        allow_credentials=cors_settings["allow_credentials"],
        allow_methods=cors_settings["allow_methods"],
        allow_headers=cors_settings["allow_headers"],
        expose_headers=cors_settings.get("expose_headers", [])
    )
    
    # セキュリティミドルウェア追加（順序重要）
    app.middleware("http")(add_security_headers)
    app.middleware("http")(validate_request_headers)
    
    # アプリケーションミドルウェア追加
    app.middleware("http")(performance_middleware)
    app.middleware("http")(logging_middleware)
    app.middleware("http")(rate_limit_middleware)
    app.middleware("http")(auth_middleware)
    app.middleware("http")(error_handler)
    
    # ルーター登録
    app.include_router(health.router, prefix="/health", tags=["Health"])
    app.include_router(save.router, prefix="", tags=["Memory"])
    app.include_router(search.router, prefix="", tags=["Memory"])
    app.include_router(memory.router, prefix="", tags=["Memory"])
    app.include_router(batch.router, prefix="", tags=["Batch"])
    
    # デバッグモード時のみデバッグエンドポイント追加
    if os.getenv("DEBUG_MODE", "false").lower() == "true":
        app.include_router(debug.router, prefix="/debug", tags=["Debug"])
        logger.info("debug_endpoints_enabled")
    
    # ルートエンドポイント
    @app.get("/")
    async def root():
        """ルートエンドポイント"""
        return {
            "service": "EmotionMemCore API",
            "version": "0.1.0",
            "description": "感情付き記憶RAGシステム",
            "endpoints": {
                "docs": "/docs",
                "health": "/health",
                "save": "/save",
                "search": "/search",
                "memories": "/memories",
                "memory": "/memory/{id}",
                "batch_save": "/batch-save",
                "batch_search": "/batch-search"
            },
            "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true"
        }
    
    # カスタムOpenAPI設定を適用
    app.openapi = lambda: get_custom_openapi(app)
    
    logger.info("fastapi_app_created")
    return app


# アプリケーションインスタンス
app = create_app()


if __name__ == "__main__":
    # 開発サーバー起動
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT", "development") == "development",
        log_level="info"
    )