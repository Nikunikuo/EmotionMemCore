#!/usr/bin/env python3
"""
テスト実行スクリプト
様々なテストパターンの実行を簡単にする
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd: list, description: str) -> bool:
    """コマンド実行"""
    print(f"\n🔄 {description}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} - 成功")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - 失敗")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def setup_test_environment():
    """テスト環境セットアップ"""
    print("🔧 テスト環境をセットアップ中...")
    
    # テスト用環境変数設定
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DEBUG_MODE"] = "true"
    os.environ["LLM_MOCK_MODE"] = "true"
    os.environ["CHROMA_PERSIST_DIRECTORY"] = "./test_chroma_db"
    
    # テスト用ディレクトリクリーンアップ
    test_db_path = Path("./test_chroma_db")
    if test_db_path.exists():
        import shutil
        shutil.rmtree(test_db_path)
    
    print("✅ テスト環境セットアップ完了")


def run_unit_tests(verbose: bool = False, coverage: bool = False) -> bool:
    """単体テスト実行"""
    cmd = ["python", "-m", "pytest", "tests/unit/", "-m", "unit"]
    
    if verbose:
        cmd.append("-v")
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
    
    return run_command(cmd, "単体テスト実行")


def run_integration_tests(verbose: bool = False) -> bool:
    """統合テスト実行"""
    cmd = ["python", "-m", "pytest", "tests/integration/", "-m", "integration"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "統合テスト実行")


def run_e2e_tests(verbose: bool = False) -> bool:
    """E2Eテスト実行"""
    cmd = ["python", "-m", "pytest", "tests/e2e/", "-m", "e2e"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "E2Eテスト実行")


def run_all_tests(verbose: bool = False, coverage: bool = False) -> bool:
    """全テスト実行"""
    cmd = ["python", "-m", "pytest", "tests/"]
    
    if verbose:
        cmd.append("-v")
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
    
    # 実際のAPIキーが必要なテストをスキップ
    cmd.extend(["-m", "not requires_api_key and not requires_internet"])
    
    return run_command(cmd, "全テスト実行")


def run_fast_tests(verbose: bool = False) -> bool:
    """高速テスト実行（slowマーカー除外）"""
    cmd = ["python", "-m", "pytest", "tests/", "-m", "not slow"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "高速テスト実行")


def run_linting() -> bool:
    """リンティング実行"""
    success = True
    
    # flake8がある場合
    try:
        success &= run_command(["flake8", ".", "--exclude=.venv,__pycache__"], "flake8リンティング")
    except FileNotFoundError:
        print("⚠️ flake8が見つかりません。スキップします。")
    
    # black チェック
    try:
        success &= run_command(["black", "--check", "."], "blackフォーマットチェック")
    except FileNotFoundError:
        print("⚠️ blackが見つかりません。スキップします。")
    
    return success


def run_type_checking() -> bool:
    """型チェック実行"""
    try:
        return run_command(["mypy", ".", "--ignore-missing-imports"], "型チェック (mypy)")
    except FileNotFoundError:
        print("⚠️ mypyが見つかりません。スキップします。")
        return True


def run_security_check() -> bool:
    """セキュリティチェック"""
    try:
        return run_command(["safety", "check"], "セキュリティチェック (safety)")
    except FileNotFoundError:
        print("⚠️ safetyが見つかりません。スキップします。")
        return True


def run_dependency_check() -> bool:
    """依存関係チェック"""
    try:
        return run_command(["pip", "check"], "依存関係チェック")
    except FileNotFoundError:
        return False


def run_api_test() -> bool:
    """API起動テスト"""
    print("\n🚀 API起動テストを開始...")
    
    # APIを別プロセスで起動
    import time
    import threading
    import requests
    from api.app import app
    import uvicorn
    
    # テストサーバー起動
    config = uvicorn.Config(app, host="127.0.0.1", port=8001, log_level="warning")
    server = uvicorn.Server(config)
    
    # 別スレッドでサーバー起動
    def run_server():
        import asyncio
        asyncio.run(server.serve())
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # サーバー起動待ち
    time.sleep(3)
    
    try:
        # ヘルスチェック
        response = requests.get("http://127.0.0.1:8001/health/", timeout=10)
        if response.status_code == 200:
            print("✅ API起動テスト - 成功")
            print(f"Health check response: {response.json()}")
            return True
        else:
            print(f"❌ API起動テスト - 失敗 (status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ API起動テスト - エラー: {e}")
        return False


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="EmotionMemCore テストランナー")
    parser.add_argument("--unit", action="store_true", help="単体テストのみ実行")
    parser.add_argument("--integration", action="store_true", help="統合テストのみ実行")
    parser.add_argument("--e2e", action="store_true", help="E2Eテストのみ実行")
    parser.add_argument("--fast", action="store_true", help="高速テストのみ実行")
    parser.add_argument("--all", action="store_true", help="全テスト実行")
    parser.add_argument("--lint", action="store_true", help="リンティング実行")
    parser.add_argument("--type", action="store_true", help="型チェック実行")
    parser.add_argument("--security", action="store_true", help="セキュリティチェック実行")
    parser.add_argument("--api", action="store_true", help="API起動テスト実行")
    parser.add_argument("--coverage", action="store_true", help="カバレッジ測定")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細出力")
    parser.add_argument("--ci", action="store_true", help="CI/CD用全チェック実行")
    
    args = parser.parse_args()
    
    # 引数がない場合は使用方法を表示
    if not any(vars(args).values()):
        parser.print_help()
        print("\n🔍 使用例:")
        print("  python scripts/test_runner.py --fast          # 高速テスト")
        print("  python scripts/test_runner.py --unit --coverage  # 単体テスト+カバレッジ")
        print("  python scripts/test_runner.py --ci            # CI用全チェック")
        return
    
    print("🧪 EmotionMemCore テストランナー")
    print("=" * 50)
    
    # テスト環境セットアップ
    setup_test_environment()
    
    success = True
    
    # CI/CD用全チェック
    if args.ci:
        print("\n🔄 CI/CD用全チェックを実行中...")
        success &= run_dependency_check()
        success &= run_linting()
        success &= run_type_checking()
        success &= run_security_check()
        success &= run_fast_tests(verbose=args.verbose)
        success &= run_api_test()
    
    # 個別テスト実行
    if args.unit:
        success &= run_unit_tests(verbose=args.verbose, coverage=args.coverage)
    
    if args.integration:
        success &= run_integration_tests(verbose=args.verbose)
    
    if args.e2e:
        success &= run_e2e_tests(verbose=args.verbose)
    
    if args.fast:
        success &= run_fast_tests(verbose=args.verbose)
    
    if args.all:
        success &= run_all_tests(verbose=args.verbose, coverage=args.coverage)
    
    if args.lint:
        success &= run_linting()
    
    if args.type:
        success &= run_type_checking()
    
    if args.security:
        success &= run_security_check()
    
    if args.api:
        success &= run_api_test()
    
    # 結果表示
    print("\n" + "=" * 50)
    if success:
        print("🎉 全てのテストが成功しました！")
        sys.exit(0)
    else:
        print("❌ 一部のテストが失敗しました。")
        sys.exit(1)


if __name__ == "__main__":
    main()