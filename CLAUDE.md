# Claude Code Instructions

## Memory System
- **Always load:** `memory/summaries/project_snapshot.md` at session start
- **Full spec:** `docs/CLAUDE_MEMORY_GUIDELINES.md`
- **Runtime rules:** `memory/CLAUDE_MEMORY_RULES.md`

## Project Context
- **Stack:** Next.js 14 + FastAPI + RQ worker + PostgreSQL/Qdrant
- **Structure:** Monorepo (apps/web, apps/api, apps/worker)
- **Goal:** Micro app opportunity discovery via Reddit/HN/PH/IH signals

## Development Rules
- Use Docker Compose for all services
- Reference code as `path:line` or `path@hash`
- Log decisions in `memory/decisions/*.md`
- Keep responses token-efficient

## Recent Features

### Reddit Pain Point Discovery (001-reddit-pain-point)
**Endpoints**:
- `POST /api/auth/register` - Create user account
- `POST /api/auth/login` - Authenticate (JWT + httponly cookie)
- `POST /api/reddit/search` - Create search run (authenticated)
- `GET /api/reddit/runs/{id}` - Get run status (owner only)
- `GET /api/reddit/runs/{id}/pain-points` - Get paginated results (50/page)
- `GET /api/reddit/dashboard` - User search history

**Key Patterns**:
- **Auth**: JWT with httponly cookies, `get_current_user()` dependency
- **Reddit API**: PRAW client, 14 curated subreddits, composite scoring
- **Data Retention**: Raw Reddit content 48h TTL (Redis), aggregates indefinite (PostgreSQL)
- **Compliance**: Daily deletion sync, no PII retention, Reddit ToS enforcement
- **Privacy**: User-scoped data, FK constraints + middleware ownership checks
- **Scoring**: `0.3*upvotes + 0.25*comments + 0.25*recency + 0.2*sentiment`

**Models**: User, Topic, SearchRun, RedditPost (temp cache), PainPoint (derived aggregate)

### HackerNews Integration for Unified Search (002-integrate-hacker-news)
**Multi-Source Architecture**:
- **Parallel Fetching**: Reddit + HackerNews queried simultaneously via RQ jobs
- **Algolia HN API**: No rate limits, Ask HN focus, min 10 points threshold
- **48h Cache Pattern**: HackerNewsItem model mirrors RedditPost retention
- **Cross-Source Deduplication**: URL normalization + 85% semantic similarity (Jaccard)
- **Unified Aggregation**: Task chaining (reddit_job + hn_job → unified_job)
- **Circuit Breaker**: Algolia API protection (3 failures → 2min timeout)

**Updated Models**:
- **HackerNewsItem**: 48h cache (hn_id, title, text, points, comment_count, expires_at)
- **PainPoint**: Multi-source fields (`source_platform`, `source_post_ids`)
- **SearchRun**: Source tracking (`sources_queried`, `hn_items_fetched`)

**Composite Scoring** (unchanged):
- Formula: `0.3×upvotes + 0.25×comments + 0.25×recency + 0.2×sentiment`
- Log-scale normalization for engagement (max ~1000)
- Exponential recency decay (30-day half-life)

**Worker Tasks**:
- `tasks/reddit_search.py`: Reddit PRAW pipeline
- `tasks/hackernews_search.py`: HN Algolia fetch + cache
- `tasks/unified_search.py`: Dedupe + aggregate + rank (depends_on=[reddit, hn])
- `jobs/hackernews_cleanup.py`: Daily 3AM cleanup (48h TTL)

**Services**:
- `HackerNewsService`: Algolia API, caching, cleanup
- `DeduplicationService`: URL/title similarity, cross-source merging
- `UnifiedSearchService`: Multi-source ranking, pagination

**Key Changes**:
- Search now queries `["reddit", "hackernews"]` by default
- Pain points preserve source platform and IDs
- Circuit breaker prevents HN API cascade failures
- RQ job chaining ensures unified results after both sources complete
