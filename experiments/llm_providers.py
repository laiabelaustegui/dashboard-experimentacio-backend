"""
LLM Provider abstraction layer.
Implements the Strategy pattern for different LLM providers.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from openai import OpenAI
import logging

from .constants import DEFAULT_API_TIMEOUT

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def create_completion(
        self,
        model_name: str,
        system_prompt: str,
        user_prompt: str,
        schema: Dict[str, Any],
        temperature: float,
        top_p: Optional[float] = None,
        timeout: int = DEFAULT_API_TIMEOUT
    ) -> str:
        """
        Create a chat completion.
        
        Returns:
            str: The response content from the LLM
        """
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation."""
    
    def __init__(self, api_key: str, timeout: int = DEFAULT_API_TIMEOUT):
        self.client = OpenAI(api_key=api_key, timeout=timeout)
    
    def create_completion(
        self,
        model_name: str,
        system_prompt: str,
        user_prompt: str,
        schema: Dict[str, Any],
        temperature: float,
        top_p: Optional[float] = None,
        timeout: int = DEFAULT_API_TIMEOUT
    ) -> str:
        """Create a chat completion using OpenAI API."""
        params = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": schema,
            "temperature": temperature,
        }
        
        if top_p is not None:
            params["top_p"] = top_p
        
        try:
            response = self.client.chat.completions.create(**params)
            content = response.choices[0].message.content
            
            if not content:
                raise ValueError("Empty response from OpenAI API")
            
            return content
        except Exception as e:
            logger.error(f"OpenAI API request failed: {str(e)}")
            raise RuntimeError(f"OpenAI API request failed: {str(e)}")


class LLMProviderFactory:
    """Factory for creating LLM provider instances."""
    
    _providers = {
        'OpenAI': OpenAIProvider,
    }
    
    @classmethod
    def create_provider(cls, provider_name: str, api_key: str) -> LLMProvider:
        """
        Create an LLM provider instance.
        
        Args:
            provider_name: Name of the provider (e.g., 'OpenAI')
            api_key: API key for the provider
            
        Returns:
            LLMProvider: An instance of the appropriate provider
            
        Raises:
            NotImplementedError: If the provider is not supported
        """
        provider_class = cls._providers.get(provider_name)
        
        if not provider_class:
            raise NotImplementedError(
                f"Provider {provider_name} not supported. "
                f"Available providers: {', '.join(cls._providers.keys())}"
            )
        
        return provider_class(api_key=api_key)
    
    @classmethod
    def register_provider(cls, provider_name: str, provider_class: type):
        """Register a new provider class."""
        cls._providers[provider_name] = provider_class
