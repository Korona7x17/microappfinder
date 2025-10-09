# Feature Specification: Multi-Dimensional Opportunity Analysis Layer

**Feature Branch**: `003-multi-dimensional-opportunity`
**Created**: 2025-10-08
**Status**: Draft
**Input**: User description: "Add multi-dimensional opportunity analysis layer that transforms raw pain points into validated business opportunities with IdeaBrowser-level sophistication. After each search completes, automatically analyze the top pain points to generate six-dimensional scores: (1) problem severity 0-10 measuring pain intensity and urgency, (2) market size indicator (niche/mid/large) estimating affected population, (3) monetization potential 0-10 assessing willingness to pay, (4) technical complexity 0-10 rating build difficulty, (5) competition level (low/medium/high/saturated) based on mentioned solutions, and (6) trend direction (declining/stable/growing/explosive) from discussion patterns."

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

## User Scenarios & Testing *(mandatory)*

### Primary User Story
A founder visits the platform to discover validated micro-app opportunities without knowing what to build. Behind the scenes, the system continuously analyzes pain points from all searches to build a global knowledge base of opportunities with six-dimensional business scores: problem severity (how painful/urgent), market size (niche/mid/large population), monetization potential (willingness to pay), technical complexity (build difficulty), competition level (crowding), and trend direction (growth trajectory). These analyzed opportunities are stored persistently in a public opportunities database, surviving beyond the 48-hour Reddit compliance window. Users can browse, filter, and sort this growing catalog of validated opportunities—similar to IdeaBrowser's discovery-first model—to find ideas worth investigating further. The system transforms from a "search tool" into an "opportunity discovery platform."

### Personas
- **Opportunity Seekers**: Founders, builders, and entrepreneurs searching for validated micro-app ideas
- **System Administrators**: Platform operators monitoring analysis coverage, performance, and accuracy

## Clarifications

### Session 2025-10-08
- Q: Should API access be user-scoped (show only opportunities from searches user performed) or global (show all opportunities)? → A: Global - all opportunities are public and browsable by everyone for discovery-first model like IdeaBrowser
- Q: What pagination limits and performance targets apply to opportunity queries? → A: 12 results per page with heading and short summary (lightweight response); <500ms p95 response time target; cursor-based pagination for scalability
- Q: When the same pain point appears in multiple searches or new signals arrive, should opportunities be re-analyzed? → A: Accumulative enrichment - merge new signals into existing opportunity and recompute scores with richer context over time
- Q: After raw pain_points are deleted (48h TTL), should opportunities keep the pain_point_id reference or nullify it? → A: Nullify on deletion - set pain_point_id to null when source expires since analyzed opportunities are self-sufficient and don't need the reference
- Q: What monitoring, logging, and admin visibility is needed to track analysis health? → A: Admin dashboard with system health monitoring showing real-time analysis status, coverage trends, score distributions, and failure tracking

### User Stories
1. As a user, when I complete a search, the system automatically analyzes the top pain points in the background without affecting my search experience or response time
2. As a user, I continue to see the same top 5 results presentation (no UI changes yet), but the system now stores rich opportunity analyses that will power future advanced features
3. As a platform operator, I can verify that 80%+ of pain points receive multi-dimensional analysis within 30 seconds of search completion
4. As a platform operator, I can spot-check opportunity scores to validate that severity, market size, monetization, complexity, competition, and trend assessments align with human judgment

### Acceptance Scenarios
1. **Given** a user completes a search returning 5 pain points, **When** the unified aggregation completes, **Then** the system queues an asynchronous analysis task that analyzes 5-10 top pain points
2. **Given** a pain point contains discussion context with frustration indicators and usage frequency mentions, **When** the analysis runs, **Then** the system generates a problem severity score (0-10) reflecting pain intensity and urgency
3. **Given** a pain point mentions affected user groups or discussion volume patterns, **When** the analysis runs, **Then** the system estimates market size as niche/mid/large based on population indicators
4. **Given** a pain point includes pricing discussions or willingness-to-pay signals, **When** the analysis runs, **Then** the system scores monetization potential (0-10) based on payment readiness
5. **Given** a pain point involves technical requirements or implementation complexity hints, **When** the analysis runs, **Then** the system rates technical complexity (0-10) reflecting build difficulty
6. **Given** a pain point mentions existing solutions or competitive tools, **When** the analysis runs, **Then** the system classifies competition level as low/medium/high/saturated
7. **Given** a pain point shows discussion frequency patterns over time, **When** the analysis runs, **Then** the system determines trend direction as declining/stable/growing/explosive
8. **Given** an analyzed opportunity is created, **When** stored in the database, **Then** it persists indefinitely (not subject to 48-hour TTL) since it contains derived insights, not raw Reddit content
9. **Given** the system completes analysis, **When** measured over time, **Then** 80%+ of pain points receive complete analysis with all six dimensional scores
10. **Given** the analysis task runs, **When** measured, **Then** completion time is ≤30 seconds from search aggregation finish
11. **Given** an opportunity analysis completes, **When** accessed via API, **Then** it includes all six scores, trend_data JSON time-series, geographic_spread array, affected_industries array, confidence_level (0-1), and analyzed_at timestamp
12. **Given** multiple opportunities exist in the database, **When** queried via API, **Then** results can be filtered by score ranges, sorted by any dimension, and include rich metadata for dashboard consumption

### Edge Cases
- What happens when a pain point has insufficient context for scoring one or more dimensions? → System assigns null score for that dimension and sets lower confidence_level; opportunity still created with available scores
- What happens when analysis takes longer than 30 seconds? → System continues processing but logs performance warning; no user impact since analysis is asynchronous
- What happens when the same pain point is analyzed multiple times (e.g., across different searches)? → System creates one opportunity per pain_point_id (unique constraint); subsequent analyses update existing opportunity with latest scores
- What happens when raw pain_points are deleted after 48 hours but opportunities reference them? → Opportunities retain pain_point_id for tracking but are self-sufficient (contain all analysis); orphaned references are acceptable since opportunities store derived insights independently
- How are geographic_spread and affected_industries determined when not explicitly mentioned? → Analysis infers from discussion context (subreddit names, user locations mentioned, industry terminology); may be empty arrays if indeterminate

---

## Requirements *(mandatory)*

### Functional Requirements

#### Analysis Trigger and Workflow
- **FR-001**: System MUST automatically trigger multi-dimensional analysis after unified search aggregation completes, without user action or awareness
- **FR-002**: System MUST analyze the top 5-10 pain points from each completed search run, prioritizing those with highest relevance scores
- **FR-003**: System MUST execute analysis asynchronously to avoid blocking user-facing search responses or degrading search performance
- **FR-004**: System MUST complete analysis within 30 seconds (target) of search aggregation finish to maintain timely opportunity database updates

#### Six-Dimensional Scoring
- **FR-005**: System MUST generate a **problem severity score** (0-10 scale) measuring pain intensity and urgency based on frustration language, impact descriptions, and urgency signals in pain point text
- **FR-006**: System MUST generate a **market size indicator** (niche/mid/large enum) estimating affected population based on discussion volume, affected user group mentions, and community size indicators
- **FR-007**: System MUST generate a **monetization potential score** (0-10 scale) assessing willingness to pay based on pricing discussions, budget mentions, current spending patterns, and value perception signals
- **FR-008**: System MUST generate a **technical complexity score** (0-10 scale) rating build difficulty based on technical requirements mentioned, implementation hints, and domain complexity indicators
- **FR-009**: System MUST generate a **competition level classification** (low/medium/high/saturated enum) based on mentions of existing solutions, competitive tools, and market saturation indicators
- **FR-010**: System MUST generate a **trend direction classification** (declining/stable/growing/explosive enum) based on discussion frequency patterns, time-series analysis of related discussions, and growth language
- **FR-011**: System MUST determine scores by sending pain point context to an AI analysis service with a structured prompt requesting each dimension with reasoning
- **FR-012**: System MUST generate a **confidence level score** (0-1 float) indicating analysis certainty based on available context quality and completeness

#### Data Persistence and Structure
- **FR-013**: System MUST store analyzed opportunities in a new persistent opportunities table that survives indefinitely beyond the 48-hour Reddit compliance window for raw content
- **FR-014**: System MUST store each opportunity with: unique opportunity_id, pain_point_id reference, all six dimensional scores (severity, market_size, monetization, complexity, competition, trend), trend_data as JSON time-series, geographic_spread as array, affected_industries as array, confidence_level float, analyzed_at timestamp
- **FR-015**: System MUST store trend_data as JSON containing time-series information about discussion patterns, growth indicators, and temporal analysis
- **FR-016**: System MUST store geographic_spread as array of location indicators extracted or inferred from discussion context
- **FR-017**: System MUST store affected_industries as array of industry/sector identifiers extracted or inferred from discussion context
- **FR-018**: System MUST maintain referential link between opportunities and pain_points via pain_point_id, but opportunities MUST remain self-sufficient since pain_points expire after 48 hours

#### Analysis Coverage and Quality
- **FR-019**: System MUST achieve 80%+ coverage rate, meaning at least 80% of pain points from completed searches receive full multi-dimensional analysis
- **FR-020**: System MUST handle analysis failures gracefully: if one dimension fails to score, system MUST store opportunity with remaining scores and set appropriate confidence_level
- **FR-021**: System MUST allow spot-checking and validation: sample analyses can be compared against human judgment to verify score accuracy and reasonableness
- **FR-022**: System MUST support accumulative enrichment where new signals about existing opportunities trigger re-analysis that merges additional context and recomputes all six dimensional scores with richer data, improving accuracy over time

#### API Access and Querying
- **FR-023**: System MUST provide API endpoints to retrieve opportunities with filtering by score ranges (e.g., severity ≥7, monetization ≥8)
- **FR-024**: System MUST provide API endpoints to sort opportunities by any dimensional score (severity, market_size, monetization, complexity, competition, trend)
- **FR-025**: System MUST provide API endpoints that return rich metadata including all scores, trend_data, geographic_spread, affected_industries, and confidence_level for dashboard presentation
- **FR-026**: System MUST provide global API access where all opportunities are publicly accessible to all users without ownership filtering, enabling discovery-first browsing model
- **FR-027**: System MUST paginate opportunity queries at 12 results per page returning title and summary (lightweight response) with <500ms p95 response time using cursor-based pagination for scalability

#### Reddit Compliance and Data Lifecycle
- **FR-028**: System MUST maintain Reddit API compliance by keeping raw pain_points ephemeral with 48-hour TTL as currently implemented
- **FR-029**: System MUST store opportunities indefinitely since they contain derived insights (analysis scores) not raw Reddit content, which is permissible under Reddit ToS
- **FR-030**: System MUST ensure opportunity analyses are based on pain point text and context but do not directly copy Reddit user-generated content verbatim
- **FR-031**: System MUST nullify pain_point_id references when source pain_points are deleted after 48h TTL, setting field to null since analyzed opportunities are self-sufficient and do not require source references

#### User Experience and Non-Functional
- **FR-032**: System MUST NOT change current user-facing search experience: users continue to see top 5 results with existing presentation format
- **FR-033**: System MUST run all analysis in the background without affecting search response times or perceived performance
- **FR-034**: System MUST provide infrastructure foundation for future features including clustering, market research automation, and interactive dashboards
- **FR-035**: System MUST provide admin dashboard with system health monitoring showing real-time analysis status, coverage trends (% of pain points successfully enriched), score distributions across all six dimensions, and failure tracking with error categorization

### Key Entities *(include if feature involves data)*
- **Opportunity**: Represents an analyzed business opportunity derived from a pain point; contains opportunity_id (primary key), pain_point_id (foreign key reference), six dimensional scores (problem_severity float 0-10, market_size_indicator enum niche/mid/large, monetization_potential float 0-10, technical_complexity float 0-10, competition_level enum low/medium/high/saturated, trend_direction enum declining/stable/growing/explosive), trend_data (JSON time-series of discussion patterns), geographic_spread (array of location strings), affected_industries (array of industry/sector strings), confidence_level (float 0-1), analyzed_at (timestamp); persists indefinitely as derived insight; related to PainPoint via pain_point_id but self-sufficient

- **PainPoint**: (Existing entity) Represents raw pain point extracted from Reddit/HN discussions; subject to 48-hour TTL for Reddit compliance; referenced by Opportunity but not dependent upon for opportunity persistence

---

## Scope

### In Scope
- Automatic asynchronous analysis triggered after search aggregation
- Six-dimensional scoring (severity, market size, monetization, complexity, competition, trend)
- Persistent opportunities storage surviving beyond 48-hour Reddit window
- AI-based analysis using structured prompts to determine scores
- Trend data, geographic spread, and industry tracking
- 80%+ coverage and 30-second analysis time targets
- API endpoints for filtering, sorting, and retrieving opportunities with rich metadata
- Foundation infrastructure for future clustering, research, and dashboard features

### Out of Scope
- User-facing UI changes or opportunity presentation (remains top 5 results for now)
- Advanced dashboards, interactive filtering, or comparison views (future Phase 5)
- Opportunity clustering or grouping related opportunities (future Phase 2)
- Market research automation (Google Trends, Crunchbase, Product Hunt integration) (future Phase 3)
- AI advisory layer, founder-fit matching, or strategy generation (future Phase 6)
- Real-time user notifications about new high-scoring opportunities
- Opportunity editing, curation, or manual overrides by administrators

---

## Non-Functional Goals
- **Coverage**: Achieve 80%+ analysis coverage (most pain points analyzed)
- **Performance**: Complete analysis within 30 seconds of search aggregation (target)
- **Quality**: Scores align with human judgment when spot-checked (sample validation)
- **Compliance**: Maintain Reddit API compliance via persistent derived insights, not raw content storage
- **Unobtrusiveness**: Zero impact on user-facing search performance or experience
- **Foundation**: Build infrastructure supporting future phases (clustering, research, dashboards)

---

## Constraints & Assumptions

### Constraints
- Must maintain Reddit API compliance: raw pain_points remain ephemeral (48h TTL); only derived insights (opportunity analyses) stored indefinitely
- Analysis must run asynchronously without affecting user-facing search performance
- No user-facing UI changes in this phase: opportunities built in backend only
- Must avoid storing raw Reddit content verbatim: opportunities contain analysis/scores, not copyrighted user text

### Assumptions
- Current unified search aggregation produces pain points with sufficient context (title, text, source discussion) for multi-dimensional analysis
- AI analysis service (e.g., Claude Sonnet) can determine scores from structured prompts with reasonable accuracy
- Persistent opportunities database can grow indefinitely without storage/performance constraints in near term
- [NEEDS CLARIFICATION: Are there existing background job processing capabilities (e.g., RQ worker, Celery) to handle asynchronous analysis tasks?]
- [NEEDS CLARIFICATION: Is there existing infrastructure for querying AI services (e.g., Anthropic API) or must integration be created from scratch?]

---

## Dependencies
- Current unified search aggregation pipeline (must complete before triggering analysis)
- Existing PainPoint entity and database schema
- Background job processing system for asynchronous analysis tasks
- AI analysis service API for generating dimensional scores from structured prompts
- [NEEDS CLARIFICATION: Specific services, libraries, or APIs used for background jobs and AI integration]

---

## Risks & Mitigation

### Risks
1. **Analysis accuracy varies with pain point context quality**
   - Mitigation: Generate confidence_level score per opportunity; allow null scores for insufficient data; spot-check samples to validate

2. **30-second analysis target may not be achievable if AI API is slow**
   - Mitigation: Set generous timeout; log performance warnings; analysis is async so no user impact even if slower

3. **80%+ coverage target may be missed if analysis fails frequently**
   - Mitigation: Graceful degradation (store opportunities with partial scores); retry logic for transient failures; monitoring alerts on coverage drop

4. **Persistent storage may grow large over time affecting database performance**
   - Mitigation: No immediate concern for Phase 1; monitor growth; future optimization via archiving, indexing, or partitioning

5. **Derived insights interpretation may not fully comply with Reddit ToS edge cases**
   - Mitigation: Ensure opportunities contain analysis (scores, metadata), not verbatim Reddit text; legal review if needed

---

## Success Metrics
- **Coverage**: ≥80% of pain points from completed searches receive full multi-dimensional analysis
- **Performance**: Analysis completes within 30 seconds (p95) of search aggregation finish
- **Quality**: Sample spot-checks show scores align with human judgment (subjective but directional validation)
- **Availability**: Analysis service operates reliably without causing search pipeline failures or degradation
- **Foundation**: Infrastructure successfully supports future features (clustering, research, dashboards tested against opportunities database)

---

## Deliverable
A business-facing feature specification describing how the system transforms raw pain points into validated business opportunities with six-dimensional scoring (severity, market size, monetization, complexity, competition, trend), persistent storage surviving Reddit compliance windows, asynchronous background analysis achieving 80%+ coverage in ≤30 seconds, and API access enabling future advanced features—without changing current user experience.

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain *(6 clarifications needed)*
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked (6 areas need clarification)
- [x] User scenarios defined
- [x] Requirements generated (35 functional requirements)
- [x] Entities identified (Opportunity, PainPoint)
- [x] Review checklist passed *(with warnings for clarifications)*

---

**INFO**: Specification generation complete. 6 areas marked for clarification:
1. FR-022: Re-analysis triggers for existing opportunities
2. FR-026: API access scope (user-scoped vs global)
3. FR-027: Pagination limits and performance targets for queries
4. FR-031: Orphaned pain_point_id handling after 48h deletion
5. FR-035: Monitoring, logging, admin visibility requirements
6. Assumptions: Background job infrastructure and AI integration details

These clarifications should be resolved via `/clarify` command before proceeding to implementation planning.
