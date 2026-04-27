"""Budget management for Nexus Agent with monthly reset and atomic persistence."""

from __future__ import annotations

import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
import asyncio

from .exceptions import BudgetExceededError
from .memory import save_json_atomic


@dataclass
class BudgetState:
    spent: Decimal
    count: int
    last_reset_date: str


class Budget:
    """Budget tracker that owns the lock and saves state atomically."""

    def __init__(self, budget_file: str, monthly_cap: Decimal) -> None:
        self._budget_path = Path(budget_file)
        self._monthly_cap = monthly_cap
        self._lock = asyncio.Lock()
        self._state = BudgetState(
            spent=Decimal("0"),
            count=0,
            last_reset_date=time.strftime("%Y-%m"),
        )
        self._load_state()

    def _load_state(self) -> None:
        if not self._budget_path.exists():
            self._ensure_parent()
            self._save_state()
            return

        try:
            data = self._budget_path.read_text(encoding="utf-8")
            payload = __import__("json").loads(data)
            self._state = BudgetState(
                spent=Decimal(str(payload.get("spent", "0"))),
                count=int(payload.get("count", 0)),
                last_reset_date=str(payload.get("last_reset_date", time.strftime("%Y-%m"))),
            )
        except (ValueError, TypeError, OSError) as exc:
            raise BudgetExceededError("Failed to load budget state") from exc

    def _ensure_parent(self) -> None:
        self._budget_path.parent.mkdir(parents=True, exist_ok=True)

    def _save_state(self) -> None:
        save_json_atomic(
            self._budget_path,
            {
                "spent": str(self._state.spent),
                "count": self._state.count,
                "last_reset_date": self._state.last_reset_date,
            },
        )

    def _maybe_reset(self) -> None:
        current_month = time.strftime("%Y-%m")
        if current_month != self._state.last_reset_date:
            self._state.spent = Decimal("0")
            self._state.count = 0
            self._state.last_reset_date = current_month
            self._save_state()

    async def check_and_record(self, amount: Decimal) -> None:
        async with self._lock:
            if amount <= Decimal("0"):
                raise BudgetExceededError("Amount must be greater than zero")

            self._maybe_reset()

            if self._state.spent + amount > self._monthly_cap:
                raise BudgetExceededError(
                    f"Budget exceeded: {self._state.spent + amount} would exceed cap {self._monthly_cap}"
                )

            self._state.spent += amount
            self._state.count += 1
            self._save_state()
