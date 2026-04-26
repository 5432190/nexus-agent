import asyncio, respx
from pathlib import Path
from decimal import Decimal
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
    backend = Ed25519Backend(key_path=str(base / 'wallet.pem'))
    try: backend.initialize()
    except PermissionError as e: print(f'⚠️  {e}')
    wallet = Wallet(backend=backend)
    budget = Budget(budget_file=str(base / 'budget.json'), monthly_cap=Decimal('500'))
    policy = PolicyEvaluator(config=PolicyConfig(
        monthly_budget=Decimal('500'), single_transaction_limit=Decimal('50'),
        allowed_categories=['api_key'], blocked_categories=[], risk_tolerance='LOW'))
    commerce = CommerceTool(base_url='http://localhost:8080', wallet=wallet, rate_limiter=TokenBucket(2.0, 5))
    audit_chain = AuditChain(audit_file=str(base / 'audit.jsonl'), public_key_path=str(base / 'wallet_public.pem'))
    agent = NexusAgent(budget=budget, policy=policy, commerce=commerce, audit_chain=audit_chain,
                       trusted_merchants_path=str(base / 'trusted_merchants.json'), approval_requester=StubApproval())
    with respx.mock:
        respx.post('http://localhost:8080/purchase').mock(return_value=Response(200, json={'order_id': 'ord_123', 'status': 'confirmed', 'amount': '10.00'}))
        result = await agent.process_purchase(intent_payload={'merchant_id': 'api.example.com', 'category': 'api_key', 'params': {'amount': '10.00', 'aom_id': 'gpu-001'}})
        print(f'✅ Result: {result}')

asyncio.run(main())

