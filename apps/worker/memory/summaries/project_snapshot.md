# MicroAppFinder - Project Snapshot

**Last Updated**: 2025-10-06

## Project Overview
Multi-source micro app opportunity discovery platform aggregating pain points from Reddit and HackerNews.

**Stack**: Next.js 14 (Frontend) + FastAPI (API) + RQ Worker (Background) + PostgreSQL + Redis

## Current State

### Feature 002: HackerNews Integration ✅ COMPLETE
**Branch**: `001-reddit-pain-point` (merged with HN work)

**Status**: Fully operational multi-source search with unified aggregation

**Architecture**:
- Parallel job execution: Reddit + HackerNews fetch simultaneously
- Unified aggregation job waits for both via RQ `depends_on`
- Cross-platform deduplication (URL + semantic similarity)
- Composite scoring: 0.3×upvotes + 0.25×comments + 0.25×recency + 0.2×sentiment

**Key Files**:
- `apps/worker/worker/tasks/unified_search.py` - Unified aggregation task
- `apps/api/app/services/unified_search_service.py` - Multi-source aggregation & scoring
- `apps/api/app/services/deduplication_service.py` - Cross-platform dedup (URL + Jaccard)
- `apps/api/app/models/pain_point.py` - Multi-source schema with `source_platform`, `source_post_ids`

## Critical Learnings

### Worker Python Cache Issues
**Problem**: SQLAlchemy models cached in `__pycache__` causing "invalid keyword argument" errors after schema changes

**Solution**:
1. Clear all cache: `find . -type d -name __pycache__ -exec rm -rf {} +`
2. Run worker with: `PYTHONDONTWRITEBYTECODE=1 python worker.py`
3. Kill ALL old worker processes before starting new one

**Why**: Multiple workers with stale cached models compete for jobs, causing intermittent failures

### RedditPost Model Field Names
**Critical**: RedditPost model uses database-friendly names, NOT PRAW field names:
- ✅ `post.text` (NOT `post.selftext`)
- ✅ `post.comment_count` (NOT `post.num_comments`)

**Affected Files**:
- `apps/api/app/services/unified_search_service.py:67,71`
- `apps/api/app/services/deduplication_service.py:247,250`

### RQ Worker Management
**Best Practice**: Run only ONE worker process at a time
- Multiple workers cause race conditions with cache states
- Use `ps aux | grep "Python worker.py"` to verify single worker
- Kill all before restart: `ps aux | grep "Python worker.py" | awk '{print $2}' | xargs kill -9`

## Database Schema

### PainPoint (Multi-Source Support)
```sql
source_platform VARCHAR(20) NOT NULL DEFAULT 'reddit'
source_post_ids JSONB NOT NULL  -- Array of platform-agnostic IDs
source_deleted BOOLEAN DEFAULT FALSE
```

**Migration**: Renamed `source_reddit_post_ids` → `source_post_ids` for platform agnosticism

## API Endpoints

### Multi-Source Search
- `POST /api/reddit/search` - Creates search with Reddit + HN parallel fetch
- `GET /api/reddit/search/{id}` - Status (pending → in_progress → completed)
- `GET /api/reddit/search/{id}/results` - Unified, deduplicated, scored results

## Active Worker Configuration
```bash
cd apps/worker
PYTHONDONTWRITEBYTECODE=1 \
OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES \
DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/microappfinder" \
REDDIT_CLIENT_ID="..." \
REDDIT_CLIENT_SECRET="..." \
REDDIT_USER_AGENT="..." \
PYTHONPATH=../api:$PYTHONPATH \
python worker.py
```

## Next Steps
- Feature 003: Product Hunt integration
- Feature 004: Indie Hackers integration
- Enhanced semantic deduplication (embeddings)
- Sentiment analysis integration
