#!/usr/bin/env python
"""
EmotionMemCore Windows実行ファイル(.exe)ビルドスクリプト
YouTube見るだけ層でも使える超簡単実行ファイルを作成
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def install_pyinstaller():
    """PyInstaller をインストール"""
    print("📦 PyInstaller をインストール中...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("✅ PyInstaller インストール完了")
        return True
    except subprocess.CalledProcessError:
        print("❌ PyInstaller インストールに失敗")
        return False

def create_main_exe_script():
    """メイン実行ファイル用スクリプト作成"""
    script_content = '''
import os
import sys
import time
import threading
import webbrowser
import subprocess
from pathlib import Path

def resource_path(relative_path):
    """PyInstallerでバンドルされたリソースのパスを取得"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def print_banner():
    """起動バナー表示"""
    print("=" * 50)
    print("🤖 EmotionMemCore - 感情付き記憶システム")
    print("   YouTube見るだけ層でも使える簡単版")
    print("=" * 50)
    print()

def check_ports():
    """ポート使用状況チェック"""
    import socket
    
    def is_port_available(port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result != 0
    
    if not is_port_available(8000):
        print("⚠️  ポート8000が使用中です")
        print("   他のアプリを終了してください")
        input("Enterキーで終了...")
        sys.exit(1)
    
    if not is_port_available(8080):
        print("⚠️  ポート8080が使用中です") 
        print("   他のアプリを終了してください")
        input("Enterキーで終了...")
        sys.exit(1)

def start_api_server():
    """APIサーバー起動"""
    try:
        print("📡 APIサーバー起動中...")
        api_script = resource_path("main.py")
        if os.path.exists(api_script):
            return subprocess.Popen([sys.executable, api_script])
        else:
            print("❌ APIサーバーファイルが見つかりません")
            return None
    except Exception as e:
        print(f"❌ APIサーバー起動エラー: {e}")
        return None

def start_dashboard():
    """ダッシュボード起動"""
    try:
        print("🎨 ダッシュボード起動中...")
        dashboard_script = resource_path("run_dashboard.py")
        if os.path.exists(dashboard_script):
            return subprocess.Popen([sys.executable, dashboard_script])
        else:
            print("❌ ダッシュボードファイルが見つかりません")
            return None
    except Exception as e:
        print(f"❌ ダッシュボード起動エラー: {e}")
        return None

def open_browser():
    """ブラウザを開く"""
    def delayed_open():
        time.sleep(8)  # サーバー起動を待つ
        try:
            print("🌐 ブラウザを開いています...")
            webbrowser.open("http://localhost:8080")
        except Exception as e:
            print(f"⚠️  ブラウザ自動起動に失敗: {e}")
            print("   手動で http://localhost:8080 にアクセスしてください")
    
    browser_thread = threading.Thread(target=delayed_open)
    browser_thread.daemon = True
    browser_thread.start()

def main():
    """メイン処理"""
    print_banner()
    
    print("📋 システムチェック中...")
    check_ports()
    print("✅ ポートチェック: OK")
    
    # サーバー起動
    api_process = start_api_server()
    if not api_process:
        input("Enterキーで終了...")
        sys.exit(1)
    
    time.sleep(3)  # APIサーバー起動待機
    
    dashboard_process = start_dashboard()
    if not dashboard_process:
        api_process.terminate()
        input("Enterキーで終了...")
        sys.exit(1)
    
    # ブラウザ起動
    open_browser()
    
    print()
    print("✨ 起動完了！")
    print()
    print("🌐 ダッシュボード: http://localhost:8080")
    print("📚 API仕様書:     http://localhost:8000/docs")
    print()
    print("💡 使い方:")
    print("   1. ブラウザでダッシュボードが開きます")
    print("   2. 「機能テスト」ボタンで試してみてください")
    print("   3. 終了するときはこのウィンドウを閉じてください")
    print()
    print("⚠️  このウィンドウは閉じないでください！")
    print("   （システムが停止します）")
    print()
    
    try:
        # プロセス監視
        while True:
            if api_process.poll() is not None or dashboard_process.poll() is not None:
                print("⚠️  サーバープロセスが異常終了しました")
                break
            time.sleep(5)
    
    except KeyboardInterrupt:
        print("\\n🛑 終了処理中...")
    
    finally:
        # クリーンアップ
        try:
            api_process.terminate()
            dashboard_process.terminate()
            time.sleep(2)
            api_process.kill()
            dashboard_process.kill()
        except:
            pass
        
        print("👋 EmotionMemCore を終了しました")
        input("Enterキーで終了...")

if __name__ == "__main__":
    main()
'''
    
    with open("emotionmemcore_launcher.py", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print("✅ ランチャースクリプト作成完了: emotionmemcore_launcher.py")

def create_spec_file():
    """PyInstaller spec ファイル作成"""
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 必要なデータファイル
datas = [
    ('api', 'api'),
    ('core', 'core'),
    ('infrastructure', 'infrastructure'),
    ('services', 'services'),
    ('ui', 'ui'),
    ('docs', 'docs'),
    ('main.py', '.'),
    ('run_dashboard.py', '.'),
    ('pyproject.toml', '.'),
    ('README.md', '.'),
    ('CLAUDE.md', '.'),
]

# 隠しimport（自動検出されないモジュール）
hiddenimports = [
    'fastapi',
    'uvicorn',
    'jinja2',
    'multipart',
    'chromadb',
    'openai',
    'anthropic',
    'structlog',
    'pydantic',
    'python_multipart',
    'sqlite3',
    'json',
    'asyncio',
]

a = Analysis(
    ['emotionmemcore_launcher.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='EmotionMemCore',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    cofile=None,
    icon=None,
)
'''
    
    with open("emotionmemcore.spec", "w", encoding="utf-8") as f:
        f.write(spec_content)
    
    print("✅ PyInstaller spec ファイル作成完了: emotionmemcore.spec")

def build_exe():
    """実行ファイルをビルド"""
    print("🔨 実行ファイルをビルド中...")
    print("   ※この処理には数分かかります...")
    
    try:
        # PyInstaller実行
        cmd = [
            "pyinstaller", 
            "--onefile",
            "--name=EmotionMemCore",
            "--console",
            "--distpath=./dist",
            "--workpath=./build",
            "--specpath=./",
            "emotionmemcore.spec"
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if os.path.exists("dist/EmotionMemCore.exe"):
            print("✅ 実行ファイルビルド完了!")
            print(f"📁 場所: {os.path.abspath('dist/EmotionMemCore.exe')}")
            return True
        else:
            print("❌ 実行ファイルが見つかりません")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ ビルドエラー: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def create_installer_script():
    """インストーラー用バッチファイル作成"""
    installer_content = '''@echo off
chcp 65001 > nul
title EmotionMemCore インストーラー

echo.
echo =========================================
echo   🤖 EmotionMemCore インストーラー
echo   YouTube見るだけ層でも使える簡単版
echo =========================================
echo.

echo 📋 インストール準備中...

REM デスクトップパス取得
set DESKTOP=%USERPROFILE%\\Desktop

REM インストールフォルダ作成
set INSTALL_DIR=%DESKTOP%\\EmotionMemCore
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo 📁 インストール先: %INSTALL_DIR%

REM 実行ファイルをコピー
if exist "EmotionMemCore.exe" (
    copy "EmotionMemCore.exe" "%INSTALL_DIR%\\" > nul
    echo ✅ プログラムファイル: コピー完了
) else (
    echo ❌ EmotionMemCore.exe が見つかりません
    pause
    exit /b 1
)

REM ショートカット作成
set SHORTCUT_PATH=%DESKTOP%\\EmotionMemCore.lnk
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%INSTALL_DIR%\\EmotionMemCore.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'EmotionMemCore - 感情付き記憶システム'; $Shortcut.Save()"

if exist "%SHORTCUT_PATH%" (
    echo ✅ デスクトップショートカット: 作成完了
) else (
    echo ⚠️  ショートカット作成に失敗しましたが、続行します
)

echo.
echo 🎉 インストール完了！
echo.
echo 💡 使い方:
echo    1. デスクトップの「EmotionMemCore」をダブルクリック
echo    2. 初回起動時は少し時間がかかります
echo    3. ブラウザが自動で開きます
echo.
echo 📁 インストール場所: %INSTALL_DIR%
echo.

pause
'''
    
    with open("installer.bat", "w", encoding="utf-8") as f:
        f.write(installer_content)
    
    print("✅ インストーラー作成完了: installer.bat")

def create_readme_exe():
    """実行ファイル版README作成"""
    readme_content = '''# 🤖 EmotionMemCore - 実行ファイル版

## 🎯 これは何？

**YouTube見るだけ層でも使える超簡単版**

- プログラミング知識不要
- インストール不要 
- ダブルクリックで起動
- 自動でブラウザが開く

## 🚀 使い方（3ステップ）

### 1️⃣ ダウンロード
- `EmotionMemCore.exe` をダウンロード
- デスクトップに保存（推奨）

### 2️⃣ 起動
- `EmotionMemCore.exe` をダブルクリック
- 初回は起動に少し時間がかかります
- 黒い画面が表示されます（これは正常です）

### 3️⃣ 使用開始
- 自動でブラウザが開きます
- 「機能テスト」ボタンで体験してみてください
- 終了時は黒い画面を閉じてください

## 💡 トラブルシューティング

### ❓ 起動しない
- Windows Defenderで止められている場合
  - 「詳細情報」→「実行」で起動可能
  - 安全なソフトです

### ❓ ブラウザが開かない  
- 手動で http://localhost:8080 にアクセス

### ❓ エラーが出る
- 他のアプリを終了してください
- パソコンを再起動してください

## 📁 ファイル構成

```
EmotionMemCore.exe     <- これをダブルクリック
installer.bat          <- 自動インストール用（オプション）
README_実行ファイル版.md  <- このファイル
```

## 🔗 詳細情報

- GitHub: https://github.com/Nikunikuo/EmotionMemCore
- ドキュメント: CLAUDE.md（開発者向け）

---

**🎉 YouTube見るだけ層でも3分で使えます！**
'''
    
    with open("README_実行ファイル版.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("✅ 実行ファイル版README作成完了: README_実行ファイル版.md")

def main():
    """メインビルド処理"""
    print("🔨 EmotionMemCore Windows実行ファイル(.exe) ビルド開始")
    print("=" * 60)
    
    # 前回のビルドファイルをクリーンアップ
    if os.path.exists("dist"):
        shutil.rmtree("dist")
        print("🧹 前回のdistフォルダを削除")
    
    if os.path.exists("build"):
        shutil.rmtree("build")
        print("🧹 前回のbuildフォルダを削除")
    
    # PyInstaller インストール
    if not install_pyinstaller():
        return False
    
    # ファイル作成
    create_main_exe_script()
    create_spec_file()
    create_installer_script()
    create_readme_exe()
    
    # ビルド実行
    success = build_exe()
    
    if success:
        print()
        print("🎉 ビルド完了！")
        print("=" * 60)
        print("📁 生成ファイル:")
        print(f"   EmotionMemCore.exe - メイン実行ファイル")
        print(f"   installer.bat - 自動インストーラー")
        print(f"   README_実行ファイル版.md - 使い方ガイド")
        print()
        print("💡 配布方法:")
        print("   1. dist/ フォルダ内のファイルをZIPで配布")
        print("   2. ユーザーはEmotionMemCore.exeをダブルクリックするだけ")
        print()
        print("🎯 ターゲットユーザー: YouTube見るだけ層")
        print("   - プログラミング知識不要")
        print("   - インストール作業不要") 
        print("   - ダブルクリックで即起動")
        
        return True
    else:
        print("❌ ビルドに失敗しました")
        return False

if __name__ == "__main__":
    success = main()
    input("\nEnterキーで終了...")
    sys.exit(0 if success else 1)