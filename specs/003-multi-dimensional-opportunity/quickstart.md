# Quickstart: Local Testing Guide

**Feature**: 003-multi-dimensional-opportunity
**Date**: 2025-10-08

## Prerequisites

- Docker Compose running (PostgreSQL, Redis, Qdrant)
- Python 3.11+ environment active
- API server running on `http://localhost:8000`
- Worker process running
- Valid JWT token for authenticated endpoints

## 6-Step Validation

### Step 1: Run Database Migration

```bash
cd apps/api
alembic upgrade head
```

**Expected**: New `opportunities` table created with indexes.

**Verification**:
```bash
docker exec -it microappfinder_postgres psql -U postgres -d microappfinder \
  -c "\d opportunities"
```

### Step 2: Start Worker with Analysis Task

```bash
cd apps/worker
python worker.py
```

**Expected**: Worker logs show `opportunity_analysis.analyze_top_pain_points` task registered.

### Step 3: Trigger Search Run

```bash
export TOKEN="your_jwt_token_here"

curl -X POST http://localhost:8000/api/reddit/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topics": ["etsy seo", "shopify analytics"],
    "time_range": "1month"
  }'
```

**Expected**: Returns `search_run_id`. Search queries Reddit + HackerNews in parallel.

### Step 4: Wait for Analysis Completion

```bash
# Monitor worker logs
tail -f apps/worker/logs/worker.log

# Check job status
redis-cli LLEN rq:queue:default
```

**Expected**: Jobs execute in order:
1. `reddit_search` (completes in ~10s)
2. `hackernews_search` (completes in ~5s)
3. `unified_search.aggregate_and_extract_unified` (completes in ~3s)
4. `opportunity_analysis.analyze_top_pain_points` (completes in ~30s)

### Step 5: Query Opportunities

```bash
# List all opportunities (sorted by analyzed_at DESC)
curl http://localhost:8000/api/opportunities?limit=12

# Filter by high severity
curl http://localhost:8000/api/opportunities?severity_min=7.0&limit=12

# Sort by monetization potential
curl http://localhost:8000/api/opportunities?sort_by=monetization&sort_order=desc

# Get full details
curl http://localhost:8000/api/opportunities/{opportunity_id}
```

**Expected**: JSON response with opportunities array, next_cursor, has_more fields.

### Step 6: Validate Enrichment

```bash
# Run same search again
curl -X POST http://localhost:8000/api/reddit/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topics": ["etsy seo"],
    "time_range": "1month"
  }'

# Wait for analysis, then check enrichment_count
curl http://localhost:8000/api/opportunities/{opportunity_id}
```

**Expected**: `enrichment_count` increments, `last_enriched_at` updates.

## Validation Checklist

- [ ] Opportunities table exists with 6 indexes
- [ ] Search run creates pain points (visible in logs)
- [ ] Analysis task enqueued after unified aggregation completes
- [ ] All 6 dimensional scores populated (non-null)
- [ ] Confidence level between 0.0-1.0
- [ ] API returns 12 results with next_cursor
- [ ] Filtering by severity_min works correctly
- [ ] Sorting by monetization DESC returns highest scores first
- [ ] Detail endpoint includes trend_data, geographic_spread, affected_industries
- [ ] Enrichment count increments on duplicate signals
- [ ] pain_point_id becomes NULL after 48h (manual test with date override)
- [ ] API response time <500ms p95 (use curl -w "%{time_total}\n")

## Troubleshooting

**Issue**: Analysis task not enqueued
**Fix**: Check worker logs for exceptions in `unified_search.py`. Verify RQ job chaining with `redis-cli LLEN rq:queue:default`.

**Issue**: LLM analysis fails
**Fix**: Verify OpenAI/Anthropic API keys in `.env`. Check token budget limits. Review structured output schema validation errors.

**Issue**: API returns empty array
**Fix**: Confirm opportunities created with `SELECT COUNT(*) FROM opportunities;`. Check filter parameters (e.g., severity_min too high).

**Issue**: Pagination cursor errors
**Fix**: Verify cursor is Base64-encoded JSON. Check composite index exists on `(id, analyzed_at)`.

---

**Status**: Ready for testing after Phase 2 implementation
