# Quickstart: Hacker News Integration Testing

**Feature**: 002-integrate-hacker-news
**Purpose**: Validate HN integration end-to-end via manual testing scenarios

## Prerequisites

1. **Environment Setup**:
   ```bash
   cd /Users/sutiteeraniti/dev/microappfinder
   docker-compose up -d postgres redis
   ```

2. **Database Migrations**:
   ```bash
   cd apps/api
   python -m alembic upgrade head  # Applies HackerNewsItem, PainPoint, SearchRun changes
   ```

3. **Worker Running**:
   ```bash
   cd apps/worker
   OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/microappfinder" PYTHONPATH=../api:$PYTHONPATH python worker.py
   ```

4. **API Server Running**:
   ```bash
   cd apps/api
   uvicorn app.main:app --reload --port 8000
   ```

5. **Test User Created**:
   ```bash
   # Register test user via API or create directly in DB
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "test123"}'
   ```

---

## Test Scenarios

### Scenario 1: Basic HN Integration (User Story 1)

**Goal**: Verify that HN items appear in top-3 results with correct schema.

**Steps**:
1. Login and get JWT token:
   ```bash
   TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "test123"}' \
     | jq -r '.access_token')
   ```

2. Create search run (triggers HN + Reddit fetch):
   ```bash
   RUN_ID=$(curl -X POST http://localhost:8000/api/reddit/search \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"topics": ["productivity tools"], "time_range": "week"}' \
     | jq -r '.run_id')
   ```

3. Wait for background job (30-60 seconds):
   ```bash
   sleep 45
   ```

4. Fetch results:
   ```bash
   curl -X GET "http://localhost:8000/api/reddit/runs/$RUN_ID/pain-points" \
     -H "Authorization: Bearer $TOKEN" | jq
   ```

**Expected**:
- Response contains `pain_points` array with ≤50 items (paginated)
- At least one item has `source_platform: "hackernews"`
- HN items have fields: `title`, `extracted_text`, `relevance_score`, `source_post_ids`
- `source_post_ids` contains HN item IDs (e.g., `["12345678"]`)

**Validation**:
```bash
# Count HN vs Reddit items
curl -X GET "http://localhost:8000/api/reddit/runs/$RUN_ID/pain-points" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '[.pain_points[] | .source_platform] | group_by(.) | map({platform: .[0], count: length})'

# Example output:
# [
#   {"platform": "reddit", "count": 32},
#   {"platform": "hackernews", "count": 18}
# ]
```

---

### Scenario 2: Automatic Source Blending (User Story 2)

**Goal**: Confirm users never see source selection UI (backend-only integration).

**Steps**:
1. Perform search (same as Scenario 1, steps 1-4)
2. Inspect frontend (if applicable) or API response

**Expected**:
- No `source` query parameter in API
- No source filter in request body schema
- Results automatically blended from Reddit + HN

**Validation**:
```bash
# Check search run metadata
curl -X GET "http://localhost:8000/api/reddit/runs/$RUN_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.sources_queried'

# Expected: ["reddit", "hackernews"]
```

---

### Scenario 3: Fresh HN Items (User Story 3)

**Goal**: Verify HN items ≤1 hour old appear in results.

**Steps**:
1. Manually trigger hourly HN fetch job (bypass scheduler for testing):
   ```python
   # In worker Python shell
   from worker.jobs.fetch_hackernews import fetch_hackernews_job
   fetch_hackernews_job(query="productivity", time_range="day")
   ```

2. Query `hackernews_items` table:
   ```sql
   SELECT hn_id, title, created_utc, fetched_at
   FROM hackernews_items
   WHERE created_utc > NOW() - INTERVAL '1 hour'
   ORDER BY created_utc DESC
   LIMIT 10;
   ```

3. Perform search (steps from Scenario 1)

**Expected**:
- HN items with `created_utc` within last hour present in DB
- These items eligible for scoring and ranking
- At least one recent HN item appears in top-3 results (if scored competitively)

**Validation**:
```bash
# Check freshness of HN items in results
curl -X GET "http://localhost:8000/api/reddit/runs/$RUN_ID/pain-points" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.pain_points[] | select(.source_platform == "hackernews") | {title, created_at: .source_post_ids[0]}'
```

---

### Scenario 4: HN API Downtime Graceful Degradation (Edge Case)

**Goal**: Confirm system returns Reddit-only results when HN unavailable.

**Steps**:
1. **Simulate HN outage** (modify worker code temporarily):
   ```python
   # In apps/worker/worker/jobs/fetch_hackernews.py
   # Add at start of fetch_hackernews_job():
   raise Exception("Simulated Algolia HN API timeout")
   ```

2. Restart worker
3. Perform search (steps from Scenario 1)
4. Check logs for HN failure warning
5. Verify results still returned (Reddit-only)

**Expected**:
- Worker logs show: `WARNING: HN fetch failed, falling back to Reddit-only`
- Search run completes with `status: "completed"`
- Results contain Reddit items only (`source_platform: "reddit"`)
- No error shown to user (graceful degradation)

**Validation**:
```bash
# Check sources_queried metadata
curl -X GET "http://localhost:8000/api/reddit/runs/$RUN_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '{sources_queried, hn_items_fetched}'

# Expected:
# {
#   "sources_queried": ["reddit"],  # HN omitted due to failure
#   "hn_items_fetched": null
# }
```

---

### Scenario 5: Deduplication Across Sources (Acceptance Scenario 3)

**Goal**: Verify URL-based deduplication prevents same story from both sources.

**Steps**:
1. Identify a popular story that appears on both Reddit and HN (manually check):
   - Example: "Show HN: I built X" often cross-posted to r/programming

2. Perform search targeting that topic
3. Inspect results for duplicates

**Expected**:
- If same URL appears in both Reddit and HN raw data, only ONE appears in final results
- Higher-scored version wins (Reddit vs HN based on composite score)

**Validation**:
```bash
# Check for duplicate URLs in results
curl -X GET "http://localhost:8000/api/reddit/runs/$RUN_ID/pain-points" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '[.pain_points[].source_post_ids[]] | group_by(.) | map(select(length > 1))'

# Expected: [] (no duplicates)
```

**Manual Check**:
```sql
-- Query raw cache for potential duplicates
SELECT r.url, r.reddit_id, h.hn_url, h.hn_id
FROM reddit_posts r
FULL OUTER JOIN hackernews_items h ON r.url = h.url
WHERE r.url IS NOT NULL AND h.url IS NOT NULL;
```

---

### Scenario 6: Performance SLA (Acceptance Scenario 5)

**Goal**: Confirm p95 latency ≤1 second.

**Steps**:
1. Run load test with 100 concurrent searches:
   ```bash
   # Using Apache Bench or wrk
   ab -n 100 -c 10 -T application/json -H "Authorization: Bearer $TOKEN" \
     -p search_payload.json http://localhost:8000/api/reddit/search
   ```

2. Measure response times

**Expected**:
- p95 latency ≤1 second for search run creation (enqueue job)
- Background job completes within 60 seconds
- Results retrieval ≤200ms (database query)

**Validation**:
```bash
# Check endpoint response time
curl -w "@curl-format.txt" -o /dev/null -s \
  -X POST http://localhost:8000/api/reddit/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"topics": ["productivity"], "time_range": "week"}'

# curl-format.txt:
# time_total: %{time_total}s
```

---

## Automated Test Checklist

After manual validation, run automated tests:

```bash
cd apps/api
pytest tests/integration/test_hackernews_search.py -v

cd apps/worker
pytest tests/unit/test_hn_client.py -v
pytest tests/unit/test_hn_normalizer.py -v
pytest tests/unit/test_hn_scorer.py -v
```

**Expected**: All tests pass (green).

---

## Success Criteria

- [x] Scenario 1: HN items appear in results with correct schema
- [x] Scenario 2: No source selection UI (backend-only)
- [x] Scenario 3: HN items ≤1 hour old are eligible
- [x] Scenario 4: Graceful degradation when HN unavailable
- [x] Scenario 5: No duplicate URLs across sources
- [x] Scenario 6: p95 latency ≤1 second
- [x] All automated tests pass

---

## Rollback Plan

If critical issues found:

1. **Disable HN integration**:
   ```python
   # In apps/worker/worker/tasks/reddit_search.py
   ENABLE_HN = False  # Set to False
   ```

2. **Revert migrations** (if needed):
   ```bash
   cd apps/api
   python -m alembic downgrade -1  # Rollback last migration
   ```

3. **Monitor error rates** via Sentry

---

## Next Steps

After quickstart validation:
1. Run A/B test comparing baseline (Reddit-only) vs HN-integrated results
2. Collect user feedback on relevance
3. Monitor HN API uptime and latency
4. Plan Phase 2: Semantic deduplication (85% cosine threshold)
