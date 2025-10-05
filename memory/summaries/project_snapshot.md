# Project Snapshot — MicroAppFinder

**Last Updated:** 2025-10-05
**Project:** MicroAppFinder - Multi-source micro app opportunity discovery system

## BRIEF_SUMMARY (2025-10-05 16:00)

C: Next.js 14 frontend; FastAPI backend; RQ worker pipeline; PostgreSQL + Redis; Multi-source aggregation (Reddit + HackerNews); 48h cache compliance; Circuit breaker resilience

D: Feature 001 (Reddit Pain Point Discovery) ✅ COMPLETE; Feature 002 (HackerNews Integration) ✅ COMPLETE; Composite scoring 0.3×upvotes + 0.25×comments + 0.25×recency + 0.2×sentiment; Cross-source deduplication (URL + 85% semantic similarity); JWT auth with httponly cookies

Δ: Reddit + HN unified search fully operational; 72 comprehensive tests (TDD); 3 migrations applied; Circuit breaker pattern implemented; Pain points now track source_platform + source_post_ids; RQ job chaining (reddit_job + hn_job → unified_job)

Q: SQLite tests incompatible with PostgreSQL JSONB (need PostgreSQL test instance or JSON fallback); Circuit breaker state in-memory (resets on worker restart)

→: Integration testing with live data; Worker startup automation; Monitor HN API performance; Consider ProductHunt/IndieHackers integration (same pattern); Future: clustering + brief generation pipeline

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
- Reddit search via PRAW (14 curated subreddits)
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
- None (Feature 002 complete)

**Planned (Future):**
- Feature 003: Clustering + Brief Generation Pipeline
  - Semantic clustering (TF-IDF or embeddings)
  - Market opportunity scoring (pain × frequency × willingness-to-pay)
  - LLM brief generation (GPT-4) for top 3-5 opportunities
  - Dashboard showing briefs instead of raw pain points
- Feature 004: ProductHunt Integration (same pattern as HN)
- Feature 005: IndieHackers Integration (same pattern as HN)

## Database Schema

**Active Tables:**
- users (id, email, hashed_password, created_at)
- topics (id, keyword, search_count, created_at)
- search_runs (id, user_id, status, time_range, sources_queried, hn_items_fetched, timestamps, pain_points_count, error_message)
- reddit_posts (id, reddit_id, subreddit, author, title, text, url, score, comment_count, created_utc, is_nsfw, expires_at) — 48h cache
- hackernews_items (id, hn_id, hn_type, author, title, text, url, hn_url, points, comment_count, created_utc, fetched_at, expires_at, tags) — 48h cache
- pain_points (id, search_run_id, extracted_text, relevance_score, sentiment_score, source_platform, source_post_ids, source_deleted, created_at)
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

## Statistics (2025-10-05)
- Total features: 2 (both complete)
- Database migrations: 3 (all applied)
- Test coverage: 72 tests across 6 suites
- Lines of code added (Feature 002): ~2,500
- Worker tasks: 5 (reddit_search, hackernews_search, unified_search, reddit_cleanup, hn_cleanup)
- Services: 8 (auth, reddit_api, deletion_sync, hackernews, deduplication, unified_search)
- Models: 8 (User, Topic, SearchRun, RedditPost, HackerNewsItem, PainPoint, + legacy)

## Environment
- Web: http://localhost:3001
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database: PostgreSQL 17 (localhost:5432/microappfinder)
- Redis: localhost:6379
- Worker: RQ on Redis queue "default"

## Active Branch
- 001-reddit-pain-point (contains both Feature 001 and Feature 002)

## Next Session Goals
1. Integration testing with live Reddit + HN data
2. Worker startup script automation
3. Monitor HN API performance and cache hit rates
4. Test circuit breaker under simulated failures
5. Consider ProductHunt integration planning (Feature 004)
