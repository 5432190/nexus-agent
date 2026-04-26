"""Unit tests for Nexus Agent business logic."""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from nexus_agent.agent import TaskIntentSchema
from nexus_agent.budget import Budget
from nexus_agent.exceptions import BudgetExceededError
from nexus_agent.policy import PolicyConfig, PolicyEvaluator


@pytest.mark.asyncio
async def test_policy_allows_valid_amount_and_category() -> None:
    config = PolicyConfig(
        allowed_categories={"api_key"},
        max_single_purchase=Decimal("100"),
        max_category_amount={"api_key": Decimal("25")},
    )
    policy = PolicyEvaluator(config=config)

    await policy.evaluate_async(Decimal("25"), "api_key")


@pytest.mark.asyncio
async def test_budget_cap_enforcement(tmp_path) -> None:
    budget_file = tmp_path / "budget.json"
    budget = Budget(str(budget_file), Decimal("100"))

    await budget.check_and_record(Decimal("40"))
    await budget.check_and_record(Decimal("40"))

    with pytest.raises(BudgetExceededError):
        await budget.check_and_record(Decimal("30"))


def test_decimal_casting_from_int_string() -> None:
    intent = TaskIntentSchema.model_validate(
        {
            "merchant_id": "merchant-1",
            "category": "office",
            "params": {"amount": "12.34"},
        }
    )

    amount = Decimal(str(intent.params.get("amount", 0)))
    assert amount == Decimal("12.34")


def test_task_intent_schema_validation_error() -> None:
    with pytest.raises(ValidationError):
        TaskIntentSchema.model_validate(
            {
                "merchant_id": 123,
                "category": "office",
                "params": {"amount": "12.34"},
            }
        )
