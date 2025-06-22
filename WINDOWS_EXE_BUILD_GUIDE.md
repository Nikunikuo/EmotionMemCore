# 🔨 Windows 実行ファイル (.exe) ビルドガイド

> **YouTube見るだけ層向け** - プログラミング知識不要でダブルクリック起動

---

## 🎯 目的

EmotionMemCore を **1つの実行ファイル** にして、プログラミング知識が全くない人でも使えるようにします。

### ✨ 実現されること
- ✅ **Python インストール不要**
- ✅ **ライブラリインストール不要**  
- ✅ **ダブルクリックで起動**
- ✅ **自動でブラウザが開く**
- ✅ **YouTube見るだけ層でも使える**

---

## 🛠️ ビルド手順（開発者向け）

### 📋 前提条件
- Windows 10/11
- Python 3.8+ がインストール済み
- EmotionMemCore のソースコード

### ⚡ 1. 必要ツールのインストール

```bash
pip install pyinstaller
```

### ⚡ 2. ランチャースクリプトの作成

`emotionmemcore_launcher.py` を作成:

```python
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
```

### ⚡ 3. PyInstaller 設定ファイル作成

`emotionmemcore.spec` を作成:

```python
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
```

### ⚡ 4. ビルド実行

```bash
pyinstaller --onefile --name=EmotionMemCore --console emotionmemcore.spec
```

### ⚡ 5. インストーラー作成

`installer.bat` を作成:

```batch
@echo off
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
set DESKTOP=%USERPROFILE%\Desktop

REM インストールフォルダ作成
set INSTALL_DIR=%DESKTOP%\EmotionMemCore
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo 📁 インストール先: %INSTALL_DIR%

REM 実行ファイルをコピー
if exist "EmotionMemCore.exe" (
    copy "EmotionMemCore.exe" "%INSTALL_DIR%\" > nul
    echo ✅ プログラムファイル: コピー完了
) else (
    echo ❌ EmotionMemCore.exe が見つかりません
    pause
    exit /b 1
)

REM ショートカット作成
set SHORTCUT_PATH=%DESKTOP%\EmotionMemCore.lnk
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%INSTALL_DIR%\EmotionMemCore.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'EmotionMemCore - 感情付き記憶システム'; $Shortcut.Save()"

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
```

---

## 📦 配布用パッケージ構成

### 📁 フォルダ構成
```
EmotionMemCore_配布用/
├── EmotionMemCore.exe          <- メイン実行ファイル
├── installer.bat               <- 自動インストーラー
├── README_ユーザー向け.md        <- 使い方ガイド
└── トラブルシューティング.md     <- よくある質問
```

### 📋 README_ユーザー向け.md

```markdown
# 🤖 EmotionMemCore - 超簡単版

## 🎯 これは何？

**YouTube見るだけ層でも使える**感情付き記憶システム

- プログラミング知識不要
- インストール不要 
- ダブルクリックで起動
- 自動でブラウザが開く

## 🚀 使い方（3ステップ）

### 1️⃣ インストール（オプション）
- `installer.bat` をダブルクリック
- デスクトップにショートカットが作成されます

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

---

**🎉 YouTube見るだけ層でも3分で使えます！**
```

---

## 🎯 ユーザー体験フロー

### 👶 超初心者の場合

1. **ダウンロード**
   - ZIPファイルをダウンロード
   - デスクトップに解凍

2. **インストール**（オプション）
   - `installer.bat` をダブルクリック
   - 自動でデスクトップにショートカット作成

3. **起動**
   - `EmotionMemCore.exe` をダブルクリック
   - 黒い画面が表示（これは正常）

4. **使用開始**
   - 自動でブラウザが開く
   - ウェルカムページが表示
   - 「機能テスト」で体験

5. **終了**
   - 黒い画面を閉じる

### 🔧 技術的詳細

#### PyInstaller の利点
- ✅ **1ファイル実行** - DLL地獄なし
- ✅ **Python不要** - ランタイム同梱
- ✅ **ライブラリ不要** - 依存関係解決済み
- ✅ **高速起動** - 最適化済み

#### ファイルサイズ最適化
- UPX圧縮有効
- 不要モジュール除外
- データファイル最小化

#### セキュリティ対応
- Windows Defender対策
- デジタル署名（将来対応）
- ウイルススキャン対応

---

## 📈 期待効果

### 🎯 ターゲットユーザーへの効果

#### Before（現状）
- ❌ Python インストールが難しい
- ❌ コマンドラインが怖い
- ❌ エラーメッセージが英語
- ❌ 設定が複雑

#### After（実行ファイル版）
- ✅ **ダブルクリックだけ**
- ✅ **ブラウザが自動で開く**
- ✅ **日本語エラーメッセージ**
- ✅ **設定不要**

### 🌟 ビジネス効果
- **ユーザー層拡大** - プログラマー以外にもリーチ
- **サポート工数削減** - インストール問題がゼロ
- **口コミ効果** - 「簡単に使えた」体験
- **採用促進** - AITuberKit 連携の敷居が下がる

---

## 🚀 次のステップ

1. **Windows環境でのビルド実行**
2. **実行ファイルの動作確認**
3. **配布用ZIPパッケージ作成**
4. **ユーザーテスト実施**
5. **GitHub Release 公開**

---

**💡 これで「YouTube見るだけ層」でも EmotionMemCore を使えるようになります！**