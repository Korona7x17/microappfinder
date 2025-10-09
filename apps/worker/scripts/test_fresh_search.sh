#!/bin/bash
# Test script: Trigger fresh Reddit/HackerNews search via API

set -e

API_URL="http://localhost:8000"
EMAIL="test@microappfinder.com"
PASSWORD="TestPassword123"

echo "============================================================"
echo "🚀 Fresh Data Search Test"
echo "============================================================"
echo ""

# Step 1: Login (create user if needed)
echo "📝 Step 1: Authenticating..."

# Try login first
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}" \
  -c /tmp/cookies.txt 2>&1)

if echo "$LOGIN_RESPONSE" | grep -q "user_id"; then
  echo "   ✅ Login successful"
elif echo "$LOGIN_RESPONSE" | grep -q "Invalid credentials"; then
  # User doesn't exist, register
  echo "   📝 Registering new user..."
  REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}" \
    -c /tmp/cookies.txt 2>&1)

  if echo "$REGISTER_RESPONSE" | grep -q "user_id"; then
    echo "   ✅ User registered and logged in"
  else
    echo "   ❌ Registration failed: $REGISTER_RESPONSE"
    exit 1
  fi
else
  echo "   ❌ Auth failed: $LOGIN_RESPONSE"
  exit 1
fi

# Step 2: Trigger search
echo ""
echo "🔍 Step 2: Triggering Reddit/HackerNews search..."
echo "   Topics: saas, productivity, developer tools"
echo "   Time range: 1month"
echo ""

SEARCH_RESPONSE=$(curl -s -X POST "$API_URL/api/reddit/search" \
  -H "Content-Type: application/json" \
  -b /tmp/cookies.txt \
  -d '{
    "topics": ["saas", "productivity", "developer tools"],
    "time_range": "1month"
  }')

SEARCH_ID=$(echo "$SEARCH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('search_run_id', ''))" 2>/dev/null || echo "")

if [ -z "$SEARCH_ID" ]; then
  echo "   ❌ Search failed: $SEARCH_RESPONSE"
  exit 1
fi

echo "   ✅ Search initiated"
echo "   📋 Search ID: $SEARCH_ID"

# Step 3: Poll for completion
echo ""
echo "⏳ Step 3: Waiting for search to complete..."
echo "   This typically takes 2-5 minutes..."
echo ""

MAX_ATTEMPTS=60
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  sleep 5
  ATTEMPT=$((ATTEMPT + 1))

  STATUS_RESPONSE=$(curl -s -X GET "$API_URL/api/reddit/search/$SEARCH_ID" \
    -b /tmp/cookies.txt)

  STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null || echo "")
  PAIN_POINTS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('pain_points_count', 0))" 2>/dev/null || echo "0")

  echo "   [$ATTEMPT] Status: $STATUS | Pain points: $PAIN_POINTS"

  if [ "$STATUS" = "completed" ]; then
    echo ""
    echo "   ✅ Search completed!"
    echo "   📊 Pain points extracted: $PAIN_POINTS"
    break
  fi

  if [ "$STATUS" = "failed" ]; then
    echo ""
    echo "   ❌ Search failed!"
    exit 1
  fi
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
  echo ""
  echo "   ⚠️  Search timeout (5 minutes)"
  exit 1
fi

# Step 4: Check opportunities created
echo ""
echo "🎯 Step 4: Checking opportunities..."

# Wait a bit for opportunity analysis to complete
sleep 10

OPPS_COUNT=$(curl -s "$API_URL/api/opportunities?limit=1" | \
  python3 -c "import sys, json; print(len(json.load(sys.stdin).get('opportunities', [])))" 2>/dev/null || echo "0")

echo "   📈 Total opportunities available: $(curl -s "$API_URL/api/opportunities?limit=1000" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('opportunities', [])))" 2>/dev/null)"

echo ""
echo "============================================================"
echo "✨ FRESH DATA TEST COMPLETE!"
echo "============================================================"
echo ""
echo "🌐 View results at: http://localhost:3000/opportunities"
echo ""
