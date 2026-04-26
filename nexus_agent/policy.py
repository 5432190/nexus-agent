"""Policy evaluation for Nexus Agent."""

from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Dict, Set

from pydantic import BaseModel, Field, model_validator

from .exceptions import PolicyViolationError


class PolicyConfig(BaseModel):
    """Configuration for policy evaluation."""

    allowed_categories: Set[str] = Field(default_factory=lambda: {"office", "software", "cloud"})
    max_single_purchase: Decimal = Field(default=Decimal("1000"))
    max_category_amount: Dict[str, Decimal] = Field(
        default_factory=lambda: {
            "software": Decimal("1000"),
            "cloud": Decimal("2000"),
            "office": Decimal("500"),
        }
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_decimal(cls, values):
        if not isinstance(values, dict):
            return values

        normalized = dict(values)

        if "max_single_purchase" in normalized and not isinstance(normalized["max_single_purchase"], Decimal):
            normalized["max_single_purchase"] = Decimal(str(normalized["max_single_purchase"]))

        if "max_category_amount" in normalized and isinstance(normalized["max_category_amount"], dict):
            normalized["max_category_amount"] = {
                category: Decimal(str(limit)) if not isinstance(limit, Decimal) else limit
                for category, limit in normalized["max_category_amount"].items()
            }

        return normalized


class PolicyEvaluator:
    """Asynchronous policy evaluator."""

    def __init__(self, config: PolicyConfig | None = None) -> None:
        self._config = config or PolicyConfig()
        self._lock = asyncio.Lock()

    async def evaluate_async(self, amount: Decimal, category: str) -> None:
        async with self._lock:
            if amount <= Decimal("0"):
                raise PolicyViolationError("Amount must be greater than zero")

            if amount > self._config.max_single_purchase:
                raise PolicyViolationError(
                    f"Amount {amount} exceeds single purchase limit of {self._config.max_single_purchase}"
                )

            if category not in self._config.allowed_categories:
                raise PolicyViolationError(f"Category '{category}' is not allowed")

            max_amount = self._config.max_category_amount.get(category)
            if max_amount is not None and amount > max_amount:
                raise PolicyViolationError(
                    f"Amount {amount} exceeds category limit of {max_amount} for '{category}'"
                )
