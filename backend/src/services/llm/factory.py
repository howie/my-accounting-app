"""LLM provider factory for creating provider instances."""

from enum import Enum
from typing import Any

from src.services.llm.base import LLMProvider


class LLMProviderType(str, Enum):
    """Available LLM provider types."""

    GEMINI = "gemini"
    CLAUDE = "claude"
    OLLAMA = "ollama"


class LLMFactory:
    """Factory for creating LLM provider instances.

    Usage:
        provider = LLMFactory.create("gemini", api_key="your-key")
        provider = LLMFactory.create(LLMProviderType.CLAUDE, api_key="your-key")
    """

    @staticmethod
    def create(
        provider_type: str | LLMProviderType,
        **config: Any,
    ) -> LLMProvider:
        """Create an LLM provider instance.

        Args:
            provider_type: Type of provider to create
            **config: Provider-specific configuration

        Returns:
            Configured LLMProvider instance

        Raises:
            ValueError: If provider_type is unknown
        """
        # Normalize provider type
        if isinstance(provider_type, str):
            try:
                provider_type = LLMProviderType(provider_type.lower())
            except ValueError as e:
                valid_types = [t.value for t in LLMProviderType]
                raise ValueError(
                    f"Unknown LLM provider: {provider_type}. Valid options: {valid_types}"
                ) from e

        # Import providers here to avoid circular imports
        if provider_type == LLMProviderType.GEMINI:
            from src.services.llm.gemini_provider import GeminiProvider

            return GeminiProvider(
                api_key=config.get("api_key", ""),
                model_name=config.get("model_name", "gemini-2.0-flash"),
            )

        elif provider_type == LLMProviderType.CLAUDE:
            from src.services.llm.claude_provider import ClaudeProvider

            return ClaudeProvider(
                api_key=config.get("api_key", ""),
                model_name=config.get("model_name", "claude-sonnet-4-20250514"),
            )

        elif provider_type == LLMProviderType.OLLAMA:
            from src.services.llm.ollama_provider import OllamaProvider

            return OllamaProvider(
                base_url=config.get("base_url", "http://localhost:11434"),
                model_name=config.get("model_name", "llama3.2"),
                timeout=config.get("timeout", 120.0),
            )

        # Should never reach here due to enum validation
        raise ValueError(f"Unhandled provider type: {provider_type}")

    @staticmethod
    def get_available_providers() -> list[str]:
        """Get list of available provider types.

        Returns:
            List of provider type strings
        """
        return [t.value for t in LLMProviderType]
