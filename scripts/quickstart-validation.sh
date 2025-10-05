#!/bin/bash
# T049: Quickstart validation
# E2E validation following specs/001-reddit-pain-point/quickstart.md

set -e

API_URL="${API_URL:-http://localhost:8000}"
TEST_EMAIL="test_$(date +%s)@example.com"
TEST_PASSWORD="TestPassword123"

echo "=== Reddit Pain Point Discovery - Quickstart Validation ==="
echo "API URL: $API_URL"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

pass() {
    echo -e "${GREEN}✓${NC} $1"
}

fail() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

# Step 1: Register user
echo "Step 1: Register new user..."
REGISTER_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" \
    -c cookies.txt)

HTTP_CODE=$(echo "$REGISTER_RESPONSE" | tail -n1)
REGISTER_BODY=$(echo "$REGISTER_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "201" ]; then
    USER_ID=$(echo "$REGISTER_BODY" | grep -o '"user_id":"[^"]*"' | cut -d'"' -f4)
    pass "User registered successfully (ID: $USER_ID)"
else
    fail "Registration failed (HTTP $HTTP_CODE)"
fi

# Step 2: Login
echo "Step 2: Login..."
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" \
    -c cookies.txt -b cookies.txt)

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
    pass "Login successful"
else
    fail "Login failed (HTTP $HTTP_CODE)"
fi

# Step 3: Create search
echo "Step 3: Create search..."
SEARCH_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/reddit/search" \
    -H "Content-Type: application/json" \
    -d '{"topics":["productivity tools","time management"],"time_range":"7days"}' \
    -b cookies.txt)

HTTP_CODE=$(echo "$SEARCH_RESPONSE" | tail -n1)
SEARCH_BODY=$(echo "$SEARCH_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "201" ]; then
    SEARCH_RUN_ID=$(echo "$SEARCH_BODY" | grep -o '"search_run_id":"[^"]*"' | cut -d'"' -f4)
    pass "Search created (ID: $SEARCH_RUN_ID)"
else
    fail "Search creation failed (HTTP $HTTP_CODE)"
fi

# Step 4: Poll search status
echo "Step 4: Poll search status (max 30s)..."
MAX_ATTEMPTS=30
ATTEMPT=0
COMPLETED=false

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    STATUS_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/reddit/search/$SEARCH_RUN_ID" \
        -b cookies.txt)

    HTTP_CODE=$(echo "$STATUS_RESPONSE" | tail -n1)
    STATUS_BODY=$(echo "$STATUS_RESPONSE" | head -n-1)

    if [ "$HTTP_CODE" != "200" ]; then
        fail "Status check failed (HTTP $HTTP_CODE)"
    fi

    STATUS=$(echo "$STATUS_BODY" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

    if [ "$STATUS" = "completed" ]; then
        COMPLETED=true
        pass "Search completed"
        break
    elif [ "$STATUS" = "failed" ]; then
        ERROR=$(echo "$STATUS_BODY" | grep -o '"error_message":"[^"]*"' | cut -d'"' -f4)
        fail "Search failed: $ERROR"
    fi

    echo "   Status: $STATUS (attempt $((ATTEMPT+1))/$MAX_ATTEMPTS)"
    sleep 1
    ATTEMPT=$((ATTEMPT+1))
done

if [ "$COMPLETED" != "true" ]; then
    fail "Search did not complete within 30 seconds"
fi

# Step 5: Get results with pagination
echo "Step 5: Get search results..."
RESULTS_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/reddit/search/$SEARCH_RUN_ID/results?page=1&limit=50" \
    -b cookies.txt)

HTTP_CODE=$(echo "$RESULTS_RESPONSE" | tail -n1)
RESULTS_BODY=$(echo "$RESULTS_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    TOTAL=$(echo "$RESULTS_BODY" | grep -o '"total":[0-9]*' | cut -d':' -f2)
    pass "Results retrieved (Total: $TOTAL pain points)"
else
    fail "Results retrieval failed (HTTP $HTTP_CODE)"
fi

# Step 6: Privacy check (try to access with different user)
echo "Step 6: Privacy isolation check..."
OTHER_EMAIL="other_$(date +%s)@example.com"

# Register second user
curl -s -X POST "$API_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$OTHER_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" \
    -c cookies2.txt > /dev/null

# Try to access first user's search
PRIVACY_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/reddit/search/$SEARCH_RUN_ID" \
    -b cookies2.txt)

HTTP_CODE=$(echo "$PRIVACY_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "403" ]; then
    pass "Privacy check passed (403 Forbidden)"
else
    fail "Privacy check failed (Expected 403, got $HTTP_CODE)"
fi

# Step 7: Empty results fallback
echo "Step 7: Get recent pain points (fallback)..."
RECENT_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/reddit/recent?limit=20" \
    -b cookies.txt)

HTTP_CODE=$(echo "$RECENT_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
    pass "Recent pain points retrieved"
else
    fail "Recent pain points failed (HTTP $HTTP_CODE)"
fi

# Cleanup
rm -f cookies.txt cookies2.txt

echo ""
echo "=== All validation steps passed! ==="
