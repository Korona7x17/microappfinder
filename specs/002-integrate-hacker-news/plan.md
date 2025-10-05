# Implementation Plan: Hacker News Integration for Unified Search

**Branch**: `002-integrate-hacker-news` | **Date**: 2025-10-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-integrate-hacker-news/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 8. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

Integrate Hacker News (via Algolia HN API) as an additional background data source into the existing unified search pipeline. HN items will be fetched hourly, normalized into the same schema as Reddit pain points, scored using the mirrored Reddit scoring algorithm (points→upvotes mapping), and deduplicated using semantic similarity (85% cosine threshold) before being blended into the top-3 unified search results. This enhances coverage and freshness without changing the user experience.

**Technical Approach**:
- Create `HackerNewsItem` model mirroring `RedditPost` structure (48h cache for consistency)
- Implement hourly background job to fetch from Algolia HN API
- Extend existing scoring pipeline to handle HN items using same weights as Reddit
- Leverage existing semantic deduplication infrastructure with 85% threshold
- Add HN provider to search aggregator with parallel query execution
- Implement circuit breaker and 500ms timeout for HN API calls

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript/Next.js 14 (frontend - minimal changes)
**Primary Dependencies**:
- FastAPI + SQLAlchemy + Pydantic (backend)
- RQ (Redis Queue) for background jobs
- Algolia HN API client (requests or httpx)
- Existing embedding service for semantic similarity
**Storage**: PostgreSQL (metadata), Redis (48h cache + RQ jobs)
**Testing**: pytest (backend unit/integration), contract tests via OpenAPI schema
**Target Platform**: Linux server (Docker Compose dev, Hetzner VPS prod)
**Project Type**: Web (monorepo: apps/api, apps/worker, apps/web)
**Performance Goals**:
- p95 latency ≤1 second for unified search
- Hourly HN refresh cycle
- 500ms timeout for HN API calls
**Constraints**:
- No UI changes (backend-only feature)
- Must mirror Reddit scoring exactly (0.3×upvotes + 0.25×comments + 0.25×recency + 0.2×sentiment)
- 48h data retention for raw HN content (consistency with Reddit compliance)
- Algolia HN API rate limits (research needed)
**Scale/Scope**:
- Support 100 concurrent users (MVP target)
- Process 1000 signals per run
- Hourly background job for HN ingestion

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ I. Micro-App Fit First (NON-NEGOTIABLE)
- [x] Solves 1 core job-to-be-done: Enhances search result quality by adding HN as a source
- [x] ≤3 screens: No new UI (backend integration only)
- [x] <1 week buildable: Yes (extends existing Reddit pattern)
- [x] ≤15 seconds user input: No change (same search UX)
- [x] $0 infrastructure initially: Uses existing PostgreSQL + Redis (Algolia HN API is free)

**Status**: ✅ PASS

### ✅ II. Lean & Fast-to-Ship
- [x] MVP speed over perfection: Mirrors existing Reddit implementation for fast delivery
- [x] No premature optimization: Hourly refresh (not real-time) keeps it simple
- [x] Provider-agnostic: Algolia HN is official public API (no scraping)
- [x] Docker-first: Existing Docker Compose setup supports this
- [x] No bloat: Reuses existing models, scoring, deduplication infrastructure

**Status**: ✅ PASS

### ✅ III. Data Privacy & Compliance (NON-NEGOTIABLE)
- [x] Store only public content: HN data is public, no PII
- [x] Respect platform ToS: Algolia HN API is official, documented
- [x] Per-domain throttling <1 rps: Hourly batch fetch reduces API calls significantly
- [x] Cache 48h: Mirrors Reddit retention for consistency
- [x] No PII collection: HN items are public stories/discussions

**Status**: ✅ PASS

### ✅ IV. Deterministic Scoring + Transparent Methodology
- [x] Mirrors Reddit scoring: 0.3×points + 0.25×comments + 0.25×recency + 0.2×sentiment
- [x] Reproducible: Same inputs → same scores
- [x] Auditable: Score components visible
- [x] Explainable: Users understand HN items compete with Reddit on same rubric

**Status**: ✅ PASS

### ✅ V. Quality Over Quantity
- [x] Top-3 results focus maintained
- [x] Deduplication: Semantic similarity (85% cosine) prevents cross-source duplicates
- [x] Confidence scoring: Existing confidence logic applies to HN
- [x] No quality degradation: A/B testing validates relevance

**Status**: ✅ PASS

### ✅ VI. Source Reliability & Safety
- [x] Uses official Algolia HN API (approved primary source per constitution)
- [x] No scraping required
- [x] Stable, documented API

**Status**: ✅ PASS

### ✅ VII. Observability & Debugging
- [x] Structured logging: Reuse existing run_id pattern
- [x] Progress tracking: Extend existing pipeline visibility
- [x] Error transparency: Graceful degradation if HN unavailable
- [x] Monitoring: Existing Sentry + Uptime Kuma apply

**Status**: ✅ PASS

**Overall Constitution Check**: ✅ **PASS** — No violations, no complexity justifications needed.

## Project Structure

### Documentation (this feature)
```
specs/002-integrate-hacker-news/
├── spec.md              # Feature specification (input)
├── plan.md              # This file (/plan output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── hackernews-api.yaml
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
apps/
├── api/
│   └── app/
│       ├── models/
│       │   ├── hackernews_item.py        # NEW: HN cache model
│       │   ├── pain_point.py             # MODIFY: Support multi-source
│       │   └── search_run.py             # MODIFY: Track HN in metadata
│       ├── routers/
│       │   └── search.py                 # MODIFY: Add HN to aggregator
│       ├── services/
│       │   ├── hackernews/              # NEW: HN provider
│       │   │   ├── __init__.py
│       │   │   ├── client.py            # Algolia HN API client
│       │   │   ├── normalizer.py        # HN → unified schema
│       │   │   └── scorer.py            # Mirror Reddit scoring
│       │   ├── scoring/
│       │   │   └── unified_scorer.py     # MODIFY: Multi-source scoring
│       │   └── deduplication/
│       │       └── semantic_dedup.py     # MODIFY: Cross-source dedup
│       └── schemas/
│           └── hackernews.py             # NEW: HN Pydantic schemas
├── worker/
│   ├── jobs/
│   │   └── fetch_hackernews.py          # NEW: Hourly HN ingestion job
│   └── worker.py                        # MODIFY: Register HN job
└── web/
    └── (no changes - backend only)

tests/
├── api/
│   ├── contracts/
│   │   └── test_hackernews_contract.py  # NEW: HN contract tests
│   ├── integration/
│   │   ├── test_hackernews_search.py    # NEW: HN search integration
│   │   └── test_unified_dedup.py        # MODIFY: Cross-source dedup
│   └── unit/
│       ├── test_hn_client.py            # NEW: HN API client unit tests
│       ├── test_hn_normalizer.py        # NEW: HN normalization tests
│       └── test_hn_scorer.py            # NEW: HN scoring tests
└── worker/
    └── test_fetch_hackernews_job.py     # NEW: HN job tests
```

**Structure Decision**: Web application monorepo (apps/api, apps/worker, apps/web). Backend-heavy feature with no frontend changes. Mirrors existing Reddit provider pattern established in feature 001-reddit-pain-point.

## Phase 0: Outline & Research

**Goal**: Resolve remaining NEEDS CLARIFICATION items and establish technical decisions.

**Unknowns from Spec**:
1. FR-019: Expected query volume and concurrent user load
2. FR-022: Algolia HN API rate limits and handling
3. Assumptions: Existing API infrastructure for external calls
4. Assumptions: Existing deduplication/normalization libraries
5. Dependencies: Specific services/modules for search aggregation

**Research Tasks**:
1. **Algolia HN API Investigation**:
   - Endpoint: https://hn.algolia.com/api
   - Rate limits: Document official limits
   - Query parameters for search + filtering
   - Response schema mapping to unified format
   - Error handling and retry strategies

2. **Existing Infrastructure Audit**:
   - Review `apps/worker/jobs/` for background job patterns
   - Review `apps/api/app/services/` for external API client patterns
   - Review `apps/api/app/models/reddit_post.py` for 48h cache pattern
   - Identify embedding service for semantic similarity (if exists, else plan fallback)

3. **Scoring & Deduplication Discovery**:
   - Locate existing scoring implementation (check worker.py or services/)
   - Confirm Reddit scoring formula matches spec (0.3×upvotes + 0.25×comments + 0.25×recency + 0.2×sentiment)
   - Identify semantic similarity library (sentence-transformers, OpenAI embeddings, etc.)
   - Confirm 85% cosine threshold is feasible

4. **Performance Baseline**:
   - Document current search endpoint p95 latency (target: <1s)
   - Confirm parallel query execution capability (asyncio or similar)
   - Validate 500ms timeout feasibility for external API

**Output**: `research.md` with decisions, rationale, and alternatives considered for each unknown.

## Phase 1: Design & Contracts

*Prerequisites: research.md complete*

### 1. Data Model Design (`data-model.md`)

**Entities**:

#### HackerNewsItem (NEW)
- **Purpose**: 48h cache of HN content (mirrors RedditPost pattern)
- **Fields**:
  - `id`: UUID (PK)
  - `hn_id`: String (unique, HN item ID)
  - `hn_type`: String (story/comment/poll)
  - `author`: String (nullable)
  - `title`: Text
  - `text`: Text (nullable, for self posts)
  - `url`: String (HN permalink)
  - `points`: Integer (HN score)
  - `comment_count`: Integer
  - `created_utc`: TIMESTAMP
  - `fetched_at`: TIMESTAMP
  - `expires_at`: TIMESTAMP (fetched_at + 48h)
- **Relationships**: None (cache only, soft-referenced by PainPoint)
- **Validation**: `expires_at = fetched_at + 48h`, `points >= 0`, `comment_count >= 0`

#### PainPoint (MODIFY)
- **Changes**:
  - Add `source_type`: String (enum: 'reddit', 'hackernews') to track origin
  - Modify `source_reddit_post_ids`: Rename to `source_post_ids` (JSONB, agnostic)
  - Add `source_platform`: String to metadata
- **Migration**: Alembic migration to add new fields with defaults for existing rows

#### SearchRun (MODIFY)
- **Changes**:
  - Add `sources_queried`: JSONB array (e.g., ["reddit", "hackernews"])
  - Add `hn_items_fetched`: Integer (nullable, HN-specific count)
- **Migration**: Add optional metadata fields

### 2. API Contracts (`contracts/hackernews-api.yaml`)

**No new public endpoints** (backend integration only). Document internal service contract:

```yaml
# Internal Service Contract: HackerNews Provider
HackerNewsClient.search(query: str, time_range: str) -> List[HNItemSchema]
  - Queries Algolia HN API
  - Returns normalized HN items
  - Timeout: 500ms
  - Circuit breaker on 3 consecutive failures

HNNormalizer.to_unified_schema(hn_item: HNItemSchema) -> UnifiedSearchResult
  - Maps HN fields to unified schema
  - Applies source attribution

HNScorer.calculate_score(hn_item: HNItemSchema) -> float
  - Mirrors Reddit formula: 0.3×points + 0.25×comments + 0.25×recency + 0.2×sentiment
  - Returns score 0-1
```

### 3. Contract Tests (TDD)

Generate failing tests:
- `tests/api/unit/test_hn_client.py`: Mock Algolia HN API responses
- `tests/api/unit/test_hn_normalizer.py`: Validate field mapping
- `tests/api/unit/test_hn_scorer.py`: Assert scoring formula correctness
- `tests/api/integration/test_hackernews_search.py`: End-to-end HN search flow
- `tests/api/integration/test_unified_dedup.py`: Cross-source deduplication with Reddit + HN

### 4. Quickstart Test Scenarios (`quickstart.md`)

Extract from user stories:
1. **User Story 1**: Search "productivity tools" → Validate top 3 results include HN items with correct schema
2. **User Story 2**: No source selection → Confirm automatic blending
3. **User Story 3**: Fresh results → Confirm HN items ≤1 hour old appear
4. **Edge Case**: HN API down → Confirm graceful degradation (Redis returns without error)

### 5. Update CLAUDE.md

Run: `.specify/scripts/bash/update-agent-context.sh claude`

Add to context:
- Recent change: HN integration (feature 002)
- Tech: Algolia HN API, semantic deduplication (85% threshold)
- Patterns: Hourly background job, mirrored scoring, 48h cache

**Output**: `data-model.md`, `contracts/hackernews-api.yaml`, failing tests, `quickstart.md`, updated `CLAUDE.md`

## Phase 2: Task Planning Approach

*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. Load `.specify/templates/tasks-template.md`
2. Generate tasks from Phase 1 artifacts:
   - data-model.md entities → model creation tasks
   - contracts → contract test tasks
   - quickstart scenarios → integration test tasks
3. Follow TDD order: Tests first, implementation second
4. Mark [P] for parallelizable tasks (independent files)

**Task Categories**:
- **Database**: Alembic migration for `HackerNewsItem`, `PainPoint`, `SearchRun` schema changes
- **Models**: Create `HackerNewsItem` model
- **Services**: HN client, normalizer, scorer
- **Integration**: Extend search aggregator to query HN in parallel with Reddit
- **Worker**: Hourly HN fetch job
- **Tests**: Contract tests, unit tests, integration tests
- **Validation**: Quickstart execution, A/B test setup

**Ordering Strategy**:
1. Database migrations (blocking)
2. Model creation [P]
3. Service layer (client, normalizer, scorer) [P]
4. Integration (aggregator, deduplication) [depends on services]
5. Worker job [depends on services]
6. Tests [throughout, TDD]
7. Quickstart validation [final]

**Estimated Output**: 20-25 tasks in dependency order

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation

*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md)
**Phase 5**: Validation (pytest, quickstart.md, A/B testing)

## Complexity Tracking

*No constitutional violations — this section is empty.*

## Progress Tracking

*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) ✅
- [x] Phase 1: Design complete (/plan command) ✅
- [x] Phase 2: Task planning complete (/plan command - describe approach only) ✅
- [x] Phase 3: Tasks generated (/tasks command) ✅
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS ✅
- [x] Post-Design Constitution Check: PASS ✅
- [x] All NEEDS CLARIFICATION resolved ✅
- [x] Complexity deviations documented (none) ✅

**Artifacts Generated**:
- [x] research.md (Phase 0)
- [x] data-model.md (Phase 1)
- [x] contracts/hackernews-api.yaml (Phase 1)
- [x] quickstart.md (Phase 1)
- [x] CLAUDE.md updated (Phase 1)
- [x] tasks.md (Phase 3) - 28 tasks, 16 parallel

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
