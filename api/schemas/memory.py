"""
記憶関連のスキーマ定義
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator

from .base import BaseSchema, TimestampMixin, MetadataMixin
from .emotion import Emotion


class SaveRequest(BaseSchema, MetadataMixin):
    """記憶保存リクエスト"""
    user: str = Field(..., description="ユーザーの発言")
    ai: str = Field(..., description="AIの応答")
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="対話のタイムスタンプ"
    )
    context_window: Optional[List[Dict[str, str]]] = Field(
        None,
        description="前後の会話文脈（オプション）"
    )
    
    @validator("user", "ai")
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("発言内容は空にできません")
        return v.strip()


class SearchRequest(BaseSchema):
    """記憶検索リクエスト"""
    query: str = Field(..., description="検索クエリ")
    top_k: int = Field(5, ge=1, le=20, description="取得する結果数")
    emotion_filter: Optional[List[Emotion]] = Field(
        None,
        description="感情タグでフィルタリング"
    )
    user_id: Optional[str] = Field(None, description="ユーザーIDでフィルタリング")
    date_from: Optional[datetime] = Field(None, description="期間指定（開始）")
    date_to: Optional[datetime] = Field(None, description="期間指定（終了）")


class Memory(BaseSchema, TimestampMixin, MetadataMixin):
    """記憶データモデル"""
    id: UUID = Field(default_factory=uuid4, description="記憶ID")
    summary: str = Field(..., description="LLMによる要約")
    emotions: List[Emotion] = Field(..., description="感情タグリスト")
    original_user: str = Field(..., description="元のユーザー発言")
    original_ai: str = Field(..., description="元のAI応答")
    embedding: Optional[List[float]] = Field(None, description="ベクトル埋め込み")
    
    # デバッグ用メタデータ
    debug_info: Optional[Dict[str, Any]] = Field(
        None,
        description="デバッグ情報（処理時間、LLMレスポンス等）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "summary": "ユーザーが不安を表現し、AIが寄り添った会話",
                "emotions": ["不安", "安心"],
                "original_user": "最近ちょっと不安で…",
                "original_ai": "そばにいるよ、大丈夫。",
                "created_at": "2025-06-22T10:00:00Z"
            }
        }


class SearchResult(BaseSchema):
    """検索結果"""
    memory: Memory = Field(..., description="記憶データ")
    score: float = Field(..., ge=0.0, le=1.0, description="類似度スコア")
    
    class Config:
        json_schema_extra = {
            "example": {
                "memory": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "summary": "ユーザーが不安を表現し、AIが寄り添った会話",
                    "emotions": ["不安", "安心"],
                    "original_user": "最近ちょっと不安で…",
                    "original_ai": "そばにいるよ、大丈夫。",
                    "created_at": "2025-06-22T10:00:00Z"
                },
                "score": 0.93
            }
        }


class SearchResponse(BaseSchema):
    """検索レスポンス"""
    results: List[SearchResult] = Field(..., description="検索結果リスト")
    total_found: int = Field(..., description="見つかった結果の総数")
    query_processed: str = Field(..., description="処理されたクエリ")
    processing_time_ms: Optional[float] = Field(
        None,
        description="処理時間（ミリ秒）"
    )