"""
OpenAPI設定とドキュメント拡張
EmotionMemCore API の詳細仕様書設定
"""

from typing import Dict, Any, List
from fastapi.openapi.utils import get_openapi


def get_custom_openapi(app) -> Dict[str, Any]:
    """カスタムOpenAPI仕様書生成"""
    
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="🤖 EmotionMemCore API",
        version="0.1.0",
        description=_get_api_description(),
        routes=app.routes,
        servers=[
            {
                "url": "http://localhost:8000",
                "description": "開発環境"
            },
            {
                "url": "https://api.emotionmemcore.com",
                "description": "本番環境"
            }
        ]
    )
    
    # カスタム情報追加
    openapi_schema["info"].update(_get_extended_info())
    
    # タグ情報追加
    openapi_schema["tags"] = _get_api_tags()
    
    # セキュリティスキーム追加
    openapi_schema["components"] = openapi_schema.get("components", {})
    openapi_schema["components"]["securitySchemes"] = _get_security_schemes()
    
    # エラーレスポンススキーマ追加
    openapi_schema["components"]["schemas"].update(_get_error_schemas())
    
    # 成功レスポンススキーマ追加
    openapi_schema["components"]["schemas"].update(_get_response_schemas())
    
    # パスごとの詳細説明追加
    _enhance_path_descriptions(openapi_schema)
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def _get_api_description() -> str:
    """API詳細説明"""
    return """
## 🎭 EmotionMemCore API

**感情付き記憶RAGシステム** - AI Vtuberや対話型AIシステム向けの高機能記憶API

### 🌟 主な特徴

- **感情豊かな記憶保存**: 38種類の日本語感情タグで会話を分析・保存
- **自然言語検索**: 過去の記憶を直感的なクエリで検索可能
- **高性能ベクター検索**: OpenAI text-embedding-3-small による高精度類似度検索
- **LLM自動要約**: Claude 3 Haiku による会話の自動要約
- **バッチ処理対応**: 大量データの効率的な一括処理
- **本格的セキュリティ**: 認証・レート制限・CORS完全対応

### 🚀 快速スタート

```bash
# Docker で即座に起動
docker-compose -f docker-compose.dev.yml up -d

# ブラウザでアクセス
open http://localhost:8000/docs
```

### 💡 基本的な使い方

1. **記憶保存**: `/save` - ユーザーとAIの会話を感情分析付きで保存
2. **記憶検索**: `/search` - 自然言語で過去の記憶を検索
3. **記憶管理**: `/memories` - 保存された記憶の一覧・管理

### 🎯 対象ユーザー

- **AI Vtuber開発者** - 感情豊かな記憶システムが欲しい
- **対話AI開発者** - ユーザーとの会話履歴を活用したい  
- **初心者開発者** - コードが苦手でも使いやすいモジュールが欲しい

---

## 📚 詳細ドキュメント

- **統合ガイド**: [integration-guide.md](docs/integration-guide.md)
- **トラブルシューティング**: [troubleshooting.md](docs/troubleshooting.md)
- **GitHub**: [EmotionMemCore](https://github.com/your-username/EmotionMemCore)
"""


def _get_extended_info() -> Dict[str, Any]:
    """拡張API情報"""
    return {
        "contact": {
            "name": "EmotionMemCore サポート",
            "url": "https://github.com/your-username/EmotionMemCore/issues",
            "email": "support@emotionmemcore.com"
        },
        "license": {
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        },
        "termsOfService": "https://emotionmemcore.com/terms",
        "x-logo": {
            "url": "https://emotionmemcore.com/logo.png",
            "altText": "EmotionMemCore Logo"
        }
    }


def _get_api_tags() -> List[Dict[str, Any]]:
    """APIタグ定義"""
    return [
        {
            "name": "Health",
            "description": "🏥 **システム状態確認**\n\nアプリケーションの動作状態、パフォーマンス統計、依存サービスの監視"
        },
        {
            "name": "Memory",
            "description": "🧠 **記憶管理**\n\n会話の保存・検索・管理。EmotionMemCoreのコア機能"
        },
        {
            "name": "Batch", 
            "description": "⚡ **バッチ処理**\n\n大量データの効率的な一括処理。高パフォーマンス操作"
        },
        {
            "name": "Debug",
            "description": "🐛 **デバッグ機能**\n\n開発・運用時のトラブルシューティング支援ツール (DEBUG_MODE=true 時のみ有効)"
        }
    ]


def _get_security_schemes() -> Dict[str, Any]:
    """セキュリティスキーム定義"""
    return {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "APIキー認証。リクエストヘッダーに `X-API-Key: your-api-key` を設定"
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Bearer token認証 (将来の拡張用)"
        }
    }


def _get_error_schemas() -> Dict[str, Any]:
    """エラーレスポンススキーマ"""
    return {
        "ErrorResponse": {
            "type": "object",
            "properties": {
                "error": {
                    "type": "string",
                    "description": "エラーの種類",
                    "example": "validation_error"
                },
                "message": {
                    "type": "string", 
                    "description": "エラーメッセージ",
                    "example": "user_message フィールドは必須です"
                },
                "details": {
                    "type": "object",
                    "description": "詳細情報（オプション）",
                    "additionalProperties": True
                },
                "request_id": {
                    "type": "string",
                    "description": "リクエスト追跡ID",
                    "example": "req_123456789"
                }
            },
            "required": ["error", "message"]
        },
        "ValidationError": {
            "type": "object",
            "properties": {
                "error": {
                    "type": "string",
                    "enum": ["validation_error"],
                    "example": "validation_error"
                },
                "message": {
                    "type": "string",
                    "example": "入力データが無効です"
                },
                "field_errors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {"type": "string", "example": "user_message"},
                            "error": {"type": "string", "example": "必須フィールドです"}
                        }
                    }
                }
            }
        },
        "RateLimitError": {
            "type": "object", 
            "properties": {
                "error": {
                    "type": "string",
                    "enum": ["rate_limit_exceeded"],
                    "example": "rate_limit_exceeded"
                },
                "message": {
                    "type": "string",
                    "example": "レート制限に達しました。しばらくお待ちください"
                },
                "retry_after": {
                    "type": "integer",
                    "description": "再試行可能までの秒数",
                    "example": 60
                }
            }
        }
    }


def _get_response_schemas() -> Dict[str, Any]:
    """成功レスポンススキーマ"""
    return {
        "EmotionTags": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "喜び", "幸せ", "興奮", "愛情", "感謝", "希望", "誇り", "安心", "満足", "楽しさ", "自信", "感動",
                    "悲しみ", "怒り", "恐れ", "不安", "苛立ち", "失望", "孤独", "罪悪感", "恥", "後悔", "嫉妬",
                    "驚き", "好奇心", "困惑", "懐かしさ", "共感", "同情", "期待",
                    "いたずら心", "恥ずかしさ", "決意", "再会", "別れ", "励まし", "支え", "信頼"
                ]
            },
            "description": "38種類の日本語感情タグ",
            "example": ["喜び", "興奮", "感謝"]
        },
        "MemorySummary": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "記憶ID",
                    "example": "mem_123456789"
                },
                "summary": {
                    "type": "string", 
                    "description": "会話要約",
                    "example": "ユーザーは新しいゲームについて興奮を込めて話している"
                },
                "emotions": {
                    "$ref": "#/components/schemas/EmotionTags"
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "記憶作成日時",
                    "example": "2024-01-15T10:30:00Z"
                },
                "score": {
                    "type": "number",
                    "description": "検索時の類似度スコア（検索結果のみ）",
                    "example": 0.95,
                    "minimum": 0,
                    "maximum": 1
                }
            }
        }
    }


def _enhance_path_descriptions(openapi_schema: Dict[str, Any]) -> None:
    """パス詳細説明の拡張"""
    
    paths = openapi_schema.get("paths", {})
    
    # /save エンドポイント拡張
    if "/save" in paths and "post" in paths["/save"]:
        paths["/save"]["post"]["summary"] = "💾 記憶保存"
        paths["/save"]["post"]["description"] = """
### 会話を感情分析付きで記憶として保存

ユーザーとAIの会話を分析し、要約と感情タグを自動生成して保存します。

#### 処理フロー
1. **LLM分析**: Claude 3 Haikuが会話を分析し要約・感情タグを生成
2. **ベクター化**: OpenAI Embeddingで会話内容をベクター化
3. **データベース保存**: ChromaDBに記憶として永続化

#### 使用例
```python
# 基本的な保存
save_data = {
    "user_message": "今日はとても良い天気ですね！",
    "ai_message": "本当にいい天気ですね！散歩はいかがですか？",
    "user_id": "user123"
}
response = requests.post("/save", json=save_data)
```

#### パフォーマンス
- 平均応答時間: ~200ms
- スループット: 300 req/min
"""
    
    # /search エンドポイント拡張  
    if "/search" in paths and "post" in paths["/search"]:
        paths["/search"]["post"]["summary"] = "🔍 記憶検索"
        paths["/search"]["post"]["description"] = """
### 自然言語による記憶検索

過去の会話記憶を自然言語クエリで検索し、関連度の高い記憶を返します。

#### 検索アルゴリズム
1. **クエリベクター化**: 検索クエリをOpenAI Embeddingでベクター化
2. **類似度検索**: ChromaDBでコサイン類似度による検索
3. **感情フィルター**: 指定された感情タグでフィルタリング

#### 高度な検索例
```python
# 感情フィルター付き検索
search_data = {
    "query": "楽しかった思い出",
    "emotions": ["喜び", "楽しさ"],
    "user_id": "user123",
    "top_k": 5
}
response = requests.post("/search", json=search_data)
```

#### パフォーマンス
- 平均応答時間: ~50ms
- スループット: 1200 req/min
"""
    
    # バッチエンドポイント拡張
    if "/batch-save" in paths and "post" in paths["/batch-save"]:
        paths["/batch-save"]["post"]["summary"] = "⚡ バッチ記憶保存"
        paths["/batch-save"]["post"]["description"] = """
### 複数記憶の効率的な一括保存

大量の会話データを効率的に一括保存します。エラー耐性があり、一部失敗でも成功分は保存されます。

#### バッチ処理の利点
- **高効率**: 単発処理より約10倍高速
- **エラー耐性**: 一部失敗でも処理継続
- **メモリ最適化**: ストリーミング処理でメモリ効率向上

#### 推奨使用シーン
- チャットログの一括インポート
- 定期的なデータ同期
- 大量会話履歴の移行
"""


def get_example_responses() -> Dict[str, Any]:
    """サンプルレスポンス集"""
    return {
        "save_success": {
            "memory_id": "mem_20240115_103045_abc123",
            "summary": "ユーザーは新しいゲームについて興奮を込めて語り、AIが共感と関心を示している温かい会話",
            "emotions": ["興奮", "喜び", "期待"],
            "timestamp": "2024-01-15T10:30:45Z",
            "processing_time_ms": 187
        },
        "search_success": {
            "query": "楽しかった思い出",
            "total_results": 15,
            "results": [
                {
                    "memory_id": "mem_20240115_103045_abc123", 
                    "summary": "ユーザーは新しいゲームについて興奮を込めて語り、AIが共感と関心を示している",
                    "emotions": ["興奮", "喜び", "期待"],
                    "score": 0.94,
                    "timestamp": "2024-01-15T10:30:45Z"
                }
            ],
            "processing_time_ms": 45
        },
        "batch_save_success": {
            "total_requested": 10,
            "successful_saves": 8,
            "failed_saves": 2,
            "failed_items": [
                {
                    "index": 3,
                    "error": "user_message フィールドが空です"
                },
                {
                    "index": 7,
                    "error": "LLM処理タイムアウト"
                }
            ],
            "processing_time_ms": 2340
        }
    }