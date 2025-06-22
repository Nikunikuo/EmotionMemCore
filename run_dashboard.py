#!/usr/bin/env python3
"""
EmotionMemCore Dashboard 起動スクリプト
初心者向けの簡単なWebダッシュボードを起動します。
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_environment():
    """開発環境の設定"""
    # ダッシュボード用の環境変数設定
    env_vars = {
        "ENVIRONMENT": "development",
        "DEBUG_MODE": "true",
        "LLM_MOCK_MODE": "true",  # 初心者用にモックモード
        "AUTH_ENABLED": "false",  # 認証無効
        "RATE_LIMIT_ENABLED": "false",  # レート制限無効
        "LOG_LEVEL": "INFO"
    }
    
    for key, value in env_vars.items():
        if not os.getenv(key):
            os.environ[key] = value
    
    print("🔧 開発環境設定完了")
    print(f"   - 環境: {os.getenv('ENVIRONMENT')}")
    print(f"   - デバッグモード: {os.getenv('DEBUG_MODE')}")
    print(f"   - モックモード: {os.getenv('LLM_MOCK_MODE')}")

def check_dependencies():
    """依存関係チェック"""
    required_packages = [
        "fastapi",
        "uvicorn",
        "jinja2",
        "python-multipart"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 不足している依存関係:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 以下のコマンドでインストールしてください:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ 依存関係チェック完了")
    return True

async def check_main_api():
    """メインAPIサーバーの確認"""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/health/")
            if response.status_code == 200:
                print("✅ メインAPIサーバー (localhost:8000) に接続できました")
                return True
            else:
                print(f"⚠️  メインAPIサーバーの応答に問題があります (HTTP {response.status_code})")
                return False
    except Exception as e:
        print("⚠️  メインAPIサーバー (localhost:8000) に接続できません")
        print(f"   エラー: {e}")
        print("\n💡 メインAPIサーバーを先に起動してください:")
        print("   python main.py")
        return False

def print_welcome():
    """ウェルカムメッセージ"""
    print("=" * 60)
    print("🤖 EmotionMemCore Dashboard")
    print("感情付き記憶RAGシステム - 初心者向けWebダッシュボード")
    print("=" * 60)
    print()

def print_urls(port=8080):
    """アクセスURL表示"""
    print()
    print("🌐 ダッシュボードが起動しました！")
    print("=" * 40)
    print(f"📊 ダッシュボード: http://localhost:{port}")
    print(f"🧪 機能テスト:     http://localhost:{port}/test")
    print(f"🔍 記憶検索:       http://localhost:{port}/search")
    print(f"📋 記憶管理:       http://localhost:{port}/memories")
    print(f"📈 記憶可視化:     http://localhost:{port}/visualization")
    print(f"📟 リアルタイムログ: http://localhost:{port}/logs")
    print(f"⚙️  設定ガイド:     http://localhost:{port}/settings")
    print()
    print("📖 メインAPI:       http://localhost:8000/docs")
    print("💚 ヘルスチェック:  http://localhost:8000/health/")
    print("=" * 40)
    print()
    print("💡 ヒント:")
    print("   - 初回利用時は「機能テスト」ページでサンプルデータを試してみてください")
    print("   - メインAPIサーバー (port 8000) が起動していることを確認してください")
    print("   - 終了時は Ctrl+C を押してください")
    print()

async def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="EmotionMemCore Dashboard")
    parser.add_argument("--port", type=int, default=8080, help="ダッシュボードポート番号 (default: 8080)")
    parser.add_argument("--host", default="0.0.0.0", help="バインドホスト (default: 0.0.0.0)")
    parser.add_argument("--no-api-check", action="store_true", help="メインAPI接続チェックをスキップ")
    parser.add_argument("--debug", action="store_true", help="デバッグモードで起動")
    
    args = parser.parse_args()
    
    print_welcome()
    
    # 環境設定
    setup_environment()
    
    if args.debug:
        os.environ["DEBUG_MODE"] = "true"
        os.environ["LOG_LEVEL"] = "DEBUG"
    
    # 依存関係チェック
    if not check_dependencies():
        sys.exit(1)
    
    # メインAPIサーバーチェック（オプション）
    if not args.no_api_check:
        api_available = await check_main_api()
        if not api_available:
            print("\n🤔 メインAPIサーバーが起動していないようです。")
            response = input("それでもダッシュボードを起動しますか？ (y/N): ")
            if response.lower() not in ['y', 'yes']:
                print("👋 ダッシュボード起動をキャンセルしました。")
                sys.exit(0)
    
    # ダッシュボードアプリのインポートと起動
    try:
        from ui.dashboard import dashboard_app
        import uvicorn
        
        print(f"🚀 ダッシュボードを起動中... (port: {args.port})")
        
        # URL表示
        print_urls(args.port)
        
        # サーバー起動
        config = uvicorn.Config(
            app=dashboard_app,
            host=args.host,
            port=args.port,
            reload=args.debug,
            log_level="debug" if args.debug else "info"
        )
        server = uvicorn.Server(config)
        await server.serve()
        
    except KeyboardInterrupt:
        print("\n👋 ダッシュボードを終了しました。")
    except Exception as e:
        print(f"\n❌ ダッシュボード起動エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 プログラムを終了しました。")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        sys.exit(1)