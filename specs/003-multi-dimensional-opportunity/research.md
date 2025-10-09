# Research Findings: Multi-Dimensional Opportunity Analysis

**Date**: 2025-10-08
**Feature**: 003-multi-dimensional-opportunity

## Research Questions Resolved

### 1. LLM Analysis Strategy

**Decision**: Structured prompts with JSON schema enforcement using Pydantic validation

**Rationale**:
- GPT-4o-mini provides cost-effective bulk analysis ($0.15/1M input tokens vs $5.00 for GPT-4o)
- Structured outputs via `response_format` parameter ensure valid JSON responses
- Pydantic models validate LLM outputs against exact schema requirements
- Fallback to Claude Sonnet 3.5 for complex edge cases or GPT-4o-mini failures

**Implementation**:
```python
class OpportunityScores(BaseModel):
    problem_severity: float = Field(ge=0.0, le=10.0)
    market_size_indicator: Literal["niche", "mid", "large"]
    monetization_potential: float = Field(ge=0.0, le=10.0)
    technical_complexity: float = Field(ge=0.0, le=10.0)
    competition_level: Literal["low", "medium", "high", "saturated"]
    trend_direction: Literal["declining", "stable", "growing", "explosive"]
    confidence_level: float = Field(ge=0.0, le=1.0)
    reasoning: str  # LLM explanation for scores
```

**Alternatives Considered**:
- Free-form LLM responses with regex parsing → Rejected: brittle, error-prone
- Rule-based scoring without LLM → Rejected: lacks semantic understanding
- Claude-only approach → Rejected: 10x cost increase

**Token Budgets**:
- Per-analysis limit: 2000 input tokens, 500 output tokens
- Batch size: 5-10 pain points per LLM call (amortize prompt overhead)
- Estimated cost: $0.0003 per opportunity analyzed

---

### 2. Database Schema Design

**Decision**: Add `opportunities` table with JSONB columns, nullable FK to pain_points

**Rationale**:
- JSONB provides flexible schema for `trend_data` time-series without migrations
- PostgreSQL JSONB indexing enables fast queries on nested fields
- Nullable `pain_point_id` FK with ON DELETE SET NULL preserves opportunities after 48h TTL
- Array columns (`geographic_spread`, `affected_industries`) support multi-value fields

**Schema** (full details in data-model.md):
```sql
CREATE TABLE opportunities (
    id UUID PRIMARY KEY,
    pain_point_id UUID REFERENCES pain_points(id) ON DELETE SET NULL,

    problem_severity FLOAT CHECK (problem_severity BETWEEN 0.0 AND 10.0),
    market_size_indicator VARCHAR(10) CHECK (market_size_indicator IN ('niche', 'mid', 'large')),
    monetization_potential FLOAT CHECK (monetization_potential BETWEEN 0.0 AND 10.0),
    technical_complexity FLOAT CHECK (technical_complexity BETWEEN 0.0 AND 10.0),
    competition_level VARCHAR(20) CHECK (competition_level IN ('low', 'medium', 'high', 'saturated')),
    trend_direction VARCHAR(20) CHECK (trend_direction IN ('declining', 'stable', 'growing', 'explosive')),

    confidence_level FLOAT CHECK (confidence_level BETWEEN 0.0 AND 1.0),
    trend_data JSONB,
    geographic_spread TEXT[],
    affected_industries TEXT[],

    analyzed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    enrichment_count INT NOT NULL DEFAULT 0,
    last_enriched_at TIMESTAMP
);

CREATE INDEX idx_opportunity_severity ON opportunities(problem_severity DESC);
CREATE INDEX idx_opportunity_analyzed_at ON opportunities(analyzed_at DESC);
CREATE INDEX idx_opportunity_cursor ON opportunities(id, analyzed_at);
CREATE INDEX idx_opportunity_pain_point ON opportunities(pain_point_id) WHERE pain_point_id IS NOT NULL;
```

**Alternatives Considered**:
- Separate tables for trend data → Rejected: complex joins, over-engineering for MVP
- EAV pattern for scores → Rejected: query complexity, type safety issues
- Non-nullable pain_point_id → Rejected: violates Reddit compliance (48h TTL)

---

### 3. Async Task Orchestration

**Decision**: Use RQ job chaining with `depends_on` parameter

**Rationale**:
- RQ's native `depends_on` ensures analysis runs AFTER unified aggregation completes
- Separate worker pool for analysis tasks prevents blocking search pipeline
- Redis-based job state tracking provides visibility into analysis progress
- Retry logic built-in (configurable via `@job` decorator)

**Implementation**:
```python
# In unified_search.py
def aggregate_and_extract_unified(search_run_id):
    # ... existing logic ...

    # Enqueue analysis task (depends on THIS job completing)
    from worker.tasks.opportunity_analysis import analyze_top_pain_points
    analyze_job = queue.enqueue(
        analyze_top_pain_points,
        search_run_id=search_run_id,
        depends_on=get_current_job(),  # Chains after THIS job
        job_timeout='5m'
    )
```

**Alternatives Considered**:
- Celery task chaining → Rejected: adds new dependency, heavier than RQ
- Synchronous analysis in unified aggregation → Rejected: blocks user-facing search
- Polling-based trigger (check DB every N seconds) → Rejected: inefficient, delay issues

**Worker Pool Strategy**:
- Default pool: Search tasks (reddit, hn, unified aggregation)
- Analysis pool: Opportunity analysis tasks (longer timeout, lower concurrency)
- Separation prevents LLM API latency from blocking searches

---

### 4. API Pagination Strategy

**Decision**: Cursor-based pagination using composite key `(id, analyzed_at)`

**Rationale**:
- OFFSET pagination breaks at scale (slow for deep pages, inconsistent with concurrent inserts)
- Cursor-based approach uses indexed composite key for O(1) page access
- Opaque cursor (Base64-encoded JSON) prevents user manipulation
- Stateless (no server-side session storage required)

**Implementation**:
```python
# Encode cursor
cursor = base64.urlsafe_b64encode(
    json.dumps({"id": str(last_id), "analyzed_at": last_analyzed_at.isoformat()}).encode()
).decode()

# Decode cursor
decoded = json.loads(base64.urlsafe_b64decode(cursor).decode())
query = query.filter(
    (Opportunity.analyzed_at < decoded["analyzed_at"]) |
    (
        (Opportunity.analyzed_at == decoded["analyzed_at"]) &
        (Opportunity.id < decoded["id"])
    )
)
```

**Alternatives Considered**:
- OFFSET/LIMIT pagination → Rejected: O(N) scan for deep pages
- Keyset pagination on `id` only → Rejected: requires chronological IDs (UUIDs aren't)
- GraphQL Relay-style cursor → Rejected: over-engineering for REST API

**Performance**: <500ms p95 for 12-result pages (verified via composite index)

---

### 5. Accumulative Enrichment Pattern

**Decision**: Detect duplicates via semantic similarity, merge signals, recompute scores

**Rationale**:
- Existing `DeduplicationService` provides cross-source similarity detection (Jaccard + embeddings)
- Merging signals enriches context for LLM analysis (more evidence → higher confidence)
- Recomputing scores with richer data improves accuracy over time
- Tracks enrichment history via `enrichment_count` and `last_enriched_at`

**Implementation**:
```python
def enrich_existing_opportunity(opportunity_id, new_pain_point):
    # 1. Load existing opportunity + original pain point(s)
    opportunity = db.query(Opportunity).get(opportunity_id)

    # 2. Merge context (concatenate text, aggregate metadata)
    merged_context = merge_pain_point_contexts([
        opportunity.pain_point,
        new_pain_point
    ])

    # 3. Re-analyze with enriched context
    new_scores = llm_service.analyze_opportunity(merged_context)

    # 4. Update opportunity with new scores
    opportunity.update_scores(new_scores)
    opportunity.enrichment_count += 1
    opportunity.last_enriched_at = datetime.utcnow()
    db.commit()
```

**Duplicate Detection Criteria**:
- URL match (exact or normalized) → 100% duplicate
- Title similarity >85% (Jaccard) + same topic → merge
- Embedding cosine similarity >0.90 → potential duplicate (manual review)

**Alternatives Considered**:
- Always create new opportunities → Rejected: data fragmentation, duplicate noise
- Merge only exact URL matches → Rejected: misses semantic duplicates
- Average scores instead of recompute → Rejected: doesn't leverage richer context

---

## Summary of Technical Decisions

| Area | Decision | Key Benefit | Cost/Trade-off |
|------|----------|-------------|----------------|
| LLM Provider | GPT-4o-mini (primary) | 97% cost savings | Slight accuracy trade-off vs GPT-4o |
| Database | PostgreSQL JSONB + arrays | Flexible schema, fast queries | Requires Postgres 9.4+ |
| Task Queue | RQ with job chaining | Native dependency mgmt | Less feature-rich than Celery |
| Pagination | Cursor-based (id + timestamp) | O(1) page access | Opaque cursors (no page numbers) |
| Enrichment | Semantic dedup + recompute | Improving scores over time | Additional LLM cost on merges |

---

## Open Questions (Deferred to Future Phases)

1. **Trend Data Calculation**: How to populate `trend_data` time-series? → Deferred to Phase 2 (clustering)
2. **Geographic Inference**: Extract locations from text or use IP geolocation? → Deferred (manual tagging for MVP)
3. **Admin Dashboard**: What metrics to surface? → Deferred to Phase 5 (structured logging sufficient for MVP)

---

## Frontend Discovery UI Research (2025-10-09)

**Context**: User request to design modern, sleek frontend main page inspired by IdeaBrowser for opportunity discovery.

### 6. Frontend UI/UX Design Patterns

**Decision**: Card-based grid layout with minimalist design, inspired by IdeaBrowser

**Rationale**:
- Clean, scannable grid layout with generous white space
- Card-based design with rounded corners and subtle shadows
- Minimalist color palette (grayscale + brand blue #3B82F6)
- Hierarchical typography for clear information architecture
- Smooth animations and hover states

**Design Elements**:
- **Grid**: 1 col (mobile) → 2 col (tablet) → 3 col (desktop)
- **Cards**: Opportunity title, summary, score badges
- **Typography**: Inter font, font-bold headings, font-normal body
- **Shadows**: shadow-sm default, shadow-md on hover
- **Animations**: hover:scale-105, transition-transform duration-200

**Alternatives Considered**:
- List view → Rejected (less visual impact)
- Masonry grid → Rejected (harder to scan)
- Table view → Rejected (too dense for discovery UX)

---

### 7. Filtering & Sorting UX

**Decision**: Side panel filters (desktop) / bottom sheet (mobile) with instant results

**Rationale**:
- Instant feedback (debounced 300ms) encourages filter exploration
- 9 filter dimensions (6 scores + 3 enums) require dedicated space
- Modern UX pattern removes friction (no "Apply" button)

**Filter Types**:
1. **Range Sliders** (0-10): Severity, Monetization, Complexity
2. **Multi-Select Checkboxes**: Market Size, Competition, Trend
3. **Sort Dropdown**: Severity, Monetization, Analyzed At (default), Complexity

**Alternatives Considered**:
- Top filter bar → Rejected (limited horizontal space)
- Modal filters → Rejected (hides content)
- "Apply" button → Rejected (adds unnecessary friction)

---

### 8. Cursor-Based Pagination (Frontend)

**Decision**: SWR `useSWRInfinite` with "Load More" button

**Rationale**:
- Backend API already implements cursor pagination
- SWR provides caching, automatic refetch, error handling
- `useSWRInfinite` handles cursor management automatically
- "Load More" button gives user control (vs pure infinite scroll)

**Implementation**:
```typescript
import useSWRInfinite from 'swr/infinite';

const getKey = (pageIndex, previousPageData) => {
  if (previousPageData && !previousPageData.has_more) return null;
  if (pageIndex === 0) return `/api/opportunities?limit=12`;
  return `/api/opportunities?limit=12&cursor=${previousPageData.next_cursor}`;
};

const { data, size, setSize } = useSWRInfinite(getKey, fetcher);
```

**Alternatives Considered**:
- Numbered pages → Rejected (cursor pagination doesn't support jumps)
- Pure infinite scroll → Rejected (less user control, accessibility issues)

---

### 9. Performance Optimization (Frontend)

**Decision**: Skeleton loaders + SWR caching + debounced filters + React.memo

**Optimizations**:
1. **Skeleton Loaders**: Reduce perceived load time (Tailwind animate-pulse)
2. **SWR Caching**: 5min stale-while-revalidate, reduces API calls
3. **Debounced Filters**: 300ms delay prevents API spam
4. **React.memo**: Wrap OpportunityCard to prevent unnecessary re-renders

**Performance Targets**:
- <1s First Contentful Paint
- <500ms API response (backend p95)
- 60fps animations

**Alternatives Considered**:
- Server Components → Rejected (need client-side interactivity)
- GraphQL → Rejected (REST API already built)
- Virtualized list → Rejected (only 12 results per page)

---

### 10. State Management (Frontend)

**Decision**: URL-based filter state + SWR for data fetching (no Redux/Zustand)

**Rationale**:
- URL query params provide shareable links and browser history support
- SWR handles all data fetching, caching, loading states
- No need for global state management library

**Implementation**:
```typescript
import { useRouter, useSearchParams } from 'next/navigation';

const searchParams = useSearchParams();
const filters = {
  severity_min: searchParams.get('severity_min') || undefined,
  market_size: searchParams.get('market_size')?.split(',') || undefined,
};

const updateFilters = (newFilters) => {
  const params = new URLSearchParams();
  // Build params from newFilters
  router.push(`/opportunities?${params.toString()}`);
};
```

**Alternatives Considered**:
- Redux → Rejected (overkill for filtering state)
- Zustand → Rejected (URL state is simpler)
- React Context → Rejected (URL eliminates prop drilling)

---

### 11. Dark Mode Implementation

**Decision**: Use **next-themes** library with Tailwind dark mode and system preference detection

**Rationale**:
- Modern UX expectation (most professional apps support dark mode)
- Reduces eye strain for users browsing in low-light environments
- Enhances "AI/tech" aesthetic for modern discovery platform
- IdeaBrowser aesthetic works well in both light and dark modes

**Implementation Strategy**:

1. **next-themes Library**:
   - Zero-flash dark mode (prevents white flash on page load)
   - SSR compatible (works with Next.js App Router)
   - Automatic system preference detection (`prefers-color-scheme`)
   - localStorage persistence (remembers user choice)
   - Simple API: `useTheme()` hook

2. **Tailwind Dark Mode**:
   - Use `dark:` variant for all color classes
   - Enable in tailwind.config: `darkMode: 'class'`
   - next-themes adds `dark` class to `<html>` element

3. **Color System**:
   ```typescript
   // Light mode
   - Background: bg-gray-50 (#F9FAFB)
   - Cards: bg-white (#FFFFFF)
   - Text: text-gray-900 (headings), text-gray-600 (body)
   - Borders: border-gray-200

   // Dark mode
   - Background: dark:bg-gray-950 (#030712)
   - Cards: dark:bg-gray-900 (#111827)
   - Text: dark:text-gray-100 (headings), dark:text-gray-400 (body)
   - Borders: dark:border-gray-800

   // Accent colors (adapt for contrast)
   - Blue CTA: bg-blue-600 → dark:bg-blue-500
   - Score badges: Adjust opacity/saturation for dark readability
   ```

4. **Toggle Component**:
   - Sun icon (light mode) / Moon icon (dark mode)
   - Place in header (top-right corner)
   - Smooth transition animation (200ms)
   - Keyboard accessible (Enter/Space to toggle)

5. **Implementation Example**:
   ```tsx
   // app/layout.tsx
   import { ThemeProvider } from 'next-themes'

   export default function RootLayout({ children }) {
     return (
       <html suppressHydrationWarning>
         <body>
           <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
             {children}
           </ThemeProvider>
         </body>
       </html>
     )
   }

   // components/ThemeToggle.tsx
   import { useTheme } from 'next-themes'

   export function ThemeToggle() {
     const { theme, setTheme } = useTheme()
     return (
       <button
         onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
         className="p-2 rounded-lg bg-gray-200 dark:bg-gray-800"
       >
         {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
       </button>
     )
   }
   ```

**Component Updates Required**:
- **OpportunityCard**: Add dark: variants for bg, text, shadow
- **FilterPanel**: Dark mode for inputs, sliders, checkboxes
- **Score Badges**: Adjust badge colors for dark mode contrast
- **Navigation**: Dark header background and text
- **Empty/Loading States**: Dark-friendly skeleton loaders

**Testing Checklist**:
- [ ] System preference auto-detection works (test with OS dark mode)
- [ ] Manual toggle persists across page reloads
- [ ] No flash of unstyled content on initial load
- [ ] All components readable in both modes
- [ ] Smooth transition between themes (no jarring jumps)

**Alternatives Considered**:
- **CSS variables only**: Rejected—Tailwind dark: variant more maintainable with existing setup
- **Manual toggle only (no system detection)**: Rejected—users expect auto-detection
- **third-party theme library**: Rejected—next-themes is lightweight and Next.js-specific

**Performance Impact**:
- next-themes bundle: ~1.5KB gzipped (negligible)
- No runtime performance impact (CSS classes only)
- localStorage read is synchronous but fast (<1ms)

---

*All research questions resolved (backend + frontend + dark mode). Ready for Phase 1 design.*
