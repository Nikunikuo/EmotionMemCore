#!/bin/bash

# EmotionMemCore ビルド・検証スクリプト

set -e

# 色付きログ出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# スクリプトディレクトリ
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# 引数解析
ENVIRONMENT="development"
RUN_TESTS=true
BUILD_ONLY=false
CLEAN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --no-tests)
            RUN_TESTS=false
            shift
            ;;
        --build-only)
            BUILD_ONLY=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        -h|--help)
            echo "使用方法: $0 [OPTIONS]"
            echo ""
            echo "OPTIONS:"
            echo "  -e, --environment ENV    ビルド環境 (development|staging|production)"
            echo "  --no-tests               テストをスキップ"
            echo "  --build-only             ビルドのみ実行"
            echo "  --clean                  クリーンビルド"
            echo "  -h, --help               ヘルプ表示"
            exit 0
            ;;
        *)
            log_error "不明なオプション: $1"
            exit 1
            ;;
    esac
done

log_info "EmotionMemCore ビルド開始"
log_info "環境: $ENVIRONMENT"

# 必要コマンドチェック
for cmd in python docker docker-compose; do
    if ! command -v $cmd &> /dev/null; then
        log_error "$cmd が見つかりません"
        exit 1
    fi
done

# Python環境チェック
log_info "Python環境確認..."
python --version
poetry --version || log_warning "Poetry が見つかりません"

# 依存関係チェック
log_info "依存関係確認中..."
if [[ -f "pyproject.toml" ]]; then
    if command -v poetry &> /dev/null; then
        poetry check
        log_success "Poetry依存関係確認完了"
    else
        log_warning "Poetry未インストール。pip依存関係のみ確認"
        pip check || log_warning "pip依存関係に問題があります"
    fi
fi

# クリーンアップ（オプション）
if [[ "$CLEAN" == true ]]; then
    log_info "クリーンアップ実行中..."
    
    # Python キャッシュ削除
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    # テストデータ削除
    rm -rf test_chroma_db/ dev_chroma_db/ 2>/dev/null || true
    
    # Docker クリーンアップ
    docker system prune -f
    
    log_success "クリーンアップ完了"
fi

# テスト実行
if [[ "$RUN_TESTS" == true ]]; then
    log_info "テスト実行中..."
    
    if [[ -f "scripts/test_runner.py" ]]; then
        python scripts/test_runner.py --fast --verbose
        log_success "テスト完了"
    else
        log_warning "テストランナーが見つかりません"
        if command -v pytest &> /dev/null; then
            pytest tests/ -v --tb=short
            log_success "pytest実行完了"
        else
            log_warning "pytestが見つかりません。テストをスキップ"
        fi
    fi
fi

# Dockerイメージビルド
log_info "Dockerイメージビルド中..."

BUILD_ARGS=""
if [[ "$CLEAN" == true ]]; then
    BUILD_ARGS="--no-cache"
fi

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

docker-compose -f "$COMPOSE_FILE" build $BUILD_ARGS
log_success "Dockerビルド完了"

# イメージサイズ確認
log_info "イメージ情報:"
docker images | grep emotionmemcore || log_warning "イメージが見つかりません"

# セキュリティスキャン（オプション）
if command -v docker &> /dev/null; then
    log_info "セキュリティスキャン実行中..."
    
    # Dockerイメージの脆弱性スキャン
    IMAGE_ID=$(docker images -q emotionmemcore_emotionmemcore-dev:latest 2>/dev/null || docker images -q emotionmemcore_emotionmemcore:latest 2>/dev/null)
    
    if [[ -n "$IMAGE_ID" ]]; then
        # Trivyがある場合
        if command -v trivy &> /dev/null; then
            trivy image "$IMAGE_ID"
            log_success "Trivyセキュリティスキャン完了"
        else
            log_warning "Trivy未インストール。セキュリティスキャンをスキップ"
        fi
        
        # Docker Benchmarkセキュリティ（もしあれば）
        if command -v docker-bench-security &> /dev/null; then
            docker-bench-security
            log_success "Docker Benchmarkセキュリティ完了"
        fi
    else
        log_warning "スキャン対象イメージが見つかりません"
    fi
fi

# ビルドのみの場合はここで終了
if [[ "$BUILD_ONLY" == true ]]; then
    log_success "ビルド完了（起動はスキップ）"
    exit 0
fi

# テスト起動
log_info "テスト起動中..."
docker-compose -f "$COMPOSE_FILE" up -d

# ヘルスチェック
log_info "ヘルスチェック待機中..."
HEALTH_URL="http://localhost:8000/health/"
MAX_RETRIES=15
RETRY_INTERVAL=2

for i in $(seq 1 $MAX_RETRIES); do
    if curl -f "$HEALTH_URL" > /dev/null 2>&1; then
        log_success "ヘルスチェック成功"
        break
    fi
    
    if [[ $i -eq $MAX_RETRIES ]]; then
        log_error "ヘルスチェックタイムアウト"
        log_info "コンテナログ:"
        docker-compose -f "$COMPOSE_FILE" logs --tail=20
        exit 1
    fi
    
    log_info "起動待機中... ($i/$MAX_RETRIES)"
    sleep $RETRY_INTERVAL
done

# API テスト
log_info "API テスト実行中..."

# 基本エンドポイントテスト
ENDPOINTS=(
    "/"
    "/health/"
    "/health/stats"
)

for endpoint in "${ENDPOINTS[@]}"; do
    if curl -f "http://localhost:8000$endpoint" > /dev/null 2>&1; then
        log_success "API テスト成功: $endpoint"
    else
        log_error "API テスト失敗: $endpoint"
    fi
done

# OpenAPI スキーマテスト
if curl -f "http://localhost:8000/openapi.json" > /dev/null 2>&1; then
    log_success "OpenAPI スキーマ取得成功"
else
    log_warning "OpenAPI スキーマ取得失敗"
fi

# コンテナ停止
log_info "テストコンテナ停止中..."
docker-compose -f "$COMPOSE_FILE" down

# サマリー
log_success "🎉 ビルド・検証完了!"
log_info "次のステップ:"
log_info "  開発環境起動: docker-compose -f docker-compose.dev.yml up -d"
log_info "  本番デプロイ: ./scripts/deploy.sh -e production"
log_info "  テスト実行: python scripts/test_runner.py"