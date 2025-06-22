@echo off
chcp 65001 > nul
title EmotionMemCore ポートエラー解決

echo.
echo =========================================
echo   🔧 EmotionMemCore ポートエラー解決
echo =========================================
echo.

echo 📊 ポート8000の使用状況を確認中...
netstat -an | find "8000" | find "LISTENING"

if %errorlevel%==0 (
    echo.
    echo ⚠️  ポート8000が既に使用されています
    echo.
    echo 🔍 使用中のプロセスを確認:
    netstat -ano | find ":8000" | find "LISTENING"
    
    echo.
    echo 💡 解決方法:
    echo    1. 他のアプリケーションを終了する
    echo    2. 別のポートを使用する
    echo    3. プロセスを強制終了する
    echo.
    
    set /p CHOICE="プロセスを強制終了しますか？ (Y/N): "
    if /i "%CHOICE%"=="Y" (
        echo.
        echo 🛑 ポート8000を使用中のプロセスを終了中...
        for /f "tokens=5" %%a in ('netstat -ano ^| find ":8000" ^| find "LISTENING"') do (
            echo プロセスID: %%a を終了中...
            taskkill /F /PID %%a > nul 2>&1
        )
        echo ✅ プロセスを終了しました
    )
) else (
    echo ✅ ポート8000は使用されていません
    echo.
    echo 🔧 管理者権限で実行してみてください:
    echo    右クリック → 管理者として実行
)

echo.
echo 🚀 EmotionMemCore を起動してみてください:
echo    python main.py
echo.
pause