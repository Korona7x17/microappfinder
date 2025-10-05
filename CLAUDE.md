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
