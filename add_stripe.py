from pathlib import Path

stripe_code = """
class StripeTool:
    def __init__(self, api_key: str, wallet, rate_limiter):
        import stripe
        self._client = stripe.AsyncStripeClient(api_key)
        self._wallet = wallet
        self._rate_limiter = rate_limiter

    async def charge(self, amount, customer_id: str, description: str) -> dict:
        import json
        intent = {"amount": str(amount), "customer_id": customer_id, "description": description}
        # Use backend directly for signing
        signature = self._wallet._backend.sign(json.dumps(intent).encode())
        payment = await self._client.payment_intents.create(
            amount=int(amount * 100),
            currency="usd",
            customer=customer_id,
            description=description,
            metadata={"agent_signature": signature.hex(), "nexus_agent": "v1.0"}
        )
        return {"status": payment.status, "id": payment.id, "amount": str(amount)}
"""

commerce_path = Path("nexus_agent/tools/commerce.py")
content = commerce_path.read_text(encoding="utf-8")

if "class StripeTool" not in content:
    content += "\n" + stripe_code
    commerce_path.write_text(content, encoding="utf-8")
    print("✅ StripeTool appended to commerce.py")
else:
    print("ℹ️ StripeTool already exists")
