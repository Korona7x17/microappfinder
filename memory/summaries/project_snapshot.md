# Project Snapshot — MicroAppFinder

**Last Updated:** 2025-10-09
**Project:** MicroAppFinder - Multi-source micro app opportunity discovery system

## BRIEF_SUMMARY (2025-10-09 14:00)

C: Next.js 14 frontend; FastAPI backend; RQ worker pipeline; PostgreSQL + Redis; Multi-source aggregation (Reddit + HackerNews); LLM opportunity analysis (Claude Haiku 3.5); REST API with filtering/pagination; **Weekly automation at $1.17/month**

D: Feature 001 (Reddit) ✅; Feature 002 (HackerNews) ✅; Feature 003 (Multi-dimensional opportunity analysis REST API) ✅; Feature 004 (Weekly automation) ✅; 6-dimensional opportunity scoring; Cursor-based pagination; Cron-based weekly ingestion every Sunday 2:00 AM

Δ: **New REST API**: GET /api/opportunities with filtering (severity, market size, competition, trend) + sorting + cursor pagination; GET /api/opportunities/{id} for details; **Weekly automation deployed**: Fresh data ingestion + Claude Haiku analysis creates ~65 opportunities/week at $1.17/month; 20 contract tests passing

Q: None critical; All systems operational; Next automated run: Sunday 2:00 AM

→: Monitor first automated run Sunday 2025-10-13; Track actual costs via Claude dashboard; Add ProductHunt/IndieHackers sources ($1.17/month per source)

## Active Context

**Stack:**
- Frontend: Next.js 14, Tailwind, shadcn/ui, Clerk auth
- Backend: FastAPI, SQLAlchemy, Pydantic, JWT
- Worker: RQ, PRAW (Reddit), Algolia (HN), TextBlob, scikit-learn
- Data: PostgreSQL (psycopg), Redis
- Infra: Docker, Docker Compose

**Features Completed:**

### ✅ Feature 001: Reddit Pain Point Discovery (001-reddit-pain-point)
- JWT authentication with httponly cookies
- **Reddit site-wide search** (fixed from 14 hardcoded subreddits - 2025-10-07)
- Pain point extraction with composite scoring
- 48h Redis + PostgreSQL cache with deletion compliance
- User-scoped privacy (FK constraints + ownership middleware)
- Paginated results UI (/search/[id])
- Dashboard with search history

**Endpoints:**
- POST /api/auth/register, /api/auth/login
- POST /api/reddit/search (authenticated)
- GET /api/reddit/search/{id} (status)
- GET /api/reddit/search/{id}/results (paginated pain points)
- DELETE /api/reddit/search/{id}
- GET /api/reddit/dashboard

**Models:** User, Topic, SearchRun, RedditPost (48h cache), PainPoint

### ✅ Feature 002: HackerNews Integration (002-integrate-hacker-news)
- Algolia HN API integration (no rate limits, Ask HN focus)
- 48h HackerNews cache (HackerNewsItem model)
- Cross-source deduplication (URL + semantic similarity 85%)
- Unified multi-source ranking with composite scoring
- Parallel job execution (Reddit + HN → unified aggregation)
- Circuit breaker pattern (3 failures → 2min timeout → graceful degradation)
- Multi-source pain point tracking (source_platform, source_post_ids)

**Updated Models:** HackerNewsItem (new), PainPoint (+source_platform, +source_post_ids), SearchRun (+sources_queried, +hn_items_fetched)

**New Services:** HackerNewsService, DeduplicationService, UnifiedSearchService

**Worker Tasks:** hackernews_search.py, unified_search.py, hackernews_cleanup.py (daily 3AM)

**Test Coverage:** 72 tests (6 suites: model, multi-source, tracking, fetch, dedup, aggregation)

### ✅ Feature 003: Multi-Dimensional Opportunity Analysis REST API (003-multi-dimensional-opportunity)
- **REST API**: GET /api/opportunities with filtering, sorting, cursor-based pagination
- **Detail view**: GET /api/opportunities/{id} with full 6-dimensional scoring
- **6D scoring**: Problem severity, market size, monetization potential, technical complexity, competition level, trend direction
- **LLM analysis**: Claude Haiku 3.5 primary ($0.0045/opportunity), GPT-4o-mini fallback
- **Title + summary**: 100-char titles, 500-char summaries for each opportunity
- **Filtering**: severity_min/max, market_size, competition_level, trend_direction
- **Sorting**: severity, monetization, analyzed_at (asc/desc)
- **Pagination**: Cursor-based (Base64 JSON) with compound (sort_field, id) ordering
- **Reddit compliance**: pain_point_id nullable with ondelete="SET NULL" (48h TTL)

**Endpoints:**
- GET /api/opportunities - List with filters/sorts/pagination (12 per page default)
- GET /api/opportunities/{id} - Full details with all scores

**Updated Models:** Opportunity (+title, +summary fields)

**New Services:** OpportunityService (query building, cursor pagination)

**Test Coverage:** 20 contract tests (16 list + 4 detail)

**Decision Log:** `memory/decisions/003-opportunity-analysis-implementation.md`

### ✅ Feature 004: Weekly Automation (003-multi-dimensional-opportunity)
- **Cron schedule**: Every Sunday at 2:00 AM (automated ingestion)
- **Cost**: $1.17/month (~65 opportunities/week × 4 weeks)
- **LLM model**: Claude Haiku 3.5 primary ($1.00/$5.00 per 1M tokens)
- **Workflow**: Authenticate → Search Reddit/HN → Poll completion → Analyze top 65 pain points
- **Automation script**: `/apps/worker/scripts/weekly_ingestion.sh` (179 lines)
- **Logging**: `~/microappfinder_logs/weekly_ingestion_YYYYMMDD_HHMMSS.log`
- **Auth**: Auto-creates `weekly@microappfinder.com` user on first run
- **Topics**: ["saas", "productivity", "developer tools", "startup ideas"]
- **Time range**: 1 month lookback
- **Batch processing**: 10 pain points per batch × 7 batches = 65 total
- **Extensible**: Easy to add ProductHunt/IndieHackers (+$1.17/month per source)

**Cron entry:**
```
0 2 * * 0 /Users/sutiteeraniti/dev/microappfinder/apps/worker/scripts/weekly_ingestion.sh >> ~/microappfinder_logs/weekly_ingestion.log 2>&1
```

**Test script:** `/apps/worker/scripts/test_fresh_search.sh` (validated 2025-10-09)

**Decision Log:** `memory/decisions/004-weekly-automation-setup.md`

**Architecture Flow:**
```
POST /search → Create SearchRun (sources=["reddit","hackernews"])
            → Enqueue reddit_job (parallel)
            → Enqueue hn_job (parallel)
            → Enqueue unified_job (depends_on=[reddit, hn])
                     ↓
            Load cached Reddit + HN items
                     ↓
            Deduplicate (URL + semantic)
                     ↓
            Rank with composite scoring
                     ↓
            Extract pain points with source tracking
                     ↓
            Return unified results
```

**In Progress:**
- None (Features 001-004 complete)

**Planned (Future):**
- Feature 005: ProductHunt Integration (same pattern as HN) — Cost: +$1.17/month
- Feature 006: IndieHackers Integration (same pattern as HN) — Cost: +$1.17/month
- Feature 007: Frontend Opportunities View (consume GET /api/opportunities)
- Feature 008: Accumulative Enrichment (update existing opportunities with new signals)

## Database Schema

**Active Tables:**
- users (id, email, hashed_password, created_at)
- topics (id, keyword, search_count, created_at)
- search_runs (id, user_id, status, time_range, sources_queried, hn_items_fetched, timestamps, pain_points_count, error_message)
- reddit_posts (id, reddit_id, subreddit, author, title, text, url, score, comment_count, created_utc, is_nsfw, expires_at) — 48h cache
- hackernews_items (id, hn_id, hn_type, author, title, text, url, hn_url, points, comment_count, created_utc, fetched_at, expires_at, tags) — 48h cache
- pain_points (id, search_run_id, extracted_text, relevance_score, sentiment_score, source_platform, source_post_ids, source_deleted, created_at)
- **opportunities** (id, title, summary, problem_severity, market_size_indicator, monetization_potential, technical_complexity, competition_level, trend_direction, confidence_level, analyzed_at, trend_data, geographic_spread, affected_industries, pain_point_id, enrichment_count, last_enriched_at) — **NEW: Feature 003**
- search_run_topics (join table: search_run_id, topic_id, created_at)

**Unused Tables (Future):**
- clusters (id, pain_point_ids, cluster_label, centroid, size, market_score, created_at)
- briefs (id, cluster_id, name, who_hurts, job_to_be_done, killer_feature, created_at)
- runs (legacy, for full pipeline runs)
- signals (legacy, alternative pain point format)

## Key Technical Decisions

### D-2025-10-04-01 — Python 3.13 Compatibility
- psycopg[binary]>=3.2.2 (replaced psycopg2-binary)
- sqlalchemy>=2.0.36, bcrypt==4.1.3
- All models use sql_text() alias to avoid text column conflict

### D-2025-10-05-01 — Worker Environment Strategy
- Explicit env vars passed at runtime (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT, DATABASE_URL)
- Worker runs from apps/worker/, cannot access apps/api/.env

### D-2025-10-05-02 — Deferred Clustering Pipeline
- MVP delivers functional pain point extraction
- Clustering/brief generation deferred to separate feature (significant complexity)

### D-2025-10-05-03 — Algolia HN API Choice
- Official Algolia API: no rate limits, free, Ask HN filtering
- No authentication required
- Circuit breaker added for resilience despite no expected rate limits

### D-2025-10-05-04 — Deduplication Strategy
- Phase 1: URL-based exact match (after normalization)
- Phase 2: Semantic similarity (85% Jaccard threshold)
- Keeps higher engagement item, preserves both source IDs

### D-2025-10-05-05 — RQ Job Chaining
- Unified aggregation via depends_on=[reddit_job, hn_job]
- Parallel source fetching, sequential aggregation after both complete

### D-2025-10-05-06 — Circuit Breaker Configuration
- 3 failures → OPEN circuit, 2min timeout, 2 successes → CLOSED
- Graceful degradation: returns empty array when OPEN (search continues with other sources)

### D-2025-10-05-07 — 48h Cache Pattern Consistency
- HackerNewsItem mirrors RedditPost TTL for architectural consistency
- Daily cleanup at 3AM (after Reddit sync at 2AM)

### D-2025-10-07-01 — LLM Two-Tier Analysis Architecture
- GPT-4o-mini (Tier 1): Fast, cheap filter on 30 candidates → selects top 10
- Claude Sonnet 4 (Tier 2): Deep analysis on top 10 → returns unlimited opportunities
- Total cost: ~$0.06 per search ($0.003 Tier 1 + ~$0.06 Tier 2)
- No artificial limits on opportunity count (was 5, now unlimited based on quality)

### D-2025-10-07-02 — **CRITICAL: Reddit Site-Wide Search**
- **Problem**: Hardcoded 14-subreddit list (productivity, AppIdeas, etc.) caused irrelevant results
  - "etsy listing optimization" searched r/productivity → returned productivity posts
  - All searches limited to generic entrepreneurship subreddits
- **Solution**: Replaced with Reddit site-wide search (`subreddit("all")`)
  - Reddit automatically finds topic-relevant subreddits
  - "etsy listing optimization" → r/Etsy, r/EtsySellers, r/ecommerce
  - Works for ANY topic, not just entrepreneurship
- **Changes**:
  - `reddit_api.py:112-186` - Site-wide search with limit=300, score≥5
  - Removed unused `pain_phrases` array (dead code)
  - Increased quality threshold from 2 to 5

### D-2025-10-09-01 — Weekly Automation Schedule & Cost
- **Decision**: Weekly ingestion schedule (Sunday 2:00 AM) instead of daily/every-other-day
- **Rationale**:
  - Cost optimization: $1.17/month vs $60.90/month (every other day)
  - 1-month lookback captures sufficient signal volume
  - Sustainable growth: 260 opportunities/month → 3,400/year
- **Model choice**: Claude Haiku 3.5 primary ($0.0045/opp), GPT-4o-mini fallback
- **Architecture**: Cron → API auth → Search Reddit/HN → Poll → Claude batch analysis (65 opps)
- **Extensibility**: Each new source (ProductHunt, IndieHackers) adds $1.17/month
- **Files**: `apps/worker/scripts/weekly_ingestion.sh`, `test_fresh_search.sh`
- **Monitoring**: Logs in `~/microappfinder_logs/weekly_ingestion_*.log`

## System Status

### ✅ Fully Operational
- Multi-source search (Reddit + HackerNews)
- JWT authentication with httponly cookies
- Pain point extraction with composite scoring
- Cross-source deduplication (URL + semantic)
- Unified ranking and aggregation
- 48h cache with deletion compliance (Reddit)
- 48h cache with cleanup (HackerNews)
- Circuit breaker for API resilience
- User-scoped privacy enforcement
- Search results UI with pagination
- Dashboard with search history
- **REST API for opportunities** (GET /api/opportunities with filtering/sorting/pagination)
- **6-dimensional opportunity analysis** (Claude Haiku 3.5)
- **Weekly automated ingestion** (cron-based, Sunday 2:00 AM, $1.17/month)

### ❌ Not Implemented (Future Features)
- Clustering similar pain points by theme
- Market opportunity scoring at cluster level
- Micro-app brief generation (GPT-4)
- Top 3-5 opportunities view (dashboard shows raw pain points currently)
- ProductHunt integration
- IndieHackers integration

### ⚠️ Known Issues
- SQLite test database incompatible with PostgreSQL JSONB (need PostgreSQL test instance)
- Circuit breaker state is in-memory (resets on worker restart - acceptable for MVP)
- No HN comment extraction yet (only top-level posts)
- Deduplication runs on every aggregation (could be optimized with caching)

## Reference Files
- Architecture: docs/microappfinder_system_architecture.md
- Pipeline: docs/microappfinder_pipeline_revised.md
- MVP Spec: docs/microappfinder_mvp_plus_spec.md
- Structure: PROJECT_STRUCTURE.md
- Feature 001 Spec: specs/001-reddit-pain-point-discovery/spec.md
- Feature 002 Spec: specs/002-integrate-hacker-news/spec.md
- CLAUDE.md: Recent features context (Reddit + HackerNews)

## Statistics (2025-10-09)
- Total features: 4 (all complete)
- Database migrations: 4 (all applied, latest: add title/summary to opportunities)
- Test coverage: 92+ tests (72 worker tests + 20 contract tests)
- REST API endpoints: 7 (auth×2, reddit×5, opportunities×2 [NEW])
- Worker tasks: 6 (reddit_search, hackernews_search, unified_search, opportunity_analysis [NEW], reddit_cleanup, hn_cleanup)
- Services: 10 (auth, reddit_api, deletion_sync, hackernews, deduplication, unified_search, opportunity_service [NEW], opportunity_analysis [NEW])
- Models: 9 (User, Topic, SearchRun, RedditPost, HackerNewsItem, PainPoint, Opportunity [NEW], + legacy)
- Automation: 1 cron job (weekly ingestion, Sunday 2:00 AM)
- Monthly cost: $1.17 (Claude Haiku 3.5, ~260 opportunities/month)

## Environment
- Web: http://localhost:3001
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database: PostgreSQL 17 (localhost:5432/microappfinder)
- Redis: localhost:6379
- Worker: RQ on Redis queue "default"

## Active Branch
- 003-multi-dimensional-opportunity (contains Features 003 + 004)

## Next Session Goals
1. Monitor first automated ingestion run (Sunday 2025-10-13 at 2:00 AM)
2. Track actual Claude Haiku costs via Anthropic dashboard
3. Validate log format and error handling in weekly_ingestion.sh
4. Frontend implementation: Opportunities view consuming GET /api/opportunities
5. ProductHunt integration planning (Feature 005) — adds $1.17/month
