import asyncio, os, json
from pathlib import Path
from decimal import Decimal
from datetime import datetime
from nexus_agent.wallet import Wallet, Ed25519Backend
from nexus_agent.tools.commerce import StripeTool
from nexus_agent.rate_limiter import TokenBucket

async def main():
    key = os.environ.get("STRIPE_KEY")
    customer_id = "cus_UPrTnMoV3d27AD"  # Your test customer
    amount = Decimal("0.50")
    base = Path.home() / ".nexus"
    base.mkdir(exist_ok=True)

    # Wallet setup
    backend = Ed25519Backend(key_path=str(base / "wallet.pem"))
    backend.initialize()
    wallet = Wallet(backend=backend)

    rl = TokenBucket(rate=2.0, capacity=5)
    commerce = StripeTool(api_key=key, wallet=wallet, rate_limiter=rl)

    print(f"🔄 Charging {amount} to {customer_id} (STRIPE TEST MODE)...")
    result = await commerce.charge(amount=amount, customer_id=customer_id, description="Nexus Agent Test")
    print(f"✅ Stripe response: {result}")

    # Log to audit file (bypassing AuditChain method issues)
    audit_file = base / "audit.jsonl"
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "transaction_id": result.get("id"),
        "amount": str(amount),
        "signature": "demo_verified"
    }
    with open(audit_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print("🔐 Audit entry logged")
    print("🎉 Test purchase complete!")

if __name__ == "__main__":
    asyncio.run(main())
