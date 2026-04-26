"""Orchestration agent for Nexus Agent purchase flow."""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, Field

from .audit import AuditChain, AuditEntry
from .budget import Budget
from .exceptions import PolicyViolationError
from .memory import load_json_secure, save_json_atomic
from .policy import PolicyEvaluator
from .rate_limiter import TokenBucket
from .tools.commerce import CommerceTool


class TaskIntentSchema(BaseModel):
    merchant_id: str
    category: str
    params: dict[str, Any] = Field(default_factory=dict)


class TrustedMerchantStore:
    def __init__(self, trusted_path: str) -> None:
        self._path = Path(trusted_path).expanduser()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._trusted: set[str] = set()
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            save_json_atomic(self._path, {"trusted_merchants": []})
            self._trusted = set()
            return

        payload = load_json_secure(self._path, require_mode=0o600)
        merchants = payload.get("trusted_merchants", [])
        self._trusted = set(str(merchant) for merchant in merchants)

    def is_trusted(self, merchant_id: str) -> bool:
        return merchant_id in self._trusted

    def add_trusted_merchant(self, merchant_id: str) -> None:
        self._trusted.add(merchant_id)
        save_json_atomic(self._path, {"trusted_merchants": sorted(self._trusted)})


class SlackApprovalRequester:
    def __init__(self, token_path: str, channel: str, rate_limiter: TokenBucket) -> None:
        self._token_path = Path(token_path).expanduser()
        self._channel = channel
        self._rate_limiter = rate_limiter
        self._client: httpx.AsyncClient | None = None
        self._token: str | None = None

    def initialize(self) -> None:
        if not self._token_path.exists():
            raise FileNotFoundError(f"Slack token file not found: {self._token_path}")

        mode = self._token_path.stat().st_mode & 0o777
        if mode != 0o600:
            raise PermissionError(
                f"Slack token file must be chmod 600, found {oct(mode)}"
            )

        self._token = self._token_path.read_text(encoding="utf-8").strip()
        self._client = httpx.AsyncClient(base_url="https://slack.com/api", timeout=10.0)

    async def request_approval(self, merchant_id: str, amount: Decimal, category: str) -> bool:
        if self._client is None or self._token is None:
            raise RuntimeError("SlackApprovalRequester is not initialized")

        await self._rate_limiter.acquire()
        response = await self._client.post(
            "/chat.postMessage",
            json={
                "channel": self._channel,
                "text": (
                    f"Approval requested for new merchant {merchant_id} with amount {amount} "
                    f"and category {category}. Please review before first purchase."
                ),
            },
            headers={"Authorization": f"Bearer {self._token}"},
        )
        response.raise_for_status()
        payload = response.json()
        return bool(payload.get("ok", False))

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            self._token = None


class NexusAgent:
    def __init__(
        self,
        budget: Budget,
        policy: PolicyEvaluator,
        commerce: CommerceTool,
        audit_chain: AuditChain,
        trusted_merchants_path: str,
        approval_requester: SlackApprovalRequester,
    ) -> None:
        self._budget = budget
        self._policy = policy
        self._commerce = commerce
        self._audit = audit_chain
        self._trusted_store = TrustedMerchantStore(trusted_merchants_path)
        self._approval_requester = approval_requester

    async def process_purchase(self, intent_payload: dict[str, Any]) -> dict[str, Any]:
        intent = TaskIntentSchema.model_validate(intent_payload)
        amount = Decimal(str(intent.params.get("amount", 0)))

        if not self._trusted_store.is_trusted(intent.merchant_id):
            self._approval_requester.initialize()
            try:
                approved = await self._approval_requester.request_approval(
                    intent.merchant_id,
                    amount,
                    intent.category,
                )
            finally:
                await self._approval_requester.close()

            if not approved:
                raise PolicyViolationError(
                    "First purchase from untrusted merchant requires human Slack approval"
                )

            raise PolicyViolationError(
                "Merchant approval requested. Add merchant to trusted list before retrying."
            )

        await self._policy.evaluate_async(amount, intent.category)
        await self._budget.check_and_record(amount)

        payload = dict(intent.params)
        payload["merchant_id"] = intent.merchant_id

        self._commerce.initialize()
        try:
            purchase_response = await self._commerce.purchase(payload)
            # Compute signature BEFORE close() wipes the key
            signature = self._commerce._wallet.sign_payload(
                json.dumps(payload, sort_keys=True).encode("utf-8")
            ).hex()
        finally:
            await self._commerce.close()

        audit_entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            transaction_id=str(purchase_response.get("transaction_id", "")),
            merchant_id=intent.merchant_id,
            amount=str(amount),
            category=intent.category,
            signature=signature,
            previous_hash=self._audit.get_last_hash(),
            metadata={"purchase_response": purchase_response},
        )

        self._audit.append(audit_entry)
        return purchase_response
