# EmotionMemCore Dockerfile
FROM python:3.11-slim

# メタデータ
LABEL maintainer="EmotionMemCore Team"
LABEL description="感情付き記憶RAGシステム"
LABEL version="0.1.0"

# 環境変数
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# システム依存関係インストール
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# ワーキングディレクトリ設定
WORKDIR /app

# Poetryインストール
RUN pip install poetry==1.6.1

# Poetry設定
RUN poetry config virtualenvs.create false

# 依存関係ファイルコピー
COPY pyproject.toml poetry.lock* ./

# 依存関係インストール
RUN poetry install --only=main --no-dev

# アプリケーションコードコピー
COPY . .

# 非rootユーザー作成
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# データディレクトリ作成
RUN mkdir -p /app/chroma_db /app/logs

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# ポート公開
EXPOSE 8000

# 起動コマンド
CMD ["python", "main.py"]