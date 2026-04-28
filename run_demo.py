import asyncio
from pathlib import Path
from decimal import Decimal
import respx
from httpx import Response
from nexus_agent.agent import NexusAgent
from nexus_agent.budget import Budget
from nexus_agent.policy import PolicyConfig, PolicyEvaluator
from nexus_agent.audit import AuditChain
from nexus_agent.wallet import Wallet, Ed25519Backend
from nexus_agent.tools.commerce import CommerceTool
from nexus_agent.rate_limiter import TokenBucket

class StubApproval:
    def initialize(self): pass
    async def close(self): pass
    async def request_approval(self, *a, **k): return True

async def main():
    base = Path.home() / '.nexus'
    base.mkdir(exist_ok=True)
    backend = Ed25519Backend(key_path=str(base / 'wallet.pem'))
    backend.initialize()
    wallet = Wallet(backend=backend)
    budget = Budget(budget_file=str(base / 'budget.json'), monthly_cap=Decimal('500'))
    policy = PolicyEvaluator(config=PolicyConfig(
        monthly_budget=Decimal('500'),
        single_transaction_limit=Decimal('50'),
        allowed_categories=['api_key'],
        blocked_categories=[],
        risk_tolerance='LOW'
    ))
    rl = TokenBucket(rate=2.0, capacity=5)
    commerce = CommerceTool(base_url='https://api.example.com', wallet=wallet, rate_limiter=rl)
    commerce.initialize()
    audit_chain = AuditChain(
        audit_file=str(base / 'audit.jsonl'),
        public_key_path=str(base / 'wallet_public.pem')
    )
    agent = NexusAgent(
        budget=budget,
        policy=policy,
        commerce=commerce,
        audit_chain=audit_chain,
        trusted_merchants_path=str(base / 'trusted_merchants.json'),
        approval_requester=StubApproval()
    )
    with respx.mock:
        respx.post("https://api.example.com/purchase").mock(
            return_value=Response(200, json={"order_id": "ord_123", "status": "confirmed", "amount": "10.00"})
        )
        print('Running purchase...')
        # Ensure wallet backend is initialized before signing
        agent._commerce._wallet._backend.initialize()
        result = await agent.process_purchase(intent_payload={
            "merchant_id": "api.example.com",
            "category": "api_key",
            "params": {"amount": "10.00", "aom_id": "gpu-001"}
        })
        print('Result:', result)
        print('Done!')

asyncio.run(main())
