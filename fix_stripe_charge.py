import re
from pathlib import Path

p = Path("nexus_agent/tools/commerce.py")
content = p.read_text(encoding="utf-8")

# The complete, working charge method
new_charge_method = '''    async def charge(self, amount, customer_id: str, description: str) -> dict:
        """Charge a customer with policy enforcement."""
        import json
        # Sign the intent for audit
        intent = {"amount": str(amount), "customer_id": customer_id, "description": description}
        signature = self._wallet._backend.sign(json.dumps(intent).encode())
        
        # Execute Stripe charge (amount MUST be plain int cents for SDK v15+)
        # Convert Decimal to int cents safely
        amount_cents = int(float(amount) * 100)
        
        payment = await self._client.v1.payment_intents.create(
            amount=amount_cents,
            currency="usd",
            customer=customer_id,
            description=description,
            metadata={"agent_signature": signature.hex(), "nexus_agent": "v1.0"}
        )
        return {"status": payment.status, "id": payment.id, "amount": str(amount)}'''

# Pattern to find and replace the entire charge method
# Match from "async def charge" to the next "async def" or end of class
pattern = r'(    async def charge\(self, amount, customer_id: str, description: str\) -> dict:.*?)(?=\n    async def |\nclass |\Z)'

# Use re.DOTALL to match across newlines
content = re.sub(pattern, new_charge_method, content, flags=re.DOTALL)

p.write_text(content, encoding="utf-8")
print("✅ Replaced StripeTool.charge method with working version")
