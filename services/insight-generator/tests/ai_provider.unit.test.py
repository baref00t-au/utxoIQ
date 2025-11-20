"""
Unit tests for AI Provider Module

Tests the abstract base class, all provider implementations,
factory pattern, and error handling.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from dataclasses import asdict

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ai_provider import (
    AIProvider,
    AIProviderType,
    AIProviderError,
    AIProviderFactory,
    InsightContent,
    Signal,
    VertexAIProvider,
    OpenAIProvider,
    AnthropicProvider,
    GrokProvider,
    get_configured_provider
)


# Test Fixtures

@pytest.fixture
def sample_signal():
    """Sample signal for testing"""
    return Signal(
        signal_id="test-signal-123",
        signal_type="mempool",
        block_height=800000,
        confidence=0.85,
        metadata={
            "fee_rate_median": 50.5,
            "fee_rate_change_pct": 25.3,
            "tx_count": 15000,
            "mempool_size_mb": 120.5,
            "comparison_window": "1h"
        }
    )


@pytest.fixture
def sample_prompt_template():
    """Sample prompt template"""
    return """
    Analyze this mempool signal:
    - Fee Rate: {fee_rate_median} sat/vB
    - Change: {fee_rate_change_pct}%
    - TX Count: {tx_count}
    
    Respond with JSON containing headline, summary, confidence_explanation.
    """


@pytest.fixture
def sample_ai_response():
    """Sample AI response JSON"""
    return {
        "headline": "Bitcoin Fees Surge 25% as Mempool Congestion Increases",
        "summary": "Transaction fees have jumped significantly in the past hour, "
                   "indicating increased network demand. Users should expect "
                   "higher costs for priority transactions.",
        "confidence_explanation": "High confidence based on consistent fee rate "
                                  "increase across multiple blocks and growing "
                                  "mempool size."
    }


# Test AIProvider Abstract Base Class

class TestAIProviderBase:
    """Test abstract base class functionality"""
    
    def test_format_prompt_success(self, sample_signal, sample_prompt_template):
        """Test successful prompt formatting"""
        # Create a concrete implementation for testing
        class TestProvider(AIProvider):
            async def generate_insight(self, signal, prompt_template):
                pass
        
        provider = TestProvider({})
        formatted = provider._format_prompt(sample_signal, sample_prompt_template)
        
        assert "50.5 sat/vB" in formatted
        assert "25.3%" in formatted
        assert "15000" in formatted
    
    def test_format_prompt_missing_field(self, sample_signal):
        """Test prompt formatting with missing metadata field"""
        class TestProvider(AIProvider):
            async def generate_insight(self, signal, prompt_template):
                pass
        
        provider = TestProvider({})
        template = "Missing field: {nonexistent_field}"
        
        with pytest.raises(AIProviderError) as exc_info:
            provider._format_prompt(sample_signal, template)
        
        assert "Missing metadata field" in str(exc_info.value)
    
    def test_parse_json_response_success(self, sample_ai_response):
        """Test successful JSON response parsing"""
        class TestProvider(AIProvider):
            async def generate_insight(self, signal, prompt_template):
                pass
        
        provider = TestProvider({})
        response_text = json.dumps(sample_ai_response)
        
        content = provider._parse_json_response(response_text)
        
        assert isinstance(content, InsightContent)
        assert content.headline == sample_ai_response["headline"]
        assert content.summary == sample_ai_response["summary"]
        assert content.confidence_explanation == sample_ai_response["confidence_explanation"]
    
    def test_parse_json_response_invalid_json(self):
        """Test JSON parsing with invalid JSON"""
        class TestProvider(AIProvider):
            async def generate_insight(self, signal, prompt_template):
                pass
        
        provider = TestProvider({})
        
        with pytest.raises(AIProviderError) as exc_info:
            provider._parse_json_response("not valid json")
        
        assert "Invalid JSON response" in str(exc_info.value)
    
    def test_parse_json_response_missing_fields(self):
        """Test JSON parsing with missing required fields"""
        class TestProvider(AIProvider):
            async def generate_insight(self, signal, prompt_template):
                pass
        
        provider = TestProvider({})
        incomplete_response = json.dumps({"headline": "Test"})
        
        with pytest.raises(AIProviderError) as exc_info:
            provider._parse_json_response(incomplete_response)
        
        assert "Missing required fields" in str(exc_info.value)


# Test VertexAIProvider

class TestVertexAIProvider:
    """Test Vertex AI provider implementation"""
    
    @patch('ai_provider.aiplatform')
    @patch('ai_provider.GenerativeModel')
    def test_initialization_success(self, mock_model, mock_aiplatform):
        """Test successful Vertex AI initialization"""
        config = {
            "project_id": "test-project",
            "location": "us-central1",
            "model": "gemini-pro"
        }
        
        provider = VertexAIProvider(config)
        
        assert provider.project_id == "test-project"
        assert provider.location == "us-central1"
        assert provider.model_name == "gemini-pro"
        mock_aiplatform.init.assert_called_once()
    
    @patch('ai_provider.aiplatform')
    @patch('ai_provider.GenerativeModel')
    @pytest.mark.asyncio
    async def test_generate_insight_success(
        self,
        mock_model_class,
        mock_aiplatform,
        sample_signal,
        sample_prompt_template,
        sample_ai_response
    ):
        """Test successful insight generation with Vertex AI"""
        # Setup mock
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps(sample_ai_response)
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        config = {
            "project_id": "test-project",
            "location": "us-central1",
            "model": "gemini-pro"
        }
        
        provider = VertexAIProvider(config)
        provider.model = mock_model
        
        # Generate insight
        content = await provider.generate_insight(sample_signal, sample_prompt_template)
        
        assert isinstance(content, InsightContent)
        assert content.headline == sample_ai_response["headline"]
        mock_model.generate_content.assert_called_once()


# Test OpenAIProvider

class TestOpenAIProvider:
    """Test OpenAI provider implementation"""
    
    @patch('ai_provider.openai.AsyncOpenAI')
    def test_initialization_success(self, mock_openai):
        """Test successful OpenAI initialization"""
        config = {
            "api_key": "sk-test-key",
            "model": "gpt-4-turbo"
        }
        
        provider = OpenAIProvider(config)
        
        assert provider.api_key == "sk-test-key"
        assert provider.model == "gpt-4-turbo"
        mock_openai.assert_called_once()
    
    def test_initialization_missing_api_key(self):
        """Test OpenAI initialization without API key"""
        config = {"model": "gpt-4-turbo"}
        
        with pytest.raises(AIProviderError) as exc_info:
            OpenAIProvider(config)
        
        assert "API key not provided" in str(exc_info.value)
    
    @patch('ai_provider.openai.AsyncOpenAI')
    @pytest.mark.asyncio
    async def test_generate_insight_success(
        self,
        mock_openai_class,
        sample_signal,
        sample_prompt_template,
        sample_ai_response
    ):
        """Test successful insight generation with OpenAI"""
        # Setup mock
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(sample_ai_response)
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        config = {
            "api_key": "sk-test-key",
            "model": "gpt-4-turbo"
        }
        
        provider = OpenAIProvider(config)
        
        # Generate insight
        content = await provider.generate_insight(sample_signal, sample_prompt_template)
        
        assert isinstance(content, InsightContent)
        assert content.headline == sample_ai_response["headline"]
        mock_client.chat.completions.create.assert_called_once()


# Test AnthropicProvider

class TestAnthropicProvider:
    """Test Anthropic provider implementation"""
    
    @patch('ai_provider.anthropic.AsyncAnthropic')
    def test_initialization_success(self, mock_anthropic):
        """Test successful Anthropic initialization"""
        config = {
            "api_key": "sk-ant-test-key",
            "model": "claude-3-opus-20240229"
        }
        
        provider = AnthropicProvider(config)
        
        assert provider.api_key == "sk-ant-test-key"
        assert provider.model == "claude-3-opus-20240229"
        mock_anthropic.assert_called_once()
    
    @patch('ai_provider.anthropic.AsyncAnthropic')
    @pytest.mark.asyncio
    async def test_generate_insight_success(
        self,
        mock_anthropic_class,
        sample_signal,
        sample_prompt_template,
        sample_ai_response
    ):
        """Test successful insight generation with Anthropic"""
        # Setup mock
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = json.dumps(sample_ai_response)
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        config = {
            "api_key": "sk-ant-test-key",
            "model": "claude-3-opus-20240229"
        }
        
        provider = AnthropicProvider(config)
        
        # Generate insight
        content = await provider.generate_insight(sample_signal, sample_prompt_template)
        
        assert isinstance(content, InsightContent)
        assert content.headline == sample_ai_response["headline"]
        mock_client.messages.create.assert_called_once()


# Test GrokProvider

class TestGrokProvider:
    """Test Grok provider implementation"""
    
    def test_initialization_success(self):
        """Test successful Grok initialization"""
        config = {
            "api_key": "xai-test-key",
            "model": "grok-beta",
            "api_base": "https://api.x.ai/v1"
        }
        
        provider = GrokProvider(config)
        
        assert provider.api_key == "xai-test-key"
        assert provider.model == "grok-beta"
        assert provider.api_base == "https://api.x.ai/v1"
    
    @pytest.mark.asyncio
    async def test_generate_insight_success(
        self,
        sample_signal,
        sample_prompt_template,
        sample_ai_response
    ):
        """Test successful insight generation with Grok"""
        config = {
            "api_key": "xai-test-key",
            "model": "grok-beta"
        }
        
        provider = GrokProvider(config)
        
        # Mock HTTP client
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps(sample_ai_response)
                }
            }]
        }
        provider.client.post = AsyncMock(return_value=mock_response)
        
        # Generate insight
        content = await provider.generate_insight(sample_signal, sample_prompt_template)
        
        assert isinstance(content, InsightContent)
        assert content.headline == sample_ai_response["headline"]
        provider.client.post.assert_called_once()


# Test AIProviderFactory

class TestAIProviderFactory:
    """Test AI provider factory"""
    
    @patch('ai_provider.aiplatform')
    @patch('ai_provider.GenerativeModel')
    def test_create_vertex_ai_provider(self, mock_model, mock_aiplatform):
        """Test creating Vertex AI provider"""
        config = {
            "project_id": "test-project",
            "location": "us-central1",
            "model": "gemini-pro"
        }
        
        provider = AIProviderFactory.create_provider("vertex_ai", config)
        
        assert isinstance(provider, VertexAIProvider)
        assert provider.project_id == "test-project"
    
    @patch('ai_provider.openai.AsyncOpenAI')
    def test_create_openai_provider(self, mock_openai):
        """Test creating OpenAI provider"""
        config = {
            "api_key": "sk-test-key",
            "model": "gpt-4-turbo"
        }
        
        provider = AIProviderFactory.create_provider("openai", config)
        
        assert isinstance(provider, OpenAIProvider)
        assert provider.api_key == "sk-test-key"
    
    @patch('ai_provider.anthropic.AsyncAnthropic')
    def test_create_anthropic_provider(self, mock_anthropic):
        """Test creating Anthropic provider"""
        config = {
            "api_key": "sk-ant-test-key",
            "model": "claude-3-opus-20240229"
        }
        
        provider = AIProviderFactory.create_provider("anthropic", config)
        
        assert isinstance(provider, AnthropicProvider)
        assert provider.api_key == "sk-ant-test-key"
    
    def test_create_grok_provider(self):
        """Test creating Grok provider"""
        config = {
            "api_key": "xai-test-key",
            "model": "grok-beta"
        }
        
        provider = AIProviderFactory.create_provider("grok", config)
        
        assert isinstance(provider, GrokProvider)
        assert provider.api_key == "xai-test-key"
    
    def test_create_invalid_provider(self):
        """Test creating provider with invalid type"""
        with pytest.raises(AIProviderError) as exc_info:
            AIProviderFactory.create_provider("invalid_provider", {})
        
        assert "Invalid provider type" in str(exc_info.value)
    
    @patch.dict(os.environ, {
        "VERTEX_AI_PROJECT": "test-project",
        "VERTEX_AI_LOCATION": "us-central1",
        "VERTEX_AI_MODEL": "gemini-pro"
    })
    @patch('ai_provider.aiplatform')
    @patch('ai_provider.GenerativeModel')
    def test_load_config_from_env_vertex_ai(self, mock_model, mock_aiplatform):
        """Test loading Vertex AI config from environment"""
        provider = AIProviderFactory.create_provider("vertex_ai")
        
        assert isinstance(provider, VertexAIProvider)
        assert provider.project_id == "test-project"
    
    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "sk-test-key",
        "OPENAI_MODEL": "gpt-4-turbo"
    })
    @patch('ai_provider.openai.AsyncOpenAI')
    def test_load_config_from_env_openai(self, mock_openai):
        """Test loading OpenAI config from environment"""
        provider = AIProviderFactory.create_provider("openai")
        
        assert isinstance(provider, OpenAIProvider)
        assert provider.api_key == "sk-test-key"


# Test get_configured_provider

class TestGetConfiguredProvider:
    """Test get_configured_provider function"""
    
    @patch.dict(os.environ, {
        "AI_PROVIDER": "vertex_ai",
        "VERTEX_AI_PROJECT": "test-project",
        "VERTEX_AI_LOCATION": "us-central1"
    })
    @patch('ai_provider.aiplatform')
    @patch('ai_provider.GenerativeModel')
    def test_get_configured_provider_success(self, mock_model, mock_aiplatform):
        """Test getting configured provider from environment"""
        provider = get_configured_provider()
        
        assert isinstance(provider, VertexAIProvider)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_configured_provider_missing_env(self):
        """Test getting provider without AI_PROVIDER env var"""
        with pytest.raises(AIProviderError) as exc_info:
            get_configured_provider()
        
        assert "AI_PROVIDER environment variable not set" in str(exc_info.value)


# Test Error Handling

class TestErrorHandling:
    """Test error handling across all providers"""
    
    @patch('ai_provider.aiplatform')
    @patch('ai_provider.GenerativeModel')
    @pytest.mark.asyncio
    async def test_vertex_ai_generation_error(
        self,
        mock_model_class,
        mock_aiplatform,
        sample_signal,
        sample_prompt_template
    ):
        """Test Vertex AI error handling"""
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_model_class.return_value = mock_model
        
        config = {
            "project_id": "test-project",
            "location": "us-central1",
            "model": "gemini-pro"
        }
        
        provider = VertexAIProvider(config)
        provider.model = mock_model
        
        with pytest.raises(AIProviderError) as exc_info:
            await provider.generate_insight(sample_signal, sample_prompt_template)
        
        assert "Vertex AI generation failed" in str(exc_info.value)
    
    @patch('ai_provider.openai.AsyncOpenAI')
    @pytest.mark.asyncio
    async def test_openai_generation_error(
        self,
        mock_openai_class,
        sample_signal,
        sample_prompt_template
    ):
        """Test OpenAI error handling"""
        mock_client = AsyncMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        
        config = {
            "api_key": "sk-test-key",
            "model": "gpt-4-turbo"
        }
        
        provider = OpenAIProvider(config)
        
        with pytest.raises(AIProviderError) as exc_info:
            await provider.generate_insight(sample_signal, sample_prompt_template)
        
        assert "OpenAI generation failed" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
