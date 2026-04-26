#!/usr/bin/env bash
# Nexus Agent v1.0.0 - Staging Deployment Script
# Usage: bash deploy_staging.sh
# Prerequisites: GCP project, gcloud CLI, GHCR token

set -e

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="us-central1"
IMAGE_TAG="v1.0.0"
GHCR_REPO="ghcr.io/5432190/nexus-agent"
TF_STATE_BUCKET="nexus-agent-terraform-state"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ============================================================================
# VALIDATION
# ============================================================================

function check_prerequisites() {
  echo "🔍 Checking prerequisites..."
  
  # Check required tools
  for cmd in gcloud terraform docker; do
    if ! command -v $cmd &> /dev/null; then
      echo -e "${RED}❌ $cmd not found${NC}"
      exit 1
    fi
  done
  
  # Check GCP project
  if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ GCP_PROJECT_ID not set${NC}"
    echo "   Run: export GCP_PROJECT_ID='your-project-id'"
    exit 1
  fi
  
  # Check wallet files
  WALLET_FILE="${HOME}/.nexus/wallet.pem"
  CONFIG_FILE="./config/config.yaml"
  
  if [ ! -f "$WALLET_FILE" ]; then
    echo -e "${RED}❌ Wallet PEM not found at $WALLET_FILE${NC}"
    exit 1
  fi
  
  if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ Config not found at $CONFIG_FILE${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}✅ All prerequisites met${NC}"
}

# ============================================================================
# STEP 1: GCS Backend Setup
# ============================================================================

function setup_gcs_backend() {
  echo ""
  echo "📦 Setting up GCS backend..."
  
  if gsutil ls -b "gs://${TF_STATE_BUCKET}" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Bucket already exists${NC}"
  else
    gsutil mb -p "$PROJECT_ID" -l "$REGION" "gs://${TF_STATE_BUCKET}"
    echo -e "${GREEN}✅ Created GCS bucket${NC}"
  fi
}

# ============================================================================
# STEP 2: Terraform Init & Plan
# ============================================================================

function terraform_plan() {
  echo ""
  echo "📋 Terraform plan (staging)..."
  
  cd infra
  
  # Create terraform.tfvars
  cat > terraform.tfvars <<EOF
project_id         = "${PROJECT_ID}"
region              = "${REGION}"
env                 = "staging"
image_tag           = "${IMAGE_TAG}"
wallet_pem          = file("${WALLET_FILE}")
config_secret_data  = file("../config/config.yaml")
EOF
  
  terraform init -backend-config="bucket=${TF_STATE_BUCKET}"
  terraform plan -out=tfplan
  
  echo -e "${GREEN}✅ Terraform plan generated${NC}"
  echo "   Review: cat tfplan"
  echo "   Apply:  terraform apply tfplan"
  
  cd ..
}

# ============================================================================
# STEP 3: Docker Build & Push
# ============================================================================

function docker_build_push() {
  echo ""
  echo "🐳 Building and pushing Docker image..."
  
  # Verify GHCR auth
  if [ -z "$GHCR_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  GHCR_TOKEN not set (push will fail)${NC}"
    echo "   Run: export GHCR_TOKEN='your-token'"
    echo "   Then: echo \$GHCR_TOKEN | docker login ghcr.io -u USERNAME --password-stdin"
  fi
  
  docker build -t "${GHCR_REPO}:${IMAGE_TAG}" .
  docker tag "${GHCR_REPO}:${IMAGE_TAG}" "${GHCR_REPO}:latest"
  
  echo -e "${GREEN}✅ Image built${NC}"
  
  if [ -n "$GHCR_TOKEN" ]; then
    docker push "${GHCR_REPO}:${IMAGE_TAG}"
    docker push "${GHCR_REPO}:latest"
    echo -e "${GREEN}✅ Image pushed to GHCR${NC}"
  else
    echo -e "${YELLOW}⚠️  Skipping push (GHCR_TOKEN not set)${NC}"
  fi
}

# ============================================================================
# STEP 4: Git Tag & Release
# ============================================================================

function git_tag_release() {
  echo ""
  echo "🏷️  Creating v1.0.0 release tag..."
  
  if git rev-parse "v${IMAGE_TAG}" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Tag already exists${NC}"
  else
    git tag -a "v${IMAGE_TAG}" -m "Production release: Nexus Agent ${IMAGE_TAG}"
    git push origin main --tags
    echo -e "${GREEN}✅ Tagged and pushed v${IMAGE_TAG}${NC}"
  fi
}

# ============================================================================
# STEP 5: Post-Deploy Validation
# ============================================================================

function validate_staging() {
  echo ""
  echo "✅ Validating staging deployment..."
  echo ""
  echo "NEXT STEPS:"
  echo "1. Apply Terraform:"
  echo "   cd infra && terraform apply tfplan"
  echo ""
  echo "2. Wait for Cloud Run deployment (~2 min)"
  echo ""
  echo "3. Verify health:"
  echo "   curl -f \$(cd infra && terraform output -raw service_url)/health"
  echo ""
  echo "4. Test audit chain:"
  echo "   python verify_audit.py --audit-log audit/log.jsonl"
  echo ""
  echo "5. Schedule customer demo with staging URL"
}

# ============================================================================
# MAIN
# ============================================================================

function main() {
  echo "🚀 Nexus Agent v1.0.0 - Staging Deployment"
  echo "============================================"
  echo ""
  
  check_prerequisites
  setup_gcs_backend
  terraform_plan
  docker_build_push
  git_tag_release
  validate_staging
  
  echo ""
  echo -e "${GREEN}✅ Deployment preparation complete${NC}"
}

main "$@"
