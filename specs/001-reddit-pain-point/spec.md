# Feature Specification: Reddit Pain Point Discovery

**Feature Branch**: `001-reddit-pain-point`
**Created**: 2025-10-04
**Status**: Clarified - Ready for Planning
**Input**: User description: "Reddit Pain Point Discovery"

## Execution Flow (main)
```
1. Parse user description from Input
   → If empty: ERROR "No feature description provided"
2. Extract key concepts from description
   → Identified: users search Reddit for pain points, system extracts signals
3. For each unclear aspect:
   → All ambiguities resolved through clarification
4. Fill User Scenarios & Testing section
   → Primary flow: user defines topic → system searches Reddit → returns pain points
5. Generate Functional Requirements
   → 16 requirements identified, all clarifications resolved
6. Identify Key Entities
   → Topic, RedditPost, PainPoint, SearchRun
7. Run Review Checklist
   → PASS "All clarifications resolved"
8. Return: SUCCESS (spec ready for planning phase)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## Clarifications

### Session 2025-10-04
- Q: When a search returns zero pain points (no matching Reddit content found), what should the system display to the user? → A: Show most popular recent pain points from any topic as fallback
- Q: What is the acceptable maximum response time for displaying pain point results after a search completes? → A: < 30 seconds (long-running analysis acceptable)
- Q: How long should the system retain archived search results, given Reddit API deletion requirements? → A: Raw Reddit content (text, URLs, author info) ≤ 48 hours then purge; Aggregates (topics, clusters, trend scores) kept indefinitely as derived non-user-content; Always delete source data if Reddit post/account deleted
- Q: Who should have access to initiate Reddit pain point searches? → A: Authenticated users only (email/password login)
- Q: Should users be able to view or access each other's search results and pain point discoveries? → A: Private only - users can only view their own searches

---

## User Scenarios & Testing

### Primary User Story
An authenticated user wants to discover unmet needs and pain points expressed on Reddit to identify micro app opportunities. After logging in with email/password, they provide one or more topic keywords (e.g., "productivity", "small business tools"), and the system searches relevant Reddit discussions to extract and present pain points with supporting evidence.

### Acceptance Scenarios
1. **Given** unauthenticated user tries to access search, **When** they attempt to submit a topic, **Then** system requires login/registration before proceeding
2. **Given** authenticated user is logged in, **When** they submit a topic keyword "remote work tools", **Then** system returns a list of pain points extracted from Reddit posts related to that topic
3. **Given** user receives pain point results, **When** they view a pain point, **Then** they see the original Reddit post context and a summary of the problem being expressed
4. **Given** user initiates a search, **When** the search completes, **Then** pain points are ranked by relevance or demand signal strength
5. **Given** multiple authenticated users search the same topic, **When** results are cached, **Then** subsequent users receive results faster without re-scanning Reddit
6. **Given** authenticated user logs in, **When** they view their dashboard, **Then** they only see their own search history and results, not other users' searches

### Edge Cases
- What happens when a topic returns no Reddit posts? (Display most popular recent pain points from any topic as fallback)
- What happens when a topic returns thousands of posts? (System caps at top 500 pain points)
- How does system handle Reddit API rate limits or downtime? (Queue and exponential backoff)
- What happens if Reddit content is deleted after extraction? (Raw content immediately purged via daily deletion sync; derived aggregates recomputed excluding deleted items)
- How should system handle inappropriate or spam content? (Filtered and blocked from results)

## Requirements

### Functional Requirements
- **FR-001**: System MUST require user authentication (email/password login) before allowing search access
- **FR-001a**: System MUST accept one or more topic keywords as search input from authenticated users
- **FR-002**: System MUST search the following subreddits in priority order:
  - **Core** (highest priority): r/AppIdeas, r/SomebodyMakeThis, r/SideProject, r/nocode, r/zapier, r/shortcuts, r/Notion, r/ObsidianMD
  - **Solopreneurs**: r/freelance, r/smallbusiness, r/Entrepreneur, r/youtubers
  - **Productivity**: r/productivity, r/GetDisciplined
- **FR-002a**: System MUST support search phrases like "any app that", "is there a way to", "how do I track", "automation for" to identify pain points
- **FR-003**: System MUST allow users to select time range for post search (options: 24h, 7 days, 30 days, 90 days, 1 year, all time)
- **FR-004**: System MUST extract pain points, problems, or unmet needs from Reddit post content
- **FR-005**: System MUST cache the original Reddit post text and URL as evidence/context for each pain point (subject to 48-hour TTL and deletion sync compliance)
- **FR-006**: System MUST identify and extract key attributes: post author, subreddit, timestamp, upvotes, comment count
- **FR-007**: System MUST rank or score pain points using composite scoring: upvotes, comment engagement, recency, and sentiment analysis
- **FR-008**: System MUST store derived aggregates (topics, clusters, trend scores) in PostgreSQL indefinitely and cache raw Reddit content (text, URLs, author info) for maximum 48 hours before automatic purge
- **FR-008a**: System MUST immediately delete all cached Reddit content (text, URLs, author info, embeddings) when source post/comment/account is deleted on Reddit, implementing daily deletion sync checks
- **FR-009**: System MUST display extracted pain points to the user with supporting context
- **FR-010**: System MUST authenticate with Reddit API using system-level credentials (client ID and secret)
- **FR-011**: System MUST respect Reddit API rate limits by queueing requests and implementing exponential backoff retry logic when limits are reached
- **FR-012**: System MUST allow users to initiate a new search run
- **FR-013**: System MUST track search run status (pending, in-progress, completed, failed)
- **FR-014**: System MUST limit results to top 500 pain points per search run and support pagination with 50 results per page in UI display
- **FR-015**: System MUST filter and block inappropriate content (NSFW, adult content) and spam from search results
- **FR-016**: System MUST display most popular recent pain points from any topic as fallback when a search returns zero results
- **FR-017**: System MUST enforce user-level privacy: each user can only view, access, and manage their own search runs and results; cross-user access is prohibited

### Non-Functional Requirements
- **NFR-001**: System MUST display search results within 30 seconds of search completion
- **NFR-002**: System MUST support concurrent searches from multiple users without performance degradation
- **NFR-003**: System MUST comply with Reddit API Terms: no retention of deleted content (even if anonymized), daily deletion sync, 48-hour max cache for raw user content
- **NFR-004**: System MUST enforce authentication for all search operations; unauthenticated requests MUST be rejected
- **NFR-005**: System MUST implement user-level authorization: search results are private to the user who initiated them; no cross-user data access permitted

### Key Entities
- **User**: Authenticated account with email/password credentials - stored indefinitely
- **Topic**: The search keyword or phrase provided by user (e.g., "productivity tools", "side hustle") - stored indefinitely
- **SearchRun**: A user-initiated discovery session for one or more topics, linked to User, tracks status and results - stored indefinitely
- **RedditPost**: Temporary cache (≤48 hours TTL) of Reddit submission metadata (subreddit, timestamp, score, URL, text) for evidence linking; purged on source deletion
- **PainPoint**: Derived aggregate containing extracted problem description and relevance score (not raw Reddit text) - stored indefinitely as non-user-content

---

## Review & Acceptance Checklist

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed

---
