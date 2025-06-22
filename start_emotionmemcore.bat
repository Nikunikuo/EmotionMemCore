@echo off
chcp 65001 > nul
title EmotionMemCore - 感情付き記憶システム

echo.
echo =========================================
echo   🤖 EmotionMemCore 起動中...
echo   感情付き記憶システム - かんたんモード
echo =========================================
echo.

echo 📋 システムチェック中...

REM Python のインストール確認
python --version > nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ Pythonがインストールされていません
    echo.
    echo 📥 Pythonをインストールしてください:
    echo    https://python.org
    echo.
    echo ✨ インストール時の注意:
    echo    「Add Python to PATH」にチェックを入れてください
    echo.
    pause
    exit /b 1
)

echo ✅ Python: OK

REM 必要なライブラリのインストール
echo 📦 必要なライブラリをインストール中...
pip install fastapi uvicorn jinja2 python-multipart > nul 2>&1
if errorlevel 1 (
    echo ⚠️  ライブラリインストールで問題が発生しましたが、続行します...
)

echo ✅ ライブラリ: OK

REM ポート使用状況チェック
netstat -an | find "8000" | find "LISTENING" > nul
if not errorlevel 1 (
    echo.
    echo ⚠️  ポート8000が既に使用されています
    echo    他のアプリを終了してからもう一度お試しください
    echo.
    pause
    exit /b 1
)

netstat -an | find "8080" | find "LISTENING" > nul
if not errorlevel 1 (
    echo.
    echo ⚠️  ポート8080が既に使用されています
    echo    他のアプリを終了してからもう一度お試しください
    echo.
    pause
    exit /b 1
)

echo.
echo 🚀 EmotionMemCore を起動します...
echo.
echo 📡 APIサーバー起動中... (ポート 8000)
start /min cmd /c "python main.py"

REM APIサーバーの起動を待機
timeout /t 3 /nobreak > nul

echo 🎨 ダッシュボード起動中... (ポート 8080)
start /min cmd /c "python run_dashboard.py"

REM ダッシュボードの起動を待機
timeout /t 5 /nobreak > nul

echo.
echo ✨ 起動完了！ブラウザを開いています...
echo.

REM ブラウザでダッシュボードを開く
start http://localhost:8080

echo 🌐 ダッシュボード: http://localhost:8080
echo 📚 API仕様書:     http://localhost:8000/docs
echo.
echo 💡 使い方:
echo    1. ブラウザでダッシュボードが開きます
echo    2. 「機能テスト」ボタンで試してみてください
echo    3. 終了するときはこのウィンドウを閉じてください
echo.
echo ⚠️  このウィンドウは閉じないでください！
echo    （システムが停止します）
echo.

REM システム監視ループ
:monitor
timeout /t 10 /nobreak > nul

REM プロセス生存確認
tasklist | find "python.exe" > nul
if errorlevel 1 (
    echo.
    echo ⚠️  Pythonプロセスが見つかりません
    echo    システムを再起動します...
    echo.
    goto restart
)

REM ポート生存確認
netstat -an | find "8080" | find "LISTENING" > nul
if errorlevel 1 (
    echo.
    echo ⚠️  ダッシュボードが停止しました
    echo    システムを再起動します...
    echo.
    goto restart
)

goto monitor

:restart
echo 🔄 再起動中...
taskkill /f /im python.exe > nul 2>&1
timeout /t 2 /nobreak > nul
goto start_servers

:start_servers
start /min cmd /c "python main.py"
timeout /t 3 /nobreak > nul
start /min cmd /c "python run_dashboard.py"
timeout /t 5 /nobreak > nul
goto monitor