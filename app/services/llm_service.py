"""
Multi-provider LLM service for recipe extraction.
Supports OpenAI, Google Gemini, and Anthropic Claude.

Provider selection based on:
- Speed: Gemini 2.0 Flash > Claude Haiku > GPT-4o > GPT-4o-mini
- Cost: Gemini 2.0 Flash < GPT-4o-mini < Claude Haiku < GPT-4o
- Quality: All comparable for recipe extraction

Recommended:
- Gemini 2.0 Flash: Best speed AND cost ($0.10/1M input, $0.40/1M output)
- GPT-4o-mini: Fallback if Gemini unavailable
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider"""
    content: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float


class BaseLLMProvider(ABC):
    """Base class for LLM providers"""

    # Pricing per 1M tokens
    PRICING: Dict[str, Dict[str, float]] = {}

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """Generate a response from the LLM"""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> AsyncIterator[str]:
        """Stream response from the LLM for real-time feedback"""
        pass

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost based on token usage"""
        if model not in self.PRICING:
            return 0.0
        prices = self.PRICING[model]
        return (
            (input_tokens / 1_000_000) * prices.get("input", 0) +
            (output_tokens / 1_000_000) * prices.get("output", 0)
        )


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider"""

    PRICING = {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 2.50, "output": 10.00},
    }

    def __init__(self, model: str = "gpt-4o-mini"):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            organization=settings.OPENAI_ORGANIZATION_ID,
            project=settings.OPENAI_PROJECT_ID
        )
        self.model = model

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> LLMResponse:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=temperature,
            max_tokens=max_tokens
        )

        usage = response.usage
        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            provider="openai",
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            estimated_cost_usd=self.calculate_cost(self.model, usage.prompt_tokens, usage.completion_tokens)
        )

    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> AsyncIterator[str]:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )

        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider - fastest and cheapest"""

    PRICING = {
        "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    }

    def __init__(self, model: str = "gemini-2.0-flash"):
        import google.generativeai as genai

        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")

        genai.configure(api_key=api_key)
        self.model_name = model
        self._genai = genai

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> LLMResponse:
        import asyncio

        generation_config = self._genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json"
        )

        model = self._genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=generation_config,
            system_instruction=system_prompt
        )

        # Run in thread pool since the SDK is synchronous
        def _generate():
            return model.generate_content(user_prompt)

        response = await asyncio.to_thread(_generate)

        # Get token counts
        input_tokens = model.count_tokens(system_prompt + user_prompt).total_tokens
        output_tokens = len(response.text) // 4  # Estimate

        return LLMResponse(
            content=response.text,
            model=self.model_name,
            provider="gemini",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            estimated_cost_usd=self.calculate_cost(self.model_name, input_tokens, output_tokens)
        )

    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> AsyncIterator[str]:
        import asyncio

        generation_config = self._genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json"
        )

        model = self._genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=generation_config,
            system_instruction=system_prompt
        )

        # Run streaming in thread pool
        def _stream():
            return model.generate_content(user_prompt, stream=True)

        response = await asyncio.to_thread(_stream)

        for chunk in response:
            if chunk.text:
                yield chunk.text


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude provider"""

    PRICING = {
        "claude-3-5-haiku-latest": {"input": 1.00, "output": 5.00},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    }

    def __init__(self, model: str = "claude-3-5-haiku-latest"):
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> LLMResponse:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        content = response.content[0].text
        return LLMResponse(
            content=content,
            model=self.model,
            provider="anthropic",
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            estimated_cost_usd=self.calculate_cost(
                self.model,
                response.usage.input_tokens,
                response.usage.output_tokens
            )
        )

    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> AsyncIterator[str]:
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        ) as stream:
            async for text in stream.text_stream:
                yield text


class LLMService:
    """
    Multi-provider LLM service with automatic fallback.

    Priority order:
    1. Gemini 2.0 Flash (fastest, cheapest)
    2. OpenAI GPT-4o-mini (reliable fallback)
    3. Claude Haiku (alternative fallback)
    """

    def __init__(self, preferred_provider: Optional[str] = None):
        """
        Initialize LLM service with optional preferred provider.

        Args:
            preferred_provider: One of "gemini", "openai", "anthropic", or None for auto
        """
        self.preferred_provider = preferred_provider
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize available providers based on API keys"""
        # Try Gemini first (fastest and cheapest)
        if os.environ.get("GOOGLE_API_KEY"):
            try:
                self._providers["gemini"] = GeminiProvider("gemini-2.0-flash")
                logger.info("Gemini provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {e}")

        # OpenAI as reliable fallback
        if settings.OPENAI_API_KEY:
            try:
                self._providers["openai"] = OpenAIProvider("gpt-4o-mini")
                logger.info("OpenAI provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")

        # Claude as alternative
        if os.environ.get("ANTHROPIC_API_KEY"):
            try:
                self._providers["anthropic"] = ClaudeProvider("claude-3-5-haiku-latest")
                logger.info("Anthropic provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic: {e}")

        if not self._providers:
            raise RuntimeError("No LLM providers available. Set at least one API key.")

    def _get_provider(self) -> BaseLLMProvider:
        """Get the best available provider"""
        # Use preferred provider if specified and available
        if self.preferred_provider and self.preferred_provider in self._providers:
            return self._providers[self.preferred_provider]

        # Priority: Gemini > OpenAI > Anthropic
        for provider_name in ["gemini", "openai", "anthropic"]:
            if provider_name in self._providers:
                return self._providers[provider_name]

        raise RuntimeError("No LLM providers available")

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """Generate a response using the best available provider"""
        provider = self._get_provider()
        logger.info(f"Using LLM provider: {provider.__class__.__name__}")

        try:
            return await provider.generate(system_prompt, user_prompt, temperature, max_tokens)
        except Exception as e:
            logger.error(f"Error with {provider.__class__.__name__}: {e}")
            # Try fallback providers
            for name, fallback in self._providers.items():
                if fallback != provider:
                    try:
                        logger.info(f"Trying fallback provider: {name}")
                        return await fallback.generate(system_prompt, user_prompt, temperature, max_tokens)
                    except Exception as fallback_error:
                        logger.error(f"Fallback {name} also failed: {fallback_error}")
            raise

    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> AsyncIterator[str]:
        """Stream a response using the best available provider"""
        provider = self._get_provider()
        logger.info(f"Using LLM provider (streaming): {provider.__class__.__name__}")

        async for chunk in provider.generate_stream(system_prompt, user_prompt, temperature, max_tokens):
            yield chunk

    @property
    def available_providers(self) -> list[str]:
        """List available providers"""
        return list(self._providers.keys())

    @property
    def active_provider(self) -> str:
        """Get the name of the active provider"""
        provider = self._get_provider()
        for name, p in self._providers.items():
            if p == provider:
                return name
        return "unknown"
