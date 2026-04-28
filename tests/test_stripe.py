"""Tests for StripeTool integration."""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from nexus_agent.tools.commerce import StripeTool
from nexus_agent.wallet import Wallet, Ed25519Backend
from nexus_agent.rate_limiter import TokenBucket

@pytest.mark.asyncio
async def test_stripe_charge_success(tmp_path):
    key_path = tmp_path / "key.pem"
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    key = Ed25519PrivateKey.generate()
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    key_path.write_bytes(pem)
    backend = Ed25519Backend(key_path=str(key_path))
    backend.initialize()
    wallet = Wallet(backend=backend)
    
    rl = TokenBucket(rate=10, capacity=10)
    tool = StripeTool(api_key="sk_test_mock", wallet=wallet, rate_limiter=rl)
    
    with patch.object(tool._client.v1.payment_intents, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = type("obj", (object,), {"status": "succeeded", "id": "pi_123"})()
        result = await tool.charge(Decimal("1.00"), "cus_test", "Test charge")
        assert result["status"] == "succeeded"
        assert result["id"] == "pi_123"
        assert result["amount"] == "1.00"
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        assert "agent_signature" in call_kwargs["metadata"]

@pytest.mark.asyncio
async def test_stripe_charge_amount_in_cents(tmp_path):
    key_path = tmp_path / "key.pem"
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    key = Ed25519PrivateKey.generate()
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    key_path.write_bytes(pem)
    backend = Ed25519Backend(key_path=str(key_path))
    backend.initialize()
    wallet = Wallet(backend=backend)
    
    rl = TokenBucket(rate=10, capacity=10)
    tool = StripeTool(api_key="sk_test_mock", wallet=wallet, rate_limiter=rl)
    
    with patch.object(tool._client.v1.payment_intents, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = type("obj", (object,), {"status": "succeeded", "id": "pi_456"})()
        await tool.charge(Decimal("2.50"), "cus_test", "Test charge")
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["amount"] == 250

