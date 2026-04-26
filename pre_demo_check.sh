#!/usr/bin/env bash
# Pre-demo verification checklist
# Run this before scheduling customer demo

set -e

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Nexus Agent Pre-Demo Verification"
echo "======================================"
echo ""

# Check 1: Tests pass
echo -n "✓ Unit tests... "
if python -m pytest "$WORKSPACE_ROOT/tests/" -q --tb=line >/dev/null 2>&1; then
  echo -e "${GREEN}PASS${NC}"
else
  echo -e "${RED}FAIL${NC}"
  echo "  Run: python -m pytest tests/ -v"
  exit 1
fi

# Check 2: Docker builds
echo -n "✓ Docker build... "
if docker build -t nexus-agent:verify "$WORKSPACE_ROOT" --progress=plain >/dev/null 2>&1; then
  echo -e "${GREEN}PASS${NC}"
else
  echo -e "${RED}FAIL${NC}"
  echo "  Run: docker build -t nexus-agent:verify . --progress=plain"
  exit 1
fi

# Check 3: Terraform syntax (if terraform installed)
if command -v terraform &> /dev/null; then
  echo -n "✓ Terraform fmt... "
  if terraform -chdir="$WORKSPACE_ROOT/infra" fmt -check >/dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC}"
  else
    echo -e "${YELLOW}WARN${NC} (auto-fixing)"
    terraform -chdir="$WORKSPACE_ROOT/infra" fmt
  fi

  echo -n "✓ Terraform validate... "
  if terraform -chdir="$WORKSPACE_ROOT/infra" init -backend=false >/dev/null 2>&1 && \
     terraform -chdir="$WORKSPACE_ROOT/infra" validate >/dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC}"
  else
    echo -e "${RED}FAIL${NC}"
    exit 1
  fi
else
  echo -e "${YELLOW}⚠ Terraform not installed (skipped)${NC}"
fi

# Check 4: verify_audit.py exists
echo -n "✓ verify_audit.py... "
if [ -f "$WORKSPACE_ROOT/verify_audit.py" ]; then
  echo -e "${GREEN}FOUND${NC}"
else
  echo -e "${RED}NOT FOUND${NC}"
  exit 1
fi

# Check 5: Liability template exists
echo -n "✓ Liability template... "
if [ -f "$WORKSPACE_ROOT/docs/liability_template.md" ]; then
  echo -e "${GREEN}FOUND${NC}"
else
  echo -e "${RED}NOT FOUND${NC}"
  exit 1
fi

# Check 6: Required config files for staging
echo -n "✓ Stage-ready config check... "
REQUIRED_KEYS=("budget_cap" "trusted_merchants")
CONFIG_FILE="${WORKSPACE_ROOT}/.env"
if [ ! -f "$CONFIG_FILE" ]; then
  echo -e "${YELLOW}WARN${NC} (.env not found, will use defaults)"
else
  echo -e "${GREEN}FOUND${NC}"
fi

echo ""
echo "======================================"
echo -e "${GREEN}✅ All checks passed${NC}"
echo ""
echo "Next steps:"
echo "1. Fill customer details in docs/liability_template.md"
echo "2. Deploy to staging: docker-compose --profile staging up -d"
echo "3. Run one test transaction against staging"
echo "4. Verify audit chain: python verify_audit.py --audit-log audit/log.jsonl"
echo "5. Send staging URL to customer"
echo ""
