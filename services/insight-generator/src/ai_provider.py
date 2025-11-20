"""
AI Provider Module for Insight Generation

This module provides an abstract interface for multiple AI providers
(Vertex AI, OpenAI, Anthropic, xAI Grok) to generate insights from signals.

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum

import httpx


logger = logging.getLogger(__name__)


class AIProviderType(Enum):
    """Supported AI provider types"""
    VERTEX_AI = "vertex_ai"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROK = "grok"


@dataclass
class InsightContent:
    """AI-generated insight content"""
    headline: str
    summary: str
    confidence_explanation: str


@dataclass
class Signal:
    """Signal data structure for AI processing"""
    signal_id: str
    signal_type: str
    block_height: int
    confidence: float
    metadata: Dict[str, Any]


class AIProvider(ABC):
    """
    Abstract base class for AI providers.
    
    All AI providers must implement the generate_insight method
    to transform signals into human-readable insights.
    
    Requirements: 8.1, 8.6
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize AI provider with configuration.
        
        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config
        self.provider_name = self.__class__.__name__
    
    @abstractmethod
    async def generate_insight(
        self,
        signal: Signal,
        prompt_template: str
    ) -> InsightContent:
        """
        Generate insight from signal using AI model.
        
        Args:
            signal: Signal data to generate insight from
            prompt_template: Formatted prompt template with placeholders
            
        Returns:
            InsightContent with headline, summary, and confidence explanation
            
        Raises:
            AIProviderError: If generation fails
        """
        pass
    
    def _format_prompt(self, signal: Signal, template: str) -> str:
        """
        Format prompt template with signal metadata.
        
        Args:
            signal: Signal containing metadata
            template: Template string with {field} placeholders
            
        Returns:
            Formatted prompt string
        """
        try:
            return template.format(**signal.metadata)
        except KeyError as e:
            logger.error(
                f"Missing metadata field in prompt template: {e}",
                extra={"signal_id": signal.signal_id}
            )
            raise AIProviderError(f"Missing metadata field: {e}")
    
    def _parse_json_response(self, response_text: str) -> InsightContent:
        """
        Parse JSON response from AI provider.
        
        Args:
            response_text: Raw response text from AI provider
            
        Returns:
            InsightContent parsed from JSON
            
        Raises:
            AIProviderError: If JSON parsing fails or required fields missing
        """
        try:
            data = json.loads(response_text)
            
            # Validate required fields
            required_fields = ["headline", "summary", "confidence_explanation"]
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                raise AIProviderError(
                    f"Missing required fields in AI response: {missing_fields}"
                )
            
            return InsightContent(
                headline=data["headline"],
                summary=data["summary"],
                confidence_explanation=data["confidence_explanation"]
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise AIProviderError(f"Invalid JSON response: {e}")


class AIProviderError(Exception):
    """Exception raised for AI provider errors"""
    pass


class VertexAIProvider(AIProvider):
    """
    Vertex AI provider using Gemini Pro model.
    
    Requirements: 8.2
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Vertex AI provider.
        
        Args:
            config: Configuration with project_id, location, model
        """
        super().__init__(config)
        
        try:
            from google.cloud import aiplatform
            from vertexai.preview.generative_models import GenerativeModel
            
            self.project_id = config.get("project_id")
            self.location = config.get("location", "us-central1")
            self.model_name = config.get("model", "gemini-pro")
            
            # Initialize Vertex AI
            aiplatform.init(project=self.project_id, location=self.location)
            self.model = GenerativeModel(self.model_name)
            
            logger.info(
                f"Initialized Vertex AI provider with model {self.model_name}",
                extra={
                    "project_id": self.project_id,
                    "location": self.location
                }
            )
            
        except ImportError:
            raise AIProviderError(
                "Vertex AI dependencies not installed. "
                "Install with: pip install google-cloud-aiplatform"
            )
        except Exception as e:
            raise AIProviderError(f"Failed to initialize Vertex AI: {e}")
    
    async def generate_insight(
        self,
        signal: Signal,
        prompt_template: str
    ) -> InsightContent:
        """
        Generate insight using Vertex AI Gemini Pro.
        
        Args:
            signal: Signal data
            prompt_template: Prompt template
            
        Returns:
            Generated InsightContent
        """
        try:
            # Format prompt
            prompt = self._format_prompt(signal, prompt_template)
            
            # Generate content
            logger.info(
                "Generating insight with Vertex AI",
                extra={"signal_id": signal.signal_id}
            )
            
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Parse JSON response
            return self._parse_json_response(response_text)
            
        except Exception as e:
            logger.error(
                f"Vertex AI generation failed: {e}",
                extra={"signal_id": signal.signal_id}
            )
            raise AIProviderError(f"Vertex AI generation failed: {e}")


class OpenAIProvider(AIProvider):
    """
    OpenAI provider using GPT models.
    
    Requirements: 8.3
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OpenAI provider.
        
        Args:
            config: Configuration with api_key and model
        """
        super().__init__(config)
        
        try:
            import openai
            
            self.api_key = config.get("api_key")
            self.model = config.get("model", "gpt-4-turbo")
            
            if not self.api_key:
                raise AIProviderError("OpenAI API key not provided")
            
            # Initialize async client
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
            
            logger.info(
                f"Initialized OpenAI provider with model {self.model}"
            )
            
        except ImportError:
            raise AIProviderError(
                "OpenAI dependencies not installed. "
                "Install with: pip install openai"
            )
        except Exception as e:
            raise AIProviderError(f"Failed to initialize OpenAI: {e}")
    
    async def generate_insight(
        self,
        signal: Signal,
        prompt_template: str
    ) -> InsightContent:
        """
        Generate insight using OpenAI GPT.
        
        Args:
            signal: Signal data
            prompt_template: Prompt template
            
        Returns:
            Generated InsightContent
        """
        try:
            # Format prompt
            prompt = self._format_prompt(signal, prompt_template)
            
            # Generate content
            logger.info(
                "Generating insight with OpenAI",
                extra={"signal_id": signal.signal_id}
            )
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Bitcoin blockchain analyst. "
                                   "Respond only with valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content
            
            # Parse JSON response
            return self._parse_json_response(response_text)
            
        except Exception as e:
            logger.error(
                f"OpenAI generation failed: {e}",
                extra={"signal_id": signal.signal_id}
            )
            raise AIProviderError(f"OpenAI generation failed: {e}")


class AnthropicProvider(AIProvider):
    """
    Anthropic provider using Claude models.
    
    Requirements: 8.4
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Anthropic provider.
        
        Args:
            config: Configuration with api_key and model
        """
        super().__init__(config)
        
        try:
            import anthropic
            
            self.api_key = config.get("api_key")
            self.model = config.get("model", "claude-3-opus-20240229")
            
            if not self.api_key:
                raise AIProviderError("Anthropic API key not provided")
            
            # Initialize async client
            self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            logger.info(
                f"Initialized Anthropic provider with model {self.model}"
            )
            
        except ImportError:
            raise AIProviderError(
                "Anthropic dependencies not installed. "
                "Install with: pip install anthropic"
            )
        except Exception as e:
            raise AIProviderError(f"Failed to initialize Anthropic: {e}")
    
    async def generate_insight(
        self,
        signal: Signal,
        prompt_template: str
    ) -> InsightContent:
        """
        Generate insight using Anthropic Claude.
        
        Args:
            signal: Signal data
            prompt_template: Prompt template
            
        Returns:
            Generated InsightContent
        """
        try:
            # Format prompt
            prompt = self._format_prompt(signal, prompt_template)
            
            # Generate content
            logger.info(
                "Generating insight with Anthropic",
                extra={"signal_id": signal.signal_id}
            )
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": f"{prompt}\n\nRespond only with valid JSON."
                    }
                ]
            )
            
            response_text = response.content[0].text
            
            # Parse JSON response
            return self._parse_json_response(response_text)
            
        except Exception as e:
            logger.error(
                f"Anthropic generation failed: {e}",
                extra={"signal_id": signal.signal_id}
            )
            raise AIProviderError(f"Anthropic generation failed: {e}")


class GrokProvider(AIProvider):
    """
    xAI Grok provider.
    
    Requirements: 8.5
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Grok provider.
        
        Args:
            config: Configuration with api_key and model
        """
        super().__init__(config)
        
        self.api_key = config.get("api_key")
        self.model = config.get("model", "grok-beta")
        self.api_base = config.get("api_base", "https://api.x.ai/v1")
        
        if not self.api_key:
            raise AIProviderError("Grok API key not provided")
        
        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.api_base,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
        
        logger.info(
            f"Initialized Grok provider with model {self.model}"
        )
    
    async def generate_insight(
        self,
        signal: Signal,
        prompt_template: str
    ) -> InsightContent:
        """
        Generate insight using xAI Grok.
        
        Args:
            signal: Signal data
            prompt_template: Prompt template
            
        Returns:
            Generated InsightContent
        """
        try:
            # Format prompt
            prompt = self._format_prompt(signal, prompt_template)
            
            # Generate content
            logger.info(
                "Generating insight with Grok",
                extra={"signal_id": signal.signal_id}
            )
            
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a Bitcoin blockchain analyst. "
                                       "Respond only with valid JSON."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "response_format": {"type": "json_object"}
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            response_text = data["choices"][0]["message"]["content"]
            
            # Parse JSON response
            return self._parse_json_response(response_text)
            
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Grok API error: {e.response.status_code}",
                extra={"signal_id": signal.signal_id}
            )
            raise AIProviderError(f"Grok API error: {e.response.status_code}")
        except Exception as e:
            logger.error(
                f"Grok generation failed: {e}",
                extra={"signal_id": signal.signal_id}
            )
            raise AIProviderError(f"Grok generation failed: {e}")
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


class AIProviderFactory:
    """
    Factory for creating AI provider instances.
    
    Requirements: 8.1
    """
    
    @staticmethod
    def create_provider(
        provider_type: str,
        config: Optional[Dict[str, Any]] = None
    ) -> AIProvider:
        """
        Create AI provider instance based on type.
        
        Args:
            provider_type: Type of provider (vertex_ai, openai, anthropic, grok)
            config: Provider-specific configuration (if None, loads from env)
            
        Returns:
            Initialized AIProvider instance
            
        Raises:
            AIProviderError: If provider type is invalid or initialization fails
        """
        # Load config from environment if not provided
        if config is None:
            config = AIProviderFactory._load_config_from_env(provider_type)
        
        # Create provider based on type
        provider_map = {
            AIProviderType.VERTEX_AI.value: VertexAIProvider,
            AIProviderType.OPENAI.value: OpenAIProvider,
            AIProviderType.ANTHROPIC.value: AnthropicProvider,
            AIProviderType.GROK.value: GrokProvider
        }
        
        provider_class = provider_map.get(provider_type)
        
        if not provider_class:
            raise AIProviderError(
                f"Invalid provider type: {provider_type}. "
                f"Valid types: {list(provider_map.keys())}"
            )
        
        try:
            return provider_class(config)
        except Exception as e:
            logger.error(
                f"Failed to create {provider_type} provider: {e}"
            )
            raise AIProviderError(
                f"Failed to create {provider_type} provider: {e}"
            )
    
    @staticmethod
    def _load_config_from_env(provider_type: str) -> Dict[str, Any]:
        """
        Load provider configuration from environment variables.
        
        Args:
            provider_type: Type of provider
            
        Returns:
            Configuration dictionary
        """
        if provider_type == AIProviderType.VERTEX_AI.value:
            return {
                "project_id": os.getenv("VERTEX_AI_PROJECT"),
                "location": os.getenv("VERTEX_AI_LOCATION", "us-central1"),
                "model": os.getenv("VERTEX_AI_MODEL", "gemini-pro")
            }
        
        elif provider_type == AIProviderType.OPENAI.value:
            return {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "model": os.getenv("OPENAI_MODEL", "gpt-4-turbo")
            }
        
        elif provider_type == AIProviderType.ANTHROPIC.value:
            return {
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "model": os.getenv(
                    "ANTHROPIC_MODEL",
                    "claude-3-opus-20240229"
                )
            }
        
        elif provider_type == AIProviderType.GROK.value:
            return {
                "api_key": os.getenv("GROK_API_KEY"),
                "model": os.getenv("GROK_MODEL", "grok-beta"),
                "api_base": os.getenv("GROK_API_BASE", "https://api.x.ai/v1")
            }
        
        else:
            raise AIProviderError(f"Unknown provider type: {provider_type}")


def get_configured_provider() -> AIProvider:
    """
    Get AI provider instance based on environment configuration.
    
    Returns:
        Configured AIProvider instance
        
    Raises:
        AIProviderError: If AI_PROVIDER env var not set or invalid
        
    Requirements: 8.1
    """
    provider_type = os.getenv("AI_PROVIDER")
    
    if not provider_type:
        raise AIProviderError(
            "AI_PROVIDER environment variable not set. "
            "Valid values: vertex_ai, openai, anthropic, grok"
        )
    
    logger.info(f"Loading AI provider: {provider_type}")
    
    return AIProviderFactory.create_provider(provider_type)
