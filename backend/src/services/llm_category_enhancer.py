"""LLM-based category enhancement for credit card transactions."""

import json
import logging

from src.schemas.data_import import AccountType, ParsedAccountPath, ParsedTransaction
from src.services.category_suggester import CATEGORY_KEYWORDS, DEFAULT_CATEGORY

logger = logging.getLogger(__name__)


class LLMCategoryEnhancer:
    """Enhance transaction category suggestions using LLM."""

    def __init__(self) -> None:
        from src.core.config import get_settings
        from src.services.llm import LLMFactory

        settings = get_settings()
        provider_type = settings.llm_provider
        self._provider = None

        try:
            if provider_type == "gemini" and settings.gemini_api_key:
                self._provider = LLMFactory.create(
                    "gemini",
                    api_key=settings.gemini_api_key,
                    model_name=settings.gemini_model,
                )
            elif provider_type == "claude" and settings.claude_api_key:
                self._provider = LLMFactory.create(
                    "claude",
                    api_key=settings.claude_api_key,
                    model_name=settings.claude_model,
                )
            elif provider_type == "ollama":
                self._provider = LLMFactory.create(
                    "ollama",
                    base_url=settings.ollama_base_url,
                    model_name=settings.ollama_model,
                )
        except Exception:
            self._provider = None

    def enhance_batch(
        self,
        transactions: list[ParsedTransaction],
        expense_accounts: list,
    ) -> list[ParsedTransaction]:
        """Enhance category suggestions using LLM.

        Args:
            transactions: List of parsed transactions to enhance
            expense_accounts: Existing EXPENSE accounts from the database

        Returns:
            Updated transactions with LLM-suggested categories (or original on failure)
        """
        if not self._provider or not self._provider.is_configured:
            return transactions

        if not transactions:
            return transactions

        try:
            # Build candidate list from DB accounts or fallback to keyword keys
            if expense_accounts:
                candidates = [acc.name for acc in expense_accounts]
            else:
                candidates = list(CATEGORY_KEYWORDS.keys()) + [DEFAULT_CATEGORY]

            # Build batch prompt
            descriptions = [tx.description for tx in transactions]
            numbered = "\n".join(f"{i + 1}. {desc}" for i, desc in enumerate(descriptions))
            candidates_str = "、".join(candidates)

            system_prompt = (
                f"你是記帳助手。根據下列可用支出科目，將每筆消費描述分類。\n"
                f"可用科目：{candidates_str}\n"
                f"若無合適科目，回傳「{DEFAULT_CATEGORY}」。\n"
                f'只回傳 JSON，格式：[{{"index": 1, "category": "科目名稱"}}, ...]'
            )

            from src.services.llm.base import LLMMessage

            messages = [
                LLMMessage(
                    role="user",
                    content=f"請分類以下消費：\n{numbered}",
                )
            ]

            response = self._provider.chat(
                messages=messages,
                tools=[],
                system_prompt=system_prompt,
            )

            # Parse JSON response
            raw = response.text.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            results: list[dict] = json.loads(raw)
            index_to_category = {item["index"]: item["category"] for item in results}

            # Apply LLM suggestions
            updated = []
            for i, tx in enumerate(transactions):
                category = index_to_category.get(i + 1)
                if category and category in candidates:
                    tx = tx.model_copy(
                        update={
                            "to_account_name": category,
                            "to_account_path": ParsedAccountPath(
                                account_type=AccountType.EXPENSE,
                                path_segments=[category],
                                raw_name=category,
                            ),
                        }
                    )
                updated.append(tx)

            return updated

        except Exception as e:
            logger.warning("LLM category enhancement failed, using rule-based results: %s", e)
            return transactions
