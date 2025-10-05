# Feature Specification: Hacker News Integration for Unified Search

**Feature Branch**: `002-integrate-hacker-news`
**Created**: 2025-10-05
**Status**: Draft
**Input**: User description: "Integrate Hacker News (via Algolia) as a background data source that enhances the unified top-3 search results without changing the user experience."

## Execution Flow (main)
```
1. Parse user description from Input
   → If empty: ERROR "No feature description provided"
2. Extract key concepts from description
   → Identify: actors, actions, data, constraints
3. For each unclear aspect:
   → Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
   → If no clear user flow: ERROR "Cannot determine user scenarios"
5. Generate Functional Requirements
   → Each requirement must be testable
   → Mark ambiguous requirements
6. Identify Key Entities (if data involved)
7. Run Review Checklist
   → If any [NEEDS CLARIFICATION]: WARN "Spec has uncertainties"
   → If implementation details found: ERROR "Remove tech details"
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

### Section Requirements
- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation
When creating this spec from a user prompt:
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "login system" without auth method), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **Common underspecified areas**:
   - User types and permissions
   - Data retention/deletion policies
   - Performance targets and scale
   - Error handling behaviors
   - Integration requirements
   - Security/compliance needs

---

## Clarifications

### Session 2025-10-05
- Q: What deduplication strategy should the system use to identify near-duplicate results across sources? → A: Semantic similarity with threshold (e.g., 85% cosine similarity)
- Q: What scoring factors should be used for ranking Hacker News items alongside other sources? → A: Mirror Reddit scoring (upvotes→points, using existing weights)
- Q: How recent must Hacker News items be to appear in search results? → A: Hourly refresh (acceptable 1-hour lag)
- Q: What is the target response time SLA for search queries (including HN integration)? → A: ≤1 second (p95) - responsive, standard web performance
- Q: How should perceived relevance be measured to validate the ≥90% success target? → A: A/B test comparing baseline vs. HN-integrated results

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
A founder or researcher searches for "AI code review tools" to identify market gaps. The system queries multiple sources including Hacker News, normalizes and scores all results, applies deduplication to remove near-identical items, and returns the top three most relevant results. Some results may come from Hacker News discussions, others from existing sources—the user sees a unified, ranked list without knowing or choosing which sources contributed.

### Personas
- **Founder/Researcher**: Scanning for emerging market signals and opportunities
- **Builder**: Tracking pain points, problems, and trends in specific domains

### User Stories
1. As a user, when I search for a topic, I receive up to three highly relevant results compiled from all supported sources (including Hacker News), each with consistent fields: title, excerpt, link, attribution, and timestamp
2. As a user, I never need to choose or filter sources; the system automatically blends, scores, and deduplicates results across all sources
3. As a user, I perceive fresher, more diverse, and more relevant results without any additional steps or UI changes

### Acceptance Scenarios
1. **Given** a user searches for "productivity tools for developers", **When** the system queries all sources including Hacker News, **Then** the top 3 results are returned with consistent formatting (title, excerpt, link, attribution, time) regardless of source
2. **Given** Hacker News contains a highly-scored discussion about a search topic, **When** that discussion ranks in the top 3 by the unified scoring algorithm, **Then** it appears in the search results with proper attribution to Hacker News
3. **Given** the same URL or topic appears in both Hacker News and another source, **When** the system applies deduplication logic, **Then** only one result for that URL/topic appears in the final results
4. **Given** the Hacker News data source experiences downtime or rate limiting, **When** a user searches, **Then** the system gracefully returns results from other available sources without error or delay
5. **Given** a user performs consecutive searches, **When** comparing response times before and after HN integration, **Then** p95 latency remains ≤1 second with no measurable UX degradation

### Edge Cases
- What happens when Hacker News API is unavailable or rate-limited? → System continues to function normally using other sources; no error shown to user
- What happens when HN returns very recent items (posted within minutes)? → They become eligible after the next hourly refresh cycle (up to 1-hour lag is acceptable)
- How does the system handle duplicate content (same story discussed across sources)? → Cross-source deduplication prevents showing near-duplicates by comparing URLs and topic similarity
- What happens when HN dominates all top results? → Using the same scoring weights as Reddit (mirrored algorithm) ensures fair competition; calibration may adjust if systematic bias emerges

---

## Requirements *(mandatory)*

### Functional Requirements

#### Search Integration
- **FR-001**: System MUST include Hacker News as an additional data source queried during unified search operations
- **FR-002**: System MUST normalize Hacker News items into the existing cross-source result schema with fields: title, excerpt, link, attribution, and timestamp
- **FR-003**: System MUST maintain the existing single-query user experience without adding source selection UI or per-source filters
- **FR-004**: System MUST return up to three top-ranked results from all sources combined (including Hacker News)

#### Scoring and Ranking
- **FR-005**: System MUST apply unified scoring and ranking logic so Hacker News items compete fairly with items from other sources
- **FR-006**: System MUST score Hacker News items using the same algorithm and weights as Reddit items, mapping HN points to Reddit upvotes, HN comments to Reddit comments, and applying existing recency and sentiment factors
- **FR-007**: System MUST calibrate scoring to prevent any single source (including Hacker News) from systematically dominating or underperforming in results

#### Deduplication
- **FR-008**: System MUST apply cross-source deduplication to prevent near-duplicate results from appearing when the same URL or topic is found across multiple sources
- **FR-009**: System MUST use semantic similarity with a threshold (e.g., 85% cosine similarity) to identify and remove near-duplicate results across sources based on content similarity

#### Freshness and Reliability
- **FR-010**: System MUST make relevant new Hacker News items eligible for search results promptly after they are available in the data source
- **FR-011**: System MUST refresh Hacker News data at least hourly, with acceptable freshness lag of up to 1 hour between HN publication and search eligibility
- **FR-012**: System MUST gracefully degrade to other sources when Hacker News experiences outages or rate limits without displaying errors to users
- **FR-013**: System MUST cache Hacker News results with a 1-hour TTL aligned with the refresh interval; fallback to cached data during API failures

#### Attribution and Presentation
- **FR-014**: System MUST include clear source attribution for each result to indicate when an item originated from Hacker News
- **FR-015**: System MUST maintain consistent field presentation (title, excerpt, link, attribution, time) across all sources including Hacker News

#### Performance and Scale
- **FR-016**: System MUST maintain or improve overall search response time compared to baseline (pre-HN integration)
- **FR-017**: System MUST return search results within 1 second (p95 latency) under normal query volume
- **FR-018**: System MUST perform reliably under normal query volume without degradation due to HN integration
- **FR-019**: System MUST [NEEDS CLARIFICATION: expected query volume and concurrent user load for capacity planning]

#### Data Source Constraints
- **FR-020**: System MUST use the public Algolia Hacker News index as a read-only data source
- **FR-021**: System MUST NOT perform write actions to Hacker News (posting, voting, commenting)
- **FR-022**: System MUST [NEEDS CLARIFICATION: rate limit handling - what are Algolia HN API rate limits and how to stay within them?]

### Key Entities *(include if feature involves data)*
- **HackerNewsItem**: Represents a story or discussion from Hacker News; includes attributes such as title, URL, text excerpt, points (score), comment count, author, and timestamp; related to UnifiedSearchResult through normalization mapping
- **UnifiedSearchResult**: Represents a normalized search result from any source; includes title, excerpt, link, source attribution, timestamp, and computed relevance score; aggregates items from multiple sources including HackerNewsItem
- **SourceAttribution**: Identifies the origin of each result (e.g., "Hacker News", existing sources); used for display and analytics; linked to UnifiedSearchResult

---

## Scope

### In Scope
- Treat Hacker News (via Algolia API) as an additional input to the unified search aggregator
- Normalize HN items into the existing cross-source result schema
- Apply existing deduplication, consistency, and ranking logic so HN items compete fairly with other sources
- Update blending and scoring algorithms as needed to maintain overall relevance
- Ensure graceful degradation when HN is unavailable

### Out of Scope
- Any source-selection UI, per-source filters, or user controls for choosing sources
- Write actions to Hacker News (posting stories, voting, commenting)
- Stand-alone Hacker News browsing interface, feeds, or dashboards
- Historical backfill of HN data prior to integration launch
- User-facing HN-specific features or analytics

---

## Non-Functional Goals
- **Relevance**: Maintain or improve overall relevance and freshness of search results compared with baseline (pre-integration)
- **Latency**: No added user-facing latency or friction in the search experience
- **Reliability**: Reliable performance under normal query volume with graceful handling of HN outages or rate limits
- **Simplicity**: Preserve the one-step search UX without introducing complexity or choices

---

## Constraints & Assumptions

### Constraints
- Use the public Algolia Hacker News index exclusively as a read-only data source
- Follow existing normalization, ranking, and deduplication conventions established for other sources
- No changes to user-facing search interface or workflow
- Avoid detailed implementation instructions in this specification (reserved for planning phase)

### Assumptions
- Current unified search pipeline, normalization schema, ranking, and deduplication rules are well-defined and documented
- Algolia HN API provides sufficient data freshness and query capabilities for integration
- [NEEDS CLARIFICATION: is there existing infrastructure for querying external APIs, handling rate limits, and caching results?]
- [NEEDS CLARIFICATION: are there existing deduplication and normalization libraries/services that can be extended?]

---

## Dependencies
- Current unified search pipeline and aggregator service
- Existing normalization schema and result formatting logic
- Existing ranking algorithm and scoring components
- Existing cross-source deduplication rules and implementation
- [NEEDS CLARIFICATION: specific services, modules, or APIs that provide search aggregation, normalization, scoring, and deduplication]

---

## Risks & Mitigation

### Risks
1. **Algolia rate limits or index lag affecting freshness**
   - Mitigation: Hourly refresh cycle with 1-hour TTL caching reduces API call frequency; graceful fallback to cached data or other sources during outages

2. **Ranking calibration needed so HN neither dominates nor underperforms**
   - Mitigation: A/B testing comparing baseline vs. HN-integrated results; iterative tuning of scoring weights based on relevance metrics; monitor source distribution in top-3 results

3. **Deduplication complexity across heterogeneous sources**
   - Mitigation: Use semantic similarity (85% cosine similarity threshold) to identify duplicates; leverage existing embedding infrastructure if available

4. **Increased latency from additional API call**
   - Mitigation: Parallel querying of sources; aggressive timeout (e.g., 500ms) for HN API calls to stay within 1-second p95 SLA; circuit breakers for repeated failures

---

## Success Metrics
- **Relevance**: ≥90% of test queries show equal or better perceived relevance compared to baseline, measured via A/B testing between baseline (Reddit-only) and HN-integrated variants
- **Performance**: p95 response time ≤1 second; no measurable UX degradation in search speed or simplicity
- **Coverage**: Hacker News items appear in top-3 results when they are competitive by score (no systematic exclusion or dominance)
- **Reliability**: ≥99% of searches return results successfully even during HN outages (graceful degradation to other sources)

---

## Deliverable
A business-facing feature specification describing how Hacker News becomes an internal signal source powering the unified top-3 search, with clear user stories, scope boundaries, functional requirements, and measurable success criteria—without introducing new UI controls or source-selection mechanisms.

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain *(5 resolved, 5 deferred to planning)*
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed *(with warnings for clarifications)*

---

**INFO**: Clarification session completed. 5 critical ambiguities resolved:
1. ✅ FR-006: HN scoring mirrors Reddit algorithm (points→upvotes mapping)
2. ✅ FR-009: Semantic similarity deduplication (85% cosine threshold)
3. ✅ FR-011: Hourly refresh with 1-hour acceptable lag
4. ✅ FR-013: 1-hour cache TTL aligned with refresh cycle
5. ✅ FR-017: p95 latency ≤1 second SLA

**Deferred to planning phase** (implementation-level details):
6. FR-019: Expected query volume and concurrent load
7. FR-022: Algolia rate limit handling specifics
8. Assumptions: Existing API infrastructure details
9. Assumptions: Existing deduplication/normalization libraries
10. Dependencies: Specific services/modules identification

These deferred items are better resolved during technical planning when architecture decisions are made.
