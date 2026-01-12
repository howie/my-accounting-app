"""Google Gemini LLM provider implementation."""

from typing import Any

import google.generativeai as genai

from src.services.llm.base import (
    LLMMessage,
    LLMProvider,
    LLMResponse,
    LLMToolCall,
    LLMToolDefinition,
)


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        """Initialize Gemini provider.

        Args:
            api_key: Google AI API key
            model_name: Gemini model to use
        """
        self.api_key = api_key
        self.model_name = model_name
        self._model: genai.GenerativeModel | None = None
        self._chat: Any = None

        if self.api_key:
            genai.configure(api_key=self.api_key)

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _convert_tools(self, tools: list[LLMToolDefinition]) -> list[dict[str, Any]]:
        """Convert standard tool definitions to Gemini format."""
        gemini_tools = []
        for tool in tools:
            gemini_tool = {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": tool.parameters,
                },
            }
            if tool.required:
                gemini_tool["parameters"]["required"] = tool.required
            gemini_tools.append(gemini_tool)
        return gemini_tools

    def _convert_messages(self, messages: list[LLMMessage]) -> list[dict[str, Any]]:
        """Convert standard messages to Gemini format."""
        gemini_messages = []
        for msg in messages:
            if msg.role == "user":
                gemini_messages.append({"role": "user", "parts": [msg.content]})
            elif msg.role == "assistant":
                if msg.tool_calls:
                    # Assistant message with tool calls
                    parts = []
                    if msg.content:
                        parts.append(msg.content)
                    for tc in msg.tool_calls:
                        parts.append(
                            genai.protos.Part(
                                function_call=genai.protos.FunctionCall(
                                    name=tc.name,
                                    args=tc.arguments,
                                )
                            )
                        )
                    gemini_messages.append({"role": "model", "parts": parts})
                else:
                    gemini_messages.append({"role": "model", "parts": [msg.content]})
            elif msg.role == "tool":
                # Tool response - handled separately in send_tool_results
                pass
        return gemini_messages

    def _parse_response(self, response: Any) -> LLMResponse:
        """Parse Gemini response to standard format."""
        tool_calls: list[LLMToolCall] = []
        text = ""
        finish_reason = "end_turn"

        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    tool_calls.append(
                        LLMToolCall(
                            name=fc.name,
                            arguments=dict(fc.args) if fc.args else {},
                        )
                    )
                    finish_reason = "tool_use"
                elif hasattr(part, "text") and part.text:
                    text += part.text

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
        """Send messages to Gemini and get response."""
        if not self.is_configured:
            return LLMResponse(
                text="Gemini API key not configured.",
                tool_calls=[],
                finish_reason="error",
            )

        # Create model with tools and system prompt
        gemini_tools = self._convert_tools(tools)
        self._model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt,
            tools=gemini_tools,
        )

        # Start chat and send messages
        self._chat = self._model.start_chat()

        # Process message history (skip system messages)
        for msg in messages[:-1]:  # All but last message
            if msg.role == "user":
                self._chat.send_message(msg.content)

        # Send the last user message and get response
        last_message = messages[-1]
        response = self._chat.send_message(last_message.content)

        return self._parse_response(response)

    def send_tool_results(
        self,
        messages: list[LLMMessage],
        tool_results: list[dict[str, Any]],
        tools: list[LLMToolDefinition],
        system_prompt: str,
    ) -> LLMResponse:
        """Send tool execution results back to Gemini."""
        if not self._chat:
            # Reinitialize if chat session lost
            return self.chat(messages, tools, system_prompt)

        # Build function response parts
        parts = []
        for result in tool_results:
            parts.append(
                genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=result["name"],
                        response={"result": result["result"]},
                    )
                )
            )

        # Send tool results back
        response = self._chat.send_message(genai.protos.Content(parts=parts))

        return self._parse_response(response)
