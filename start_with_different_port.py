#!/usr/bin/env python3
"""
EmotionMemCore - 別ポートで起動
ポート8000が使用中の場合の代替起動スクリプト
"""

import os
import sys
import socket
from pathlib import Path

def check_port(port):
    """ポートが使用可能かチェック"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

def find_available_port(start_port=8001, end_port=8010):
    """利用可能なポートを探す"""
    for port in range(start_port, end_port + 1):
        if check_port(port):
            return port
    return None

def main():
    print("🔍 利用可能なポートを検索中...")
    
    # まず8000が使えるかチェック
    if check_port(8000):
        print("✅ ポート8000が利用可能です")
        port = 8000
    else:
        print("⚠️  ポート8000は使用中です")
        port = find_available_port()
        
        if port:
            print(f"✅ ポート{port}を使用します")
        else:
            print("❌ 利用可能なポートが見つかりません")
            print("💡 解決方法:")
            print("   1. 他のアプリケーションを終了してください")
            print("   2. または fix_port_error.bat を実行してください")
            sys.exit(1)
    
    # 環境変数を設定
    os.environ['API_PORT'] = str(port)
    
    print(f"🚀 EmotionMemCore をポート{port}で起動中...")
    print(f"📚 API仕様書: http://localhost:{port}/docs")
    print(f"🎯 健康チェック: http://localhost:{port}/health")
    print()
    
    # メインアプリを起動
    try:
        from api.app import app
        import uvicorn
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            reload=True if os.getenv("ENVIRONMENT") == "development" else False
        )
    except KeyboardInterrupt:
        print("\n👋 EmotionMemCore を終了しました")
    except Exception as e:
        print(f"❌ 起動エラー: {e}")
        print("\n💡 解決方法:")
        print("   1. 依存関係をインストール: pip install -r requirements.txt")
        print("   2. .env ファイルを作成: copy .env.example .env")
        print("   3. quick_setup.bat を実行")

if __name__ == "__main__":
    main()