#!/bin/bash
# Weekly Automation: Fetch fresh pain points and create opportunities
# Schedule: Every Sunday at 2:00 AM
# Cron: 0 2 * * 0 /path/to/weekly_ingestion.sh >> /var/log/microappfinder/weekly_ingestion.log 2>&1

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/weekly_ingestion_$(date +%Y%m%d_%H%M%S).log"

echo "============================================================" | tee -a "$LOG_FILE"
echo "🗓️  Weekly Data Ingestion - $(date)" | tee -a "$LOG_FILE"
echo "============================================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
EMAIL="${INGESTION_EMAIL:-weekly@microappfinder.com}"
PASSWORD="${INGESTION_PASSWORD:-[REDACTED]}"

# Step 1: Authenticate
echo "🔐 Step 1: Authenticating..." | tee -a "$LOG_FILE"

LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}" \
  -c /tmp/weekly_cookies.txt 2>&1)

if echo "$LOGIN_RESPONSE" | grep -q "user_id"; then
  echo "   ✅ Login successful" | tee -a "$LOG_FILE"
elif echo "$LOGIN_RESPONSE" | grep -q "Invalid credentials"; then
  # Create automation user
  echo "   📝 Creating automation user..." | tee -a "$LOG_FILE"
  REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}" \
    -c /tmp/weekly_cookies.txt 2>&1)

  if echo "$REGISTER_RESPONSE" | grep -q "user_id"; then
    echo "   ✅ User created and logged in" | tee -a "$LOG_FILE"
  else
    echo "   ❌ Failed to create user: $REGISTER_RESPONSE" | tee -a "$LOG_FILE"
    exit 1
  fi
else
  echo "   ❌ Auth failed: $LOGIN_RESPONSE" | tee -a "$LOG_FILE"
  exit 1
fi

# Step 2: Trigger search
echo "" | tee -a "$LOG_FILE"
echo "🔍 Step 2: Triggering Reddit/HackerNews search..." | tee -a "$LOG_FILE"
echo "   Topics: saas, productivity, developer tools, startup ideas" | tee -a "$LOG_FILE"
echo "   Time range: 1month" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

SEARCH_RESPONSE=$(curl -s -X POST "$API_URL/api/reddit/search" \
  -H "Content-Type: application/json" \
  -b /tmp/weekly_cookies.txt \
  -d '{
    "topics": ["saas", "productivity", "developer tools", "startup ideas"],
    "time_range": "1month"
  }')

SEARCH_ID=$(echo "$SEARCH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('search_run_id', ''))" 2>/dev/null || echo "")

if [ -z "$SEARCH_ID" ]; then
  echo "   ❌ Search failed: $SEARCH_RESPONSE" | tee -a "$LOG_FILE"
  exit 1
fi

echo "   ✅ Search initiated" | tee -a "$LOG_FILE"
echo "   📋 Search ID: $SEARCH_ID" | tee -a "$LOG_FILE"

# Step 3: Wait for completion
echo "" | tee -a "$LOG_FILE"
echo "⏳ Step 3: Waiting for search completion..." | tee -a "$LOG_FILE"

MAX_ATTEMPTS=60
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  sleep 5
  ATTEMPT=$((ATTEMPT + 1))

  STATUS_RESPONSE=$(curl -s -X GET "$API_URL/api/reddit/search/$SEARCH_ID" \
    -b /tmp/weekly_cookies.txt)

  STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null || echo "")
  PAIN_POINTS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('pain_points_count', 0))" 2>/dev/null || echo "0")

  if [ $((ATTEMPT % 6)) -eq 0 ]; then
    echo "   [$ATTEMPT] Status: $STATUS | Pain points: $PAIN_POINTS" | tee -a "$LOG_FILE"
  fi

  if [ "$STATUS" = "completed" ]; then
    echo "" | tee -a "$LOG_FILE"
    echo "   ✅ Search completed!" | tee -a "$LOG_FILE"
    echo "   📊 Pain points extracted: $PAIN_POINTS" | tee -a "$LOG_FILE"
    break
  fi

  if [ "$STATUS" = "failed" ]; then
    echo "" | tee -a "$LOG_FILE"
    echo "   ❌ Search failed!" | tee -a "$LOG_FILE"
    exit 1
  fi
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
  echo "" | tee -a "$LOG_FILE"
  echo "   ⚠️  Search timeout (5 minutes)" | tee -a "$LOG_FILE"
  exit 1
fi

# Step 4: Trigger opportunity analysis
echo "" | tee -a "$LOG_FILE"
echo "🤖 Step 4: Analyzing opportunities with Claude Haiku..." | tee -a "$LOG_FILE"

# Run Python script to analyze pain points
cd "$SCRIPT_DIR/.."
./venv/bin/python3 -c "
import sys
import os
from pathlib import Path
from uuid import UUID

# Load env
from dotenv import load_dotenv
load_dotenv(Path('.env'))
os.environ['DATABASE_URL'] = 'postgresql+psycopg://postgres:postgres@localhost:5432/microappfinder'

sys.path.insert(0, str(Path('../api')))
from app.database import SessionLocal
from app.models import PainPoint
from worker.tasks.opportunity_analysis import analyze_top_pain_points

search_run_id = UUID('$SEARCH_ID')
db = SessionLocal()

pain_points = db.query(PainPoint).filter(
    PainPoint.search_run_id == search_run_id
).order_by(
    PainPoint.relevance_score.desc()
).limit(65).all()

pain_point_ids = [pp.id for pp in pain_points]
print(f'   Analyzing {len(pain_point_ids)} pain points...')

db.close()

if pain_point_ids:
    # Process in batches of 10
    total_created = 0
    for i in range(0, len(pain_point_ids), 10):
        batch = pain_point_ids[i:i+10]
        result = analyze_top_pain_points(search_run_id, batch)
        total_created += result['opportunities_created']
        print(f'   Batch {i//10 + 1}: {result[\"opportunities_created\"]} opportunities')

    print(f'   ✅ Total created: {total_created} opportunities')
    print(f'   💰 Cost: \${total_created * 0.0045:.2f}')
" | tee -a "$LOG_FILE"

# Step 5: Summary
echo "" | tee -a "$LOG_FILE"
echo "============================================================" | tee -a "$LOG_FILE"
echo "✨ Weekly Ingestion Complete - $(date)" | tee -a "$LOG_FILE"
echo "============================================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "📊 View opportunities at: http://localhost:3000/opportunities" | tee -a "$LOG_FILE"
echo "📝 Log saved to: $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Cleanup
rm -f /tmp/weekly_cookies.txt

exit 0
