# Implementation Tasks: Multi-Dimensional Opportunity Analysis Layer

**Feature**: 003-multi-dimensional-opportunity | **Date**: 2025-10-08 | **Branch**: `003-multi-dimensional-opportunity`

## Overview

This document contains the ordered implementation tasks for Feature 003. Tasks follow TDD (Test-Driven Development) order: write failing tests first, then implement functionality to make tests pass.

**Estimated Duration**: 14-18 hours (2-3 days)
**Constitution Compliance**: All principles validated in plan.md

## Task Dependencies

```
T001 (Migration) ━━┳━━ T002 (Model)
                   ┃
                   ┣━━ T003 (Analysis Contract Test)
                   ┣━━ T004 (API Contract Test)
                   ┃
T003, T004 ━━━━━━━━╋━━ T005 (LLM Service)
                   ┃
T005 ━━━━━━━━━━━━━━╋━━ T006 (Scoring Logic)
                   ┃
T006 ━━━━━━━━━━━━━━╋━━ T007 (Worker Task)
                   ┃
T007 ━━━━━━━━━━━━━━╋━━ T008 (Unified Search Update)
                   ┃
T002, T008 ━━━━━━━━╋━━ T009 (List API)
                   ┣━━ T010 (Detail API)
                   ┃
T009, T010 ━━━━━━━━╋━━ T011 (Run Contract Tests)
                   ┃
T011 ━━━━━━━━━━━━━━╋━━ T012 (Integration Test)
                   ┣━━ T013 (Enrichment Logic)
                   ┣━━ T014 (Structured Logging)
                   ┣━━ T015 (Performance Tests)
                   ┃
T015 ━━━━━━━━━━━━━━┻━━ T016 (Validation)
```

## Tasks

### T001: Create Database Migration

**Priority**: High | **Parallelizable**: Yes | **Estimated**: 30min

**Objective**: Create Alembic migration script for `opportunities` table.

**Files**:
- Create: `apps/api/alembic/versions/xxx_add_opportunities_table.py`

**Requirements**:
- Generate migration with `alembic revision -m "add opportunities table"`
- Implement `upgrade()` function with table creation (reference data-model.md lines 219-248)
- Implement `downgrade()` function with table drop
- Include all 6 indexes (severity, analyzed_at, cursor, pain_point, monetization, market_size)
- Add CHECK constraints for all score ranges and enum values

**Acceptance Criteria**:
- [ ] Migration runs successfully: `alembic upgrade head`
- [ ] Migration is reversible: `alembic downgrade -1`
- [ ] All indexes created (verify with `\d opportunities` in psql)
- [ ] CHECK constraints enforce valid ranges (test with invalid insert)

**References**:
- data-model.md:199-248 (migration script template)

---

### T002: Create Opportunity Model

**Priority**: High | **Parallelizable**: Yes (after T001) | **Estimated**: 45min

**Objective**: Implement SQLAlchemy model for `Opportunity` entity with Pydantic validation schemas.

**Files**:
- Create: `apps/api/app/models/opportunity.py`
- Update: `apps/api/app/models/__init__.py` (add import)
- Update: `apps/api/app/models/pain_point.py` (add relationship)

**Requirements**:
- Implement `Opportunity` SQLAlchemy model (data-model.md:61-101)
- Implement Pydantic schemas:
  - `OpportunityScores` (LLM output validation)
  - `TrendData` (JSONB schema)
  - `OpportunityCreate` (service input)
  - `OpportunityResponse` (API list response)
  - `OpportunityDetail` (API detail response)
- Add `update_scores()` method for enrichment
- Add `opportunity` back_populates relationship to `PainPoint` model

**Acceptance Criteria**:
- [ ] Model imports without errors
- [ ] Pydantic validation enforces all field constraints
- [ ] Test invalid score values raise ValidationError
- [ ] Relationship with PainPoint works bidirectionally

**References**:
- data-model.md:49-153 (model and schema definitions)

---

### T003: Write Analysis Task Contract Test

**Priority**: High | **Parallelizable**: Yes (after T001) | **Estimated**: 30min

**Objective**: Create contract test for opportunity analysis RQ task (should FAIL initially).

**Files**:
- Create: `apps/worker/tests/contract/test_opportunity_analysis_contract.py`

**Requirements**:
- Test unified aggregation completes → analysis task enqueued
- Test analysis task receives correct `pain_point_ids` (top 5-10 by relevance_score)
- Test analysis output creates opportunities with all 6 scores
- Test invalid `pain_point_id` → graceful skip (log warning, continue)
- Test task timeout after 5 minutes
- Test retry on failure (max 2 retries)

**Acceptance Criteria**:
- [ ] All tests FAIL initially (task not implemented yet)
- [ ] Tests use pytest fixtures with sample data
- [ ] Tests verify contract compliance (opportunity_analysis.yaml)
- [ ] Tests run in <10s

**References**:
- contracts/opportunity_analysis.yaml (task contract)

---

### T004: Write API Contract Test

**Priority**: High | **Parallelizable**: Yes (after T001) | **Estimated**: 45min

**Objective**: Create contract tests for opportunity API endpoints (should FAIL initially).

**Files**:
- Create: `apps/api/tests/contract/test_opportunity_api_contract.py`

**Requirements**:
- Test GET /api/opportunities:
  - Returns 12 results with pagination cursor
  - Filtering by `severity_min` → only results >= threshold
  - Filtering by `market_size` → only matching enum value
  - Sorting by `monetization` DESC → highest scores first
  - Cursor pagination → stateful iteration through all results
- Test GET /api/opportunities/{id}:
  - Returns full details including `trend_data`, `geographic_spread`, `affected_industries`
  - Returns 404 for non-existent ID

**Acceptance Criteria**:
- [ ] All tests FAIL initially (endpoints not implemented yet)
- [ ] Tests verify response schemas match opportunity_api.yaml
- [ ] Tests use FastAPI TestClient
- [ ] Tests run in <15s

**References**:
- contracts/opportunity_api.yaml (API contract)

---

### T005: Create LLM Analysis Service

**Priority**: High | **Dependencies**: T003, T004 | **Estimated**: 1.5h

**Objective**: Implement service for GPT-4o-mini LLM analysis with structured JSON outputs.

**Files**:
- Create: `apps/api/app/services/opportunity_analysis_service.py`

**Requirements**:
- Implement `OpportunityAnalysisService` class:
  - `analyze_pain_point(pain_point: PainPoint) -> OpportunityScores`
    - Call GPT-4o-mini with structured prompt
    - Use `response_format={"type": "json_object"}` parameter
    - Validate output with `OpportunityScores` Pydantic model
    - Token budget: 2000 input, 500 output
  - `_build_analysis_prompt(pain_point: PainPoint) -> str`
    - Template with 6-dimensional rubric
    - Include extracted_text, source_platform, relevance_score
  - `_fallback_to_claude(pain_point: PainPoint) -> OpportunityScores`
    - Retry with Claude Sonnet 3.5 on GPT-4o-mini failure
- Implement error handling:
  - Log API errors with structured logging
  - Return `None` on analysis failure (skip opportunity creation)
  - Track token usage for monitoring

**Acceptance Criteria**:
- [ ] Service analyzes sample pain point successfully
- [ ] Returns valid `OpportunityScores` object
- [ ] Handles API errors gracefully (returns None)
- [ ] Respects token budgets (<2500 tokens total)
- [ ] Fallback to Claude works on GPT-4o-mini failure

**References**:
- research.md:8-40 (LLM strategy decision)
- data-model.md:106-116 (OpportunityScores schema)

---

### T006: Implement Six-Dimensional Scoring Logic

**Priority**: High | **Dependencies**: T005 | **Estimated**: 1h

**Objective**: Complete LLM prompt template with explicit rubrics for each dimension.

**Files**:
- Update: `apps/api/app/services/opportunity_analysis_service.py`

**Requirements**:
- Implement `_build_analysis_prompt()` with rubrics:
  - **Problem Severity (0-10)**: Pain intensity, frequency, impact on workflow
  - **Market Size (niche/mid/large)**: User count estimates, community size
  - **Monetization Potential (0-10)**: Willingness to pay, urgency indicators
  - **Technical Complexity (0-10)**: Build difficulty, required expertise
  - **Competition Level (low/medium/high/saturated)**: Existing solutions count
  - **Trend Direction (declining/stable/growing/explosive)**: Discussion velocity
- Include examples for each score range (e.g., severity 0-3 = minor inconvenience)
- Add JSON schema to prompt for structured output

**Acceptance Criteria**:
- [ ] Prompt generates consistent scores across similar pain points
- [ ] All 6 dimensions included in every analysis
- [ ] Confidence level correlates with evidence quality
- [ ] Reasoning field explains score rationale
- [ ] Manual validation: 5 sample pain points scored accurately

**References**:
- specs/003-multi-dimensional-opportunity/spec.md:FR-002 to FR-007 (dimension definitions)
- research.md:19-28 (scoring rubric Pydantic model)

---

### T007: Create RQ Analysis Task

**Priority**: High | **Dependencies**: T006 | **Estimated**: 1h

**Objective**: Implement RQ worker task that analyzes top pain points after unified aggregation.

**Files**:
- Create: `apps/worker/worker/tasks/opportunity_analysis.py`

**Requirements**:
- Implement `analyze_top_pain_points(search_run_id: UUID) -> dict`:
  - Query top 5-10 pain points by `relevance_score` DESC
  - For each pain point:
    - Call `OpportunityAnalysisService.analyze_pain_point()`
    - Create `Opportunity` record with scores
    - Handle analysis failures (skip, log warning, continue)
  - Track metrics: `opportunities_created`, `analysis_duration_ms`, `coverage_rate`
  - Return metrics dict for monitoring
- Configure task:
  - Timeout: 300 seconds (5 minutes)
  - Max retries: 2
  - Queue: `default`
- Add structured logging with search_run_id context

**Acceptance Criteria**:
- [ ] Task processes 5-10 pain points successfully
- [ ] Creates opportunities in database
- [ ] Returns metrics dict matching contract (opportunity_analysis.yaml)
- [ ] Handles pain_point not found gracefully
- [ ] Completes within timeout (<5min for 10 analyses)
- [ ] T003 contract tests now PASS

**References**:
- contracts/opportunity_analysis.yaml (task contract)
- research.md:89-124 (async task orchestration decision)

---

### T008: Update Unified Search to Enqueue Analysis

**Priority**: High | **Dependencies**: T007 | **Estimated**: 30min

**Objective**: Chain analysis task after unified aggregation completes.

**Files**:
- Update: `apps/worker/worker/tasks/unified_search.py`

**Requirements**:
- At end of `aggregate_and_extract_unified()` function:
  - Import `analyze_top_pain_points` from `worker.tasks.opportunity_analysis`
  - Enqueue analysis task with `depends_on=get_current_job()`
  - Pass `search_run_id` parameter
  - Configure timeout: `job_timeout='5m'`
- Add logging: "Enqueued opportunity analysis for search {search_run_id}"

**Acceptance Criteria**:
- [ ] Analysis task enqueues after unified aggregation succeeds
- [ ] Analysis task does NOT run if aggregation fails
- [ ] Job chaining verified in RQ dashboard (or logs)
- [ ] No blocking (unified aggregation completes immediately)

**References**:
- research.md:93-113 (RQ job chaining implementation)

---

### T009: Implement List Opportunities API

**Priority**: High | **Dependencies**: T002, T008 | **Estimated**: 1.5h

**Objective**: Create GET /api/opportunities endpoint with filtering, sorting, and cursor pagination.

**Files**:
- Create: `apps/api/app/routers/opportunities.py`
- Update: `apps/api/app/main.py` (register router)
- Create: `apps/api/app/services/opportunity_service.py` (query logic)

**Requirements**:
- Implement `GET /api/opportunities`:
  - Query parameters: `severity_min`, `severity_max`, `market_size`, `competition_level`, `trend_direction`, `sort_by`, `sort_order`, `cursor`, `limit` (default=12, max=50)
  - Filtering logic for each parameter
  - Sorting: severity DESC, monetization DESC, analyzed_at DESC (default)
  - Cursor-based pagination:
    - Encode cursor: Base64(JSON({id, analyzed_at}))
    - Decode cursor and apply WHERE clause
    - Return `next_cursor` if more results exist
  - Response: `{opportunities: [...], next_cursor: str | null, has_more: bool}`
  - Title/summary derived from pain_point.extracted_text (first 100/300 chars)
- Handle orphaned opportunities (pain_point_id=NULL):
  - Use cached title/summary or return placeholder
- No authentication required (global access per spec clarifications)

**Acceptance Criteria**:
- [ ] Endpoint returns 12 results by default
- [ ] Filtering works for all parameters (test each)
- [ ] Sorting works for all sort_by options
- [ ] Cursor pagination maintains stable order
- [ ] Response matches `OpportunityResponse` schema
- [ ] p95 latency <500ms (test with 1000+ records)
- [ ] T004 contract tests for list endpoint now PASS

**References**:
- contracts/opportunity_api.yaml:7-111 (endpoint spec)
- research.md:127-160 (cursor pagination decision)

---

### T010: Implement Get Opportunity Details API

**Priority**: High | **Dependencies**: T002, T008 | **Estimated**: 45min

**Objective**: Create GET /api/opportunities/{id} endpoint with full opportunity details.

**Files**:
- Update: `apps/api/app/routers/opportunities.py`

**Requirements**:
- Implement `GET /api/opportunities/{id}`:
  - Path parameter: `id` (UUID)
  - Query single opportunity by ID
  - Include all fields: 6 scores + trend_data + geographic_spread + affected_industries + enrichment metadata
  - Handle orphaned opportunities (pain_point_id=NULL)
  - Return 404 if opportunity not found
- Response matches `OpportunityDetail` schema

**Acceptance Criteria**:
- [ ] Endpoint returns full details for valid ID
- [ ] Returns 404 for non-existent ID
- [ ] Response matches `OpportunityDetail` schema
- [ ] p95 latency <100ms
- [ ] T004 contract tests for detail endpoint now PASS

**References**:
- contracts/opportunity_api.yaml:114-196 (endpoint spec)

---

### T011: Run Contract Tests (Validation Gate)

**Priority**: High | **Dependencies**: T009, T010 | **Estimated**: 15min

**Objective**: Verify all contract tests now PASS.

**Command**:
```bash
pytest apps/worker/tests/contract/test_opportunity_analysis_contract.py -v
pytest apps/api/tests/contract/test_opportunity_api_contract.py -v
```

**Requirements**:
- All tests from T003 and T004 must PASS
- Fix any failing tests before proceeding

**Acceptance Criteria**:
- [ ] Analysis contract tests: 100% pass
- [ ] API contract tests: 100% pass
- [ ] No skipped or xfailed tests

**References**:
- contracts/opportunity_analysis.yaml
- contracts/opportunity_api.yaml

---

### T012: Write Integration Test

**Priority**: Medium | **Dependencies**: T011 | **Estimated**: 1h

**Objective**: Test full pipeline from search → analysis → API query.

**Files**:
- Create: `apps/api/tests/integration/test_opportunity_end_to_end.py`

**Requirements**:
- Test scenario:
  1. Create search run with test topics
  2. Trigger unified aggregation (creates pain points)
  3. Wait for analysis task to complete (poll RQ job status)
  4. Query GET /api/opportunities
  5. Verify opportunities created with correct scores
  6. Query GET /api/opportunities/{id}
  7. Verify full details returned
- Use pytest fixtures for test data cleanup
- Mock LLM API calls (use VCR.py or similar)

**Acceptance Criteria**:
- [ ] Full pipeline test passes end-to-end
- [ ] Test runs in <60s (with mocked LLM)
- [ ] Test cleans up all created records
- [ ] Test is deterministic (no flakiness)

**References**:
- quickstart.md:262-287 (testing workflow)

---

### T013: Implement Accumulative Enrichment

**Priority**: Medium | **Dependencies**: T012 | **Estimated**: 1.5h

**Objective**: Add logic to merge duplicate signals into existing opportunities.

**Files**:
- Update: `apps/worker/worker/tasks/opportunity_analysis.py`
- Create: `apps/api/app/services/enrichment_service.py`

**Requirements**:
- Implement duplicate detection:
  - Before creating new opportunity, check for existing opportunity with similar pain_point
  - Use `DeduplicationService` (existing) to check URL match or semantic similarity (>85% Jaccard, >0.90 embedding cosine)
- Implement enrichment logic:
  - Merge pain_point contexts (concatenate text, aggregate metadata)
  - Re-analyze with enriched context (call LLM again)
  - Update existing opportunity scores
  - Increment `enrichment_count`
  - Set `last_enriched_at` timestamp
- Add logging: "Enriched opportunity {id} (count={enrichment_count})"

**Acceptance Criteria**:
- [ ] Running same search twice enriches opportunities (not creates duplicates)
- [ ] `enrichment_count` increments correctly
- [ ] Scores improve with richer context (manual validation)
- [ ] No duplicate opportunities created for similar pain points

**References**:
- research.md:164-205 (enrichment pattern decision)

---

### T014: Add Structured Logging

**Priority**: Medium | **Dependencies**: T012 | **Estimated**: 30min

**Objective**: Add structured logging for analysis coverage tracking.

**Files**:
- Update: `apps/worker/worker/tasks/opportunity_analysis.py`
- Create: `apps/worker/config/logging_config.py` (if not exists)

**Requirements**:
- Log at task completion:
  - `search_run_id`
  - `opportunities_created`
  - `pain_points_analyzed`
  - `coverage_rate` (opportunities_created / pain_points_analyzed)
  - `analysis_duration_ms`
  - `failures_count` (pain points that failed analysis)
- Use structured format (JSON) for log aggregation
- Include context in all log messages (search_run_id)

**Acceptance Criteria**:
- [ ] Logs include all required fields
- [ ] Logs are JSON-formatted
- [ ] Coverage rate calculated correctly
- [ ] Logs searchable by search_run_id

**References**:
- plan.md:51 (observability principle compliance)

---

### T015: Performance Testing

**Priority**: Medium | **Dependencies**: T014 | **Estimated**: 1h

**Objective**: Verify API endpoints meet p95 latency requirements.

**Files**:
- Create: `apps/api/tests/performance/test_opportunity_performance.py`

**Requirements**:
- Load test GET /api/opportunities:
  - Create 1000 opportunities in database
  - Run 100 requests with various filters
  - Measure p95 latency
  - Verify <500ms p95
- Load test GET /api/opportunities/{id}:
  - Run 100 requests for random IDs
  - Measure p95 latency
  - Verify <100ms p95
- Test cursor pagination:
  - Iterate through all 1000 records using cursor
  - Verify stable performance (no degradation on deep pages)

**Acceptance Criteria**:
- [ ] List endpoint: p95 <500ms
- [ ] Detail endpoint: p95 <100ms
- [ ] Cursor pagination: consistent performance across all pages
- [ ] No N+1 query issues (check with SQLAlchemy logging)

**References**:
- contracts/opportunity_api.yaml:108-110, 193-195 (performance targets)
- research.md:187-188 (index strategy for performance)

---

### T016: Run Quickstart Validation

**Priority**: High | **Dependencies**: T015 | **Estimated**: 30min

**Objective**: Execute quickstart.md validation checklist to confirm feature completeness.

**Files**:
- Reference: `specs/003-multi-dimensional-opportunity/quickstart.md`

**Procedure**:
1. Run migrations: `alembic upgrade head`
2. Start worker: `python worker.py`
3. Trigger search via API
4. Wait for analysis task completion
5. Query opportunities API
6. Verify enrichment (run same search again)
7. Run all tests: `pytest`

**Validation Checklist** (from quickstart.md):
- [ ] Opportunities table populated after search completes
- [ ] All 6 dimensional scores present (non-null)
- [ ] Confidence level between 0.0-1.0
- [ ] API returns 12 results with next_cursor
- [ ] Enrichment count increments on duplicate signals
- [ ] Analysis completes within 30s target
- [ ] Coverage rate >80% (opportunities created / pain points)
- [ ] No errors in worker logs
- [ ] No errors in API logs
- [ ] p95 latency <500ms for list endpoint
- [ ] p95 latency <100ms for detail endpoint
- [ ] Contract tests: 100% pass

**Acceptance Criteria**:
- [ ] All 12 validation checks pass
- [ ] Feature is production-ready

**References**:
- quickstart.md:282-287 (validation checklist)

---

## Completion Checklist

**Phase Status**:
- [ ] All 16 tasks completed
- [ ] Contract tests pass (T011)
- [ ] Integration test passes (T012)
- [ ] Performance tests pass (T015)
- [ ] Quickstart validation passes (T016)

**Deliverables**:
- [ ] Database migration applied
- [ ] Opportunity model created
- [ ] LLM analysis service implemented
- [ ] RQ analysis task implemented
- [ ] API endpoints implemented
- [ ] Enrichment logic implemented
- [ ] Structured logging added
- [ ] All tests passing

**Ready for Merge**:
- [ ] Branch: `003-multi-dimensional-opportunity`
- [ ] PR title: "Feature 003: Multi-Dimensional Opportunity Analysis Layer"
- [ ] PR description includes:
  - Link to spec.md
  - Performance benchmarks
  - Screenshots of API responses (optional)
  - Breaking changes: None

---

**Estimated Total Duration**: 14-18 hours (2-3 days)
**Based on**: plan.md Phase 2 task planning approach
