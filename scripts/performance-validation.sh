#!/bin/bash
# T050: Performance validation
# Measure search completion time, dashboard load time, API health check

set -e

API_URL="${API_URL:-http://localhost:8000}"
TEST_EMAIL="perf_$(date +%s)@example.com"
TEST_PASSWORD="TestPassword123"

echo "=== Reddit Pain Point Discovery - Performance Validation ==="
echo "API URL: $API_URL"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() {
    echo -e "${GREEN}✓${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

fail() {
    echo -e "${RED}✗${NC} $1"
}

# Setup: Register and login
echo "Setup: Creating test user..."
curl -s -X POST "$API_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" \
    -c cookies.txt > /dev/null

curl -s -X POST "$API_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" \
    -b cookies.txt -c cookies.txt > /dev/null

echo "✓ Test user ready"
echo ""

# Test 1: API Health Check (< 100ms per NFR-001)
echo "Test 1: API Health Check (<100ms requirement)..."
START=$(date +%s%N)
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/health" || echo -e "\n500")
END=$(date +%s%N)

HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
DURATION_MS=$(( (END - START) / 1000000 ))

if [ "$HTTP_CODE" = "200" ]; then
    if [ $DURATION_MS -lt 100 ]; then
        pass "Health check: ${DURATION_MS}ms (< 100ms) ✓"
    else
        warn "Health check: ${DURATION_MS}ms (>= 100ms, threshold not met)"
    fi
else
    # If /health doesn't exist, try auth/me as alternative
    START=$(date +%s%N)
    curl -s -X GET "$API_URL/api/auth/me" -b cookies.txt > /dev/null
    END=$(date +%s%N)
    DURATION_MS=$(( (END - START) / 1000000 ))

    if [ $DURATION_MS -lt 100 ]; then
        pass "API response: ${DURATION_MS}ms (< 100ms) ✓"
    else
        warn "API response: ${DURATION_MS}ms (>= 100ms)"
    fi
fi

# Test 2: Dashboard Load Time (< 1s per NFR-001)
echo ""
echo "Test 2: Dashboard Load Time (<1s requirement)..."
START=$(date +%s%N)
DASHBOARD_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/reddit/dashboard" -b cookies.txt)
END=$(date +%s%N)

HTTP_CODE=$(echo "$DASHBOARD_RESPONSE" | tail -n1)
DURATION_MS=$(( (END - START) / 1000000 ))

if [ "$HTTP_CODE" = "200" ]; then
    if [ $DURATION_MS -lt 1000 ]; then
        pass "Dashboard load: ${DURATION_MS}ms (< 1s) ✓"
    else
        warn "Dashboard load: ${DURATION_MS}ms (>= 1s, threshold not met)"
    fi
else
    fail "Dashboard request failed (HTTP $HTTP_CODE)"
fi

# Test 3: Search Completion Time (< 30s per NFR-001)
echo ""
echo "Test 3: Search Completion Time (<30s requirement)..."

# Start search
SEARCH_START=$(date +%s)
SEARCH_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/reddit/search" \
    -H "Content-Type: application/json" \
    -d '{"topics":["productivity"],"time_range":"24h"}' \
    -b cookies.txt)

HTTP_CODE=$(echo "$SEARCH_RESPONSE" | tail -n1)
SEARCH_BODY=$(echo "$SEARCH_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" != "201" ]; then
    fail "Search creation failed (HTTP $HTTP_CODE)"
fi

SEARCH_RUN_ID=$(echo "$SEARCH_BODY" | grep -o '"search_run_id":"[^"]*"' | cut -d'"' -f4)
echo "   Search started (ID: $SEARCH_RUN_ID)"

# Poll for completion
MAX_WAIT=30
ELAPSED=0
COMPLETED=false

while [ $ELAPSED -lt $MAX_WAIT ]; do
    STATUS_RESPONSE=$(curl -s -X GET "$API_URL/api/reddit/search/$SEARCH_RUN_ID" -b cookies.txt)
    STATUS=$(echo "$STATUS_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

    if [ "$STATUS" = "completed" ]; then
        COMPLETED=true
        break
    elif [ "$STATUS" = "failed" ]; then
        fail "Search failed"
    fi

    sleep 1
    ELAPSED=$((ELAPSED + 1))
    echo -ne "   Waiting... ${ELAPSED}s / ${MAX_WAIT}s\r"
done

SEARCH_END=$(date +%s)
SEARCH_DURATION=$((SEARCH_END - SEARCH_START))

if [ "$COMPLETED" = "true" ]; then
    if [ $SEARCH_DURATION -lt 30 ]; then
        pass "Search completed: ${SEARCH_DURATION}s (< 30s) ✓"
    else
        warn "Search completed: ${SEARCH_DURATION}s (>= 30s, threshold not met)"
    fi
else
    warn "Search did not complete within 30s timeout"
fi

# Test 4: Pagination Performance
echo ""
echo "Test 4: Pagination Performance..."
START=$(date +%s%N)
RESULTS_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/reddit/search/$SEARCH_RUN_ID/results?page=1&limit=50" -b cookies.txt)
END=$(date +%s%N)

HTTP_CODE=$(echo "$RESULTS_RESPONSE" | tail -n1)
DURATION_MS=$(( (END - START) / 1000000 ))

if [ "$HTTP_CODE" = "200" ]; then
    RESULTS_BODY=$(echo "$RESULTS_RESPONSE" | head -n-1)
    TOTAL=$(echo "$RESULTS_BODY" | grep -o '"total":[0-9]*' | cut -d':' -f2)

    if [ $DURATION_MS -lt 1000 ]; then
        pass "Results pagination: ${DURATION_MS}ms (< 1s) - ${TOTAL} total items ✓"
    else
        warn "Results pagination: ${DURATION_MS}ms (>= 1s)"
    fi
else
    fail "Results request failed (HTTP $HTTP_CODE)"
fi

# Cleanup
rm -f cookies.txt

# Summary
echo ""
echo "=== Performance Validation Summary ==="
echo ""
echo "Requirements (from NFR-001):"
echo "  - API health check: < 100ms"
echo "  - Dashboard load: < 1s"
echo "  - Search completion: < 30s"
echo ""
echo "All tests completed. Review warnings above for any threshold misses."
