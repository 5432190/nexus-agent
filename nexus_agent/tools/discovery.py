"""Merchant discovery tool for Nexus Agent."""

from __future__ import annotations

from typing import Any

import httpx

from ..rate_limiter import TokenBucket


class DiscoveryTool:
    """Discovery tool responsible for merchant lookup and metadata retrieval."""

    def __init__(self, base_url: str, rate_limiter: TokenBucket) -> None:
        self._base_url = base_url
        self._rate_limiter = rate_limiter
        self._client: httpx.AsyncClient | None = None

    def initialize(self) -> None:
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=10.0)

    async def find_merchant(self, merchant_id: str) -> dict[str, Any]:
        if self._client is None:
            raise RuntimeError("DiscoveryTool is not initialized")

        await self._rate_limiter.acquire()
        response = await self._client.get(f"/merchants/{merchant_id}")
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
