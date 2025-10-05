# Implementation Plan: Reddit Pain Point Discovery

**Branch**: `001-reddit-pain-point` | **Date**: 2025-10-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-reddit-pain-point/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✅ COMPLETE: Spec loaded successfully
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → ✅ COMPLETE: All clarifications resolved in spec
   → Detected Project Type: web (apps/web + apps/api + apps/worker)
   → Structure Decision: Monorepo with Next.js frontend, FastAPI backend, RQ worker
3. Fill the Constitution Check section
   → ✅ COMPLETE: Evaluated against constitution principles
4. Evaluate Constitution Check section
   → ✅ PASS: No violations detected
   → Update Progress Tracking: Initial Constitution Check ✅
5. Execute Phase 0 → research.md
   → ✅ COMPLETE: Technical decisions documented
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
   → ✅ COMPLETE: All Phase 1 artifacts generated
7. Re-evaluate Constitution Check section
   → ✅ PASS: Design conforms to constitutional principles
   → Update Progress Tracking: Post-Design Constitution Check ✅
8. Plan Phase 2 → Task generation approach documented
9. ✅ COMPLETE - Ready for /tasks command
```

## Summary

Reddit Pain Point Discovery enables authenticated users to search curated Reddit communities for micro-app opportunities. Users provide topic keywords, and the system searches 14 target subreddits (r/AppIdeas, r/SomebodyMakeThis, etc.) to extract, score, and rank pain points using composite metrics (upvotes, engagement, recency, sentiment). The feature implements strict Reddit API compliance with 48-hour raw content caching and daily deletion sync, user-level privacy (no cross-user access), and <30s response times. The system stores derived aggregates indefinitely while purging user-generated content per Reddit ToS.

## Technical Context

**Language/Version**: Python 3.11+ (backend/worker), TypeScript/Node 20+ (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy, Pydantic, PRAW (Reddit API), Redis/RQ, Next.js 14, Tailwind, shadcn/ui
**Storage**: PostgreSQL (active data, aggregates), Redis (queue, cache with TTL), S3/MinIO (optional archival)
**Testing**: pytest (backend), vitest/React Testing Library (frontend)
**Target Platform**: Docker containers (Linux) → Hetzner VPS/Railway deployment
**Project Type**: Web monorepo - frontend + backend + worker
**Performance Goals**: <30s pain point extraction, <1s report loading, 100 concurrent users
**Constraints**: Reddit API rate limits (<60 req/min), 48h max raw content retention, daily deletion sync, user-scoped privacy
**Scale/Scope**: 14 subreddits, 6 time ranges, 500 results/run, 50 results/page pagination

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Initial Check (Pre-Research)
- ✅ **Micro-App Fit First**: Passes gate - solves 1 JTBD (discover pain points), buildable in <1 week, minimal user input
- ✅ **Lean & Fast-to-Ship**: Uses existing stack (FastAPI, Next.js, PostgreSQL), no new infra needed
- ✅ **Data Privacy & Compliance**: Reddit API ToS compliant (48h cache, deletion sync, no PII retention)
- ✅ **Deterministic Scoring**: Composite scoring (upvotes, engagement, recency, sentiment) - transparent & reproducible
- ✅ **Quality Over Quantity**: 500 cap per run, pagination prevents overwhelming users
- ✅ **Source Reliability**: Reddit API (official, documented, stable)
- ✅ **Observability**: Structured logging with run_id, real-time status tracking

### Post-Design Check (Phase 1 Complete)
- ✅ **No complexity violations**: Uses existing monorepo structure, standard REST patterns
- ✅ **Constitutional compliance**: All non-negotiable principles satisfied
- ✅ **Performance standards**: <30s execution (within 5min pipeline target), <1s UI loading

**Status**: ✅ PASS - No deviations or violations

## Project Structure

### Documentation (this feature)
```
specs/001-reddit-pain-point/
├── spec.md              # Feature specification (input)
├── plan.md              # This file (/plan output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 API contracts
│   ├── openapi.yaml
│   └── schemas/
└── tasks.md             # Phase 2 output (/tasks command)
```

### Source Code (repository root)
```
apps/
├── web/                 # Next.js 14 frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/
│   │   │   │   ├── login/
│   │   │   │   └── register/
│   │   │   ├── dashboard/
│   │   │   └── runs/
│   │   │       └── [id]/
│   │   ├── components/
│   │   │   ├── auth/
│   │   │   ├── search/
│   │   │   └── results/
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── auth.ts
│   │   └── types/
│   └── tests/
│       ├── components/
│       └── integration/
│
├── api/                 # FastAPI backend
│   ├── app/
│   │   ├── core/
│   │   │   ├── auth.py        # NEW: JWT auth middleware
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── models/
│   │   │   ├── user.py        # NEW: User model
│   │   │   ├── topic.py       # NEW: Topic model
│   │   │   ├── search_run.py  # NEW: SearchRun model
│   │   │   ├── reddit_post.py # NEW: RedditPost (temp cache)
│   │   │   └── pain_point.py  # NEW: PainPoint model
│   │   ├── schemas/
│   │   │   ├── auth.py        # NEW: Auth schemas
│   │   │   ├── search.py      # NEW: Search request/response
│   │   │   └── pain_point.py  # NEW: PainPoint schemas
│   │   ├── routers/
│   │   │   ├── auth.py        # NEW: Login/register endpoints
│   │   │   └── reddit_search.py # NEW: Search endpoints
│   │   ├── services/
│   │   │   ├── reddit_api.py  # NEW: Reddit API client (PRAW)
│   │   │   ├── auth_service.py # NEW: User auth logic
│   │   │   └── deletion_sync.py # NEW: Daily deletion checker
│   │   └── providers/
│   │       └── reddit.py      # EXTEND: Add Reddit search
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── contract/
│
└── worker/              # RQ background worker
    ├── worker/
    │   ├── tasks/
    │   │   └── reddit_search.py # NEW: Reddit extraction task
    │   ├── pipeline/
    │   │   ├── extractor.py   # NEW: Pain point extraction
    │   │   ├── scorer.py      # NEW: Composite scoring
    │   │   └── filter.py      # NEW: NSFW/spam filtering
    │   └── jobs/
    │       └── deletion_sync.py # NEW: Scheduled deletion sync
    └── tests/

infra/
├── migrations/
│   └── versions/
│       └── xxx_add_reddit_search.py # NEW: DB migration
└── docker/
```

**Structure Decision**: Monorepo web application with existing Next.js frontend (`apps/web/`), FastAPI backend (`apps/api/`), and RQ worker (`apps/worker/`). Reddit Pain Point Discovery extends the existing architecture by adding auth layer, new models (User, Topic, SearchRun, RedditPost, PainPoint), Reddit-specific search endpoints, and worker tasks for background extraction. Frontend adds authentication flow and search/results UI. All components follow established patterns (SQLAlchemy models, Pydantic schemas, FastAPI routers, Next.js App Router).

## Phase 0: Outline & Research

### Technical Decisions

**Authentication Strategy**:
- **Decision**: JWT-based auth with httponly cookies
- **Rationale**: Stateless, scalable, prevents XSS attacks; aligns with existing FastAPI patterns
- **Alternatives considered**: Session-based (more DB load), OAuth only (complex for MVP)

**Reddit API Client**:
- **Decision**: PRAW (Python Reddit API Wrapper)
- **Rationale**: Official, well-maintained, handles auth/rate-limiting, supports search/subreddit filtering
- **Alternatives considered**: Direct REST calls (more boilerplate), Pushshift (deprecated)

**Content Caching & TTL**:
- **Decision**: Redis with 48-hour TTL + PostgreSQL for aggregates
- **Rationale**: Automatic expiry handles Reddit ToS compliance; fast cache reads; Postgres for durable data
- **Alternatives considered**: PostgreSQL only (manual TTL cleanup), S3 (slower reads)

**Deletion Sync Implementation**:
- **Decision**: Daily cron job (RQ Scheduler) checking Reddit API for deleted posts
- **Rationale**: Batch processing efficient; daily sync meets ToS requirements; RQ Scheduler already in stack
- **Alternatives considered**: Real-time webhooks (Reddit doesn't provide), on-demand sync (too slow)

**Composite Scoring Algorithm**:
- **Decision**: Weighted sum: `score = 0.3*upvotes_norm + 0.25*comments_norm + 0.25*recency_norm + 0.2*sentiment`
- **Rationale**: Balances popularity (upvotes), engagement (comments), freshness (recency), and pain intensity (sentiment)
- **Alternatives considered**: ML-based ranking (overkill for MVP), upvotes-only (misses context)

**NSFW/Spam Filtering**:
- **Decision**: Reddit API `over_18` flag + keyword blocklist + low-score threshold
- **Rationale**: Reddit provides NSFW metadata; simple keyword filter catches obvious spam; score threshold removes low-quality
- **Alternatives considered**: ML content moderation (expensive), manual review (not scalable)

**Sentiment Analysis**:
- **Decision**: TextBlob polarity score for pain intensity
- **Rationale**: Lightweight, no external API costs, good enough for MVP scoring component
- **Alternatives considered**: OpenAI embeddings (costly), rule-based (less accurate)

**User Privacy Enforcement**:
- **Decision**: Database-level user_id foreign key + API middleware checking ownership
- **Rationale**: Prevents accidental leaks; enforced at both DB and application layers
- **Alternatives considered**: Frontend-only (insecure), separate user DBs (complex)

**Empty Results Fallback**:
- **Decision**: Query top 20 recent pain points (any topic, last 7 days) from database
- **Rationale**: Always shows value to user; uses existing data; promotes discovery
- **Alternatives considered**: "No results" message (poor UX), suggested topics (requires ML)

**Output**: All technical decisions resolved, no NEEDS CLARIFICATION remaining

## Phase 1: Design & Contracts

### Data Model

**See**: [data-model.md](./data-model.md)

Key entities:
- User (id, email, hashed_password, created_at)
- Topic (id, keyword, created_at)
- SearchRun (id, user_id FK, topic_ids[], status, time_range, created_at, completed_at)
- RedditPost (id, reddit_id, subreddit, author, title, text, url, score, comment_count, created_utc, fetched_at, expires_at TTL)
- PainPoint (id, search_run_id FK, extracted_text, relevance_score, sentiment_score, source_reddit_post_ids[], created_at)

### API Contracts

**See**: [contracts/openapi.yaml](./contracts/openapi.yaml)

**Authentication Endpoints**:
- `POST /api/auth/register` - Create new user account
- `POST /api/auth/login` - Authenticate and receive JWT token
- `POST /api/auth/logout` - Invalidate session
- `GET /api/auth/me` - Get current user profile

**Search Endpoints**:
- `POST /api/reddit/search` - Create new Reddit search run (authenticated)
  - Request: `{topics: string[], time_range: enum, page_size?: number}`
  - Response: `{run_id: uuid, status: "pending"}`
- `GET /api/reddit/runs/{id}` - Get search run status (owner only)
  - Response: `{id, status, progress, pain_points_count, created_at, completed_at}`
- `GET /api/reddit/runs/{id}/pain-points` - Get paginated pain points (owner only)
  - Query: `?page=1&limit=50`
  - Response: `{items: PainPoint[], total, page, pages}`
- `GET /api/reddit/dashboard` - Get user's search history (owner only)
  - Response: `{runs: SearchRun[], total_searches, recent_pain_points}`

### Contract Tests

**See**: `apps/api/tests/contract/test_reddit_search_contracts.py`

Tests verify:
- Request/response schemas match OpenAPI spec
- Authentication headers required for protected endpoints
- User ownership validation (403 for other users' runs)
- Pagination parameters validated
- Time range enum values accepted
- Empty results return fallback pain points

### Quickstart Test

**See**: [quickstart.md](./quickstart.md)

End-to-end validation:
1. Register new user → Verify JWT received
2. Login with credentials → Verify auth success
3. Submit search "productivity tools" (7 days) → Verify run created
4. Poll run status → Verify status transitions (pending → in_progress → completed)
5. Fetch pain points → Verify results ranked, paginated
6. Verify privacy → Other user cannot access results (403)
7. Test empty results → Verify fallback pain points shown

### Agent Context Update

**See**: [CLAUDE.md](/Users/sutiteeraniti/dev/microappfinder/CLAUDE.md)

Updated with:
- Reddit Pain Point Discovery endpoints
- PRAW client usage patterns
- 48-hour TTL + deletion sync requirements
- Composite scoring formula
- User privacy enforcement patterns

## Phase 2: Task Planning Approach

*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate from Phase 1 contracts and data model
- **Authentication tasks** (3):
  - User model + schema [P]
  - Auth endpoints (register, login, logout)
  - JWT middleware + tests [P]
- **Data model tasks** (5):
  - Topic, SearchRun, RedditPost, PainPoint models [P]
  - Alembic migration
- **Reddit integration tasks** (6):
  - PRAW client setup [P]
  - Subreddit search logic
  - Composite scoring implementation [P]
  - NSFW/spam filtering [P]
  - Deletion sync job
  - Contract tests [P]
- **Worker tasks** (4):
  - Reddit extraction task
  - Pain point extraction + scoring
  - Fallback logic for empty results
  - Integration test
- **Frontend tasks** (8):
  - Auth UI (login, register) [P]
  - Search form component [P]
  - Results display (pagination) [P]
  - Dashboard (search history) [P]
  - API client integration
  - E2E test (quickstart scenario)

**Ordering Strategy**:
- Phase 1: Models → Auth → Contracts (TDD: tests first)
- Phase 2: Reddit client → Scoring → Worker
- Phase 3: Frontend components (parallel)
- Phase 4: Integration tests → E2E tests

**Estimated Output**: 26 numbered tasks (12 parallel [P])

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation

*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking

*No constitutional violations - table empty*

## Progress Tracking

*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - approach documented)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none)

---
*Based on Constitution v1.0.0 - See `/.specify/memory/constitution.md`*
