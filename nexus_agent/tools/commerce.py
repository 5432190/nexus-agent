"""Commerce execution tool for Nexus Agent."""

from __future__ import annotations

import json
from typing import Any

import httpx

from ..wallet import Wallet
from ..rate_limiter import TokenBucket


class CommerceTool:
    """Commerce tool that performs purchases and signs payloads."""

    def __init__(self, base_url: str, wallet: Wallet, rate_limiter: TokenBucket) -> None:
        self._base_url = base_url
        self._wallet = wallet
        self._rate_limiter = rate_limiter
        self._client: httpx.AsyncClient | None = None

    def initialize(self) -> None:
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=10.0)
        self._wallet.initialize()

    async def purchase(self, params: dict[str, Any]) -> dict[str, Any]:
        if self._client is None:
            raise RuntimeError("CommerceTool is not initialized")

        payload = json.dumps(params, sort_keys=True).encode("utf-8")
        signature = self._wallet.sign_payload(payload)

        request_body = {**params, "signature": signature.hex()}
        request_payload = json.dumps(request_body, sort_keys=True).encode("utf-8")

        headers = {"Content-Type": "application/json"}

        await self._rate_limiter.acquire()
        response = await self._client.post("/purchase", content=request_payload, headers=headers)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        self._wallet.close()


class StripeTool:
    def __init__(self, api_key: str, wallet, rate_limiter):
        import stripe
        self._client = stripe.StripeClient(api_key)
        self._wallet = wallet
        self._rate_limiter = rate_limiter

    async def charge(self, amount, customer_id: str, description: str) -> dict:
        import json
        intent = {"amount": str(amount), "customer_id": customer_id, "description": description}
        # Use backend directly for signing
        signature = self._wallet._backend.sign(json.dumps(intent).encode())
        payment = await self._client.v1.payment_intents.create(
            amount=int(amount * 100),
            currency="usd",
            customer=customer_id,
            description=description,
            metadata={"agent_signature": signature.hex(), "nexus_agent": "v1.0"}
        )
        return {"status": payment.status, "id": payment.id, "amount": str(amount)}
