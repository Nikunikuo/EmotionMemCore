"""
基本スキーマ定義
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class BaseSchema(BaseModel):
    """基底スキーマクラス"""
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class TimestampMixin(BaseModel):
    """タイムスタンプを持つモデルのMixin"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class MetadataMixin(BaseModel):
    """メタデータを持つモデルのMixin"""
    session_id: Optional[str] = Field(None, description="会話セッションID")
    user_id: Optional[str] = Field(None, description="ユーザー識別子")
    app_name: Optional[str] = Field(None, description="連携アプリケーション名")