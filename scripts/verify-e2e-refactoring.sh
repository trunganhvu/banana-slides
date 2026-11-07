#!/bin/bash

# Config
# Config

set -e

echo "======================================"
echo "🔍 E2E "
echo "======================================"
echo

# Config
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Config
echo "1.  E2E ..."
if [ -d "frontend/e2e" ]; then
    check_pass "frontend/e2e/ "
else
    check_fail "frontend/e2e/ "
fi

# Config
echo "2.  E2E ..."
if [ -f "frontend/e2e/ui-full-flow.spec.ts" ]; then
    check_pass "ui-full-flow.spec.ts  frontend/e2e/"
else
    check_fail "ui-full-flow.spec.ts  frontend/e2e/"
fi

if [ -f "frontend/e2e/visual-regression.spec.ts" ]; then
    check_pass "visual-regression.spec.ts  frontend/e2e/"
else
    check_fail "visual-regression.spec.ts  frontend/e2e/"
fi

# Config
echo "3.  Playwright ..."
if [ -f "frontend/playwright.config.ts" ]; then
    check_pass "playwright.config.ts  frontend/"
else
    check_fail "playwright.config.ts  frontend/"
fi

# Config
echo "4.  package.json..."
if grep -q "@playwright/test" frontend/package.json; then
    check_pass "frontend/package.json  Playwright "
else
    check_fail "frontend/package.json  Playwright "
fi

if grep -q "test:e2e" frontend/package.json; then
    check_pass "frontend/package.json  E2E "
else
    check_fail "frontend/package.json  E2E "
fi

# Config
echo "5. ..."
if [ -f "backend/tests/integration/test_api_full_flow.py" ]; then
    check_pass "test_api_full_flow.py  backend/tests/integration/"
else
    check_fail "test_api_full_flow.py  backend/tests/integration/"
fi

# Config
echo "6. ..."
if [ ! -d "e2e" ]; then
    check_pass " e2e/ "
else
    check_warn " e2e/ "
fi

if [ ! -f "playwright.config.ts" ]; then
    check_pass " playwright.config.ts "
else
    check_warn " playwright.config.ts "
fi

if [ ! -f "tsconfig.json" ]; then
    check_pass " tsconfig.json "
else
    check_warn " tsconfig.json "
fi

if [ ! -d "node_modules" ]; then
    check_pass " node_modules/ "
else
    check_warn " node_modules/ "
fi

# Config
echo "7.  CI ..."
if grep -q "cd frontend" .github/workflows/ci-test.yml; then
    check_pass "CI  'cd frontend'"
else
    check_warn "CI "
fi

if grep -q "test_api_full_flow.py" .github/workflows/ci-test.yml; then
    check_pass "CI  API "
else
    check_warn "CI  API "
fi

# Config
echo "8.  .gitignore..."
if grep -q "test-results/" frontend/.gitignore; then
    check_pass "frontend/.gitignore "
else
    check_warn "frontend/.gitignore "
fi

echo
echo "======================================"
echo "✅ E2E "
echo "======================================"
echo
echo ""
echo "1. cd frontend && npm install  #  Playwright"
echo "2. cd frontend && npm run test:e2e  #  E2E "
echo "3. cd backend && uv run pytest tests/integration/ -v  # "
echo
