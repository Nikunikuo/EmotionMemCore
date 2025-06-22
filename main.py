"""
EmotionMemCore メインエントリポイント
"""

import os
import uvicorn
from api.app import app

if __name__ == "__main__":
    # 環境変数から設定を取得
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
    environment = os.getenv("ENVIRONMENT", "development")
    
    # 開発環境ではリロードを有効化
    reload = environment == "development"
    
    print(f"🤖 EmotionMemCore API starting...")
    print(f"   Environment: {environment}")
    print(f"   Debug Mode: {debug_mode}")
    print(f"   Host: {host}:{port}")
    print(f"   Docs: http://{host}:{port}/docs")
    
    uvicorn.run(
        "api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info" if not debug_mode else "debug"
    )