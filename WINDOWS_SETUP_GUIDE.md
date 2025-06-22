# 🪟 Windows セットアップガイド

> **Windows で EmotionMemCore を動かす最も簡単な方法**

---

## 🚀 方法1: 超簡単セットアップ（推奨）

### 1️⃣ `quick_setup.bat` をダブルクリック

これだけです！自動で全てセットアップされます。

---

## 🛠️ 方法2: 手動セットアップ

### 📋 前提条件
- Windows 10/11
- インターネット接続

### 1️⃣ Python のインストール

1. https://python.org にアクセス
2. 「Download Python 3.11」をクリック
3. ダウンロードした exe を実行
4. **重要**: 「Add Python to PATH」にチェックを入れる
5. 「Install Now」をクリック

### 2️⃣ Poetry のインストール（PowerShell）

**PowerShell を管理者として実行**して以下を実行：

```powershell
# PowerShell用のコマンド
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

または、**コマンドプロンプト（CMD）**で：

```cmd
# コマンドプロンプト用
curl -sSL https://install.python-poetry.org | python
```

### 3️⃣ EmotionMemCore のセットアップ

```powershell
# フォルダに移動
cd D:\VibeCoding\EmotionMemCore

# 依存関係インストール
poetry install

# 起動
poetry run python main.py
```

---

## ⚠️ よくあるエラーと解決法

### ❌ "curl -sSL" でエラー

**原因**: PowerShell では curl が Invoke-WebRequest のエイリアス

**解決法1**: PowerShell で正しいコマンドを使う
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

**解決法2**: Git Bash を使う
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**解決法3**: 直接ダウンロード
1. https://install.python-poetry.org をブラウザで開く
2. ファイルを保存（例: install-poetry.py）
3. 実行: `python install-poetry.py`

### ❌ "python3: command not found"

**原因**: Windows では `python3` ではなく `python`

**解決法**: 
```powershell
# python3 の代わりに python を使う
python --version
```

### ❌ "poetry: command not found"

**原因**: PATH が通っていない

**解決法**:
1. PowerShell を**新しく開き直す**
2. 以下を実行してPATHに追加:
```powershell
$env:Path += ";$env:APPDATA\Python\Scripts"
```

### ❌ "pip install poetry" でインストールできない？

**代替方法**: pip でインストール
```powershell
pip install poetry
```

---

## 🎯 最も簡単な方法まとめ

### オプション1: バッチファイル（最推奨）
```
1. quick_setup.bat をダブルクリック
2. 指示に従う
3. 完了！
```

### オプション2: 手動だが簡単
```powershell
# 1. Python をインストール（python.org から）

# 2. pip で poetry をインストール
pip install poetry

# 3. 依存関係インストール
cd D:\VibeCoding\EmotionMemCore
poetry install

# 4. 起動
poetry run python main.py
```

### オプション3: Poetry なしで動かす
```powershell
# Poetry を使わず直接インストール
pip install fastapi uvicorn chromadb openai anthropic structlog pydantic jinja2 python-multipart

# 起動
python main.py
```

---

## 💡 Windows 特有の注意点

### PowerShell の実行ポリシー

もし「スクリプトの実行が無効」エラーが出たら：

```powershell
# 管理者として PowerShell を開いて実行
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### ファイアウォール

初回起動時に「Windows Defender ファイアウォール」の許可を求められたら「アクセスを許可」をクリック

### アンチウイルス

一部のアンチウイルスソフトが Python の実行をブロックする場合があります。その場合は例外設定に追加してください。

---

## 🚀 起動確認

正常に起動すると：

```
INFO     [2025-06-22 10:00:00] Initializing EmotionMemCore...
INFO     [2025-06-22 10:00:01] API server starting on http://localhost:8000
INFO     [2025-06-22 10:00:01] Dashboard available at http://localhost:8080
```

ブラウザで以下にアクセス：
- http://localhost:8000/docs - API仕様書
- http://localhost:8080 - ダッシュボード

---

## 🆘 それでも動かない場合

1. **quick_setup.bat を試す** - 最も確実
2. **Python を再インストール** - PATH設定を確認
3. **WSL2 を使う** - Linux 環境で実行
4. **Docker Desktop** - コンテナで実行

最終手段：
```powershell
# 最小構成で起動テスト
pip install fastapi uvicorn
python -c "from fastapi import FastAPI; app = FastAPI(); import uvicorn; uvicorn.run(app)"
```

これで http://localhost:8000 にアクセスできれば環境は正常です。