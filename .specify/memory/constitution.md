# MicroAppFinder Constitution

## Core Principles

### I. Micro-App Fit First (NON-NEGOTIABLE)
Every opportunity must pass the **Micro-App Fit Gate**:
- Solves **1 core job-to-be-done** (no feature creep)
- Solvable in **≤ 3 screens** (no complex flows)
- Buildable in **< 1 week** (fast to ship)
- Requires **≤ 15 seconds** user input (minimal friction)
- Runs with **$0 infrastructure** cost initially (serverless-first)

**Rationale**: We focus on lightweight, focused apps that solve specific pain points, not bloated SaaS products.

### II. Lean & Fast-to-Ship
- MVP speed over perfection: ship working prototypes, iterate based on feedback
- No premature optimization: start simple, scale when needed
- Provider-agnostic architecture: abstract LLM, database, and provider dependencies
- Docker-first deployment: reproducible environments from day one
- No bloat: every component must justify its existence

**Rationale**: Time-to-market matters more than architectural purity for MVP validation.

### III. Data Privacy & Compliance (NON-NEGOTIABLE)
- Store **only public content** (URLs + short snippets, no usernames)
- Respect robots.txt and platform ToS
- Per-domain throttling **< 1 rps** with jitter
- Cache fetched content (48h) to minimize repeat requests
- No PII collection: only community labels, no individual identifiers
- API keys stored server-side only, rotated regularly

**Rationale**: Legal and ethical data collection is foundational; violations kill projects.

### IV. Deterministic Scoring + Transparent Methodology
Weighted rubric (0-100 scale):
- Pain intensity: 30%
- Frequency: 20%
- WTP (willingness to pay): 20%
- Pull evidence: 15%
- Social validation: 10%
- Urgency: 5%
- Recency bonus: +5 (<7 days), +10 (<24h)

All scores must be:
- **Reproducible**: same inputs → same scores
- **Auditable**: score components visible in reports
- **Explainable**: users understand why clusters rank high/low

**Rationale**: Trust requires transparency; users need to understand how opportunities are prioritized.

### V. Quality Over Quantity
- Target: **3 high-quality briefs** per run, not 50 mediocre ones
- Minimum cluster size: **≥5 signals** (avoid spurious patterns)
- Confidence scoring: every signal has confidence (0.0-1.0) based on engagement, recency, clarity
- Deduplication: URL + semantic embedding to merge cross-platform duplicates
- Brief validation: automated checks for scope creep (>3 screens = reject)

**Rationale**: One actionable brief beats ten vague ideas; focus on quality signals.

### VI. Source Reliability & Safety
Primary sources (MVP):
- ✅ **Reddit API** (official, ToS-compliant)
- ✅ **Hacker News Algolia API** (official, fast)
- ✅ **Product Hunt GraphQL** (official, structured)
- ✅ **Indie Hackers** (SERP-first discovery, polite crawl4ai fetch <1 rps)

**Excluded from MVP**:
- ❌ TikTok (scraping-sensitive, high legal risk)
- ❌ Twitter/X (API costs + instability)
- ❌ LinkedIn (ToS violations)

**crawl4ai** as default fetcher:
- JS rendering **disabled by default** (speed + cost)
- Fallbacks (Firecrawl/SerpAPI) **only on repeated failures**
- Polite User-Agent with contact info
- Immediate backoff on 403/429 errors

**Rationale**: Legal and stable sources reduce risk; we start with proven, documented APIs.

### VII. Observability & Debugging
- Structured logging: all pipeline steps logged with run_id
- Progress tracking: frontend shows real-time pipeline progress
- Error transparency: failures visible to users with retry options
- Monitoring: Sentry for exceptions, Uptime Kuma for health checks
- Simple dashboards: avoid over-engineering observability

**Rationale**: Users and developers need visibility into what's happening and what failed.

## Technology Constraints

### Stack (Non-Negotiable for MVP)
- **Frontend**: Next.js 14 (App Router) + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI + SQLAlchemy + Pydantic
- **Worker**: Python + RQ (Redis Queue)
- **Database**: PostgreSQL (Supabase/Neon) + Qdrant (optional)
- **LLM**: OpenAI (gpt-4o-mini for summaries, gpt-4o for briefs) or Anthropic Claude
- **Deployment**: Docker Compose (dev) → Hetzner VPS or Railway (prod)

### LLM Usage
- **Cheap model** (GPT-4o-mini/Haiku) for signal summarization (batch 10-20 per call)
- **Premium model** (GPT-4o/Sonnet) **only for top 3 briefs** (cost control)
- Strict JSON output schemas (no free-form LLM responses)
- Token budgets: max 2000 tokens per brief generation
- Fallback: if LLM fails, use heuristic-based brief templates

**Rationale**: LLM costs add up; use cheap models for bulk work, premium only for final output.

### Database Schema
- **Signals**: normalized pain points with confidence scores
- **Clusters**: grouped signals with theme labels
- **Briefs**: actionable micro-app specs with proof links
- **Runs**: user-triggered analysis jobs with status tracking

All schemas use **Alembic migrations** for version control.

## Development Workflow

### Feature Implementation Order
1. **Providers** (Reddit → HN → Product Hunt → Indie Hackers)
2. **Normalizer** (RawItem → Signal with LLM extraction)
3. **Deduplication** (URL + embedding-based merge)
4. **Clustering** (HDBSCAN or K-means with LLM labels)
5. **Scoring** (weighted rubric implementation)
6. **Brief Generation** (LLM with guardrail prompts)
7. **Frontend** (dashboard, reports, exports)

### Testing Requirements
- **Unit tests**: core scoring, normalization, deduplication logic
- **Integration tests**: provider API calls (with mocks for CI)
- **End-to-end tests**: full pipeline run with sample data
- Minimum **80% coverage** on core pipeline code

### Code Quality
- **Type hints**: all Python functions must be typed
- **Linting**: black (Python), eslint + prettier (TypeScript)
- **Documentation**: docstrings for all public functions
- **Error handling**: graceful degradation, no silent failures

## Security Requirements

### API Keys & Secrets
- All secrets in `.env` files (never committed)
- Server-side storage only (no client-side API keys)
- Rotation policy: quarterly or on suspected compromise
- Per-plan rate limits enforced at API level

### User Data
- No password storage (use Clerk/Supabase Auth)
- Minimal data collection: email + plan tier only
- Audit logs for all runs and exports
- GDPR compliance: delete user data on request

## Performance Standards

### Response Times
- **API health check**: < 100ms
- **Run creation**: < 500ms (enqueue job)
- **Pipeline execution**: < 5 minutes for 100 signals
- **Report loading**: < 1s (paginated results)

### Scalability Targets (MVP)
- Support **100 concurrent users**
- Process **1000 signals per run** (Pro tier)
- Store **1 year** of historical runs per user
- Export reports **< 30 seconds** (MD/PDF)

## Governance

### Constitution Supremacy
- This constitution supersedes all ad-hoc decisions
- All PRs must verify compliance with these principles
- Complexity must be justified (default: start simple)
- If unsure, bias toward **lean & fast-to-ship**

### Amendment Process
1. Propose change with rationale (GitHub issue/discussion)
2. Review by maintainers (evaluate impact on existing code)
3. If approved: update constitution + migration plan
4. Communicate changes to all contributors

### Conflict Resolution
When trade-offs arise:
1. **Micro-App Fit First** (non-negotiable gate)
2. **Data Privacy & Compliance** (legal necessity)
3. **Lean & Fast-to-Ship** (bias toward MVP speed)
4. **Quality Over Quantity** (3 good briefs > 50 bad ones)

### Review Checklist (for all features)
- [ ] Passes Micro-App Fit criteria (≤3 screens, <1 week build, 1 JTBD)
- [ ] Respects data privacy (no PII, ToS compliance)
- [ ] Uses deterministic scoring (transparent + explainable)
- [ ] Has tests (unit + integration where needed)
- [ ] Documented (code comments + user-facing docs)
- [ ] Observability hooks (logging, error tracking)
- [ ] Cost-aware (LLM token budgets, provider rate limits)

---

**Version**: 1.0.0  
**Ratified**: 2025-10-04  
**Last Amended**: 2025-10-04

**Purpose**: This constitution ensures MicroAppFinder stays focused on its core mission: discovering high-quality, actionable micro-app opportunities while respecting user privacy, platform ToS, and shipping speed.