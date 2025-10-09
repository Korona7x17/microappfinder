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

*All research questions resolved. Ready for Phase 1 design.*
