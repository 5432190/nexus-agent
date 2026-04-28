from pathlib import Path
import re

p = Path("nexus_agent/tools/commerce.py")
content = p.read_text(encoding="utf-8")

# Corrected StripeTool using classic module API
new_tool = '''
class StripeTool:
    """Stripe adapter using classic module API (works on SDK v14 & v15+)."""
    def __init__(self, api_key: str, wallet, rate_limiter):
        self._api_key = api_key
        self._wallet = wallet
        self._rate_limiter = rate_limiter

    async def charge(self, amount, customer_id: str, description: str) -> dict:
        import json
        import stripe
        
        # Sign intent for audit chain
        intent = {"amount": str(amount), "customer_id": customer_id, "description": description}
        signature = self._wallet._backend.sign(json.dumps(intent).encode())
        
        # Configure Stripe & convert amount to cents
        stripe.api_key = self._api_key
        amount_cents = int(float(amount) * 100)
        
        # Create payment (sync call, fully compatible with async context)
        payment = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="usd",
            customer=customer_id,
            description=description,
            metadata={"agent_signature": signature.hex(), "nexus_agent": "v1.0"}
        )
        return {"status": payment.status, "id": payment.id, "amount": str(amount)}
'''

# Replace existing StripeTool class or append if not found
pattern = r'(class StripeTool:.*?)(?=\nclass |\Z)'
if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, new_tool.strip(), content, flags=re.DOTALL)
    p.write_text(content, encoding="utf-8")
    print("✅ StripeTool patched for real Stripe API calls")
else:
    with open(p, "a", encoding="utf-8") as f:
        f.write("\n" + new_tool)
    print("✅ StripeTool appended")
