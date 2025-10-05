# Research: Reddit Pain Point Discovery

**Feature**: Reddit Pain Point Discovery
**Date**: 2025-10-04
**Status**: Complete

## Technical Decisions

### 1. Authentication Strategy

**Decision**: JWT-based auth with httponly cookies

**Rationale**:
- Stateless design scales horizontally (no server-side session storage)
- httponly cookies prevent XSS attacks (token not accessible to JavaScript)
- Refresh token rotation provides security without compromising UX
- Aligns with existing FastAPI ecosystem (python-jose, passlib)

**Alternatives Considered**:
- **Session-based auth**: Rejected - requires Redis/DB for session storage, adds latency, harder to scale
- **OAuth only**: Rejected - adds complexity for MVP, requires third-party provider setup, overkill for email/password

**Implementation Notes**:
- Use `python-jose` for JWT encoding/decoding
- Store access token in httponly cookie (15min expiry)
- Refresh token in separate httponly cookie (7 days expiry)
- Middleware validates JWT on protected routes

---

### 2. Reddit API Client

**Decision**: PRAW (Python Reddit API Wrapper) v7.7+

**Rationale**:
- Official Python wrapper maintained by Reddit community
- Handles OAuth2 authentication automatically
- Built-in rate limiting and retry logic
- Supports subreddit search, time filtering, and pagination
- Active maintenance (last update Oct 2024)

**Alternatives Considered**:
- **Direct REST API calls**: Rejected - requires manual OAuth flow, rate limit tracking, pagination logic
- **Pushshift API**: Rejected - deprecated in 2023, unreliable for new implementations
- **Reddit Scraping (BeautifulSoup)**: Rejected - violates ToS, fragile to HTML changes

**Implementation Notes**:
- Use `client_credentials` flow (system-level auth, no user OAuth)
- Configure PRAW with `client_id` and `client_secret` from .env
- Set `user_agent` to identify application per Reddit guidelines

---

### 3. Content Caching & TTL

**Decision**: Redis with 48-hour TTL + PostgreSQL for aggregates

**Rationale**:
- Redis `EXPIRE` command handles automatic TTL enforcement (no manual cleanup)
- In-memory cache provides <10ms read latency for hot data
- PostgreSQL stores durable aggregates (pain points, scores) indefinitely
- Separation of concerns: ephemeral (Redis) vs. permanent (Postgres)

**Alternatives Considered**:
- **PostgreSQL only with CRON cleanup**: Rejected - slower reads, manual TTL management prone to bugs
- **S3 for raw content**: Rejected - 100-200ms latency unacceptable for <30s SLA

**Implementation Notes**:
- Redis key pattern: `reddit:post:{reddit_id}` with `SETEX` 172800 (48 hours)
- Store JSON serialized RedditPost model
- PostgreSQL stores only derived `PainPoint` records (no raw text)

---

### 4. Deletion Sync Implementation

**Decision**: Daily cron job using RQ Scheduler checking Reddit API for deleted posts

**Rationale**:
- Batch processing efficient (check all cached posts once/day vs. real-time checks)
- Reddit API `/info` endpoint returns `null` for deleted posts (reliable indicator)
- Daily sync meets Reddit ToS requirement ("timely deletion")
- RQ Scheduler already in stack (no new dependencies)

**Alternatives Considered**:
- **Real-time webhooks**: Rejected - Reddit doesn't provide deletion webhooks
- **On-demand sync per user request**: Rejected - too slow, delays user response

**Implementation Notes**:
- Schedule job at 2AM UTC (low traffic period)
- Query all RedditPost records from Redis
- Batch check Reddit API `/api/info` with post IDs
- Delete from Redis if API returns null/404
- Update PainPoint `source_deleted=true` flag in PostgreSQL

---

### 5. Composite Scoring Algorithm

**Decision**: Weighted sum with normalization

```python
score = (
    0.30 * normalize(upvotes) +
    0.25 * normalize(comment_count) +
    0.25 * recency_score(created_utc) +
    0.20 * sentiment_polarity
)
```

**Rationale**:
- **Upvotes (30%)**: Primary signal of community validation
- **Comments (25%)**: Engagement depth indicates real pain vs. casual mention
- **Recency (25%)**: Fresh pain points more actionable than stale ones
- **Sentiment (20%)**: Negative polarity indicates stronger pain intensity
- Normalization (min-max scaling) ensures fair comparison across metrics

**Alternatives Considered**:
- **ML-based ranking (embeddings + classifier)**: Rejected - overkill for MVP, adds LLM costs
- **Upvotes-only**: Rejected - misses nuance (low upvote but high engagement can be valuable)

**Implementation Notes**:
- Min-max normalize upvotes/comments within each search run cohort
- Recency score: `1 - (age_hours / max_age_hours)` (linear decay)
- Sentiment via TextBlob: `polarity` ranges [-1, 1], map to [0, 1]

---

### 6. NSFW/Spam Filtering

**Decision**: Multi-layer filtering

1. **Reddit API `over_18` flag** → Block all NSFW posts
2. **Keyword blocklist** → Reject posts containing spam terms (e.g., "buy now", "click here", crypto scams)
3. **Low-score threshold** → Drop posts with `score < 2` (likely spam or low-quality)

**Rationale**:
- Reddit's NSFW flag is reliable (user-reported + mod-verified)
- Keyword filter catches obvious spam without ML overhead
- Score threshold leverages community curation (downvoted = filtered)

**Alternatives Considered**:
- **ML content moderation (OpenAI Moderation API)**: Rejected - $0.002/1K tokens adds cost, latency
- **Manual review queue**: Rejected - not scalable for MVP

**Implementation Notes**:
- Blocklist: `["buy now", "click here", "limited time", "crypto", "forex", "investment opportunity"]`
- Apply filters in worker pipeline before pain point extraction
- Log filtered posts to `filtered_posts` table for analysis

---

### 7. Sentiment Analysis

**Decision**: TextBlob polarity score for pain intensity

**Rationale**:
- Lightweight Python library (no external API calls)
- Zero marginal cost per analysis
- Sufficient accuracy for composite scoring (not primary ranking factor)
- Well-tested on social media text

**Alternatives Considered**:
- **OpenAI embeddings + similarity**: Rejected - $0.0001/1K tokens × 500 posts = $0.05/run (adds up)
- **Rule-based (word lists)**: Rejected - less accurate, brittle to linguistic variation

**Implementation Notes**:
```python
from textblob import TextBlob
polarity = TextBlob(post_text).sentiment.polarity  # -1 (negative) to 1 (positive)
pain_intensity = abs(polarity) if polarity < 0 else 0  # Only negative sentiment indicates pain
```

---

### 8. User Privacy Enforcement

**Decision**: Database-level FK constraints + API middleware ownership checks

**Rationale**:
- **Database layer**: `user_id` FK on `SearchRun` prevents orphaned data
- **API layer**: Middleware verifies `current_user.id == search_run.user_id` before access
- Defense in depth (two layers prevent accidental leaks)

**Alternatives Considered**:
- **Frontend-only access control**: Rejected - insecure, easily bypassed
- **Separate user databases**: Rejected - complex, breaks referential integrity

**Implementation Notes**:
- FastAPI dependency `get_current_user()` injects authenticated user
- Ownership check in endpoint:
  ```python
  if search_run.user_id != current_user.id:
      raise HTTPException(403, "Access denied")
  ```
- PostgreSQL row-level security (RLS) as future enhancement

---

### 9. Empty Results Fallback

**Decision**: Query top 20 recent pain points from database (any topic, last 7 days, sorted by score)

**Rationale**:
- Always shows value to user (discovery > empty state)
- Uses existing data (no additional Reddit API calls)
- Promotes topic exploration
- 7-day window ensures freshness

**Alternatives Considered**:
- **"No results" message**: Rejected - poor UX, user leaves discouraged
- **AI-generated topic suggestions**: Rejected - requires embedding similarity search (v2 feature)

**Implementation Notes**:
```sql
SELECT * FROM pain_points
WHERE created_at > NOW() - INTERVAL '7 days'
ORDER BY relevance_score DESC
LIMIT 20;
```

---

## Dependencies Added

| Package | Version | Purpose |
|---------|---------|---------|
| `praw` | ^7.7.0 | Reddit API client |
| `python-jose[cryptography]` | ^3.3.0 | JWT encoding/decoding |
| `passlib[bcrypt]` | ^1.7.4 | Password hashing |
| `textblob` | ^0.17.1 | Sentiment analysis |
| `rq-scheduler` | ^0.13.1 | Scheduled deletion sync |

**Frontend**:
| Package | Version | Purpose |
|---------|---------|---------|
| `@tanstack/react-query` | ^5.0.0 | API state management |
| `js-cookie` | ^3.0.5 | Cookie handling |
| `zod` | ^3.22.0 | Form validation |

---

## Best Practices Applied

### Reddit API Usage
- **Rate Limiting**: PRAW handles 60 req/min limit automatically
- **User-Agent**: Set to `MicroAppFinder:v1.0 (by /u/yourusername)`
- **Respect `robots.txt`**: PRAW enforces this by default
- **Backoff on 429**: PRAW retries with exponential backoff

### Security
- **Password Hashing**: bcrypt with cost factor 12
- **JWT Secret**: 256-bit random key in `.env`
- **SQL Injection Prevention**: SQLAlchemy ORM parameterizes queries
- **CORS**: Restrict to frontend domain in production

### Performance
- **Database Indexing**:
  - `CREATE INDEX idx_reddit_posts_expires_at ON reddit_posts(expires_at);` (TTL queries)
  - `CREATE INDEX idx_search_runs_user_id ON search_runs(user_id);` (user lookups)
- **Pagination**: Limit 50 results/page (prevents memory issues)
- **Redis Connection Pool**: Max 20 connections

---

## Outstanding Questions

None - all technical decisions resolved.

---

**Status**: ✅ Ready for Phase 1 (Design & Contracts)
