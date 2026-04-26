# Nexus Agent v1.0.0 - Deployment Checklist

This document traces the exact steps to deploy Nexus Agent to staging, then production.

## Pre-Deployment Checklist

### Code Readiness ✅
- [x] Tests pass: 7/7
- [x] Docker builds clean
- [x] Cold-start warmup deployed to main
- [x] Pre-demo verification tools ready (`verify_audit.py`, `pre_demo_check.sh`)
- [x] Liability template available (`docs/liability_template.md`)

### Infrastructure Readiness (GCP)
Before `terraform apply`, ensure you have:

```bash
# 1. GCP Project with billing enabled
export GCP_PROJECT_ID="your-nexus-project-id"

# 2. gcloud CLI authenticated
gcloud auth application-default login
gcloud config set project $GCP_PROJECT_ID

# 3. Required APIs enabled
gcloud services enable run.googleapis.com \
  secretmanager.googleapis.com \
  iam.googleapis.com \
  container.googleapis.com

# 4. Service account for GitHub Actions (for prod later)
gcloud iam service-accounts create github-actions-deploy \
  --display-name="GitHub Actions Deploy"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:github-actions-deploy@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:github-actions-deploy@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:github-actions-deploy@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Credentials & Secrets
You need:

1. **Wallet PEM** — Agent's Ed25519 signing key
   ```bash
   # If you have: ~/.nexus/wallet.pem
   ls -la ~/.nexus/wallet.pem
   ```

2. **Config file** — Budget caps, trusted merchants
   ```bash
   # Expected: ./config/config.yaml
   ls -la config/config.yaml
   ```

3. **GHCR Token** — To push container image
   ```bash
   # Create at: https://github.com/settings/tokens/new
   # Scopes: repo, write:packages, delete:packages
   export GHCR_TOKEN="ghcr_your_token_here"
   ```

---

## Step 1: Terraform Review & Plan

```bash
cd /workspaces/nexus-agent

# Review Terraform configuration
cat infra/main.tf     # Cloud Run service
cat infra/variables.tf # Input variables
cat infra/outputs.tf  # Outputs (service URL, etc)

# Initialize Terraform (with backend)
cd infra
terraform init -backend-config="bucket=nexus-agent-terraform-state"

# Plan staging deployment
terraform plan \
  -var="project_id=$GCP_PROJECT_ID" \
  -var="region=us-central1" \
  -var="env=staging" \
  -var="image_tag=v1.0.0" \
  -var="wallet_pem=$(cat ~/.nexus/wallet.pem)" \
  -var="config_secret_data=$(cat ../config/config.yaml)" \
  -out=tfplan

# Review output for:
# ✅ google_secret_manager_secret_version.wallet_secret_version created
# ✅ google_cloud_run_v2_service.agent created
# ✅ google_cloud_run_service_iam_member.staging_invoker (count=1, allUsers)
# ❌ NOT: google_cloud_run_service_iam_member.prod_invoker (prod-only)

echo "Review looks good? Run: terraform apply tfplan"
```

---

## Step 2: Deploy to Staging

```bash
cd infra

# Apply Terraform (creates Cloud Run service + secrets)
terraform apply tfplan

# Capture outputs
SERVICE_URL=$(terraform output -raw service_url)
WALLET_SECRET=$(terraform output -raw secret_version_name)

echo "Service URL: $SERVICE_URL"
echo "Secrets deployed: $WALLET_SECRET"
```

Wait 1-2 minutes for Cloud Run to deploy the container image.

---

## Step 3: Verify Staging Deployment

```bash
cd /workspaces/nexus-agent

# 1. Health check
curl -f "$SERVICE_URL/health"
# Expected: 200 OK

# 2. Verify audit chain (after test purchase)
python verify_audit.py \
  --audit-log audit/log.jsonl \
  --public-key keys/agent.pub

# Expected output: "✅ Chain verified from genesis to [hash]..."

# 3. Run pre-demo validation
bash pre_demo_check.sh
```

---

## Step 4: Tag v1.0.0 Release

Once staging is validated:

```bash
git tag -a v1.0.0 -m "Production release: Nexus Agent v1.0.0"
git push origin main --tags

# This triggers GitHub Actions:
# - Runs full test suite
# - Builds Docker image: ghcr.io/5432190/nexus-agent:v1.0.0
# - Can push manually: docker push ghcr.io/5432190/nexus-agent:v1.0.0
```

---

## Step 5: Schedule Customer Demo

Once staging is validated:

1. **Fill in customer details** in `docs/liability_template.md`
2. **Send staging URL** to customer
3. **Walk through demo:**
   ```
   1. CI queue > 10 minutes → agent detects AOM
   2. Agent checks trusted_merchants.json
   3. If untrusted → Slack approval webhook sent
   4. Customer clicks APPROVE in Slack
   5. Agent signs transaction + executes purchase
   6. Audit log entry created
   7. Run: python verify_audit.py → chain verified ✅
   ```

---

## Step 6: Pilot Close

Before invoice:

- [ ] Customer signs `docs/liability_template.md` (with dates, names)
- [ ] Slack integration tested end-to-end (approval workflow)
- [ ] Budget cap verified under concurrent load
- [ ] Audit chain verifiable by customer
- [ ] Kill-switch documented in `~/.nexus/policy_override.yaml`

---

## Automated Deployment Script

Instead of manual steps, you can run:

```bash
bash deploy_staging.sh
```

This script:
1. ✅ Checks prerequisites (gcloud, terraform, docker)
2. ✅ Creates GCS backend bucket
3. ✅ Runs `terraform plan`
4. ✅ Builds + pushes Docker image
5. ✅ Tags v1.0.0 release
6. ✅ Outputs next steps

**Requirements:**
```bash
export GCP_PROJECT_ID="your-project"
export GHCR_TOKEN="your-ghcr-token"
bash deploy_staging.sh
```

---

## Troubleshooting

### Terraform state backend error
```
Error: backend initialization required
```
**Fix:** Create GCS bucket first
```bash
gsutil mb gs://nexus-agent-terraform-state
```

### Secrets not accessible to Cloud Run
**Fix:** Verify service account IAM binding
```bash
gcloud projects get-iam-policy $GCP_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:nexus-agent-staging*"
```

### Docker push fails
**Authenticate with GHCR:**
```bash
echo $GHCR_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin
```

### Audit chain verification fails
**Ensure audit log exists and public key matches:**
```bash
ls -la audit/log.jsonl keys/agent.pub
file audit/log.jsonl
```

---

## What Happens Next

| Phase | Action | Success Metric |
|-------|--------|---------------|
| **Staging Demo** | Customer sees approval flow | "This saves us time!" |
| **Pilot Signed** | Customer signs liability addendum | Document in `/contracts/` |
| **Week 1 Prod** | Deploy to prod with real credentials | $0 → $799 MRR |
| **Week 2 Pilot** | Customer approves $50 purchases autonomously | First invoice sent |

---

**Ready to deploy? Run:** `bash deploy_staging.sh`
