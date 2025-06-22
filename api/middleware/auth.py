"""
認証ミドルウェア
APIキー認証とアクセス制御
"""

import os
import time
import hashlib
from typing import Optional, List, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from infrastructure.config.logger import get_logger

logger = get_logger(__name__)

# HTTPベアラー認証スキーム
security = HTTPBearer(auto_error=False)


class APIKeyAuth:
    """APIキー認証クラス"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # 環境変数からAPIキー設定取得
        self.auth_enabled = os.getenv("AUTH_ENABLED", "false").lower() == "true"
        self.master_api_key = os.getenv("MASTER_API_KEY")
        self.allowed_api_keys = self._load_api_keys()
        
        # APIキー設定のバリデーション
        if self.auth_enabled and not self.allowed_api_keys:
            self.logger.warning(
                "auth_enabled_but_no_keys",
                message="認証が有効ですがAPIキーが設定されていません"
            )
        
        self.logger.info(
            "api_auth_initialized",
            auth_enabled=self.auth_enabled,
            key_count=len(self.allowed_api_keys)
        )
    
    def _load_api_keys(self) -> List[str]:
        """APIキー一覧を読み込み"""
        keys = []
        
        # マスターキー追加
        if self.master_api_key:
            keys.append(self.master_api_key)
        
        # 環境変数からAPIキーリスト取得（カンマ区切り）
        api_keys_env = os.getenv("API_KEYS", "")
        if api_keys_env:
            env_keys = [key.strip() for key in api_keys_env.split(",") if key.strip()]
            keys.extend(env_keys)
        
        # APIキーファイルから読み込み（存在する場合）
        api_keys_file = os.getenv("API_KEYS_FILE", "./api_keys.txt")
        if os.path.exists(api_keys_file):
            try:
                with open(api_keys_file, 'r') as f:
                    file_keys = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    keys.extend(file_keys)
                self.logger.info("api_keys_loaded_from_file", file=api_keys_file, count=len(file_keys))
            except Exception as e:
                self.logger.error("api_keys_file_read_failed", file=api_keys_file, error=str(e))
        
        return list(set(keys))  # 重複除去
    
    def _extract_api_key(self, request: Request) -> Optional[str]:
        """リクエストからAPIキーを抽出"""
        
        # Authorization ヘッダーから取得 (Bearer token)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # "Bearer " を除去
        
        # X-API-Key ヘッダーから取得
        api_key_header = request.headers.get("X-API-Key")
        if api_key_header:
            return api_key_header
        
        # クエリパラメータから取得（非推奨だが対応）
        api_key_query = request.query_params.get("api_key")
        if api_key_query:
            self.logger.warning(
                "api_key_in_query_deprecated",
                client_ip=request.client.host if request.client else "unknown"
            )
            return api_key_query
        
        return None
    
    def _validate_api_key(self, api_key: str) -> bool:
        """APIキーの有効性を検証"""
        if not api_key:
            return False
        
        # 直接比較
        if api_key in self.allowed_api_keys:
            return True
        
        # ハッシュ化キーとの比較（オプション）
        for stored_key in self.allowed_api_keys:
            if stored_key.startswith("sha256:"):
                # ハッシュ化されたキーとの比較
                hash_value = stored_key[7:]  # "sha256:" を除去
                api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
                if api_key_hash == hash_value:
                    return True
        
        return False
    
    def _get_rate_limit_key(self, request: Request, api_key: Optional[str]) -> str:
        """レート制限用のキーを生成"""
        if api_key:
            # APIキーがある場合はキーベース
            return f"api_key:{hashlib.md5(api_key.encode()).hexdigest()}"
        else:
            # APIキーがない場合はIPベース
            client_ip = request.client.host if request.client else "unknown"
            return f"ip:{client_ip}"
    
    async def authenticate_request(self, request: Request) -> Dict[str, Any]:
        """リクエスト認証"""
        
        # 認証が無効の場合はスキップ
        if not self.auth_enabled:
            return {
                "authenticated": True,
                "auth_method": "disabled",
                "rate_limit_key": self._get_rate_limit_key(request, None)
            }
        
        # 公開エンドポイントのチェック
        public_endpoints = [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        
        if request.url.path in public_endpoints:
            return {
                "authenticated": True,
                "auth_method": "public_endpoint",
                "rate_limit_key": self._get_rate_limit_key(request, None)
            }
        
        # APIキー抽出
        api_key = self._extract_api_key(request)
        
        if not api_key:
            self.logger.warning(
                "auth_missing_api_key",
                path=request.url.path,
                client_ip=request.client.host if request.client else "unknown"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="APIキーが必要です",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # APIキー検証
        if not self._validate_api_key(api_key):
            self.logger.warning(
                "auth_invalid_api_key",
                path=request.url.path,
                client_ip=request.client.host if request.client else "unknown",
                api_key_prefix=api_key[:8] + "..." if len(api_key) > 8 else "short_key"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無効なAPIキーです",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 認証成功
        self.logger.info(
            "auth_success",
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
            api_key_prefix=api_key[:8] + "..." if len(api_key) > 8 else "short_key"
        )
        
        return {
            "authenticated": True,
            "auth_method": "api_key",
            "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key,
            "rate_limit_key": self._get_rate_limit_key(request, api_key)
        }


# シングルトンインスタンス
_api_key_auth: Optional[APIKeyAuth] = None


def get_api_key_auth() -> APIKeyAuth:
    """APIキー認証インスタンス取得"""
    global _api_key_auth
    if _api_key_auth is None:
        _api_key_auth = APIKeyAuth()
    return _api_key_auth


async def auth_middleware(request: Request, call_next):
    """認証ミドルウェア"""
    
    start_time = time.time()
    auth_handler = get_api_key_auth()
    
    try:
        # 認証実行
        auth_result = await auth_handler.authenticate_request(request)
        
        # リクエストステートに認証情報を追加
        request.state.auth_result = auth_result
        
        # 次のミドルウェア/エンドポイントを呼び出し
        response = await call_next(request)
        
        # 認証情報をレスポンスヘッダーに追加
        if auth_result.get("authenticated"):
            response.headers["X-Auth-Method"] = auth_result.get("auth_method", "unknown")
        
        auth_time = (time.time() - start_time) * 1000
        logger.debug(
            "auth_middleware_completed",
            auth_time_ms=round(auth_time, 2),
            authenticated=auth_result.get("authenticated", False)
        )
        
        return response
        
    except HTTPException as e:
        # 認証エラーの場合
        auth_time = (time.time() - start_time) * 1000
        logger.info(
            "auth_middleware_rejected",
            status_code=e.status_code,
            detail=e.detail,
            auth_time_ms=round(auth_time, 2)
        )
        raise e
    
    except Exception as e:
        # 予期しないエラー
        auth_time = (time.time() - start_time) * 1000
        logger.error(
            "auth_middleware_error",
            error=str(e),
            error_type=type(e).__name__,
            auth_time_ms=round(auth_time, 2)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="認証処理でエラーが発生しました"
        )


def require_auth(request: Request) -> Dict[str, Any]:
    """認証必須デコレーター用の関数"""
    auth_result = getattr(request.state, "auth_result", None)
    
    if not auth_result or not auth_result.get("authenticated"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証が必要です",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return auth_result