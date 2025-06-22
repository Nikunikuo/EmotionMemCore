"""
LLM抽象化基底クラス
Claude/GPT切り替え可能な設計
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from api.schemas import Emotion


@dataclass
class LLMResponse:
    """LLMレスポンス結果"""
    summary: str
    emotions: List[Emotion]
    debug_info: Optional[Dict[str, Any]] = None


@dataclass
class LLMRequest:
    """LLM処理リクエスト"""
    user_message: str
    ai_message: str
    context_window: Optional[List[Dict[str, str]]] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class BaseLLM(ABC):
    """LLM抽象化基底クラス"""
    
    def __init__(self, model_config: Dict[str, Any]):
        self.model_config = model_config
        self.model_name = model_config.get("model", "unknown")
        self.max_tokens = model_config.get("max_tokens", 500)
        self.temperature = model_config.get("temperature", 0.3)
    
    @abstractmethod
    async def process_memory(self, request: LLMRequest) -> LLMResponse:
        """
        会話を記憶として処理
        
        Args:
            request: LLM処理リクエスト
            
        Returns:
            LLMResponse: 要約と感情タグを含むレスポンス
            
        Raises:
            LLMError: LLM処理エラー
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        LLMサービスのヘルスチェック
        
        Returns:
            bool: サービスが利用可能かどうか
        """
        pass
    
    def _extract_emotions(self, emotion_text: str) -> List[Emotion]:
        """感情テキストから感情Enumリストを抽出"""
        emotions = []
        
        # 日本語感情タグをパース
        for emotion in Emotion:
            if emotion.value in emotion_text:
                emotions.append(emotion)
        
        # 重複除去と上限制御
        unique_emotions = list(set(emotions))
        return unique_emotions[:5]  # 最大5個まで
    
    def _validate_response(self, summary: str, emotions: List[Emotion]) -> bool:
        """レスポンスの妥当性チェック"""
        if not summary or len(summary.strip()) < 10:
            return False
        
        if not emotions:
            return False
            
        if len(summary) > 300:  # 要約が長すぎる
            return False
            
        return True


class LLMError(Exception):
    """LLM処理エラー"""
    
    def __init__(self, message: str, provider: str = "unknown", error_code: Optional[str] = None):
        self.message = message
        self.provider = provider
        self.error_code = error_code
        super().__init__(f"[{provider}] {message}")


class LLMTimeoutError(LLMError):
    """LLMタイムアウトエラー"""
    pass


class LLMQuotaError(LLMError):
    """LLMクォータエラー"""
    pass