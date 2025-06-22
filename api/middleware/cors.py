"""
CORS設定とセキュリティミドルウェア
"""

import os
from typing import List
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware

from infrastructure.config.logger import get_logger

logger = get_logger(__name__)


def get_cors_settings() -> dict:
    """CORS設定を取得"""
    
    # 環境に応じた設定
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production":
        # 本番環境: 厳しい設定
        allowed_origins = []
        
        # 環境変数から許可オリジンを取得
        origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
        if origins_env:
            allowed_origins = [origin.strip() for origin in origins_env.split(",") if origin.strip()]
        
        # デフォルトで本番ドメインを許可
        default_origins = os.getenv("PRODUCTION_DOMAINS", "").split(",")
        allowed_origins.extend([origin.strip() for origin in default_origins if origin.strip()])
        
        cors_settings = {
            "allow_origins": allowed_origins or ["https://yourdomain.com"],  # 実際のドメインに変更
            "allow_credentials": True,
            "allow_methods": ["GET", "POST"],  # 必要なメソッドのみ
            "allow_headers": [
                "Authorization",
                "Content-Type", 
                "X-API-Key",
                "X-Request-ID"
            ],
            "expose_headers": [
                "X-Request-ID",
                "X-Processing-Time",
                "X-Auth-Method",
                "X-RateLimit-Limit-RPM",
                "X-RateLimit-Remaining-Minute"
            ]
        }
        
        logger.info(
            "cors_production_config",
            allowed_origins=allowed_origins,
            methods=cors_settings["allow_methods"]
        )
    
    elif environment == "staging":
        # ステージング環境: 中程度の設定
        cors_settings = {
            "allow_origins": [
                "https://staging.yourdomain.com",
                "https://test.yourdomain.com"
            ],
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["*"],
            "expose_headers": [
                "X-Request-ID",
                "X-Processing-Time", 
                "X-Auth-Method",
                "X-RateLimit-*"
            ]
        }
        
        logger.info("cors_staging_config")
    
    else:
        # 開発・テスト環境: 緩い設定
        cors_settings = {
            "allow_origins": ["*"],  # 開発時は全て許可
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
            "expose_headers": ["*"]
        }
        
        logger.info("cors_development_config", note="All origins allowed for development")
    
    return cors_settings


def create_cors_middleware():
    """CORSミドルウェア作成"""
    settings = get_cors_settings()
    
    return CORSMiddleware(
        allow_origins=settings["allow_origins"],
        allow_credentials=settings["allow_credentials"],
        allow_methods=settings["allow_methods"],
        allow_headers=settings["allow_headers"],
        expose_headers=settings.get("expose_headers", [])
    )


def add_security_headers(request: Request, call_next):
    """セキュリティヘッダー追加ミドルウェア"""
    
    async def middleware(request: Request, call_next):
        response = await call_next(request)
        
        # セキュリティヘッダー追加
        security_headers = {
            # XSS保護
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            
            # HTTPS強制（本番環境）
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            
            # レファラーポリシー
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # コンテンツセキュリティポリシー（基本）
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
            
            # 権限ポリシー
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
        
        # 開発環境では一部のヘッダーをスキップ
        environment = os.getenv("ENVIRONMENT", "development")
        if environment == "development":
            # HTTPS強制を削除（開発環境ではHTTPを使用）
            security_headers.pop("Strict-Transport-Security", None)
            # CSPを緩和
            security_headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval'; connect-src 'self' *;"
        
        # ヘッダー追加
        for header, value in security_headers.items():
            response.headers[header] = value
        
        # API識別ヘッダー
        response.headers["X-API-Name"] = "EmotionMemCore"
        response.headers["X-API-Version"] = "0.1.0"
        
        return response
    
    return middleware(request, call_next)


def validate_request_headers(request: Request, call_next):
    """リクエストヘッダー検証ミドルウェア"""
    
    async def middleware(request: Request, call_next):
        # 危険なヘッダーのチェック
        dangerous_headers = [
            "x-forwarded-host",
            "x-original-url", 
            "x-rewrite-url"
        ]
        
        for header in dangerous_headers:
            if header in request.headers:
                logger.warning(
                    "dangerous_header_detected",
                    header=header,
                    value=request.headers[header],
                    client_ip=request.client.host if request.client else "unknown"
                )
        
        # User-Agentチェック（ボットやスクレイパー検出）
        user_agent = request.headers.get("user-agent", "").lower()
        suspicious_agents = ["curl", "wget", "python-requests", "bot", "crawler", "spider"]
        
        if any(agent in user_agent for agent in suspicious_agents):
            logger.info(
                "suspicious_user_agent",
                user_agent=user_agent,
                client_ip=request.client.host if request.client else "unknown",
                path=request.url.path
            )
        
        # Content-Lengthチェック（大きすぎるリクエスト）
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                max_size = int(os.getenv("MAX_REQUEST_SIZE", "10485760"))  # 10MB
                if length > max_size:
                    from fastapi import HTTPException, status
                    logger.warning(
                        "request_too_large",
                        content_length=length,
                        max_size=max_size,
                        client_ip=request.client.host if request.client else "unknown"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"リクエストサイズが大きすぎます（最大: {max_size} bytes）"
                    )
            except ValueError:
                pass
        
        return await call_next(request)
    
    return middleware(request, call_next)