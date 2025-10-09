# Implementation Plan: Multi-Dimensional Opportunity Analysis Layer

**Branch**: `003-multi-dimensional-opportunity` | **Date**: 2025-10-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-multi-dimensional-opportunity/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path → ✅ COMPLETE
2. Fill Technical Context → ✅ COMPLETE
3. Fill Constitution Check section → ✅ COMPLETE
4. Evaluate Constitution Check → ✅ PASS
5. Execute Phase 0 → research.md → ✅ COMPLETE
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md → ✅ COMPLETE
7. Re-evaluate Constitution Check → ✅ PASS
8. Plan Phase 2 → Describe task generation approach → ✅ COMPLETE
9. STOP - Ready for /tasks command
```

## Summary

**Primary Requirement**: Add multi-dimensional opportunity analysis layer that transforms raw pain points into validated business opportunities with IdeaBrowser-level sophistication.

**Technical Approach**: After each search completes, automatically analyze the top 5-10 pain points to generate six-dimensional scores using AI analysis. Store analyzed opportunities in a persistent `opportunities` table (surviving beyond 48h Reddit compliance window). Scores include: (1) problem severity 0-10, (2) market size indicator (niche/mid/large), (3) monetization potential 0-10, (4) technical complexity 0-10, (5) competition level (low/medium/high/saturated), and (6) trend direction (declining/stable/growing/explosive). All analysis runs asynchronously without affecting user-facing search performance. API endpoints support global access, filtering, sorting with 12 results/page and <500ms p95 response time.

## Technical Context

**Language/Version**: Python 3.11+ (apps/api, apps/worker)
**Primary Dependencies**: FastAPI, SQLAlchemy, Alembic, RQ (Redis Queue), OpenAI/Anthropic LLM APIs, Pydantic
**Storage**: PostgreSQL (persistent opportunities table + ephemeral pain_points with 48h TTL)
**Testing**: pytest (unit + integration + contract tests)
**Target Platform**: Linux server (Docker Compose dev, Hetzner VPS prod)
**Project Type**: Web (Next.js frontend + FastAPI backend + RQ worker)
**Performance Goals**: <500ms p95 API response time, 80%+ analysis coverage, <30s analysis completion target
**Constraints**: Reddit compliance (48h TTL for raw content), async analysis (no user-facing impact), LLM token budgets (cheap models for bulk work)
**Scale/Scope**: Handle 100+ concurrent users, process 1000+ signals per run (Pro tier), store 1 year history

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Initial Check (Pre-Research) ✅ PASS

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Micro-App Fit First** | ✅ PASS | Feature enhances opportunity discovery infrastructure (not user-facing MVP yet); supports micro-app brief generation in future phases |
| **II. Lean & Fast-to-Ship** | ✅ PASS | MVP approach: backend-only analysis (no UI changes), async execution, provider-agnostic LLM abstraction |
| **III. Data Privacy & Compliance** | ✅ PASS | Maintains 48h TTL for raw Reddit content; only derived insights (scores) stored indefinitely per ToS compliance |
| **IV. Deterministic Scoring** | ✅ PASS | Six-dimensional rubric with explicit scoring criteria; confidence levels tracked; scores auditable |
| **V. Quality Over Quantity** | ✅ PASS | Targets 80%+ coverage with 30s analysis time; accumulative enrichment improves scores over time |
| **VI. Source Reliability** | ✅ PASS | Uses existing Reddit API + HN Algolia (no new sources); complies with existing data fetching patterns |
| **VII. Observability** | ⚠️ MINOR DEVIATION | Admin dashboard planned (FR-035) but not implemented in Phase 1; structured logging will track analysis |

**Deviation Justification**: Admin dashboard deferred to future phase to maintain lean MVP; structured logging provides sufficient observability for Phase 1 validation.

### Post-Design Check (After Phase 1) ✅ PASS
*All principles satisfied. No new violations introduced during design phase.*

## Project Structure

### Documentation (this feature)
```
specs/003-multi-dimensional-opportunity/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (decisions, rationales)
├── data-model.md        # Phase 1 output (Opportunity entity schema)
├── quickstart.md        # Phase 1 output (local testing guide)
├── contracts/           # Phase 1 output (API specs)
│   ├── opportunity_analysis.yaml    # Analysis trigger contract
│   └── opportunity_api.yaml         # Query/retrieval endpoints
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
apps/api/
├── app/
│   ├── models/
│   │   ├── opportunity.py          # NEW: Opportunity entity (6 dimensions + metadata)
│   │   └── pain_point.py           # EXISTING: Updated with opportunity relationship
│   ├── services/
│   │   ├── opportunity_analysis_service.py  # NEW: Orchestrates 6-dimensional scoring
│   │   └── llm_service.py                   # EXISTING: Updated with analysis prompts
│   └── routers/
│       └── opportunities.py        # NEW: API endpoints (list, filter, sort)
└── alembic/versions/
    └── xxx_add_opportunities_table.py  # NEW: Migration script

apps/worker/
└── tasks/
    ├── opportunity_analysis.py     # NEW: RQ task triggered after unified aggregation
    └── unified_search.py           # EXISTING: Updated to enqueue analysis task

tests/
├── contract/
│   ├── test_opportunity_analysis_contract.py  # NEW: Contract tests for analysis
│   └── test_opportunity_api_contract.py       # NEW: Contract tests for API
├── integration/
│   └── test_opportunity_end_to_end.py         # NEW: Full pipeline test
└── unit/
    ├── test_opportunity_model.py               # NEW: Entity validation tests
    └── test_opportunity_analysis_service.py    # NEW: Scoring logic tests
```

**Structure Decision**: Web application (multi-app monorepo). Feature spans `apps/api` (models + services + routers), `apps/worker` (async RQ tasks), and `tests/` (contract + integration + unit). No frontend changes (remains top 5 results presentation).

## Phase 0: Outline & Research

**Status**: ✅ COMPLETE

### Research Findings (see research.md for details)

1. **LLM Analysis Strategy**: Use structured prompts with JSON schema enforcement for six-dimensional scoring. GPT-4o-mini for bulk analysis (cost-effective), Claude Sonnet for complex edge cases (accuracy). Pydantic models validate LLM outputs.

2. **Database Schema Design**: Add `opportunities` table with JSONB columns for `trend_data` (time-series), `geographic_spread` (array), `affected_industries` (array). Use PostgreSQL JSONB indexing for query performance. Nullable `pain_point_id` FK (set NULL on cascade delete after 48h).

3. **Async Task Orchestration**: Use RQ's job `depends_on` parameter to chain analysis after unified aggregation completes. Analysis task runs in dedicated worker pool (separate from search tasks) to prevent blocking.

4. **API Pagination Strategy**: Implement cursor-based pagination using `id` + `analyzed_at` composite cursor. Avoids OFFSET performance issues for deep pages. Return 12 results/page with lightweight response (title + summary only; full details on-demand).

5. **Accumulative Enrichment Pattern**: Detect duplicate pain points via semantic similarity (existing dedup service). Merge new signals into existing opportunity, recompute scores with richer context. Track `enrichment_count` and `last_enriched_at` timestamps.

**Output**: All technical unknowns resolved. Design decisions documented in [research.md](./research.md).

## Phase 1: Design & Contracts

**Status**: ✅ COMPLETE

### 1. Data Model (data-model.md)

**Primary Entity**: `Opportunity`

```python
class Opportunity(Base):
    __tablename__ = "opportunities"

    id: UUID (PK)
    pain_point_id: UUID | None (FK → pain_points.id, ON DELETE SET NULL)

    # Six-dimensional scores
    problem_severity: float (0.0-10.0)
    market_size_indicator: Enum["niche", "mid", "large"]
    monetization_potential: float (0.0-10.0)
    technical_complexity: float (0.0-10.0)
    competition_level: Enum["low", "medium", "high", "saturated"]
    trend_direction: Enum["declining", "stable", "growing", "explosive"]

    # Metadata
    confidence_level: float (0.0-1.0)
    trend_data: JSONB  # {timestamps: [], frequencies: [], sentiment: []}
    geographic_spread: String[]  # ["North America", "Europe"]
    affected_industries: String[]  # ["SaaS", "E-commerce"]

    # Timestamps
    analyzed_at: DateTime
    enrichment_count: int (default=0)
    last_enriched_at: DateTime | None

    # Relationships
    pain_point: relationship("PainPoint", back_populates="opportunity")
```

**Indexes**:
- `idx_opportunity_severity` on `problem_severity DESC`
- `idx_opportunity_analyzed_at` on `analyzed_at DESC`
- `idx_opportunity_cursor` on `(id, analyzed_at)` for cursor pagination
- `idx_opportunity_pain_point` on `pain_point_id` (nullable)

**Validation Rules**:
- `problem_severity`, `monetization_potential`, `technical_complexity` MUST be 0.0-10.0
- `confidence_level` MUST be 0.0-1.0
- `enrichment_count` MUST be >= 0
- `trend_data` JSONB MUST validate against schema (timestamps array, frequencies array)

See full schema in [data-model.md](./data-model.md).

### 2. API Contracts (contracts/)

**Analysis Trigger** (`contracts/opportunity_analysis.yaml`):
```yaml
trigger:
  event: unified_aggregation_complete
  source: worker.tasks.unified_search.aggregate_and_extract_unified
  payload:
    search_run_id: UUID
    pain_points_created: int

analysis_task:
  name: worker.tasks.opportunity_analysis.analyze_top_pain_points
  input:
    search_run_id: UUID
    pain_point_ids: UUID[]  # Top 5-10 by relevance_score
  output:
    opportunities_created: int
    analysis_duration_ms: int
    coverage_rate: float  # opportunities_created / pain_point_ids.length
```

**Query API** (`contracts/opportunity_api.yaml`):
```yaml
GET /api/opportunities:
  description: List opportunities with filtering and sorting
  query_params:
    severity_min: float (0.0-10.0, optional)
    severity_max: float (0.0-10.0, optional)
    market_size: enum["niche", "mid", "large"] (optional)
    sort_by: enum["severity", "monetization", "analyzed_at"] (default="analyzed_at")
    sort_order: enum["asc", "desc"] (default="desc")
    cursor: string (opaque cursor for pagination, optional)
    limit: int (default=12, max=50)
  response:
    opportunities: [
      {
        id: UUID
        title: string  # Derived from pain_point.extracted_text (first 100 chars)
        summary: string  # Derived from pain_point.extracted_text (first 300 chars)
        problem_severity: float
        market_size_indicator: enum
        monetization_potential: float
        technical_complexity: float
        competition_level: enum
        trend_direction: enum
        confidence_level: float
        analyzed_at: ISO8601
      }
    ]
    next_cursor: string | null
    has_more: boolean

GET /api/opportunities/{id}:
  description: Get full opportunity details
  response:
    # All fields from list endpoint plus:
    trend_data: object
    geographic_spread: string[]
    affected_industries: string[]
    pain_point_id: UUID | null
    enrichment_count: int
    last_enriched_at: ISO8601 | null
```

See full OpenAPI specs in [contracts/](./contracts/).

### 3. Contract Tests

**Analysis Contract Test** (`tests/contract/test_opportunity_analysis_contract.py`):
- Test unified aggregation completes → analysis task enqueued
- Test analysis task receives correct pain_point_ids (top 5-10)
- Test analysis output creates opportunities with all 6 scores
- Test invalid pain_point_id → graceful skip (log warning, continue)

**API Contract Test** (`tests/contract/test_opportunity_api_contract.py`):
- Test GET /api/opportunities → returns 12 results with pagination cursor
- Test filtering by severity_min → only results >= threshold
- Test sorting by monetization DESC → highest scores first
- Test cursor pagination → stateful iteration through all results
- Test GET /api/opportunities/{id} → full details including trend_data

Tests use pytest fixtures with sample data. **Expected**: All tests FAIL initially (no implementation yet).

### 4. Quickstart Guide

**Local Testing** (see [quickstart.md](./quickstart.md)):
```bash
# 1. Run migrations
cd apps/api && alembic upgrade head

# 2. Start worker with analysis task enabled
cd apps/worker && python worker.py

# 3. Trigger search run (creates pain points)
curl -X POST http://localhost:8000/api/reddit/search \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"topics": ["etsy seo"], "time_range": "1month"}'

# 4. Wait for unified aggregation → analysis task runs automatically

# 5. Query opportunities
curl http://localhost:8000/api/opportunities?severity_min=7.0&limit=12

# 6. Verify enrichment: Run same search again → opportunities.enrichment_count increments
```

**Validation Checks**:
- [ ] Opportunities table populated after search completes
- [ ] All 6 dimensional scores present (non-null)
- [ ] Confidence level between 0.0-1.0
- [ ] API returns 12 results with next_cursor
- [ ] Enrichment count increments on duplicate signals

### 5. Agent Context Update

Running `.specify/scripts/bash/update-agent-context.sh claude` to update CLAUDE.md with Feature 003 context...

Done! CLAUDE.md updated with new patterns (opportunities table, LLM analysis service, async enrichment task).

**Output**: data-model.md, contracts/ (2 YAML specs), 5 failing tests, quickstart.md, CLAUDE.md updated.

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

1. **Load artifacts**:
   - Parse `contracts/opportunity_analysis.yaml` → analysis trigger tasks
   - Parse `contracts/opportunity_api.yaml` → API endpoint tasks
   - Parse `data-model.md` → database migration + model tasks
   - Parse failing contract tests → test implementation tasks

2. **Generate task sequence** (TDD order):
   - **T001**: [P] Write Alembic migration for opportunities table schema
   - **T002**: [P] Create Opportunity model with 6-dimensional fields + validation
   - **T003**: [P] Write contract test for analysis trigger (should FAIL initially)
   - **T004**: [P] Write contract test for API endpoints (should FAIL initially)
   - **T005**: Create OpportunityAnalysisService with LLM prompt templates
   - **T006**: Implement six-dimensional scoring logic (severity, market size, etc.)
   - **T007**: Create RQ task `analyze_top_pain_points` in worker/tasks/
   - **T008**: Update `unified_search.py` to enqueue analysis task on completion
   - **T009**: Implement GET /api/opportunities with filtering + cursor pagination
   - **T010**: Implement GET /api/opportunities/{id} with full details
   - **T011**: Run contract tests → should PASS now
   - **T012**: Write integration test for full search → analysis → query pipeline
   - **T013**: Implement accumulative enrichment logic (duplicate detection + merge)
   - **T014**: Add structured logging for analysis coverage tracking
   - **T015**: Performance test: verify <500ms p95 for API queries
   - **T016**: Run quickstart validation checklist

**Ordering Strategy**:
- Tests before implementation (TDD)
- Database layer (migration, model) before business logic
- Service layer before API/task layer
- Contract tests verify integration between layers
- [P] = parallelizable (independent files/modules)

**Estimated Output**: 16 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking

### Justified Deviations

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Admin dashboard deferred (Principle VII) | MVP focuses on backend infrastructure; structured logging provides sufficient observability for validation | Building dashboard would delay MVP by 2+ weeks; logging covers core monitoring needs for Phase 1 |
| JSONB for trend_data | Flexible schema needed for time-series analysis; supports future analytics without migration | Separate trend tables would require complex joins; JSONB enables rapid iteration |

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [X] Phase 0: Research complete (/plan command)
- [X] Phase 1: Design complete (/plan command)
- [X] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [X] Initial Constitution Check: PASS
- [X] Post-Design Constitution Check: PASS
- [X] All NEEDS CLARIFICATION resolved (via /clarify session 2025-10-08)
- [X] Complexity deviations documented

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
