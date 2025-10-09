
# Implementation Plan: Multi-Dimensional Opportunity Discovery Frontend

**Branch**: `003-multi-dimensional-opportunity` | **Date**: 2025-10-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-multi-dimensional-opportunity/spec.md` + User Request: "Design frontend main page with modern, sleek, AI look UI/UX inspired by IdeaBrowser"

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path ✅
   → Spec loaded: Multi-dimensional opportunity analysis layer
2. Fill Technical Context (scan for NEEDS CLARIFICATION) ✅
   → Detect Project Type: web (Next.js + FastAPI)
   → Set Structure Decision: Monorepo with apps/web frontend
3. Fill the Constitution Check section ✅
4. Evaluate Constitution Check section ✅
   → Violations: None (frontend within scope)
   → Update Progress Tracking: Initial Constitution Check ✅
5. Execute Phase 0 → research.md [PENDING]
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md [PENDING]
7. Re-evaluate Constitution Check [PENDING]
8. Plan Phase 2 → Task generation approach [PENDING]
9. STOP - Ready for /tasks command [PENDING]
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

**Primary Requirement**: Transform MicroAppFinder from a search-first tool into a discovery-first platform where users browse a curated, growing catalog of validated micro-app opportunities—similar to IdeaBrowser's browsing model.

**Technical Approach**:
- Build modern, sleek frontend main page inspired by IdeaBrowser's minimalist design
- **Support both light and dark mode** with automatic system preference detection + manual toggle
- Display opportunities from the persistent opportunities database (6-dimensional scores)
- Implement filtering (by severity, market size, monetization, complexity, competition, trend)
- Add sorting capabilities (by any dimensional score)
- Cursor-based pagination (12 results per page with title + summary)
- Public access (no authentication required for browsing)
- Maintain <500ms p95 response time per constitutional performance requirements

## Technical Context

**Language/Version**: TypeScript 5.3+ (Next.js 14), Python 3.11+ (FastAPI backend)
**Primary Dependencies**:
- Frontend: Next.js 14 App Router, React 18, Tailwind CSS, shadcn/ui, SWR for data fetching, **next-themes** for dark mode
- Backend: FastAPI, SQLAlchemy, Pydantic (already implemented in Phase 003)
**Storage**: PostgreSQL (opportunities table with 6-dimensional scores already exists)
**Testing**: Jest + React Testing Library (frontend), pytest (backend contract tests)
**Target Platform**: Web browsers (desktop + mobile responsive)
**Project Type**: web (monorepo with apps/web frontend + apps/api backend)
**Performance Goals**: <500ms p95 API response, <1s page load, smooth 60fps animations
**Constraints**:
- Must use existing opportunities API endpoints (GET /api/opportunities with filtering/sorting)
- Reddit compliance: display only derived insights (opportunities), not raw Reddit content
- 12 results per page (lightweight response with title + summary only)
- Cursor-based pagination for scalability
**Scale/Scope**: ~100-1000 opportunities initially, growing catalog over time, 100 concurrent users (MVP)

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Micro-App Fit First ✅ PASS
- **1 core job-to-be-done**: Discover validated micro-app opportunities ✅
- **≤ 3 screens**: Homepage (browse) → Opportunity Detail → that's it ✅
- **Buildable in < 1 week**: Frontend-only work, API already exists ✅
- **≤ 15 seconds user input**: No input required (browse-first model) ✅
- **$0 infrastructure cost initially**: Uses existing database and API ✅

**Rationale**: Pure discovery UI for existing backend—fits micro-app scope perfectly.

### II. Lean & Fast-to-Ship ✅ PASS
- MVP speed over perfection: Ship browsing UI, iterate based on feedback ✅
- No premature optimization: Simple grid layout → enhance later ✅
- Provider-agnostic: Frontend only consumes REST API ✅
- Docker-first: Next.js already containerized ✅
- No bloat: shadcn/ui components only (no heavy component libraries) ✅

**Rationale**: Leveraging existing shadcn/ui setup, no new dependencies needed.

### III. Data Privacy & Compliance ✅ PASS
- Store only public content: Frontend displays derived opportunity insights (no raw Reddit content) ✅
- No PII collection: Public browsing, no user tracking ✅
- Reddit compliance: Opportunities contain analysis/scores, not verbatim user text ✅

**Rationale**: Frontend displays only the persistent opportunities table (derived insights).

### IV. Deterministic Scoring + Transparent Methodology ✅ PASS
- Display all 6-dimensional scores: severity, market size, monetization, complexity, competition, trend ✅
- Show confidence level for each opportunity ✅
- Expose score components in detail view ✅

**Rationale**: UI showcases the 6-dimensional scoring system transparently.

### V. Quality Over Quantity ✅ PASS
- Display 12 high-quality opportunities per page (not overwhelming) ✅
- Filter options to surface best matches ✅
- Sort by any dimension to find top opportunities ✅

**Rationale**: Curated browsing experience, not firehose of data.

### VI. Source Reliability & Safety ✅ PASS
- Display source attribution (Reddit/HN) per opportunity ✅
- No scraping/fetching in frontend (consumes API only) ✅

### VII. Observability & Debugging ✅ PASS
- Error states for API failures ✅
- Loading states during data fetch ✅
- Empty states when no opportunities match filters ✅

**Rationale**: Standard UX error handling patterns.

**GATE STATUS**: ✅ All constitutional principles satisfied

## Project Structure

### Documentation (this feature)
```
specs/003-multi-dimensional-opportunity/
├── spec.md              # Feature specification (already exists)
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command) [PENDING]
├── data-model.md        # Phase 1 output (/plan command) [PENDING]
├── quickstart.md        # Phase 1 output (/plan command) [PENDING]
├── contracts/           # Phase 1 output (/plan command) [PENDING]
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
apps/
├── web/                              # Next.js Frontend (PRIMARY FOCUS)
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx             # NEW: Discovery homepage (replaces current landing)
│   │   │   ├── opportunities/       # NEW: Opportunity browsing routes
│   │   │   │   ├── page.tsx         # Browse/filter opportunities
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx     # Opportunity detail view
│   │   │   ├── dashboard/           # EXISTING: User search dashboard (keep as-is)
│   │   │   ├── search/              # EXISTING: Search results (keep as-is)
│   │   │   └── (auth)/              # EXISTING: Auth pages (keep as-is)
│   │   ├── components/
│   │   │   ├── opportunities/       # NEW: Opportunity components
│   │   │   │   ├── OpportunityCard.tsx
│   │   │   │   ├── OpportunityGrid.tsx
│   │   │   │   ├── FilterPanel.tsx
│   │   │   │   ├── SortControls.tsx
│   │   │   │   ├── ScoreBadges.tsx
│   │   │   │   └── ThemeToggle.tsx  # NEW: Dark mode toggle button
│   │   │   └── ui/                  # EXISTING: shadcn/ui components
│   │   ├── lib/
│   │   │   ├── api.ts               # UPDATE: Add opportunities API methods
│   │   │   └── utils.ts             # EXISTING
│   │   └── hooks/                   # NEW: Custom React hooks
│   │       └── useOpportunities.ts  # Data fetching hook with SWR
│   └── tests/
│       └── components/              # NEW: Component tests
│           └── opportunities/
│
├── api/                              # FastAPI Backend (ALREADY IMPLEMENTED)
│   ├── app/
│   │   ├── routers/
│   │   │   └── opportunities.py     # EXISTING: GET /api/opportunities (no changes)
│   │   ├── models/
│   │   │   └── opportunity.py       # EXISTING: Opportunity model (no changes)
│   │   └── services/
│   │       └── opportunity_service.py # EXISTING: Query logic (no changes)
│   └── tests/
│       └── contract/
│           └── test_opportunity_api_contract.py # EXISTING: API contract tests (no changes)
│
└── worker/                           # RQ Worker (ALREADY IMPLEMENTED)
    └── worker/
        └── tasks/
            └── opportunity_analysis.py # EXISTING: LLM analysis task (no changes)
```

**Structure Decision**: **Web application (Option 2)** - Monorepo with separate frontend (apps/web) and backend (apps/api). Frontend consumes existing backend API endpoints. No backend changes required for this phase—all work is frontend-only.

## Phase 0: Outline & Research

**Objective**: Resolve all unknowns and research best practices for IdeaBrowser-inspired discovery UI.

### Research Tasks

1. **UI/UX Design Patterns from IdeaBrowser Analysis**
   - Decision: Modern, minimalist card-based layout
   - Rationale: Based on WebFetch analysis—clean grid, generous white space, scannable information
   - Design elements to adopt:
     * Card-based opportunity display with rounded corners and subtle shadows
     * Minimalist color palette (grayscale + brand accent colors)
     * Hierarchical typography (clear heading/body distinctions)
     * Modular, scannable content blocks
     * Soft gradients and smooth animations
     * Generous white space for breathing room
   - Alternatives considered: List view (rejected—less visual impact), Masonry grid (rejected—harder to scan)

2. **Filtering & Sorting UX Best Practices**
   - Decision: Side panel filter UI with instant results (no "Apply" button)
   - Rationale: Reduces friction, provides instant feedback
   - Filters to implement:
     * Severity range slider (0-10)
     * Market size multi-select (niche/mid/large)
     * Monetization range slider (0-10)
     * Technical complexity range slider (0-10)
     * Competition level multi-select (low/medium/high/saturated)
     * Trend direction multi-select (declining/stable/growing/explosive)
   - Alternatives considered: Top filter bar (rejected—limited space), Modal filters (rejected—hides content)

3. **Cursor-Based Pagination Implementation**
   - Decision: Use SWR with infinite scroll + "Load More" button fallback
   - Rationale: Modern UX pattern, works well with cursor pagination
   - Implementation:
     * SWR hook with `useSWRInfinite` for cursor-based fetching
     * Encode cursor as Base64(JSON({id, analyzed_at}))
     * Display "Load More" button at end of grid
     * Optional: Infinite scroll trigger when user scrolls to bottom (progressive enhancement)
   - Alternatives considered: Numbered pages (rejected—cursor pagination doesn't support jumps), Pure infinite scroll (rejected—less user control)

4. **Performance Optimization Strategies**
   - Decision: Image lazy loading, skeleton loaders, SWR caching
   - Rationale: Meets <1s page load and <500ms API response requirements
   - Optimizations:
     * Use `next/image` for any visuals (if added later)
     * Skeleton loaders during initial fetch
     * SWR cache with 5min stale-while-revalidate
     * Debounced filter inputs (300ms delay)
   - Alternatives considered: Server components (rejected—need client interactivity for filters), GraphQL (rejected—REST API already built)

5. **Responsive Design Breakpoints**
   - Decision: Mobile-first with Tailwind breakpoints (sm: 640px, md: 768px, lg: 1024px, xl: 1280px)
   - Rationale: Tailwind CSS already configured, standard breakpoints
   - Layout:
     * Mobile (< 640px): Single column grid, bottom sheet filters
     * Tablet (640-1024px): 2-column grid, collapsible side filters
     * Desktop (1024px+): 3-column grid, persistent side filters
   - Alternatives considered: Desktop-first (rejected—mobile traffic significant), Custom breakpoints (rejected—unnecessary complexity)

6. **Color Palette & Typography**
   - Decision: Tailwind default gray scale + brand blue accent (#3B82F6)
   - Rationale: Matches IdeaBrowser minimalism, already configured
   - Typography:
     * Headings: font-bold with tight tracking
     * Body: font-normal with relaxed line-height (1.625)
     * Scores/badges: font-medium with smaller size
   - Alternatives considered: Custom design system (rejected—over-engineering for MVP), Material UI (rejected—heavier bundle)

7. **Dark Mode Implementation**
   - Decision: Use **next-themes** with automatic system preference detection + manual toggle
   - Rationale: Modern UX expectation, reduces eye strain, professional aesthetic
   - Implementation:
     * `next-themes` ThemeProvider wraps app (supports SSR, no flash)
     * Tailwind dark: variant for all color classes
     * System preference auto-detection (`prefers-color-scheme`)
     * Persistent user preference (localStorage)
     * Toggle button in header (sun/moon icon)
   - Color system:
     * **Light mode**: bg-gray-50, text-gray-900, card bg-white
     * **Dark mode**: bg-gray-950, text-gray-100, card bg-gray-900
     * **Accent consistent**: blue-600 (light) → blue-500 (dark) for better contrast
     * **Score badges**: Adjust opacity/brightness for dark mode readability
   - Alternatives considered: CSS variables only (rejected—Tailwind dark: more maintainable), Manual toggle only (rejected—missing auto-detection)

**Output**: research.md with all design decisions documented

## Phase 1: Design & Contracts

*Prerequisites: research.md complete*

### 1. Data Model (`data-model.md`)

**Frontend Data Models** (TypeScript interfaces):

```typescript
// Opportunity list item (lightweight response)
interface OpportunityListItem {
  id: string; // UUID
  title: string; // Derived from pain_point.extracted_text (first 100 chars)
  summary: string; // Derived from pain_point.extracted_text (first 300 chars)
  problem_severity: number; // 0-10
  market_size: 'niche' | 'mid' | 'large';
  monetization_potential: number; // 0-10
  technical_complexity: number; // 0-10
  competition_level: 'low' | 'medium' | 'high' | 'saturated';
  trend_direction: 'declining' | 'stable' | 'growing' | 'explosive';
  confidence_level: number; // 0-1
  analyzed_at: string; // ISO 8601 timestamp
}

// Opportunity detail (full response)
interface OpportunityDetail extends OpportunityListItem {
  trend_data: {
    // Time-series JSON
    timestamps: string[];
    discussion_counts: number[];
    growth_rate: number;
  };
  geographic_spread: string[]; // e.g., ["US", "UK", "Global"]
  affected_industries: string[]; // e.g., ["SaaS", "E-commerce"]
  source_platform: string; // "reddit" | "hackernews"
  enrichment_count: number;
  last_enriched_at: string | null;
}

// Filter state
interface OpportunityFilters {
  severity_min?: number;
  severity_max?: number;
  market_size?: ('niche' | 'mid' | 'large')[];
  monetization_min?: number;
  monetization_max?: number;
  complexity_min?: number;
  complexity_max?: number;
  competition_level?: ('low' | 'medium' | 'high' | 'saturated')[];
  trend_direction?: ('declining' | 'stable' | 'growing' | 'explosive')[];
}

// Sort options
type SortField = 'severity' | 'monetization' | 'analyzed_at' | 'complexity';
type SortOrder = 'asc' | 'desc';

// API response
interface OpportunitiesResponse {
  opportunities: OpportunityListItem[];
  next_cursor: string | null;
  has_more: boolean;
}
```

**Backend Models** (already exist, no changes):
- `Opportunity` SQLAlchemy model with all 6-dimensional scores
- `OpportunityResponse` Pydantic schema for list endpoint
- `OpportunityDetail` Pydantic schema for detail endpoint

### 2. API Contracts (`contracts/`)

**Frontend Consumption** (backend already implemented):

```yaml
# contracts/opportunities_frontend.yaml
OpportunitiesListEndpoint:
  method: GET
  path: /api/opportunities
  query_parameters:
    severity_min: number (0-10, optional)
    severity_max: number (0-10, optional)
    market_size: string (comma-separated: niche,mid,large, optional)
    monetization_min: number (0-10, optional)
    monetization_max: number (0-10, optional)
    complexity_min: number (0-10, optional)
    complexity_max: number (0-10, optional)
    competition_level: string (comma-separated: low,medium,high,saturated, optional)
    trend_direction: string (comma-separated: declining,stable,growing,explosive, optional)
    sort_by: string (severity|monetization|analyzed_at|complexity, default: analyzed_at)
    sort_order: string (asc|desc, default: desc)
    cursor: string (Base64 encoded, optional)
    limit: number (max 50, default 12)
  response_200:
    opportunities: OpportunityListItem[]
    next_cursor: string | null
    has_more: boolean
  performance: <500ms p95

OpportunityDetailEndpoint:
  method: GET
  path: /api/opportunities/{id}
  path_parameters:
    id: string (UUID)
  response_200:
    OpportunityDetail (full object)
  response_404:
    detail: "Opportunity not found"
  performance: <100ms p95
```

### 3. Component Tests (TDD approach)

Create failing tests for:
- `OpportunityCard.test.tsx`: Renders opportunity data, displays scores, handles click
- `OpportunityGrid.test.tsx`: Renders grid of cards, handles empty state, loading state
- `FilterPanel.test.tsx`: Renders filters, updates state on change, applies filters
- `SortControls.test.tsx`: Renders sort dropdown, changes sort order
- `useOpportunities.test.ts`: Fetches data, handles pagination, applies filters

### 4. Quickstart Validation (`quickstart.md`)

User flow to test:
1. Visit homepage → See opportunity grid with 12 results
2. Apply filter (severity ≥7) → Grid updates instantly
3. Sort by monetization DESC → Highest monetization opportunities first
4. Click opportunity card → Navigate to detail page
5. View full opportunity details → See all 6 scores + trend data
6. Click "Load More" → Fetch next page (cursor pagination)

### 5. Update Agent Context (`CLAUDE.md`)

Run `.specify/scripts/bash/update-agent-context.sh claude` to add:
- New frontend routes: /opportunities, /opportunities/[id]
- New components: OpportunityCard, OpportunityGrid, FilterPanel, SortControls
- API integration: useOpportunities hook with SWR
- Design system: IdeaBrowser-inspired minimalist UI

**Output**: data-model.md, contracts/, failing component tests, quickstart.md, updated CLAUDE.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (components, API integration, routes)
- TDD order: Component tests → Component implementation → Integration
- Frontend-only tasks (no backend changes)

**Estimated Tasks**:
1. Install next-themes dependency [P]
2. Create TypeScript interfaces (data-model.md) [P]
3. Configure ThemeProvider in root layout [depends on T001]
4. Create ThemeToggle component with dark mode switch [depends on T003]
5. Add dark mode Tailwind classes to tailwind.config [P]
6. Write OpportunityCard component test [P]
7. Implement OpportunityCard component with dark mode styles [depends on T006]
8. Write OpportunityGrid component test [P]
9. Implement OpportunityGrid component with dark mode styles [depends on T008]
10. Write FilterPanel component test [P]
11. Implement FilterPanel component with dark mode styles [depends on T010]
12. Write SortControls component test [P]
13. Implement SortControls component with dark mode styles [depends on T012]
14. Write useOpportunities hook test [P]
15. Implement useOpportunities hook (SWR integration) [depends on T014]
16. Update API client lib/api.ts [P]
17. Create /opportunities page route with ThemeToggle [depends on T009, T011, T013, T015]
18. Create /opportunities/[id] detail page route with dark mode [depends on T007, T015]
19. Redesign homepage with dark mode support [depends on T017]
20. Add responsive styles (mobile/tablet/desktop + dark mode) [depends on T017]
21. Test theme persistence and system preference detection [depends on T020]
22. Run quickstart validation [depends on T021]
23. Performance testing (<500ms API, <1s page load, dark mode toggle) [depends on T022]

**Ordering Strategy**:
- [P] = Parallelizable (independent files)
- Components before pages (pages compose components)
- Tests before implementation (TDD)
- API integration early (needed by all data-dependent components)

**Estimated Output**: ~23 numbered, ordered tasks in tasks.md (dark mode adds 5 tasks)

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*No constitutional violations detected—no entries needed*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A       | N/A        | N/A                                 |

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning approach documented (/plan command)
- [ ] Phase 3: Tasks generated (/tasks command - READY)
- [ ] Phase 4: Implementation (manual execution)
- [ ] Phase 5: Validation (manual testing)

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved (spec has Session 2025-10-08 clarifications)
- [x] Complexity deviations documented (none—all principles satisfied)

**Artifacts Generated**:
- [x] plan.md (this file)
- [x] research.md (frontend UI/UX research appended)
- [x] Data models defined inline (TypeScript interfaces in plan.md)
- [x] API contracts documented inline (YAML spec in plan.md)
- [x] Phase 2 task strategy documented

**Next Command**: Run `/tasks` to generate tasks.md with ~23 ordered implementation tasks (including dark mode)

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
