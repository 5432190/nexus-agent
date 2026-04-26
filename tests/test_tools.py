"""Tests for Nexus Agent HTTP tools."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
import respx
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from httpx import HTTPStatusError

from nexus_agent.rate_limiter import TokenBucket
from nexus_agent.tools.commerce import CommerceTool
from nexus_agent.tools.discovery import DiscoveryTool
from nexus_agent.wallet import Ed25519Backend, Wallet


@pytest.fixture
def wallet_file(tmp_path: Path) -> Path:
    private_key = Ed25519PrivateKey.generate()
    key_path = tmp_path / "test_key.pem"
    key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    key_path.write_bytes(key_bytes)
    key_path.chmod(0o600)
    return key_path


@pytest.fixture
def wallet(wallet_file: Path) -> Wallet:
    backend = Ed25519Backend(str(wallet_file))
    return Wallet(backend)


@pytest.mark.asyncio
async def test_discovery_search_success(mock_httpx) -> None:
    route = mock_httpx.get("https://api.example.com/merchants/merchant123").respond(
        json={"id": "merchant123", "name": "Test Merchant"}
    )
    rate_limiter = TokenBucket(rate=1.0, capacity=1.0)
    tool = DiscoveryTool("https://api.example.com", rate_limiter)
    tool.initialize()
    try:
        merchant = await tool.find_merchant("merchant123")
    finally:
        await tool.close()

    assert route.called
    assert merchant["id"] == "merchant123"


@pytest.mark.asyncio
async def test_commerce_purchase_includes_signature_in_payload(mock_httpx, wallet) -> None:
    route = mock_httpx.post("https://api.example.com/purchase").respond(
        json={"transaction_id": "tx-123", "status": "ok"}, status_code=200
    )
    rate_limiter = TokenBucket(rate=1.0, capacity=1.0)
    commerce = CommerceTool("https://api.example.com", wallet, rate_limiter)
    commerce.initialize()
    try:
        response = await commerce.purchase({"merchant_id": "merchant123", "amount": "10.00"})
    finally:
        await commerce.close()

    assert response["status"] == "ok"
    assert route.called
    request_json = json.loads(route.calls.last.request.content.decode("utf-8"))
    assert request_json["merchant_id"] == "merchant123"
    assert "signature" in request_json
    assert isinstance(request_json["signature"], str)


@pytest.mark.asyncio
async def test_commerce_purchase_403_rejection(mock_httpx, wallet) -> None:
    mock_httpx.post("https://api.example.com/purchase").respond(status_code=403, json={"error": "forbidden"})
    rate_limiter = TokenBucket(rate=1.0, capacity=1.0)
    commerce = CommerceTool("https://api.example.com", wallet, rate_limiter)
    commerce.initialize()
    try:
        with pytest.raises(HTTPStatusError):
            await commerce.purchase({"merchant_id": "merchant123", "amount": "10.00"})
    finally:
        await commerce.close()
