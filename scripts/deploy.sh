#!/bin/bash

# EmotionMemCore デプロイスクリプト

set -e  # エラー時に停止

# 色付きログ出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# 引数解析
ENVIRONMENT="production"
FORCE_REBUILD=false
SKIP_TESTS=false
BACKUP=true

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -f|--force-rebuild)
            FORCE_REBUILD=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --no-backup)
            BACKUP=false
            shift
            ;;
        -h|--help)
            echo "使用方法: $0 [OPTIONS]"
            echo ""
            echo "OPTIONS:"
            echo "  -e, --environment ENV    デプロイ環境 (development|staging|production)"
            echo "  -f, --force-rebuild      強制リビルド"
            echo "  --skip-tests             テストをスキップ"
            echo "  --no-backup              バックアップを作成しない"
            echo "  -h, --help               このヘルプを表示"
            exit 0
            ;;
        *)
            log_error "不明なオプション: $1"
            exit 1
            ;;
    esac
done

log_info "EmotionMemCore デプロイ開始"
log_info "環境: $ENVIRONMENT"

# 環境設定ファイルチェック
ENV_FILE="configs/${ENVIRONMENT}.env"
if [[ ! -f "$ENV_FILE" ]]; then
    log_error "環境設定ファイルが見つかりません: $ENV_FILE"
    exit 1
fi

log_success "環境設定ファイル確認: $ENV_FILE"

# Docker Composeファイル選択
case $ENVIRONMENT in
    development)
        COMPOSE_FILE="docker-compose.dev.yml"
        ;;
    staging|production)
        COMPOSE_FILE="docker-compose.yml"
        ;;
    *)
        log_error "サポートされていない環境: $ENVIRONMENT"
        exit 1
        ;;
esac

log_info "Docker Composeファイル: $COMPOSE_FILE"

# 必要なコマンドチェック
for cmd in docker docker-compose; do
    if ! command -v $cmd &> /dev/null; then
        log_error "$cmd が見つかりません"
        exit 1
    fi
done

# テスト実行（オプション）
if [[ "$SKIP_TESTS" == false ]]; then
    log_info "テスト実行中..."
    if [[ -f "scripts/test_runner.py" ]]; then
        python scripts/test_runner.py --fast
        log_success "テスト完了"
    else
        log_warning "テストランナーが見つかりません。テストをスキップします。"
    fi
fi

# バックアップ作成（本番環境）
if [[ "$BACKUP" == true && "$ENVIRONMENT" == "production" ]]; then
    log_info "データベースバックアップ作成中..."
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 実行中のコンテナからデータをコピー
    if docker ps | grep -q emotionmemcore-api; then
        docker exec emotionmemcore-api tar czf - /app/data | tar xzf - -C "$BACKUP_DIR"
        log_success "バックアップ作成完了: $BACKUP_DIR"
    else
        log_warning "実行中のコンテナが見つかりません。バックアップをスキップします。"
    fi
fi

# 既存コンテナ停止
log_info "既存コンテナを停止中..."
docker-compose -f "$COMPOSE_FILE" down

# イメージビルド
BUILD_ARGS=""
if [[ "$FORCE_REBUILD" == true ]]; then
    BUILD_ARGS="--no-cache"
fi

log_info "Dockerイメージビルド中..."
docker-compose -f "$COMPOSE_FILE" build $BUILD_ARGS

# 環境変数ファイルを設定
if [[ -f "$ENV_FILE" ]]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

# コンテナ起動
log_info "コンテナ起動中..."
docker-compose -f "$COMPOSE_FILE" up -d

# ヘルスチェック待機
log_info "ヘルスチェック待機中..."
HEALTH_URL="http://localhost:8000/health/"
MAX_RETRIES=30
RETRY_INTERVAL=2

for i in $(seq 1 $MAX_RETRIES); do
    if curl -f "$HEALTH_URL" > /dev/null 2>&1; then
        log_success "アプリケーション起動確認"
        break
    fi
    
    if [[ $i -eq $MAX_RETRIES ]]; then
        log_error "ヘルスチェックタイムアウト"
        docker-compose -f "$COMPOSE_FILE" logs --tail=50
        exit 1
    fi
    
    log_info "起動待機中... ($i/$MAX_RETRIES)"
    sleep $RETRY_INTERVAL
done

# デプロイ後の検証
log_info "デプロイ後検証中..."

# 基本エンドポイント確認
ENDPOINTS=(
    "/"
    "/health/"
    "/health/stats"
)

for endpoint in "${ENDPOINTS[@]}"; do
    if curl -f "http://localhost:8000$endpoint" > /dev/null 2>&1; then
        log_success "エンドポイント確認: $endpoint"
    else
        log_warning "エンドポイント応答なし: $endpoint"
    fi
done

# コンテナステータス表示
log_info "コンテナステータス:"
docker-compose -f "$COMPOSE_FILE" ps

# 完了メッセージ
log_success "🎉 デプロイ完了!"
log_info "アプリケーションURL: http://localhost:8000"
log_info "API ドキュメント: http://localhost:8000/docs"
log_info "ログ確認: docker-compose -f $COMPOSE_FILE logs -f"

# 環境固有の追加情報
case $ENVIRONMENT in
    development)
        log_info "開発環境情報:"
        log_info "- 認証: 無効"
        log_info "- レート制限: 無効"
        log_info "- LLM: モックモード"
        ;;
    staging)
        log_info "ステージング環境情報:"
        log_info "- 認証: 有効"
        log_info "- レート制限: 緩和設定"
        log_info "- デバッグモード: 有効"
        ;;
    production)
        log_info "本番環境情報:"
        log_info "- 認証: 有効"
        log_info "- レート制限: 厳格設定"
        log_info "- デバッグモード: 無効"
        if [[ "$BACKUP" == true ]]; then
            log_info "- バックアップ: $BACKUP_DIR"
        fi
        ;;
esac

log_info "監視設定:"
log_info "- ヘルスチェック: $HEALTH_URL"
log_info "- Prometheus: http://localhost:9090 (--profile monitoring)"
log_info "- Grafana: http://localhost:3000 (--profile monitoring)"