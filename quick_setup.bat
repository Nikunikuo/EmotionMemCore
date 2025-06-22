@echo off
chcp 65001 > nul
title EmotionMemCore 超簡単セットアップ

echo.
echo =========================================
echo   🤖 EmotionMemCore 超簡単セットアップ
echo   YouTube見るだけ層向け - 3分で完了
echo =========================================
echo.

echo 🎯 これから EmotionMemCore をセットアップします
echo    難しい作業は一切ありません！
echo.

pause

echo 📋 セットアップ開始...
echo.

REM Python チェック
echo 1️⃣ Python チェック中...
python --version > nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ Python がインストールされていません
    echo.
    echo 📥 Python を自動インストールしますか？
    echo    Y: はい（推奨）
    echo    N: いいえ（手動でインストール）
    echo.
    set /p INSTALL_PYTHON="選択してください (Y/N): "
    
    if /i "%INSTALL_PYTHON%"=="Y" (
        echo.
        echo 📥 Python をダウンロード中...
        powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe' -OutFile 'python_installer.exe'"
        
        if exist "python_installer.exe" (
            echo ✅ ダウンロード完了
            echo 🔧 Python をインストール中...
            echo    ※ 「Add Python to PATH」にチェックが入っていることを確認してください
            start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
            del python_installer.exe
            echo ✅ Python インストール完了
        ) else (
            echo ❌ ダウンロードに失敗しました
            echo    手動で https://python.org からダウンロードしてください
            pause
            exit /b 1
        )
    ) else (
        echo.
        echo 📝 手動インストール手順:
        echo    1. https://python.org にアクセス
        echo    2. 「Download Python」をクリック
        echo    3. インストール時に「Add Python to PATH」にチェック
        echo    4. インストール後、このセットアップを再実行
        echo.
        pause
        exit /b 1
    )
) else (
    echo ✅ Python: インストール済み
)

echo.
echo 2️⃣ 必要なライブラリをインストール中...
pip install poetry > nul 2>&1
if errorlevel 1 (
    echo ⚠️  Poetry インストールに失敗しましたが、続行します
) else (
    echo ✅ Poetry: インストール完了
)

echo.
echo 3️⃣ EmotionMemCore の依存関係をインストール中...
echo    ※ この処理には数分かかる場合があります
poetry install > nul 2>&1
if errorlevel 1 (
    echo ⚠️  Poetry install に失敗しました
    echo    pip で基本パッケージをインストールします...
    pip install fastapi uvicorn jinja2 python-multipart > nul 2>&1
    if errorlevel 1 (
        echo ❌ パッケージインストールに失敗しました
        echo    インターネット接続を確認してください
        pause
        exit /b 1
    )
)
echo ✅ 依存関係: インストール完了

echo.
echo 4️⃣ 設定ファイルを作成中...

REM .env ファイル作成
if not exist ".env" (
    echo # EmotionMemCore 基本設定 > .env
    echo # YouTube見るだけ層向け - 簡単設定 >> .env
    echo. >> .env
    echo # 環境設定 >> .env
    echo ENVIRONMENT=development >> .env
    echo DEBUG_MODE=true >> .env
    echo LLM_MOCK_MODE=true >> .env
    echo. >> .env
    echo # セキュリティ設定（初心者向けは無効） >> .env
    echo AUTH_ENABLED=false >> .env
    echo RATE_LIMIT_ENABLED=false >> .env
    echo. >> .env
    echo # ポート設定 >> .env
    echo API_PORT=8000 >> .env
    echo DASHBOARD_PORT=8080 >> .env
    echo. >> .env
    echo # 💡 本格利用時は以下を設定してください >> .env
    echo # OPENAI_API_KEY=your_openai_key_here >> .env
    echo # ANTHROPIC_API_KEY=your_claude_key_here >> .env
    echo ✅ 設定ファイル: 作成完了
) else (
    echo ✅ 設定ファイル: 既に存在
)

REM データベースフォルダ作成
if not exist "data" mkdir data
echo ✅ データベースフォルダ: 作成完了

echo.
echo 5️⃣ 起動テスト中...
echo    ※ 少々お待ちください...

REM APIサーバーテスト起動
start /min cmd /c "python main.py"
timeout /t 3 /nobreak > nul

REM ポートチェック
netstat -an | find "8000" | find "LISTENING" > nul
if errorlevel 1 (
    echo ❌ APIサーバーの起動に失敗しました
    echo    ポート8000が使用できません
    taskkill /f /im python.exe > nul 2>&1
    pause
    exit /b 1
) else (
    echo ✅ APIサーバー: 起動成功
)

REM ダッシュボードテスト起動
start /min cmd /c "python run_dashboard.py"
timeout /t 3 /nobreak > nul

netstat -an | find "8080" | find "LISTENING" > nul
if errorlevel 1 (
    echo ❌ ダッシュボードの起動に失敗しました
    echo    ポート8080が使用できません
    taskkill /f /im python.exe > nul 2>&1
    pause
    exit /b 1
) else (
    echo ✅ ダッシュボード: 起動成功
)

REM テストプロセス終了
taskkill /f /im python.exe > nul 2>&1

echo.
echo 🎉 セットアップ完了！
echo =========================================
echo.
echo 📁 作成されたファイル:
echo    - .env (設定ファイル)
echo    - data/ (データベースフォルダ)
echo    - start_emotionmemcore.bat (起動用)
echo.
echo 🚀 次のステップ:
echo    1. 「start_emotionmemcore.bat」をダブルクリック
echo    2. ブラウザが自動で開きます  
echo    3. 「機能テスト」ボタンで体験してみてください
echo.
echo 💡 AITuberKit 連携ガイド:
echo    - docs/aituberkit-guide.md をご覧ください
echo    - コピペするだけで連携できます
echo.
echo 🌐 便利なリンク:
echo    - ダッシュボード: http://localhost:8080
echo    - API仕様書: http://localhost:8000/docs
echo    - GitHub: https://github.com/Nikunikuo/EmotionMemCore
echo.

echo 🎯 今すぐ体験しますか？
set /p START_NOW="Y: はい / N: 後で (Y/N): "

if /i "%START_NOW%"=="Y" (
    echo.
    echo 🚀 EmotionMemCore を起動中...
    start start_emotionmemcore.bat
    echo ✨ 別ウィンドウで起動しました！
)

echo.
echo 🎉 セットアップが完了しました！
echo    困ったときは README.md をご覧ください
echo.
pause