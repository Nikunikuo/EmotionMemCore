"""
モックLLM実装 - 開発・テスト用
"""

import asyncio
import random
from typing import List, Dict, Any

from .base import BaseLLM, LLMRequest, LLMResponse
from api.schemas import Emotion
from infrastructure.config.logger import get_logger


class MockLLM(BaseLLM):
    """モックLLM - 開発・テスト用"""
    
    def __init__(self, model_config: Dict[str, Any]):
        super().__init__(model_config)
        self.logger = get_logger(__name__)
        
        # 固定パターンの感情マッピング
        self.emotion_patterns = {
            "嬉しい": [Emotion.JOY, Emotion.HAPPINESS],
            "悲しい": [Emotion.SADNESS],
            "不安": [Emotion.ANXIETY, Emotion.FEAR],
            "ありがとう": [Emotion.GRATITUDE],
            "楽しい": [Emotion.AMUSEMENT, Emotion.JOY],
            "怒り": [Emotion.ANGER, Emotion.FRUSTRATION],
            "驚き": [Emotion.SURPRISE],
            "恥ずかしい": [Emotion.SHYNESS, Emotion.SHAME],
            "会えて": [Emotion.REUNION, Emotion.JOY],
            "寂しい": [Emotion.LONELINESS, Emotion.SADNESS],
        }
    
    async def process_memory(self, request: LLMRequest) -> LLMResponse:
        """モック記憶処理 - 固定パターンで要約と感情を生成"""
        
        # 人工的な遅延（リアルなAPI感）
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # 要約生成（簡単なルールベース）
        summary = self._generate_mock_summary(request.user_message, request.ai_message)
        
        # 感情抽出
        emotions = self._extract_mock_emotions(request.user_message + " " + request.ai_message)
        
        # フォールバック感情
        if not emotions:
            emotions = [random.choice(list(Emotion))]
        
        debug_info = {
            "model": "mock-llm",
            "processing_mode": "rule_based",
            "user_length": len(request.user_message),
            "ai_length": len(request.ai_message)
        }
        
        self.logger.info(
            "mock_llm_processed",
            summary_length=len(summary),
            emotions_count=len(emotions),
            user_id=request.user_id
        )
        
        return LLMResponse(
            summary=summary,
            emotions=emotions,
            debug_info=debug_info
        )
    
    def _generate_mock_summary(self, user_msg: str, ai_msg: str) -> str:
        """モック要約生成"""
        
        # 簡単なキーワードベース要約
        if "嬉しい" in user_msg or "楽しい" in user_msg:
            return "ユーザーが喜びを表現し、AIが共感した会話"
        elif "悲しい" in user_msg or "不安" in user_msg:
            return "ユーザーがネガティブな感情を表現し、AIが寄り添った会話"
        elif "ありがとう" in user_msg:
            return "ユーザーが感謝を示し、AIが受け止めた会話"
        elif "質問" in user_msg or "？" in user_msg or "?" in user_msg:
            return "ユーザーの質問にAIが回答した会話"
        elif "おはよう" in user_msg or "こんにちは" in user_msg:
            return "ユーザーとAIが挨拶を交わした会話"
        else:
            return f"ユーザーとAIが{len(user_msg + ai_msg)//10}文字程度の会話をした"
    
    def _extract_mock_emotions(self, text: str) -> List[Emotion]:
        """モック感情抽出"""
        emotions = []
        
        # パターンマッチング
        for keyword, emotion_list in self.emotion_patterns.items():
            if keyword in text:
                emotions.extend(emotion_list)
        
        # 重複除去
        unique_emotions = list(set(emotions))
        
        # 最大3個まで
        return unique_emotions[:3]
    
    async def health_check(self) -> bool:
        """モックヘルスチェック - 常に成功"""
        await asyncio.sleep(0.01)  # 微小な遅延
        return True