# Tasks: Hacker News Integration for Unified Search

**Feature**: 002-integrate-hacker-news
**Input**: Design documents from `/specs/002-integrate-hacker-news/`
**Prerequisites**: plan.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

## Execution Summary

**Total Tasks**: 28
**Estimated Time**: 3-4 days
**Parallel Tasks**: 16 (marked with [P])
**Sequential Tasks**: 12

**Key Dependencies**:
- Database migrations (T001-T003) must complete before any model work
- All tests (T004-T010) must be written and failing before implementation starts
- Models (T011-T012) must exist before services (T013-T015)
- Services must exist before integration (T016-T019)

---

## Phase 3.1: Setup & Database Migrations

**Goal**: Prepare database schema for multi-source support.

- [ ] **T001** Create Alembic migration for `hackernews_items` table
  - **File**: `apps/api/alembic/versions/XXXXX_add_hackernews_item_model.py`
  - **Action**: Create table with all fields from data-model.md (id, hn_id, hn_type, author, title, text, url, hn_url, points, comment_count, created_utc, fetched_at, expires_at, tags)
  - **Constraints**: Add CHECK constraints for `points >= 0`, `comment_count >= 0`
  - **Indexes**: Create indexes on `hn_id` (unique), `expires_at`, `created_utc`
  - **Dependency**: None (start here)

- [ ] **T002** Create Alembic migration for `pain_points` multi-source support
  - **File**: `apps/api/alembic/versions/XXXXX_add_multi_source_support_to_pain_points.py`
  - **Action**: Add `source_platform` column (String, default 'reddit'), rename `source_reddit_post_ids` to `source_post_ids`
  - **Backfill**: Set `source_platform='reddit'` for all existing rows
  - **Dependency**: None

- [ ] **T003** Create Alembic migration for `search_runs` source tracking
  - **File**: `apps/api/alembic/versions/XXXXX_add_source_tracking_to_search_runs.py`
  - **Action**: Add `sources_queried` JSONB column (default `["reddit"]`), add `hn_items_fetched` Integer column (nullable)
  - **Constraints**: Add CHECK constraint `hn_items_fetched >= 0`
  - **Dependency**: None

- [ ] **T004** Run migrations and verify schema
  - **Command**: `cd apps/api && python -m alembic upgrade head`
  - **Verification**: Query PostgreSQL to confirm tables exist with correct columns
  - **Dependency**: T001, T002, T003 must be created first

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL**: These tests MUST be written and MUST FAIL before ANY implementation starts.

### Contract Tests

- [ ] **T005** [P] Contract test for Algolia HN API response parsing
  - **File**: `apps/api/tests/unit/test_hn_api_contract.py`
  - **Action**: Mock Algolia HN API response, assert correct field extraction (objectID → hn_id, points, num_comments, etc.)
  - **Must Fail**: HackerNewsAPIClient doesn't exist yet
  - **Dependency**: None (parallel with T006-T010)

- [ ] **T006** [P] Contract test for HN normalization to unified schema
  - **File**: `apps/api/tests/unit/test_hn_normalizer.py`
  - **Action**: Test HNNormalizer.to_unified_schema() maps fields correctly, constructs HN permalink, handles missing URLs
  - **Must Fail**: HNNormalizer doesn't exist yet
  - **Dependency**: None (parallel with T005, T007-T010)

- [ ] **T007** [P] Contract test for HN scoring using CompositeScorer
  - **File**: `apps/api/tests/unit/test_hn_scorer.py`
  - **Action**: Test that HN items (points, num_comments, created_at_i) produce correct composite scores via existing CompositeScorer
  - **Must Fail**: HN integration with scorer doesn't exist yet
  - **Dependency**: None (parallel with T005-T006, T008-T010)

### Integration Tests

- [ ] **T008** [P] Integration test: Unified search with HN items in results
  - **File**: `apps/api/tests/integration/test_hackernews_search.py`
  - **Action**: Create search run, wait for worker, fetch results, assert HN items appear with `source_platform='hackernews'`
  - **Must Fail**: HN fetch job doesn't exist yet
  - **Dependency**: None (parallel with T005-T007, T009-T010)

- [ ] **T009** [P] Integration test: URL-based cross-source deduplication
  - **File**: `apps/api/tests/integration/test_unified_dedup.py`
  - **Action**: Mock Reddit + HN both returning same URL, assert only one appears in final results (higher score wins)
  - **Must Fail**: Deduplication logic doesn't exist yet
  - **Dependency**: None (parallel with T005-T008, T010)

- [ ] **T010** [P] Integration test: HN API failure graceful degradation
  - **File**: `apps/api/tests/integration/test_hn_failure_fallback.py`
  - **Action**: Mock HN API timeout, verify search run completes with Reddit-only results, no user-facing error
  - **Must Fail**: Circuit breaker logic doesn't exist yet
  - **Dependency**: None (parallel with T005-T009)

---

## Phase 3.3: Core Implementation (ONLY after tests T005-T010 are failing)

### Models

- [ ] **T011** [P] Create `HackerNewsItem` SQLAlchemy model
  - **File**: `apps/api/app/models/hackernews_item.py`
  - **Action**: Define model matching data-model.md schema, add `__repr__`, register in `__init__.py`
  - **Fields**: id, hn_id, hn_type, author, title, text, url, hn_url, points, comment_count, created_utc, fetched_at, expires_at, tags
  - **Dependency**: T001 (migration must exist)

- [ ] **T012** [P] Update `PainPoint` model for multi-source support
  - **File**: `apps/api/app/models/pain_point.py`
  - **Action**: Add `source_platform` column, rename `source_reddit_post_ids` to `source_post_ids` in model definition
  - **Update**: Modify `__repr__` to include `source_platform`
  - **Dependency**: T002 (migration must exist)

### Services: HackerNews Provider

- [ ] **T013** [P] Create `HackerNewsAPIClient` service
  - **File**: `apps/api/app/services/hackernews_api.py`
  - **Action**: Implement class with `search(query, time_range)` method, query Algolia HN API, handle timeouts (500ms), exponential backoff on 429/503
  - **Endpoint**: `https://hn.algolia.com/api/v1/search`
  - **Dependencies**: `requests` or `httpx` library
  - **Pattern**: Mirror `apps/api/app/services/reddit_api.py` structure
  - **Dependency**: T011 (model exists for type hints)

- [ ] **T014** [P] Create `HNNormalizer` service
  - **File**: `apps/api/app/services/hackernews_api.py` (same file as T013, add class)
  - **Action**: Implement `to_unified_schema(hn_item)` method, map Algolia fields to UnifiedSearchResult schema
  - **Field Mapping**: objectID → hn_id, points → score, num_comments → comment_count, created_at_i → created_utc, construct hn_url
  - **Dependency**: T013 (sequential, same file)

- [ ] **T015** [P] Extend `CompositeScorer` for HN items
  - **File**: `apps/worker/worker/pipeline/scorer.py`
  - **Action**: Add helper method `calculate_hn_score(hn_item_dict)` that maps HN fields (points, num_comments) to Reddit-compatible dict, then calls existing `calculate_composite_score()`
  - **No Formula Changes**: Reuse existing 0.3×upvotes + 0.25×comments + 0.25×recency + 0.2×sentiment
  - **Dependency**: T011 (model exists)

### Services: Deduplication

- [ ] **T016** Create URL-based deduplication service
  - **File**: `apps/api/app/services/deduplication.py` (new file)
  - **Action**: Implement `deduplicate_by_url(reddit_results, hn_results)` function, normalize URLs (strip query params), merge results keeping higher-scored items
  - **Return**: Unified list with duplicates removed
  - **Dependency**: T014, T015 (both scorers exist)

### Worker: Hourly HN Fetch Job

- [ ] **T017** Create hourly HN fetch background job
  - **File**: `apps/worker/worker/jobs/fetch_hackernews.py` (new file)
  - **Action**: Implement `fetch_hackernews_job(query, time_range)` function, call HackerNewsAPIClient, store in `hackernews_items` table with `expires_at = fetched_at + 48h`
  - **Pattern**: Mirror `apps/worker/worker/jobs/deletion_sync.py` for RQ job structure
  - **Dependency**: T013, T014 (API client and normalizer exist)

- [ ] **T018** Register HN fetch job in RQ Scheduler
  - **File**: `apps/worker/worker/worker.py`
  - **Action**: Import `fetch_hackernews_job`, add scheduler entry for hourly execution (3600s interval)
  - **Schedule**: `scheduler.schedule(func=fetch_hackernews_job, interval=3600, repeat=None)`
  - **Dependency**: T017 (job function exists)

---

## Phase 3.4: Integration & Search Aggregation

- [ ] **T019** Extend Reddit search task to query both sources in parallel
  - **File**: `apps/worker/worker/tasks/reddit_search.py`
  - **Action**: Modify `reddit_search_job()` to use `asyncio.gather()` for parallel Reddit + HN fetching, merge results, apply deduplication, score all items, save top-ranked as `PainPoint` records with correct `source_platform`
  - **Update SearchRun**: Set `sources_queried=["reddit", "hackernews"]`, `hn_items_fetched=N`
  - **Dependency**: T016, T017 (dedup service and HN job exist)

- [ ] **T020** Add circuit breaker for HN API failures
  - **File**: `apps/api/app/services/hackernews_api.py` (update HackerNewsAPIClient)
  - **Action**: Track consecutive failures, after 3 failures skip HN for 5 minutes, log warning, allow graceful fallback to Reddit-only
  - **Dependency**: T013 (API client exists)

- [ ] **T021** Update `SearchRun` schema to expose source metadata
  - **File**: `apps/api/app/schemas/search.py`
  - **Action**: Add `sources_queried` and `hn_items_fetched` fields to `SearchRunStatus` Pydantic schema
  - **Dependency**: T003 (migration adds DB columns)

- [ ] **T022** Update `PainPoint` schema to expose source platform
  - **File**: `apps/api/app/schemas/pain_point.py`
  - **Action**: Add `source_platform` field to `PainPointResponse` Pydantic schema
  - **Dependency**: T002 (migration adds DB column)

---

## Phase 3.5: Polish & Validation

- [ ] **T023** [P] Add logging for HN fetch operations
  - **File**: `apps/worker/worker/jobs/fetch_hackernews.py`
  - **Action**: Add structured logging for fetch start, success (items count), failures (API errors), with `run_id` context
  - **Pattern**: Match existing Reddit logging in `apps/worker/worker/tasks/reddit_search.py`
  - **Dependency**: T017 (job exists)

- [ ] **T024** [P] Create Alembic downgrade scripts for rollback
  - **Files**: All 3 migration files from T001-T003
  - **Action**: Implement `downgrade()` functions to reverse schema changes (drop columns, drop table)
  - **Dependency**: T001, T002, T003 (migrations exist)

- [ ] **T025** [P] Add HN item cleanup cron job (48h TTL enforcement)
  - **File**: `apps/worker/worker/jobs/cleanup_expired_hn.py` (new file)
  - **Action**: Create daily cron job to delete `hackernews_items` where `expires_at < NOW()`, log deletion count
  - **Pattern**: Mirror `deletion_sync.py` structure
  - **Dependency**: T011 (model exists)

- [ ] **T026** Run all tests and verify they pass
  - **Command**: `cd apps/api && pytest tests/ -v`
  - **Expected**: All tests T005-T010 now pass (were failing before implementation)
  - **Dependency**: All implementation tasks T011-T022 complete

- [ ] **T027** Execute quickstart.md manual test scenarios
  - **File**: `specs/002-integrate-hacker-news/quickstart.md`
  - **Action**: Follow all 6 scenarios, validate results match expected outcomes
  - **Scenarios**: Basic integration, source blending, freshness, graceful degradation, deduplication, performance SLA
  - **Dependency**: T026 (automated tests pass)

- [ ] **T028** Update project documentation
  - **File**: `CLAUDE.md` (already updated via plan), `README.md` (if needed)
  - **Action**: Document HN integration in user-facing docs, add environment variable requirements (if any)
  - **Dependency**: T027 (quickstart validates feature works)

---

## Dependencies Graph

```
Setup:
T001, T002, T003 (migrations) → T004 (run migrations)

Tests (parallel):
T004 → [T005, T006, T007, T008, T009, T010]

Models (after migrations):
T004 → [T011, T012]

Services (after models):
T011 → [T013, T015]
T013 → T014 (same file, sequential)
[T014, T015] → T016

Worker:
[T013, T014] → T017 → T018

Integration (after services + worker):
[T016, T017] → T019
T013 → T020
T003 → T021
T002 → T022

Polish (after integration):
T017 → T023
[T001, T002, T003] → T024
T011 → T025
[T011-T022] → T026 → T027 → T028
```

---

## Parallel Execution Examples

### Phase 3.1 Migrations (Run Together)
```bash
# Create all 3 migration files concurrently:
Task: "Create Alembic migration for hackernews_items table"
Task: "Create Alembic migration for pain_points multi-source support"
Task: "Create Alembic migration for search_runs source tracking"
```

### Phase 3.2 Tests (All Parallel)
```bash
# Write all test files at once (different files, no conflicts):
Task: "Contract test for Algolia HN API response parsing in tests/unit/test_hn_api_contract.py"
Task: "Contract test for HN normalization in tests/unit/test_hn_normalizer.py"
Task: "Contract test for HN scoring in tests/unit/test_hn_scorer.py"
Task: "Integration test unified search in tests/integration/test_hackernews_search.py"
Task: "Integration test deduplication in tests/integration/test_unified_dedup.py"
Task: "Integration test HN failure in tests/integration/test_hn_failure_fallback.py"
```

### Phase 3.3 Models (Parallel)
```bash
# Different model files:
Task: "Create HackerNewsItem model in apps/api/app/models/hackernews_item.py"
Task: "Update PainPoint model in apps/api/app/models/pain_point.py"
```

### Phase 3.5 Polish (Parallel)
```bash
# Independent tasks:
Task: "Add logging for HN fetch in fetch_hackernews.py"
Task: "Create downgrade scripts for migrations"
Task: "Add HN cleanup cron job"
```

---

## Validation Checklist

✅ **From Contracts (contracts/hackernews-api.yaml)**:
- [x] T005: Algolia HN API contract test
- [x] T006: Normalization contract test
- [x] T007: Scoring contract test

✅ **From Data Model (data-model.md)**:
- [x] T001: HackerNewsItem migration
- [x] T002: PainPoint migration
- [x] T003: SearchRun migration
- [x] T011: HackerNewsItem model
- [x] T012: PainPoint model update

✅ **From User Stories (quickstart.md)**:
- [x] T008: Integration test (Scenario 1 - basic HN integration)
- [x] T009: Integration test (Scenario 5 - deduplication)
- [x] T010: Integration test (Scenario 4 - graceful degradation)
- [x] T027: Manual quickstart validation (all 6 scenarios)

✅ **TDD Ordering**:
- [x] All tests (T005-T010) before implementation (T011-T022)
- [x] Models (T011-T012) before services (T013-T016)
- [x] Services before integration (T019-T022)

✅ **Parallel Task Independence**:
- [x] All [P] tasks operate on different files
- [x] T013-T014 sequential (same file)
- [x] No file conflicts in parallel groups

✅ **File Paths Specified**:
- [x] Every task lists exact file path
- [x] Repository root implied: `/Users/sutiteeraniti/dev/microappfinder/`

---

## Notes for Execution

1. **TDD Critical**: Tasks T005-T010 MUST fail before starting T011. Run `pytest` after writing each test to confirm failure.

2. **Migration Order**: Run T004 (`alembic upgrade head`) after completing T001-T003. Do NOT run migrations piecemeal.

3. **Same File = Sequential**: T013 → T014 cannot be parallel (both modify `hackernews_api.py`). Execute T013 fully before T014.

4. **Quickstart Requires Infrastructure**: T027 (manual testing) needs worker + API server running. Use `docker-compose up` for dependencies.

5. **Commit Granularity**: Commit after each task for clean rollback points. Use task ID in commit message (e.g., "T011: Add HackerNewsItem model").

6. **Testing Async Code**: T019 modifies worker to use `asyncio.gather()`. Ensure RQ worker supports async tasks (may need `rq[async]` dependency).

7. **Circuit Breaker State**: T020 (circuit breaker) should use Redis to persist failure count across worker restarts.

---

## Success Criteria (From Spec)

After completing all tasks:
- ✅ p95 latency ≤1 second for unified search (T026, T027)
- ✅ HN items appear in top-3 when competitive by score (T027 Scenario 1)
- ✅ Cross-source deduplication prevents duplicates (T027 Scenario 5)
- ✅ Graceful degradation when HN unavailable (T027 Scenario 4)
- ✅ No UI changes (backend-only) (T027 Scenario 2)
- ✅ A/B testing ready for relevance validation (post-T028)

---

**Ready for Execution**: Begin with T001-T003 (migrations), then T004 (run migrations), then T005-T010 (tests) in parallel.
