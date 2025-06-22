"""
FastAPIミドルウェア実装（基本ミドルウェア）
"""

import time
import traceback
import uuid
from typing import Callable, Dict, Any

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from infrastructure.config.logger import get_logger

logger = get_logger(__name__)


async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """リクエストログミドルウェア"""
    
    # リクエストID生成
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # リクエスト情報
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    logger.info(
        "request_started",
        request_id=request_id,
        method=request.method,
        url=str(request.url),
        client_ip=client_ip,
        user_agent=user_agent
    )
    
    # リクエスト処理
    response = await call_next(request)
    
    # レスポンス情報
    processing_time = (time.time() - start_time) * 1000
    
    logger.info(
        "request_completed",
        request_id=request_id,
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        processing_time_ms=round(processing_time, 2)
    )
    
    # レスポンスヘッダーにリクエストID追加
    response.headers["X-Request-ID"] = request_id
    
    return response


async def performance_middleware(request: Request, call_next: Callable) -> Response:
    """パフォーマンス計測ミドルウェア"""
    
    start_time = time.time()
    
    # メモリ使用量取得（オプション）
    try:
        import psutil
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
    except ImportError:
        memory_before = None
    
    # リクエスト処理
    response = await call_next(request)
    
    # パフォーマンス情報
    processing_time = (time.time() - start_time) * 1000
    
    performance_data = {
        "processing_time_ms": round(processing_time, 2),
        "endpoint": str(request.url.path),
        "method": request.method
    }
    
    # メモリ使用量
    if memory_before is not None:
        try:
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            performance_data.update({
                "memory_before_mb": round(memory_before, 2),
                "memory_after_mb": round(memory_after, 2),
                "memory_delta_mb": round(memory_after - memory_before, 2)
            })
        except:
            pass
    
    # 遅いリクエストの警告
    if processing_time > 5000:  # 5秒以上
        logger.warning("slow_request_detected", **performance_data)
    else:
        logger.debug("request_performance", **performance_data)
    
    # パフォーマンスヘッダー追加
    response.headers["X-Processing-Time"] = str(round(processing_time, 2))
    
    return response


async def error_handler(request: Request, call_next: Callable) -> Response:
    """エラーハンドリングミドルウェア"""
    
    try:
        response = await call_next(request)
        return response
        
    except HTTPException as e:
        # HTTPExceptionはFastAPIに処理を委譲
        raise e
        
    except Exception as e:
        # 予期しないエラーをキャッチ
        request_id = getattr(request.state, "request_id", "unknown")
        error_trace = traceback.format_exc()
        
        logger.error(
            "unhandled_exception",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            error=str(e),
            error_type=type(e).__name__,
            traceback=error_trace
        )
        
        # エラーレスポンス
        error_response = {
            "error": "internal_server_error",
            "message": "サーバー内部エラーが発生しました",
            "request_id": request_id,
            "timestamp": time.time()
        }
        
        # デバッグモードでは詳細情報を含める
        import os
        if os.getenv("DEBUG_MODE", "false").lower() == "true":
            error_response.update({
                "debug_info": {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "traceback": error_trace.split("\\n")
                }
            })
        
        return JSONResponse(
            status_code=500,
            content=error_response,
            headers={"X-Request-ID": request_id}
        )


class RequestTraceMiddleware(BaseHTTPMiddleware):
    """リクエストトレースミドルウェア（デバッグ用）"""
    
    def __init__(self, app, enabled: bool = False):
        super().__init__(app)
        self.enabled = enabled
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.enabled:
            return await call_next(request)
        
        request_id = getattr(request.state, "request_id", "unknown")
        
        # リクエストボディの記録（小さいサイズのみ）
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if len(body) < 10000:  # 10KB未満のみ
                    # ボディを再利用可能にする
                    request._body = body
                else:
                    body = f"<large_body:{len(body)}_bytes>"
            except Exception:
                body = "<body_read_error>"
        
        logger.debug(
            "request_trace",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers),
            query_params=dict(request.query_params),
            path_params=request.path_params,
            body=body.decode('utf-8') if isinstance(body, bytes) else body
        )
        
        response = await call_next(request)
        
        logger.debug(
            "response_trace",
            request_id=request_id,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
        return response