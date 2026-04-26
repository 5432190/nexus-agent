# Nexus Agent Pilot Service Agreement - Liability Addendum

**Effective Date:** [Date]  
**Service Provider:** Nexus Agent  
**Customer:** [Customer Name]  
**Pilot Period:** [Start Date] to [End Date] (30 days minimum)  

---

## 1. Service Description

Nexus Agent provides autonomous transaction authorization and execution for cloud purchases within defined policy boundaries. The service:

- Operates within customer-defined budget caps (e.g., $50 per transaction)
- Enforces category allowlists (e.g., compute, storage, CI/CD)
- Requires Slack approval for untrusted merchants
- Maintains cryptographically signed audit logs
- Executes purchases on customer's behalf via cloud API credentials

---

## 2. Liability Scope

### Service Provider Liability Limits

Nexus Agent's total liability for any claim arising from this pilot is limited to **fees paid to Nexus Agent in the pilot period**, capped at **$799**.

This includes liability for:
- Unauthorized transactions within policy bounds
- Audit log tampering or loss
- Slack approval workflow failures
- Incorrect budget cap enforcement

### Customer Liability Exclusions

**Nexus Agent is NOT liable for:**

- Customer's failure to review Slack approval messages before expiry (120 seconds)
- Customer's loss of cloud API credentials prior to audit discovery
- Third-party cloud provider API errors or outages
- Transactions that comply with policy but have unintended business consequences
- Data loss due to customer's deletion of audit log files

---

## 3. Security Assumptions

Customer acknowledges and accepts:

- **Assumption 1:** Slack workspace is accessible only to authorized decision-makers
- **Assumption 2:** Cloud API credentials are rotated every 90 days minimum
- **Assumption 3:** Audit log directory (`/audit`) is backed up daily
- **Assumption 4:** Agent public key (`agent.pub`) is verified against GitHub releases before deployment
- **Assumption 5:** Policy files (`trusted_merchants.json`, budget caps) are version-controlled

**If any assumption is violated, Nexus Agent is not liable for resulting losses.**

---

## 4. Required Controls (Non-Negotiable)

Before service activation, Customer must:

- [ ] Deploy agent to staging environment with test credentials
- [ ] Run end-to-end approval workflow with at least one test transaction
- [ ] Verify audit chain with `python verify_audit.py` against staging log
- [ ] Rotate cloud API credentials to temporary "pilot" key (revoke after pilot)
- [ ] Define budget cap in policy <= $50 for Week 1 (increase after stabilization)
- [ ] Name at least 2 authorized approvers in Slack group
- [ ] Document kill-switch procedure: `~/.nexus/policy_override.yaml` with `enabled: false`

---

## 5. Approval and Signing

By signing below, both parties acknowledge:

- This pilot is experimental; production deployment requires separate SLA
- Customer has read the liability scope and accepts the limitations
- Customer has implemented all required controls listed in Section 4
- Either party may terminate with 7 days' written notice

**Service Provider:**  
Name: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
Title: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
Date: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
Signature: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  

**Customer:**  
Name: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
Title: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
Date: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
Signature: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  

---

## 6. Appendix: Verification Checklist (Pre-Demo)

Before customer demo, run these commands:

```bash
# 1. Terraform plan validates correctly
cd infra
terraform init
terraform plan -out=tfplan -var="env=staging" 2>&1 | tee tfplan.log
# → Verify: no "allUsers" bindings, secrets resolve, SA scoped to run.invoker only

# 2. Audit chain verifies after test transaction
python verify_audit.py \
  --audit-log audit/log.jsonl \
  --public-key keys/agent.pub
# → Must output: "✅ Chain verified from genesis to [hash]"

# 3. Policy enforcement tested
pytest tests/test_agent_unit.py::test_budget_cap_enforcement -v
# → Must exit 0

# 4. Slack approval timeout tested (120s max)
pytest tests/test_tools.py::test_commerce_purchase_403_rejection -v
# → Must exit 0
```

**If all commands exit 0 → you're demo-ready.**

---

## Questions?

Contact: [Your Email]  
Slack: [Workspace Channel]  
GitHub: [Agent Repository]
