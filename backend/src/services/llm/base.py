"""Abstract base interface for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class LLMToolDefinition(BaseModel):
    """Provider-agnostic tool definition."""

    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)


class LLMToolCall(BaseModel):
    """Represents a tool call from the LLM."""

    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class LLMMessage(BaseModel):
    """A message in the conversation."""

    role: str  # "user", "assistant", "tool"
    content: str
    tool_calls: list[LLMToolCall] = Field(default_factory=list)
    tool_call_id: str | None = None  # For tool response messages


class LLMResponse(BaseModel):
    """Standardized response from LLM providers."""

    text: str
    tool_calls: list[LLMToolCall] = Field(default_factory=list)
    finish_reason: str  # "end_turn", "tool_use", "error"


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    All LLM providers must implement this interface to be used
    with the ChatService through the LLMFactory.
    """

    @abstractmethod
    def chat(
        self,
        messages: list[LLMMessage],
        tools: list[LLMToolDefinition],
        system_prompt: str,
    ) -> LLMResponse:
        """Send messages to the LLM and get a response.

        Args:
            messages: Conversation history
            tools: Available tools for the LLM to call
            system_prompt: System instructions for the LLM

        Returns:
            LLMResponse with text and/or tool calls
        """
        pass

    @abstractmethod
    def send_tool_results(
        self,
        messages: list[LLMMessage],
        tool_results: list[dict[str, Any]],
        tools: list[LLMToolDefinition],
        system_prompt: str,
    ) -> LLMResponse:
        """Send tool execution results back to the LLM.

        Args:
            messages: Conversation history including the assistant's tool call
            tool_results: Results from executing the tools
            tools: Available tools (for context)
            system_prompt: System instructions

        Returns:
            LLMResponse with the assistant's next response
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider."""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the provider is properly configured (has API keys, etc.)."""
        pass
