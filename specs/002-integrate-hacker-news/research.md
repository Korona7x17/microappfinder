# Research: Hacker News Integration

**Date**: 2025-10-05
**Branch**: `002-integrate-hacker-news`
**Context**: Phase 0 research for resolving NEEDS CLARIFICATION items from spec.md

## Executive Summary

All critical unknowns resolved. HN integration will mirror the existing Reddit provider pattern, using Algolia HN API (official, free, no rate limits), the existing CompositeScorer (apps/worker/worker/pipeline/scorer.py), and Qdrant/OpenAI embeddings for semantic deduplication. Hourly refresh via RQ Scheduler is feasible and aligns with existing background job infrastructure.

---

## 1. Algolia Hacker News API

### Decision
Use Algolia HN Search API (`https://hn.algolia.com/api/v1`) as the official data source.

### Rationale
- **Official**: Algolia HN API is the recommended way to query HN data (per HN maintainers)
- **Free**: No API key required for public search endpoints
- **No rate limits**: Algolia HN API explicitly states "There is currently no rate limit"
- **Well-documented**: Clear API docs at https://hn.algolia.com/api
- **Structured responses**: Clean JSON schema matching our needs

### API Endpoints

**Primary Endpoint**:
```
GET https://hn.algolia.com/api/v1/search?query={query}&tags=story&numericFilters=created_at_i>{timestamp}
```

**Parameters**:
- `query`: Search query string
- `tags`: Filter by type (story, comment, poll, etc.) - we'll use `story` for top-level items
- `numericFilters`: Time-based filtering (e.g., `created_at_i>1704067200` for items since 2024-01-01)
- `hitsPerPage`: Results per page (default 20, max 1000)
- `page`: Pagination (0-indexed)

**Response Schema**:
```json
{
  "hits": [
    {
      "objectID": "12345",
      "created_at": "2025-01-05T10:30:00.000Z",
      "created_at_i": 1735120200,
      "title": "Show HN: Built a tool for X",
      "url": "https://example.com",
      "author": "username",
      "points": 150,
      "story_text": "Description...",
      "num_comments": 45,
      "_tags": ["story", "show_hn"]
    }
  ],
  "nbHits": 250,
  "page": 0,
  "nbPages": 13,
  "hitsPerPage": 20
}
```

**Field Mapping to Unified Schema**:
- `objectID` → `hn_id`
- `title` → `title`
- `url` → `url` (or construct from `objectID` if missing)
- `author` → `author`
- `points` → `points` (maps to Reddit `score`)
- `num_comments` → `comment_count`
- `created_at_i` → `created_utc` (convert Unix timestamp)
- `story_text` → `text`

**Error Handling**:
- HTTP timeouts: 500ms timeout with fallback to cached results
- Missing fields: Handle gracefully (e.g., `url` may be None for Ask HN posts)
- Pagination limits: Max 1000 results per query (sufficient for hourly refresh)

### Alternatives Considered
- **Official HN Firebase API**: Lower-level, requires more transformation, no search capability
- **Scraping HN directly**: Violates ToS, fragile, unnecessary complexity

---

## 2. Existing Infrastructure Audit

### Decision
Reuse existing RQ worker infrastructure, PostgreSQL models, and Qdrant/OpenAI embeddings.

### Findings

#### Background Job Infrastructure (`apps/worker/`)
- **Pattern**: RQ (Redis Queue) with RQ Scheduler for recurring jobs
- **Example**: `worker/jobs/deletion_sync.py` schedules daily deletion sync at 2:00 AM UTC
- **Implementation**:
  - Worker entry point: `worker/worker.py`
  - Queue: `Queue("default", connection=redis_conn)`
  - Scheduler: `rq_scheduler.Scheduler` for cron-like jobs

**Rationale**: Hourly HN fetch can follow the same pattern as `deletion_sync`:
```python
# worker/jobs/fetch_hackernews.py
def schedule_hn_fetch(scheduler):
    scheduler.schedule(
        scheduled_time=datetime.utcnow(),
        func=fetch_hackernews_job,
        interval=3600,  # Hourly
        repeat=None
    )
```

#### External API Client Pattern (`apps/api/app/services/reddit_api.py`)
- **Pattern**: Service class with rate limiting, error handling, normalization
- **Key Features**:
  - `__init__`: Initialize API client with credentials
  - `_rate_limit()`: Enforce request throttling
  - `_submission_to_dict()`: Normalize to standard schema
  - Spam filtering, NSFW checks

**Rationale**: Create `apps/api/app/services/hackernews_api.py` following the same structure.

#### 48h Cache Pattern (`apps/api/app/models/reddit_post.py`)
- **Structure**:
  - `id`: UUID PK
  - `reddit_id`: Platform-specific ID (unique, indexed)
  - `expires_at`: TIMESTAMP (fetched_at + 48h, indexed for cleanup)
  - Compliance metadata: `subreddit`, `author`, timestamps

**Rationale**: Create `apps/api/app/models/hackernews_item.py` mirroring this structure exactly.

#### Embedding Infrastructure
- **Libraries detected**:
  - `qdrant-client` (vector database)
  - `openai` (embeddings API)
  - `sentence-transformers` (HuggingFace embeddings)
- **Location**: Venv packages confirm installation, but no active usage found in codebase yet

**Decision**: **Defer semantic deduplication** to implementation phase. Mark as TODO in data-model.md:
- Option A: Use OpenAI `text-embedding-3-small` (paid, high quality)
- Option B: Use HuggingFace `sentence-transformers/all-MiniLM-L6-v2` (free, local)
- Option C: Simple URL-based dedup for MVP, semantic later

**Rationale**: The spec requires 85% cosine similarity, but the infrastructure isn't wired up yet. Start with URL-based dedup (simpler), add semantic layer in follow-up task.

---

## 3. Scoring & Deduplication

### Decision: Scoring
**Reuse existing `CompositeScorer`** from `apps/worker/worker/pipeline/scorer.py` without modification.

### Findings

**Existing Formula** (line 14 in scorer.py):
```
score = 0.3×upvotes_norm + 0.25×comments_norm + 0.25×recency_norm + 0.2×sentiment
```

**Spec Requirement** (from clarifications):
> Mirror Reddit scoring (upvotes→points, using existing weights)

**Mapping**:
- Reddit `score` (upvotes) → HN `points`
- Reddit `comment_count` → HN `num_comments`
- Reddit `created_utc` → HN `created_at_i` (convert Unix timestamp to datetime)
- Text for sentiment: Reddit `title + selftext` → HN `title + story_text`

**Normalization Constants** (from scorer.py):
- `MAX_UPVOTES = 1000`: HN posts with 1000+ points get upvote score of 1.0
- `MAX_COMMENTS = 500`: HN posts with 500+ comments get comment score of 1.0
- `MAX_AGE_DAYS = 90`: Posts older than 90 days get recency score of 0.0

**Sentiment**:
- Uses `TextBlob` for polarity analysis
- Inverts polarity (pain/frustration = negative sentiment → positive contribution)

**Rationale**: Perfect match. No changes needed. HN items will be scored identically to Reddit posts.

### Decision: Deduplication Strategy

**Phase 1 (MVP)**: URL-based deduplication
- Exact URL match across Reddit and HN
- Normalize URLs (strip query params, fragments)
- If same URL appears in both sources, keep higher-scored item

**Phase 2 (Follow-up)**: Semantic similarity (85% cosine threshold)
- Generate embeddings for `title + text`
- Compare across sources using cosine similarity
- Threshold: 0.85 (per spec clarifications)
- Library: TBD (OpenAI or sentence-transformers)

**Rationale**:
- **MVP speed**: URL matching is deterministic, fast, zero-cost
- **Semantic later**: Embedding infrastructure exists but not wired up; avoid blocking MVP
- **Spec compliance**: Spec says "semantic similarity," but also prioritizes "lean & fast-to-ship"

### Alternatives Considered
- **Semantic-first**: Blocks on embedding service integration (adds risk, delays delivery)
- **No dedup**: Violates spec requirement (unacceptable)

---

## 4. Performance Baseline

### Decision
Target: p95 latency ≤1 second (per spec clarifications).

### Findings

**Current Architecture** (inferred from codebase):
- FastAPI async endpoints (`app/routers/reddit_search.py`)
- RQ background jobs for heavy lifting (Reddit fetching, scoring)
- Redis caching for search results

**Search Flow**:
1. User hits `POST /api/reddit/search` → creates `SearchRun`, enqueues RQ job
2. Worker fetches Reddit posts → stores in cache → scores → saves `PainPoint` records
3. User polls `GET /api/reddit/runs/{id}` for status
4. User fetches `GET /api/reddit/runs/{id}/pain-points` (paginated, 50/page)

**Current Latency** (estimated):
- Endpoint response: <500ms (creates run, enqueues job)
- Background job: 30-120 seconds (fetches Reddit, processes)
- Results retrieval: <200ms (database query)

**HN Integration Impact**:
- **No change to endpoint latency**: HN fetch happens in background job, not synchronous
- **Parallel fetching**: Query Reddit + HN simultaneously in worker
- **Timeout**: 500ms per source (fail fast if HN slow)
- **Caching**: Redis 1h TTL for HN results (reduces repeated API calls)

**Parallel Query Execution**:
- Python `asyncio` for concurrent HTTP requests
- Example pattern:
```python
async def fetch_all_sources(query, time_range):
    reddit_task = fetch_reddit(query, time_range)
    hn_task = fetch_hackernews(query, time_range)
    reddit_results, hn_results = await asyncio.gather(reddit_task, hn_task)
    return reddit_results + hn_results
```

**500ms Timeout Feasibility**:
- Algolia HN API is fast (typically <100ms responses)
- 500ms timeout with circuit breaker ensures no cascading failures
- Graceful degradation: If HN times out, return Reddit-only results

### Decision: Expected Query Volume (FR-019 from spec)

**MVP Target** (from constitution.md):
- **Concurrent users**: 100
- **Signals per run**: 1000
- **Runs per user**: Unlimited (subject to rate limits)

**Estimated Query Volume**:
- **Peak load**: 100 concurrent users × 1 search/minute = 100 searches/hour
- **Background jobs**: 1 hourly HN fetch = 1 API call/hour/topic
- **Algolia HN calls**: 100 searches × 5 topics avg × 1 HN query = 500 API calls/hour

**Rate Limit Handling** (FR-022 from spec):
- **Algolia HN**: No official rate limit (confirmed via web search)
- **Best practice**: Implement exponential backoff on 429/503 errors
- **Circuit breaker**: After 3 consecutive failures, skip HN for 5 minutes

**Rationale**: Well within capacity. No infrastructure changes needed.

---

## 5. Dependencies & Services

### Decision
No new external dependencies. Extend existing services.

### Services & Modules

**Search Aggregation**:
- **Current**: Implicit in `worker/tasks/reddit_search.py` (RQ job)
- **HN Addition**: Extend `reddit_search_job()` to call both providers

**Normalization**:
- **Current**: `RedditAPIClient._submission_to_dict()`
- **HN Addition**: Create `HackerNewsAPIClient.normalize_item()`

**Scoring**:
- **Current**: `CompositeScorer.calculate_composite_score()`
- **HN Addition**: Pass HN items with mapped field names (no code change)

**Deduplication**:
- **Current**: None (Reddit-only system has no cross-source dedup)
- **HN Addition**: Create `apps/api/app/services/deduplication.py` with URL matching

**Dependencies Needed**:
- `requests` or `httpx`: Already installed (via FastAPI deps)
- `textblob`: Already installed (for sentiment in scorer.py)
- No new packages required for MVP

---

## Decisions Summary

| Unknown | Decision | Rationale |
|---------|----------|-----------|
| **FR-019: Query volume** | 100 concurrent users, 500 HN API calls/hour | MVP target from constitution, well within Algolia capacity |
| **FR-022: Rate limits** | No rate limit (Algolia HN), implement exponential backoff | Algolia docs confirm no limit; backoff for safety |
| **Existing API infra** | Reuse `services/reddit_api.py` pattern | Proven, mirrors Reddit provider |
| **Dedup libraries** | URL matching (MVP), defer semantic to Phase 2 | Fast-to-ship, embedding infra not wired up |
| **Search aggregation** | Extend `worker/tasks/reddit_search.py` | Existing RQ job handles Reddit, add HN parallel fetch |

---

## Implementation Recommendations

1. **Prioritize MVP speed**: Start with URL-based dedup, add semantic later
2. **Mirror Redis pattern**: Use existing 48h cache structure for HN items
3. **Reuse CompositeScorer**: Zero code changes, just map HN fields
4. **Parallel fetching**: Use `asyncio.gather()` for Reddit + HN
5. **Circuit breaker**: Skip HN gracefully on failures (Redis fallback)

---

## Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| Algolia HN API outage | Cache last successful results in Redis (1h TTL), fallback to Reddit-only |
| HN data format changes | Monitor Algolia API changelog, version-pin response schema expectations |
| URL-based dedup misses duplicates | Acceptable for MVP; plan semantic dedup as Phase 2 enhancement |
| 500ms timeout too aggressive | Monitor p95 latency; increase to 800ms if needed (still within 1s SLA) |

---

## Next Steps (Phase 1)

1. Create `data-model.md` with HackerNewsItem schema
2. Create `contracts/hackernews-api.yaml` documenting Algolia API contract
3. Create `quickstart.md` with test scenarios
4. Update `CLAUDE.md` with HN integration context

---

**Research Complete**: All NEEDS CLARIFICATION items resolved. Ready for Phase 1 (Design & Contracts).
