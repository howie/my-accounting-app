"""Chat service with pluggable LLM provider support."""

import logging
import traceback
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlmodel import Session

from src.api.mcp.tools.accounts import get_account, list_accounts
from src.api.mcp.tools.ledgers import list_ledgers
from src.api.mcp.tools.transactions import create_transaction, list_transactions
from src.core.config import get_settings
from src.models.user import User
from src.schemas.chat import ChatResponse, ToolCallResult
from src.services.llm import LLMFactory, LLMProvider, LLMToolDefinition
from src.services.llm.base import LLMMessage

# System prompt for LLM
SYSTEM_PROMPT = """你是 LedgerOne 記帳應用程式的 AI 助手。
你可以幫助使用者：
- 建立交易記錄（使用 create_transaction 工具）
- 查詢帳戶餘額（使用 list_accounts、get_account 工具）
- 查詢交易記錄（使用 list_transactions 工具）
- 查看帳本列表（使用 list_ledgers 工具）

建立交易時：
- 確認金額、來源帳戶、目標帳戶和說明
- 如果使用者沒有指定日期，預設為今天
- 支出通常從「現金」或「銀行」等資產帳戶轉到費用帳戶
- 收入通常從收入帳戶轉到「現金」或「銀行」等資產帳戶

回覆時請使用繁體中文，保持簡潔友善。
"""

# Provider-agnostic tool definitions
TOOL_DEFINITIONS = [
    LLMToolDefinition(
        name="list_accounts",
        description="列出所有帳戶及其餘額。可以按帳戶類型篩選。",
        parameters={
            "type_filter": {
                "type": "string",
                "enum": ["ASSET", "LIABILITY", "INCOME", "EXPENSE"],
                "description": "按帳戶類型篩選（資產、負債、收入、費用）",
            },
            "include_zero_balance": {
                "type": "boolean",
                "description": "是否包含餘額為零的帳戶，預設為 true",
            },
        },
    ),
    LLMToolDefinition(
        name="get_account",
        description="取得單一帳戶的詳細資訊，包括最近的交易記錄。",
        parameters={
            "account": {
                "type": "string",
                "description": "帳戶名稱或 UUID",
            },
        },
        required=["account"],
    ),
    LLMToolDefinition(
        name="create_transaction",
        description="建立一筆新的複式記帳交易。從來源帳戶扣款，記入目標帳戶。",
        parameters={
            "amount": {
                "type": "number",
                "description": "交易金額（正數）",
            },
            "from_account": {
                "type": "string",
                "description": "來源帳戶名稱（扣款方）",
            },
            "to_account": {
                "type": "string",
                "description": "目標帳戶名稱（入帳方）",
            },
            "description": {
                "type": "string",
                "description": "交易說明",
            },
            "date": {
                "type": "string",
                "description": "交易日期，格式為 YYYY-MM-DD，預設為今天",
            },
            "notes": {
                "type": "string",
                "description": "備註（選填）",
            },
        },
        required=["amount", "from_account", "to_account", "description"],
    ),
    LLMToolDefinition(
        name="list_transactions",
        description="查詢交易記錄，支援按帳戶、日期範圍篩選。",
        parameters={
            "account_name": {
                "type": "string",
                "description": "按帳戶名稱篩選",
            },
            "start_date": {
                "type": "string",
                "description": "開始日期，格式為 YYYY-MM-DD",
            },
            "end_date": {
                "type": "string",
                "description": "結束日期，格式為 YYYY-MM-DD",
            },
            "limit": {
                "type": "integer",
                "description": "回傳數量上限，預設為 20",
            },
        },
    ),
    LLMToolDefinition(
        name="list_ledgers",
        description="列出使用者的所有帳本。",
        parameters={},
    ),
]


class ChatService:
    """Service for handling chat interactions with LLM providers."""

    def __init__(self, session: Session, user: User):
        """Initialize chat service.

        Args:
            session: Database session
            user: Authenticated user
        """
        self.session = session
        self.user = user
        self.settings = get_settings()
        self._provider: LLMProvider | None = None

    def _get_provider(self) -> LLMProvider | None:
        """Get or create the LLM provider based on configuration."""
        if self._provider is not None:
            return self._provider

        provider_type = self.settings.llm_provider

        try:
            if provider_type == "gemini":
                self._provider = LLMFactory.create(
                    "gemini",
                    api_key=self.settings.gemini_api_key,
                    model_name=self.settings.gemini_model,
                )
            elif provider_type == "claude":
                self._provider = LLMFactory.create(
                    "claude",
                    api_key=self.settings.claude_api_key,
                    model_name=self.settings.claude_model,
                )
            elif provider_type == "ollama":
                self._provider = LLMFactory.create(
                    "ollama",
                    base_url=self.settings.ollama_base_url,
                    model_name=self.settings.ollama_model,
                )
            else:
                return None
        except ValueError:
            return None

        return self._provider

    def _execute_tool(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Execute an MCP tool and return its result.

        Args:
            tool_name: Name of the tool to execute
            args: Arguments for the tool

        Returns:
            Tool execution result
        """
        if tool_name == "list_accounts":
            return list_accounts(
                ledger_id=args.get("ledger_id"),
                type_filter=args.get("type_filter"),
                include_zero_balance=args.get("include_zero_balance", True),
                session=self.session,
                user=self.user,
            )
        elif tool_name == "get_account":
            return get_account(
                account=args.get("account", ""),
                ledger_id=args.get("ledger_id"),
                session=self.session,
                user=self.user,
            )
        elif tool_name == "create_transaction":
            return create_transaction(
                amount=float(args.get("amount", 0)),
                from_account=args.get("from_account", ""),
                to_account=args.get("to_account", ""),
                description=args.get("description", ""),
                date=args.get("date"),
                notes=args.get("notes"),
                ledger_id=args.get("ledger_id"),
                session=self.session,
                user=self.user,
            )
        elif tool_name == "list_transactions":
            return list_transactions(
                ledger_id=args.get("ledger_id"),
                account_id=args.get("account_id"),
                account_name=args.get("account_name"),
                start_date=args.get("start_date"),
                end_date=args.get("end_date"),
                limit=args.get("limit", 20),
                offset=args.get("offset", 0),
                session=self.session,
                user=self.user,
            )
        elif tool_name == "list_ledgers":
            return list_ledgers(
                session=self.session,
                user=self.user,
            )
        else:
            return {
                "success": False,
                "error": {"code": "UNKNOWN_TOOL", "message": f"未知的工具: {tool_name}"},
            }

    def chat(self, message: str, ledger_id: str | None = None) -> ChatResponse:
        """Process a chat message and return AI response.

        Args:
            message: User's message
            ledger_id: Optional ledger ID for context

        Returns:
            ChatResponse with AI message and any tool results
        """
        provider = self._get_provider()

        if not provider:
            return ChatResponse(
                id=str(uuid.uuid4()),
                message=f"抱歉，AI 功能尚未設定。請設定 LLM_PROVIDER 和相應的 API 金鑰。"
                f"（目前設定：{self.settings.llm_provider}）",
                tool_calls=[],
                created_at=datetime.now(UTC),
            )

        if not provider.is_configured:
            provider_name = provider.provider_name
            return ChatResponse(
                id=str(uuid.uuid4()),
                message=f"抱歉，{provider_name.upper()} 尚未正確設定。請檢查 API 金鑰或服務連線。",
                tool_calls=[],
                created_at=datetime.now(UTC),
            )

        tool_calls: list[ToolCallResult] = []
        messages: list[LLMMessage] = [
            LLMMessage(role="user", content=message),
        ]

        try:
            # Initial request to LLM
            response = provider.chat(
                messages=messages,
                tools=TOOL_DEFINITIONS,
                system_prompt=SYSTEM_PROMPT,
            )

            # Handle tool calling loop (max 10 iterations for safety)
            iteration = 0
            max_iterations = 10

            while response.finish_reason == "tool_use" and iteration < max_iterations:
                iteration += 1

                # Execute all tool calls
                tool_results = []
                for tc in response.tool_calls:
                    # Inject ledger_id if provided
                    args = tc.arguments.copy()
                    if ledger_id:
                        args["ledger_id"] = ledger_id

                    result = self._execute_tool(tc.name, args)
                    tool_calls.append(ToolCallResult(tool_name=tc.name, result=result))
                    tool_results.append(
                        {
                            "name": tc.name,
                            "tool_use_id": f"tool_{tc.name}_{iteration}",
                            "result": result,
                        }
                    )

                # Add assistant's tool call message to history
                messages.append(
                    LLMMessage(
                        role="assistant",
                        content=response.text,
                        tool_calls=response.tool_calls,
                    )
                )

                # Send tool results back to LLM
                response = provider.send_tool_results(
                    messages=messages,
                    tool_results=tool_results,
                    tools=TOOL_DEFINITIONS,
                    system_prompt=SYSTEM_PROMPT,
                )

            # Extract final text
            final_text = response.text
            if not final_text:
                final_text = "抱歉，我無法處理您的請求。請再試一次。"

            return ChatResponse(
                id=str(uuid.uuid4()),
                message=final_text,
                tool_calls=tool_calls,
                created_at=datetime.now(UTC),
            )

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error("Error in chat service:")
            logger.error(traceback.format_exc())

            return ChatResponse(
                id=str(uuid.uuid4()),
                message=f"發生錯誤：{e!s}",
                tool_calls=tool_calls,
                created_at=datetime.now(UTC),
            )
