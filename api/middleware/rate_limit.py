"""
レート制限ミドルウェア
APIの呼び出し頻度制限
"""

import os
import time
import asyncio
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from fastapi import Request, HTTPException, status

from infrastructure.config.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """レート制限クラス"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # 設定読み込み
        self.enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        self.default_rpm = int(os.getenv("RATE_LIMIT_RPM", "60"))  # requests per minute
        self.default_rph = int(os.getenv("RATE_LIMIT_RPH", "1000"))  # requests per hour
        self.burst_limit = int(os.getenv("RATE_LIMIT_BURST", "10"))  # burst requests
        
        # エンドポイント別制限設定
        self.endpoint_limits = self._load_endpoint_limits()
        
        # メモリベースのトラッキング（シンプル実装）
        self.request_counts: Dict[str, deque] = defaultdict(deque)
        self.burst_counts: Dict[str, int] = defaultdict(int)
        self.last_cleanup = time.time()
        
        # クリーンアップ間隔（秒）
        self.cleanup_interval = 300  # 5分
        
        self.logger.info(
            "rate_limiter_initialized",
            enabled=self.enabled,
            default_rpm=self.default_rpm,
            default_rph=self.default_rph,
            burst_limit=self.burst_limit
        )
    
    def _load_endpoint_limits(self) -> Dict[str, Dict[str, int]]:
        """エンドポイント別制限設定読み込み"""
        limits = {}
        
        # 保存エンドポイント（重い処理）
        limits["/save"] = {
            "rpm": int(os.getenv("SAVE_RATE_LIMIT_RPM", "30")),
            "rph": int(os.getenv("SAVE_RATE_LIMIT_RPH", "500")),
            "burst": int(os.getenv("SAVE_RATE_LIMIT_BURST", "5"))
        }
        
        # 検索エンドポイント
        limits["/search"] = {
            "rpm": int(os.getenv("SEARCH_RATE_LIMIT_RPM", "60")),
            "rph": int(os.getenv("SEARCH_RATE_LIMIT_RPH", "1000")),
            "burst": int(os.getenv("SEARCH_RATE_LIMIT_BURST", "10"))
        }
        
        # 記憶一覧エンドポイント
        limits["/memories"] = {
            "rpm": int(os.getenv("MEMORIES_RATE_LIMIT_RPM", "30")),
            "rph": int(os.getenv("MEMORIES_RATE_LIMIT_RPH", "300")),
            "burst": int(os.getenv("MEMORIES_RATE_LIMIT_BURST", "5"))
        }
        
        # デバッグエンドポイント（より厳しい制限）
        debug_endpoints = ["/debug/test-memory", "/debug/backup"]
        for endpoint in debug_endpoints:
            limits[endpoint] = {
                "rpm": int(os.getenv("DEBUG_RATE_LIMIT_RPM", "10")),
                "rph": int(os.getenv("DEBUG_RATE_LIMIT_RPH", "50")),
                "burst": int(os.getenv("DEBUG_RATE_LIMIT_BURST", "2"))
            }
        
        return limits
    
    def _get_rate_limit_key(self, request: Request) -> str:
        """レート制限キー生成"""
        # 認証情報からキー取得を試行
        auth_result = getattr(request.state, "auth_result", None)
        if auth_result and "rate_limit_key" in auth_result:
            return auth_result["rate_limit_key"]
        
        # フォールバック: IPアドレス
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def _get_endpoint_limits(self, endpoint: str) -> Dict[str, int]:
        """エンドポイント制限取得"""
        # 完全一致
        if endpoint in self.endpoint_limits:
            return self.endpoint_limits[endpoint]
        
        # パターンマッチング（例: /memory/{id}）
        for pattern, limits in self.endpoint_limits.items():
            if pattern.endswith("*") and endpoint.startswith(pattern[:-1]):
                return limits
        
        # デフォルト制限
        return {
            "rpm": self.default_rpm,
            "rph": self.default_rph,
            "burst": self.burst_limit
        }
    
    def _cleanup_old_requests(self):
        """古いリクエスト記録をクリーンアップ"""
        now = time.time()
        
        # 定期的なクリーンアップ
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff_time = now - 3600  # 1時間前
        cleaned_keys = 0
        
        for key in list(self.request_counts.keys()):
            request_times = self.request_counts[key]
            
            # 古いタイムスタンプを削除
            while request_times and request_times[0] < cutoff_time:
                request_times.popleft()
            
            # 空になったキーを削除
            if not request_times:
                del self.request_counts[key]
                if key in self.burst_counts:
                    del self.burst_counts[key]
                cleaned_keys += 1
        
        self.last_cleanup = now
        
        if cleaned_keys > 0:
            self.logger.debug(
                "rate_limit_cleanup",
                cleaned_keys=cleaned_keys,
                active_keys=len(self.request_counts)
            )
    
    def _check_rate_limit(
        self, 
        rate_limit_key: str, 
        endpoint: str
    ) -> Tuple[bool, Dict[str, any]]:
        """レート制限チェック"""
        
        now = time.time()
        limits = self._get_endpoint_limits(endpoint)
        
        # バースト制限チェック
        current_burst = self.burst_counts.get(rate_limit_key, 0)
        if current_burst >= limits["burst"]:
            # 最後のリクエストから1秒経過していればリセット
            request_times = self.request_counts.get(rate_limit_key, deque())
            if request_times and (now - request_times[-1]) >= 1.0:
                self.burst_counts[rate_limit_key] = 0
            else:
                return False, {
                    "error": "burst_limit_exceeded",
                    "limit": limits["burst"],
                    "reset_in": 1.0 - (now - request_times[-1]) if request_times else 1.0
                }
        
        # 分あたり制限チェック
        minute_cutoff = now - 60
        request_times = self.request_counts[rate_limit_key]
        
        # 1分以内のリクエストカウント
        minute_requests = sum(1 for t in request_times if t > minute_cutoff)
        if minute_requests >= limits["rpm"]:
            oldest_in_minute = next((t for t in request_times if t > minute_cutoff), now)
            return False, {
                "error": "minute_limit_exceeded",
                "limit": limits["rpm"],
                "reset_in": 60 - (now - oldest_in_minute)
            }
        
        # 時間あたり制限チェック
        hour_cutoff = now - 3600
        hour_requests = sum(1 for t in request_times if t > hour_cutoff)
        if hour_requests >= limits["rph"]:
            oldest_in_hour = next((t for t in request_times if t > hour_cutoff), now)
            return False, {
                "error": "hour_limit_exceeded",
                "limit": limits["rph"],
                "reset_in": 3600 - (now - oldest_in_hour)
            }
        
        return True, {
            "minute_requests": minute_requests,
            "hour_requests": hour_requests,
            "burst_requests": current_burst,
            "limits": limits
        }
    
    def _record_request(self, rate_limit_key: str):
        """リクエスト記録"""
        now = time.time()
        
        # リクエスト時刻を記録
        self.request_counts[rate_limit_key].append(now)
        
        # バーストカウンター更新
        self.burst_counts[rate_limit_key] = self.burst_counts.get(rate_limit_key, 0) + 1
        
        # 定期クリーンアップ
        self._cleanup_old_requests()
    
    async def check_rate_limit(self, request: Request) -> Dict[str, any]:
        """レート制限チェック（非同期対応）"""
        
        if not self.enabled:
            return {"allowed": True, "reason": "disabled"}
        
        # 公開エンドポイントは制限しない
        public_endpoints = ["/", "/health", "/docs", "/redoc", "/openapi.json"]
        if request.url.path in public_endpoints:
            return {"allowed": True, "reason": "public_endpoint"}
        
        rate_limit_key = self._get_rate_limit_key(request)
        endpoint = request.url.path
        
        # レート制限チェック
        allowed, details = self._check_rate_limit(rate_limit_key, endpoint)
        
        if allowed:
            # リクエスト記録
            self._record_request(rate_limit_key)
            
            return {
                "allowed": True,
                "rate_limit_key": rate_limit_key,
                **details
            }
        else:
            # 制限に引っかかった
            self.logger.warning(
                "rate_limit_exceeded",
                rate_limit_key=rate_limit_key,
                endpoint=endpoint,
                error=details["error"],
                limit=details["limit"]
            )
            
            return {
                "allowed": False,
                "rate_limit_key": rate_limit_key,
                **details
            }


# シングルトンインスタンス
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """レート制限インスタンス取得"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


async def rate_limit_middleware(request: Request, call_next):
    """レート制限ミドルウェア"""
    
    start_time = time.time()
    limiter = get_rate_limiter()
    
    try:
        # レート制限チェック
        limit_result = await limiter.check_rate_limit(request)
        
        if not limit_result["allowed"]:
            # レート制限に引っかかった場合
            error_detail = limit_result.get("error", "rate_limit_exceeded")
            reset_in = limit_result.get("reset_in", 60)
            
            # HTTPエラーレスポンス
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"レート制限に達しました。{reset_in:.1f}秒後に再試行してください。",
                headers={
                    "Retry-After": str(int(reset_in)),
                    "X-RateLimit-Error": error_detail,
                    "X-RateLimit-Limit": str(limit_result.get("limit", "unknown"))
                }
            )
        
        # リクエスト処理続行
        response = await call_next(request)
        
        # レート制限情報をヘッダーに追加
        if "limits" in limit_result:
            limits = limit_result["limits"]
            response.headers["X-RateLimit-Limit-RPM"] = str(limits["rpm"])
            response.headers["X-RateLimit-Limit-RPH"] = str(limits["rph"])
            response.headers["X-RateLimit-Remaining-Minute"] = str(
                max(0, limits["rpm"] - limit_result.get("minute_requests", 0))
            )
            response.headers["X-RateLimit-Remaining-Hour"] = str(
                max(0, limits["rph"] - limit_result.get("hour_requests", 0))
            )
        
        rate_limit_time = (time.time() - start_time) * 1000
        logger.debug(
            "rate_limit_middleware_completed",
            rate_limit_time_ms=round(rate_limit_time, 2),
            allowed=True
        )
        
        return response
        
    except HTTPException as e:
        # レート制限エラー
        rate_limit_time = (time.time() - start_time) * 1000
        logger.info(
            "rate_limit_middleware_rejected",
            status_code=e.status_code,
            detail=e.detail,
            rate_limit_time_ms=round(rate_limit_time, 2)
        )
        raise e
    
    except Exception as e:
        # 予期しないエラー
        rate_limit_time = (time.time() - start_time) * 1000
        logger.error(
            "rate_limit_middleware_error",
            error=str(e),
            error_type=type(e).__name__,
            rate_limit_time_ms=round(rate_limit_time, 2)
        )
        # レート制限エラーの場合は通す（フェイルオープン）
        return await call_next(request)