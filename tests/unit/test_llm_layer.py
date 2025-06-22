"""
LLM層の単体テスト
"""

import pytest
from unittest.mock import AsyncMock, patch

from core.llm.base import LLMRequest, LLMResponse, LLMError
from core.llm.mock import MockLLM
from core.llm.claude import ClaudeLLM
from core.llm.prompts import PromptTemplate
from api.schemas.emotion import Emotion


@pytest.mark.unit
class TestMockLLM:
    """MockLLMテスト"""
    
    def test_init(self):
        """初期化テスト"""
        llm = MockLLM()
        assert llm.model == "mock-llm"
        assert llm.processing_delay == 0.1
    
    @pytest.mark.asyncio
    async def test_process_memory_basic(self):
        """基本的な記憶処理テスト"""
        llm = MockLLM()
        
        request = LLMRequest(
            user_message="今日はいい天気ですね！",
            ai_message="そうですね！お散歩日和で気持ちがいいですね。"
        )
        
        response = await llm.process_memory(request)
        
        assert isinstance(response, LLMResponse)
        assert len(response.summary) > 0
        assert len(response.emotions) > 0
        assert all(isinstance(emotion, Emotion) for emotion in response.emotions)
    
    @pytest.mark.asyncio
    async def test_process_memory_with_context(self):
        """文脈付き記憶処理テスト"""
        llm = MockLLM()
        
        request = LLMRequest(
            user_message="ありがとうございます！",
            ai_message="どういたしまして。お役に立てて嬉しいです。",
            context_window=[
                {"role": "user", "content": "手伝ってもらえますか？"},
                {"role": "assistant", "content": "もちろんです！何をお手伝いしましょうか？"}
            ]
        )
        
        response = await llm.process_memory(request)
        
        assert isinstance(response, LLMResponse)
        assert len(response.summary) > 0
        assert len(response.emotions) > 0
    
    @pytest.mark.asyncio
    async def test_process_memory_empty_input(self):
        """空入力テスト"""
        llm = MockLLM()
        
        request = LLMRequest(
            user_message="",
            ai_message=""
        )
        
        with pytest.raises(LLMError):
            await llm.process_memory(request)
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """ヘルスチェックテスト"""
        llm = MockLLM()
        result = await llm.health_check()
        assert result is True


@pytest.mark.unit
class TestClaudeLLM:
    """ClaudeLLMテスト"""
    
    def test_init_with_api_key(self):
        """APIキー付き初期化テスト"""
        api_key = "test-api-key"
        llm = ClaudeLLM(api_key=api_key)
        
        assert llm.api_key == api_key
        assert llm.model == "claude-3-haiku-20240307"
        assert llm.client is not None
    
    def test_init_without_api_key(self):
        """APIキーなし初期化テスト"""
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not found"):
            ClaudeLLM(api_key=None)
    
    @pytest.mark.asyncio
    async def test_process_memory_mock_response(self):
        """モックレスポンスによる記憶処理テスト"""
        llm = ClaudeLLM(api_key="test-key")
        
        # Anthropic APIのモック
        mock_response = AsyncMock()
        mock_response.content = [
            AsyncMock(text="要約: ユーザーが天気について話した\n感情: 喜び、期待")
        ]
        
        with patch.object(llm.client.messages, 'create', return_value=mock_response):
            request = LLMRequest(
                user_message="今日はいい天気ですね！",
                ai_message="そうですね！お散歩日和で気持ちがいいですね。"
            )
            
            response = await llm.process_memory(request)
            
            assert isinstance(response, LLMResponse)
            assert "天気について話した" in response.summary
            assert len(response.emotions) > 0
    
    @pytest.mark.asyncio
    async def test_health_check_mock(self):
        """モックヘルスチェックテスト"""
        llm = ClaudeLLM(api_key="test-key")
        
        mock_response = AsyncMock()
        mock_response.content = [AsyncMock(text="要約: ヘルスチェック\n感情: なし")]
        
        with patch.object(llm.client.messages, 'create', return_value=mock_response):
            result = await llm.health_check()
            assert result is True


@pytest.mark.unit
class TestPromptTemplate:
    """PromptTemplateテスト"""
    
    def test_init(self):
        """初期化テスト"""
        template = PromptTemplate()
        
        assert template.memory_prompt_template is not None
        assert template.search_prompt_template is not None
        assert "要約" in template.memory_prompt_template
        assert "感情" in template.memory_prompt_template
    
    def test_build_memory_prompt_basic(self):
        """基本的な記憶プロンプト構築テスト"""
        template = PromptTemplate()
        
        prompt = template.build_memory_prompt(
            user_message="こんにちは",
            ai_message="こんにちは！元気ですか？"
        )
        
        assert "こんにちは" in prompt
        assert "こんにちは！元気ですか？" in prompt
        assert "要約" in prompt
        assert "感情" in prompt
    
    def test_build_memory_prompt_with_context(self):
        """文脈付き記憶プロンプト構築テスト"""
        template = PromptTemplate()
        
        context = [
            {"role": "user", "content": "前の質問です"},
            {"role": "assistant", "content": "前の回答です"}
        ]
        
        prompt = template.build_memory_prompt(
            user_message="新しい質問",
            ai_message="新しい回答",
            context_window=context
        )
        
        assert "新しい質問" in prompt
        assert "新しい回答" in prompt
        assert "前の質問です" in prompt
        assert "前の回答です" in prompt
        assert "会話の文脈" in prompt
    
    def test_build_search_prompt(self):
        """検索プロンプト構築テスト"""
        template = PromptTemplate()
        
        prompt = template.build_search_prompt("天気について教えて")
        
        assert "天気について教えて" in prompt
        assert "キーワード" in prompt
    
    def test_get_system_prompt(self):
        """システムプロンプト取得テスト"""
        template = PromptTemplate()
        
        system_prompt = template.get_system_prompt()
        
        assert "AI Vtuber" in system_prompt
        assert "感情記憶システム" in system_prompt
    
    def test_customize_prompt_with_emotions(self):
        """カスタム感情付きプロンプトテスト"""
        template = PromptTemplate()
        
        custom_emotions = ["カスタム感情1", "カスタム感情2"]
        
        customized = template.customize_prompt(
            template_type="memory",
            custom_emotions=custom_emotions
        )
        
        assert "カスタム感情1" in customized
        assert "カスタム感情2" in customized
        assert "カスタム感情" in customized
    
    def test_customize_prompt_with_instructions(self):
        """カスタム指示付きプロンプトテスト"""
        template = PromptTemplate()
        
        custom_instructions = "特別な指示です"
        
        customized = template.customize_prompt(
            template_type="memory",
            custom_instructions=custom_instructions
        )
        
        assert "特別な指示です" in customized
        assert "追加指示" in customized
    
    def test_get_validation_prompt(self):
        """検証プロンプト取得テスト"""
        template = PromptTemplate()
        
        validation_prompt = template.get_validation_prompt(
            summary="テスト要約",
            emotions=["喜び", "期待"]
        )
        
        assert "テスト要約" in validation_prompt
        assert "喜び" in validation_prompt
        assert "期待" in validation_prompt
        assert "チェック項目" in validation_prompt


@pytest.mark.unit
class TestLLMRequest:
    """LLMRequestテスト"""
    
    def test_create_basic(self):
        """基本作成テスト"""
        request = LLMRequest(
            user_message="テストメッセージ",
            ai_message="テスト回答"
        )
        
        assert request.user_message == "テストメッセージ"
        assert request.ai_message == "テスト回答"
        assert request.context_window is None
        assert request.user_id is None
        assert request.session_id is None
    
    def test_create_with_optional_fields(self):
        """オプション項目付き作成テスト"""
        context = [{"role": "user", "content": "前の会話"}]
        
        request = LLMRequest(
            user_message="テストメッセージ",
            ai_message="テスト回答",
            context_window=context,
            user_id="test_user",
            session_id="test_session"
        )
        
        assert request.context_window == context
        assert request.user_id == "test_user"
        assert request.session_id == "test_session"


@pytest.mark.unit
class TestLLMResponse:
    """LLMResponseテスト"""
    
    def test_create_basic(self):
        """基本作成テスト"""
        emotions = [Emotion.JOY, Emotion.HOPE]
        
        response = LLMResponse(
            summary="テスト要約",
            emotions=emotions
        )
        
        assert response.summary == "テスト要約"
        assert response.emotions == emotions
        assert len(response.emotions) == 2
    
    def test_create_empty_emotions(self):
        """空感情リストテスト"""
        response = LLMResponse(
            summary="テスト要約",
            emotions=[]
        )
        
        assert response.summary == "テスト要約"
        assert response.emotions == []


@pytest.mark.unit
class TestLLMErrors:
    """LLMエラーテスト"""
    
    def test_llm_error(self):
        """基本LLMエラーテスト"""
        error = LLMError("テストエラー")
        
        assert str(error) == "テストエラー"
        assert isinstance(error, Exception)
    
    def test_llm_error_inheritance(self):
        """LLMエラー継承テスト"""
        from core.llm.base import LLMTimeoutError, LLMQuotaError
        
        timeout_error = LLMTimeoutError("タイムアウト")
        quota_error = LLMQuotaError("クォータ超過")
        
        assert isinstance(timeout_error, LLMError)
        assert isinstance(quota_error, LLMError)
        assert str(timeout_error) == "タイムアウト"
        assert str(quota_error) == "クォータ超過"