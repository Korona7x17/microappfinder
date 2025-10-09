# Strategic Analysis: IdeaBrowser Sophistication Gap

**Date**: 2025-10-08
**Context**: Analyzed IdeaBrowser.com to understand sophistication gap and plan evolution roadmap
**Reference**: https://www.ideabrowser.com/idea/sora-2-agentkit-weekly-promo-machine-for-local-biz

## Current State (Phase 0/10)

### What We Have
- **Product**: Pain point discovery tool
- **Output**: Top 5 raw signals with LLM summaries
- **Scoring**: Single-dimension (5-factor composite: engagement, questions, pain, recency, topic relevance)
- **Presentation**: Flat list
- **Data Lifecycle**: Ephemeral (48h TTL)
- **Architecture**: Simple pipeline (Reddit/HN → Scorer → LLM Filter → Top 5)

### What IdeaBrowser Has (Phase 10/10)
- **Product**: Business intelligence platform
- **Output**: Validated opportunities with 40-step analysis
- **Scoring**: Multi-dimensional (8+ axes: severity, market size, monetization, complexity, competition, trend, etc.)
- **Presentation**: Interactive dashboards with data visualizations
- **Data Lifecycle**: Historical tracking for trend analysis
- **Architecture**: 6-layer intelligence stack (ingestion → enrichment → research → analysis → insights → presentation)

## Gap Analysis

### Product Category Shift Needed
| Dimension | Current | Target |
|-----------|---------|--------|
| Value proposition | "Here are pain points" | "Here's a validated opportunity" |
| Output type | Raw data | Actionable insights |
| Scoring depth | One dimension | Eight dimensions |
| Time orientation | Static snapshot | Dynamic trends |
| Personalization | Generic | Founder-fit matched |

### Key Missing Capabilities
1. **Market validation**: No trend data, competitor analysis, or market sizing
2. **Opportunity clustering**: Can't group related signals into coherent opportunities
3. **Historical tracking**: No ability to track growth/decline of problem spaces
4. **Multi-dimensional scoring**: Only relevance, missing severity/size/competition/etc.
5. **Strategic insights**: No MVP suggestions, pricing guidance, or GTM recommendations

## Approved Roadmap: Fast Follow + Rolling Updates

### Decision Rationale
- **Option A (Fast Follow, 4-6 weeks)**: Ship Phases 1-3, gather feedback, iterate ✅ **SELECTED**
- Option B (Leap Frog, 10-12 weeks): Build all 6 phases before launch ❌ Risk of over-building

### Phase 1: Signal Enrichment (1-2 weeks) - Feature 003
**Goal**: Transform raw pain points into analyzed opportunities

**Capabilities**:
1. Multi-dimensional scoring (6 axes)
   - Problem severity (0-10): Pain intensity
   - Market size indicator: niche/mid/large
   - Monetization potential: Willingness to pay
   - Technical complexity: Build difficulty
   - Competition level: low/medium/high/saturated
   - Trend direction: declining/stable/growing/explosive

2. Trend analysis
   - Time-series tracking of discussion frequency
   - Keyword volume (Google Trends integration)
   - Sentiment trajectory over time
   - Growth rate calculation

3. Source diversity metrics
   - Community spread (how many subreddits/forums)
   - Geographic indicators
   - Industry verticals affected

**Data Model Changes**:
```
OpportunityAnalysis {
  pain_point_id: uuid
  severity_score: float (0-10)
  market_size_indicator: enum[niche, mid, large]
  monetization_score: float (0-10)
  complexity_score: float (0-10)
  competition_level: enum[low, medium, high, saturated]
  trend_direction: enum[declining, stable, growing, explosive]
  trend_data: json  // time series {timestamp, discussion_count, sentiment}
  geographic_spread: string[]
  affected_industries: string[]
  confidence_level: float (0-1)
  analyzed_at: timestamp
}
```

**Key Design Decisions**:
- Keep pain_points table ephemeral (48h) for Reddit compliance
- Create NEW persistent `opportunities` table for analyzed results
- LLM performs deep analysis to generate multi-dimensional scores
- Store trend_data as JSON for flexibility
- Run analysis asynchronously after unified aggregation

### Phase 2: Opportunity Clustering (1 week) - Feature 004 (future)
**Goal**: Group related pain points into coherent opportunity spaces

**Capabilities**:
- Semantic clustering (embed + cluster similar pain points)
- Cluster-level analytics (total signals, momentum, maturity)
- Competitive landscape extraction (tools mentioned, gaps identified)

### Phase 3: Deep Research Layer (2 weeks) - Feature 005 (future)
**Goal**: Automated market research per opportunity

**Capabilities**:
- Google Trends API integration
- Crunchbase funding data
- Product Hunt competitor tracking
- LinkedIn job posting analysis

### Phases 4-6: Deferred Until User Validation
- Phase 4: Validation framework (VC-style scoring)
- Phase 5: Interactive dashboard (charts, filters, comparisons)
- Phase 6: AI advisory layer (founder-fit, strategy generation)

## Technical Architecture Changes

### From: Simple Pipeline
```
Reddit/HN → Scorer → LLM Filter → Top 5 → User
```

### To: Multi-Layer Intelligence Stack (Phase 1)
```
Layer 1: Signal Ingestion (Reddit, HN)
         ↓
Layer 2: Unified Aggregation (existing)
         ↓
Layer 3: Enrichment Analysis (NEW - Feature 003)
         ├─ Multi-dimensional Scoring
         ├─ Trend Analysis
         └─ Source Diversity Metrics
         ↓
Layer 4: Persistence (NEW)
         └─ Opportunities table (persistent)
         ↓
Layer 5: API & Dashboard (existing search + NEW opportunity endpoints)
```

### Key Shifts
1. **Ephemeral → Persistent**: Add `opportunities` table that survives beyond 48h
2. **Reactive → Proactive**: Store historical data for trend tracking
3. **Single-tier → Two-tier**:
   - Tier 1: Raw pain_points (ephemeral, Reddit compliant)
   - Tier 2: Analyzed opportunities (persistent, enriched)

## Implementation Constraints

### Reddit API Compliance
- MUST maintain 48h TTL for raw Reddit content (pain_points table)
- CAN store derived/analyzed data indefinitely (opportunities table)
- Opportunities reference pain_points by ID but contain independent analysis

### Performance Targets
- Analysis must not block user-facing search (<1s p95)
- Run enrichment asynchronously after unified aggregation
- Cache analyzed opportunities for fast retrieval

### Data Privacy
- No PII storage (usernames already excluded)
- Anonymize any quoted text
- Follow existing compliance patterns

## Success Metrics

### Phase 1 (Feature 003)
- **Depth**: Each opportunity has 6+ dimensional scores
- **Coverage**: 80%+ of pain points get enriched analysis
- **Accuracy**: Human validation shows scores align with reality (sample testing)
- **Performance**: Enrichment completes within 30s of search completion

### Product Evolution
- **Value perception**: Users say "this is useful" vs "this is just data"
- **Decision enablement**: Users can pick which opportunity to pursue
- **Competitive positioning**: Feature parity with IdeaBrowser core analysis (not full 40 steps yet)

## Next Steps

1. ✅ Log this decision (this file)
2. ⏭️ Create Feature 003 spec via `/specify` with comprehensive prompt
3. ⏭️ Run `/clarify` to resolve ambiguities
4. ⏭️ Run `/plan` to generate implementation plan
5. ⏭️ Execute implementation (data model, LLM analysis, persistence)

## References
- IdeaBrowser analysis: https://www.ideabrowser.com/idea/sora-2-agentkit-weekly-promo-machine-for-local-biz
- Current architecture: `CLAUDE.md`, `memory/summaries/project_snapshot.md`
- Reddit compliance: Feature 001 spec, `docs/REDDIT_COMPLIANCE.md` (if exists)
