"""
Claude LLM実装
"""

import os
import time
from typing import List, Dict, Any, Optional
import asyncio

import anthropic
from anthropic import AsyncAnthropic

from .base import BaseLLM, LLMRequest, LLMResponse, LLMError, LLMTimeoutError, LLMQuotaError
from .prompts import PromptTemplate
from api.schemas import Emotion
from infrastructure.config.logger import get_logger


class ClaudeLLM(BaseLLM):
    """Claude LLM実装クラス"""
    
    def __init__(self, model_config: Dict[str, Any]):
        super().__init__(model_config)
        
        self.logger = get_logger(__name__)
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            raise LLMError("ANTHROPIC_API_KEY not found", provider="claude")
        
        self.client = AsyncAnthropic(api_key=self.api_key)
        self.prompt_template = PromptTemplate()
        
        # デバッグモード
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        
    async def process_memory(self, request: LLMRequest) -> LLMResponse:
        """Claudeで会話を記憶処理"""
        start_time = time.time()
        
        try:
            # プロンプト生成
            prompt = self.prompt_template.build_memory_prompt(
                user_message=request.user_message,
                ai_message=request.ai_message,
                context_window=request.context_window
            )
            
            self.logger.info(
                "claude_request_started",
                model=self.model_name,
                user_id=request.user_id,
                session_id=request.session_id,
                prompt_length=len(prompt)
            )
            
            # Claude API呼び出し
            response = await self._call_claude_api(prompt)
            
            # レスポンス解析
            summary, emotions = self._parse_response(response)
            
            # バリデーション
            if not self._validate_response(summary, emotions):
                raise LLMError("Invalid response format", provider="claude")
            
            processing_time = (time.time() - start_time) * 1000
            
            debug_info = None
            if self.debug_mode:
                debug_info = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "raw_response": response,
                    "processing_time_ms": processing_time,
                    "token_usage": getattr(response, "usage", None)
                }
            
            self.logger.info(
                "claude_request_completed",
                processing_time_ms=processing_time,
                summary_length=len(summary),
                emotions_count=len(emotions)
            )
            
            return LLMResponse(
                summary=summary,
                emotions=emotions,
                debug_info=debug_info
            )
            
        except anthropic.APITimeoutError as e:
            self.logger.error("claude_timeout_error", error=str(e))
            raise LLMTimeoutError("Claude API timeout", provider="claude")
            
        except anthropic.RateLimitError as e:
            self.logger.error("claude_quota_error", error=str(e))
            raise LLMQuotaError("Claude API rate limit exceeded", provider="claude")
            
        except Exception as e:
            self.logger.error("claude_unexpected_error", error=str(e))
            raise LLMError(f"Claude processing failed: {str(e)}", provider="claude")
    
    async def _call_claude_api(self, prompt: str) -> str:
        """Claude APIを呼び出し"""
        try:
            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            self.logger.error("claude_api_error", error=str(e))
            raise
    
    def _parse_response(self, response: str) -> tuple[str, List[Emotion]]:
        """Claudeレスポンスを解析"""
        lines = response.strip().split("\\n")
        
        summary = ""
        emotions = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("要約:") or line.startswith("## 要約"):
                current_section = "summary"
                summary_text = line.replace("要約:", "").replace("## 要約", "").strip()
                if summary_text:
                    summary = summary_text
                continue
                
            elif line.startswith("感情:") or line.startswith("## 感情"):
                current_section = "emotions"
                emotion_text = line.replace("感情:", "").replace("## 感情", "").strip()
                if emotion_text:
                    emotions.extend(self._extract_emotions(emotion_text))
                continue
            
            # 継続行の処理
            if current_section == "summary" and line:
                if not summary:
                    summary = line
                else:
                    summary += " " + line
                    
            elif current_section == "emotions" and line:
                emotions.extend(self._extract_emotions(line))
        
        # フォールバック: 構造化されていない場合
        if not summary and not emotions:
            summary = response[:200]  # 最初の200文字を要約として使用
            emotions = self._extract_emotions(response)
        
        return summary.strip(), emotions
    
    async def health_check(self) -> bool:
        """Claudeヘルスチェック"""
        try:
            # 簡単なテストリクエスト
            test_response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=10,
                messages=[
                    {
                        "role": "user", 
                        "content": "Hello"
                    }
                ]
            )
            return True
            
        except Exception as e:
            self.logger.error("claude_health_check_failed", error=str(e))
            return False