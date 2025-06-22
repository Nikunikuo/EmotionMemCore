@echo off
chcp 65001 > nul
title EmotionMemCore 不足依存関係インストール

echo.
echo =========================================
echo   📦 EmotionMemCore 不足依存関係インストール
echo =========================================
echo.

echo 🔍 不足している依存関係を確認中...

echo.
echo 📦 python-multipart をインストール中...
pip install python-multipart

if %errorlevel%==0 (
    echo ✅ python-multipart インストール完了
) else (
    echo ❌ python-multipart インストール失敗
)

echo.
echo 📦 その他の依存関係を確認・インストール中...
pip install fastapi uvicorn jinja2

echo.
echo ✅ 依存関係インストール完了！
echo.
echo 🚀 ダッシュボードを起動してみてください:
echo    python run_dashboard.py
echo.
pause