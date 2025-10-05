# Design Decisions

> Append-only log of design decisions. Never rewrite—mark superseded entries with updated status.

## Format
```
## D-YYYY-MM-DD-NN — Decision title
Rationale: <short explanation>
Status: Accepted | Superseded | Rejected | Under Review
Date: YYYY-MM-DD
Ref: <file@hash|PR#|issue#>
```

---

## D-2025-10-04-01 — Reddit API Data Retention & Compliance Policy
Rationale: Reddit ToS prohibits retaining deleted content (even if anonymized); compliance requires deletion sync; separation of raw vs. derived data enables legal aggregates while respecting user deletions
Status: Accepted
Date: 2025-10-04
Ref: specs/001-reddit-pain-point/research.md, data-model.md
Details:
- Raw Reddit content (text, URLs, author): 48h max cache in Redis with automatic TTL
- Derived aggregates (PainPoint.extracted_text, topics, scores): Stored indefinitely in PostgreSQL as non-user-content
- Daily deletion sync job: Check Reddit API for deleted posts, purge from Redis, update PainPoint.source_deleted flag

## D-2025-10-04-02 — Composite Scoring Algorithm for Pain Point Ranking
Rationale: Multi-factor scoring provides better opportunity ranking than single metrics; weights balance community validation, engagement depth, freshness, and pain intensity
Status: Accepted
Date: 2025-10-04
Ref: specs/001-reddit-pain-point/research.md
Formula: `score = 0.3×upvotes_norm + 0.25×comments_norm + 0.25×recency_norm + 0.2×sentiment_polarity`
Alternative Considered: ML-based ranking (overkill for MVP), upvotes-only (misses nuance)

## D-2025-10-04-03 — User-Level Privacy Enforcement (Dual-Layer)
Rationale: Prevents data leaks through defense-in-depth; aligns with constitutional data privacy principle; supports user-scoped search results requirement
Status: Accepted
Date: 2025-10-04
Ref: specs/001-reddit-pain-point/plan.md, data-model.md
Implementation:
- Database layer: user_id foreign key on SearchRun table with CASCADE delete
- API layer: Middleware verifies search_run.user_id == current_user.id before access (403 if mismatch)

## D-2025-10-04-04 — Empty Results Fallback Strategy
Rationale: Always provides value to user (discovery > empty state); uses existing data (no additional API calls); promotes topic exploration
Status: Accepted
Date: 2025-10-04
Ref: specs/001-reddit-pain-point/research.md, spec.md clarifications
Details: When search returns 0 results, display top 20 recent pain points from any topic (last 7 days, sorted by relevance_score)
Alternative Considered: "No results" message (poor UX), AI-generated suggestions (requires embeddings)
