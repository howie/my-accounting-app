"""Anthropic Claude LLM provider implementation."""

from typing import Any

import anthropic

from src.services.llm.base import (
    LLMMessage,
    LLMProvider,
    LLMResponse,
    LLMToolCall,
    LLMToolDefinition,
)


class ClaudeProvider(LLMProvider):
    """Anthropic Claude LLM provider."""

    def __init__(self, api_key: str, model_name: str = "claude-sonnet-4-20250514"):
        """Initialize Claude provider.

        Args:
            api_key: Anthropic API key
            model_name: Claude model to use
        """
        self.api_key = api_key
        self.model_name = model_name
        self._client: anthropic.Anthropic | None = None

        if self.api_key:
            self._client = anthropic.Anthropic(api_key=self.api_key)

    @property
    def provider_name(self) -> str:
        return "claude"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _convert_tools(self, tools: list[LLMToolDefinition]) -> list[dict[str, Any]]:
        """Convert standard tool definitions to Claude format."""
        claude_tools = []
        for tool in tools:
            claude_tool = {
                "name": tool.name,
                "description": tool.description,
                "input_schema": {
                    "type": "object",
                    "properties": tool.parameters,
                },
            }
            if tool.required:
                claude_tool["input_schema"]["required"] = tool.required
            claude_tools.append(claude_tool)
        return claude_tools

    def _convert_messages(self, messages: list[LLMMessage]) -> list[dict[str, Any]]:
        """Convert standard messages to Claude format."""
        claude_messages = []

        for msg in messages:
            if msg.role == "user":
                claude_messages.append(
                    {
                        "role": "user",
                        "content": msg.content,
                    }
                )
            elif msg.role == "assistant":
                if msg.tool_calls:
                    # Assistant message with tool use
                    content = []
                    if msg.content:
                        content.append({"type": "text", "text": msg.content})
                    for tc in msg.tool_calls:
                        content.append(
                            {
                                "type": "tool_use",
                                "id": f"tool_{tc.name}",
                                "name": tc.name,
                                "input": tc.arguments,
                            }
                        )
                    claude_messages.append(
                        {
                            "role": "assistant",
                            "content": content,
                        }
                    )
                else:
                    claude_messages.append(
                        {
                            "role": "assistant",
                            "content": msg.content,
                        }
                    )
            elif msg.role == "tool":
                # Tool result message
                claude_messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": msg.tool_call_id or f"tool_{msg.content}",
                                "content": msg.content,
                            }
                        ],
                    }
                )

        return claude_messages

    def _parse_response(self, response: Any) -> LLMResponse:
        """Parse Claude response to standard format."""
        tool_calls: list[LLMToolCall] = []
        text = ""
        finish_reason = "end_turn"

        for block in response.content:
            if block.type == "text":
                text += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    LLMToolCall(
                        name=block.name,
                        arguments=block.input if isinstance(block.input, dict) else {},
                    )
                )
                finish_reason = "tool_use"

        if response.stop_reason == "tool_use":
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
        """Send messages to Claude and get response."""
        if not self._client:
            return LLMResponse(
                text="Claude API key not configured.",
                tool_calls=[],
                finish_reason="error",
            )

        claude_tools = self._convert_tools(tools)
        claude_messages = self._convert_messages(messages)

        response = self._client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            system=system_prompt,
            tools=claude_tools,
            messages=claude_messages,
        )

        return self._parse_response(response)

    def send_tool_results(
        self,
        messages: list[LLMMessage],
        tool_results: list[dict[str, Any]],
        tools: list[LLMToolDefinition],
        system_prompt: str,
    ) -> LLMResponse:
        """Send tool execution results back to Claude."""
        if not self._client:
            return LLMResponse(
                text="Claude API key not configured.",
                tool_calls=[],
                finish_reason="error",
            )

        # Build tool result content blocks
        tool_result_content = []
        for result in tool_results:
            tool_result_content.append(
                {
                    "type": "tool_result",
                    "tool_use_id": result.get("tool_use_id", f"tool_{result['name']}"),
                    "content": str(result["result"]),
                }
            )

        # Add tool results as user message
        messages_with_results = messages.copy()
        messages_with_results.append(
            LLMMessage(
                role="user",
                content="",  # Content is in tool_result blocks
            )
        )

        claude_tools = self._convert_tools(tools)
        claude_messages = self._convert_messages(messages[:-1])  # Exclude the placeholder

        # Add the tool results message
        claude_messages.append(
            {
                "role": "user",
                "content": tool_result_content,
            }
        )

        response = self._client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            system=system_prompt,
            tools=claude_tools,
            messages=claude_messages,
        )

        return self._parse_response(response)
