"""Ollama local LLM provider implementation."""

import json
from typing import Any

import httpx

from src.services.llm.base import (
    LLMMessage,
    LLMProvider,
    LLMResponse,
    LLMToolCall,
    LLMToolDefinition,
)


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider.

    Supports tool calling with Ollama 0.3.0+ and compatible models
    (e.g., llama3.2, mistral, qwen2.5).
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "llama3.2",
        timeout: float = 120.0,
    ):
        """Initialize Ollama provider.

        Args:
            base_url: Ollama server URL
            model_name: Model to use (must support tool calling)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def is_configured(self) -> bool:
        # Ollama doesn't require API key, just check if server is reachable
        try:
            response = self._client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    def _convert_tools(self, tools: list[LLMToolDefinition]) -> list[dict[str, Any]]:
        """Convert standard tool definitions to Ollama format."""
        ollama_tools = []
        for tool in tools:
            ollama_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                        "required": tool.required,
                    },
                },
            }
            ollama_tools.append(ollama_tool)
        return ollama_tools

    def _convert_messages(
        self,
        messages: list[LLMMessage],
        system_prompt: str,
    ) -> list[dict[str, Any]]:
        """Convert standard messages to Ollama format."""
        ollama_messages = []

        # Add system message
        if system_prompt:
            ollama_messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        for msg in messages:
            if msg.role == "user":
                ollama_messages.append(
                    {
                        "role": "user",
                        "content": msg.content,
                    }
                )
            elif msg.role == "assistant":
                message_dict: dict[str, Any] = {
                    "role": "assistant",
                    "content": msg.content or "",
                }
                if msg.tool_calls:
                    message_dict["tool_calls"] = [
                        {
                            "function": {
                                "name": tc.name,
                                "arguments": tc.arguments,
                            }
                        }
                        for tc in msg.tool_calls
                    ]
                ollama_messages.append(message_dict)
            elif msg.role == "tool":
                ollama_messages.append(
                    {
                        "role": "tool",
                        "content": msg.content,
                    }
                )

        return ollama_messages

    def _parse_response(self, response_data: dict[str, Any]) -> LLMResponse:
        """Parse Ollama response to standard format."""
        tool_calls: list[LLMToolCall] = []
        text = ""
        finish_reason = "end_turn"

        message = response_data.get("message", {})
        text = message.get("content", "")

        # Check for tool calls
        if "tool_calls" in message:
            for tc in message["tool_calls"]:
                func = tc.get("function", {})
                args = func.get("arguments", {})
                # Arguments might be a string (JSON) or dict
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}

                tool_calls.append(
                    LLMToolCall(
                        name=func.get("name", ""),
                        arguments=args,
                    )
                )
            finish_reason = "tool_use"

        return LLMResponse(
            text=text,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
        )

    def chat(
        self,
        messages: list[LLMMessage],
        tools: list[LLMToolDefinition],
        system_prompt: str,
    ) -> LLMResponse:
        """Send messages to Ollama and get response."""
        ollama_tools = self._convert_tools(tools)
        ollama_messages = self._convert_messages(messages, system_prompt)

        try:
            response = self._client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": ollama_messages,
                    "tools": ollama_tools,
                    "stream": False,
                },
            )
            response.raise_for_status()
            return self._parse_response(response.json())

        except httpx.ConnectError:
            return LLMResponse(
                text=f"無法連接到 Ollama 伺服器 ({self.base_url})。請確認 Ollama 是否正在運行。",
                tool_calls=[],
                finish_reason="error",
            )
        except httpx.HTTPStatusError as e:
            return LLMResponse(
                text=f"Ollama API 錯誤: {e.response.status_code} - {e.response.text}",
                tool_calls=[],
                finish_reason="error",
            )
        except Exception as e:
            return LLMResponse(
                text=f"Ollama 錯誤: {e!s}",
                tool_calls=[],
                finish_reason="error",
            )

    def send_tool_results(
        self,
        messages: list[LLMMessage],
        tool_results: list[dict[str, Any]],
        tools: list[LLMToolDefinition],
        system_prompt: str,
    ) -> LLMResponse:
        """Send tool execution results back to Ollama."""
        # Add tool results as tool messages
        messages_with_results = messages.copy()
        for result in tool_results:
            messages_with_results.append(
                LLMMessage(
                    role="tool",
                    content=json.dumps(result["result"], ensure_ascii=False),
                )
            )

        return self.chat(messages_with_results, tools, system_prompt)

    def __del__(self):
        """Clean up HTTP client."""
        if hasattr(self, "_client"):
            self._client.close()
