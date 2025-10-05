# Data Model: Reddit Pain Point Discovery

**Feature**: Reddit Pain Point Discovery
**Date**: 2025-10-04

## Entity Relationship Diagram

```
User
 ├─1:N─> SearchRun
 │        ├─1:N─> PainPoint
 │        └─M:N─> Topic
 │
 └─────> RedditPost (cache, no FK)
          ├── expires_at (TTL)
          └── referenced by PainPoint.source_reddit_post_ids[]
```

## Entities

### 1. User

**Purpose**: Authenticated account for search access

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique user identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email address |
| hashed_password | VARCHAR(255) | NOT NULL | bcrypt hashed password |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Account creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last profile update |

**Indexes**:
- `idx_users_email` on `email` (login lookups)

**Validation Rules**:
- Email: Valid RFC 5322 format
- Password: Min 8 chars, requires uppercase + lowercase + digit

**Retention**: Indefinite (until user deletion request)

---

### 2. Topic

**Purpose**: Search keyword/phrase for pain point discovery

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique topic identifier |
| keyword | VARCHAR(100) | NOT NULL | Search term (e.g., "productivity tools") |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | First usage timestamp |
| search_count | INTEGER | DEFAULT 0 | Times used in searches |

**Indexes**:
- `idx_topics_keyword` on `keyword` (search reuse)

**Validation Rules**:
- Keyword: 2-100 chars, alphanumeric + spaces only

**Retention**: Indefinite (aggregated, non-user-content)

---

### 3. SearchRun

**Purpose**: User-initiated Reddit pain point discovery session

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique run identifier |
| user_id | UUID | FK(User.id), NOT NULL | Owner of search run |
| status | ENUM | NOT NULL | 'pending', 'in_progress', 'completed', 'failed' |
| time_range | ENUM | NOT NULL | '24h', '7days', '30days', '90days', '1year', 'all' |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Run creation time |
| started_at | TIMESTAMP | NULL | Processing start time |
| completed_at | TIMESTAMP | NULL | Processing completion time |
| pain_points_count | INTEGER | DEFAULT 0 | Total pain points extracted |
| error_message | TEXT | NULL | Failure reason (if status=failed) |

**Indexes**:
- `idx_search_runs_user_id` on `user_id` (user dashboard queries)
- `idx_search_runs_status` on `status` (active run monitoring)

**Relationships**:
- `user_id` → User (CASCADE delete)
- M:N with Topic via `search_run_topics` join table

**State Transitions**:
```
pending → in_progress → completed
         └──────────────> failed
```

**Validation Rules**:
- Time range: Must be valid enum value
- Cannot modify `user_id` after creation

**Retention**: Indefinite (linked to user account)

---

### 4. Topic Assignment (Join Table)

**Purpose**: M:N relationship between SearchRun and Topic

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| search_run_id | UUID | FK(SearchRun.id), NOT NULL | Run identifier |
| topic_id | UUID | FK(Topic.id), NOT NULL | Topic identifier |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Assignment timestamp |

**Primary Key**: Composite (`search_run_id`, `topic_id`)

**Indexes**:
- `idx_run_topics_search_run` on `search_run_id`
- `idx_run_topics_topic` on `topic_id`

---

### 5. RedditPost (Temporary Cache)

**Purpose**: 48-hour cache of Reddit content for evidence linking

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Internal cache ID |
| reddit_id | VARCHAR(20) | UNIQUE, NOT NULL | Reddit post ID (e.g., "t3_abc123") |
| subreddit | VARCHAR(50) | NOT NULL | Source subreddit |
| author | VARCHAR(50) | NULL | Post author (deleted if account removed) |
| title | TEXT | NOT NULL | Post title |
| text | TEXT | NULL | Post body/selftext |
| url | VARCHAR(2048) | NOT NULL | Reddit permalink |
| score | INTEGER | NOT NULL | Upvote count at fetch time |
| comment_count | INTEGER | NOT NULL | Comment count at fetch time |
| created_utc | TIMESTAMP | NOT NULL | Reddit post creation timestamp |
| fetched_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Cache timestamp |
| expires_at | TIMESTAMP | NOT NULL | TTL expiry (fetched_at + 48h) |
| is_nsfw | BOOLEAN | DEFAULT FALSE | NSFW flag from Reddit |

**Storage**: Redis (primary), PostgreSQL (metadata backup for deletion sync)

**Indexes**:
- `idx_reddit_posts_reddit_id` on `reddit_id` (deletion sync lookups)
- `idx_reddit_posts_expires_at` on `expires_at` (TTL cleanup)

**Validation Rules**:
- `expires_at` MUST be `fetched_at + 48 hours`
- `reddit_id` format: `t3_[a-z0-9]{6,10}`

**Retention**: **48 hours max** (Redis TTL + daily deletion sync purge)

**⚠️ Compliance Note**: Per Reddit API ToS, this entity MUST be purged when:
1. `expires_at` reached (automatic Redis expiry)
2. Source post deleted on Reddit (daily deletion sync job)
3. Author account deleted (daily deletion sync job)

---

### 6. PainPoint (Derived Aggregate)

**Purpose**: Extracted problem/need with scoring (non-user-content)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique pain point identifier |
| search_run_id | UUID | FK(SearchRun.id), NOT NULL | Parent search run |
| extracted_text | TEXT | NOT NULL | Summarized pain point (NOT raw Reddit text) |
| relevance_score | DECIMAL(5,4) | NOT NULL | Composite score (0-1) |
| sentiment_score | DECIMAL(3,2) | NOT NULL | Sentiment polarity (-1 to 1) |
| source_reddit_post_ids | JSONB | NOT NULL | Array of RedditPost.reddit_id references |
| source_deleted | BOOLEAN | DEFAULT FALSE | Flag if source posts deleted |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Extraction timestamp |

**Indexes**:
- `idx_pain_points_search_run` on `search_run_id` (run results queries)
- `idx_pain_points_score` on `relevance_score DESC` (ranking)

**Relationships**:
- `search_run_id` → SearchRun (CASCADE delete)
- `source_reddit_post_ids` → RedditPost (soft reference, no FK)

**Validation Rules**:
- `relevance_score`: 0.0 to 1.0 range
- `sentiment_score`: -1.0 to 1.0 range
- `extracted_text`: Max 500 chars (summarized, not raw copy)
- `source_reddit_post_ids`: Valid JSON array of reddit_id strings

**Retention**: **Indefinite** (derived non-user-content, Reddit ToS compliant)

**Data Lineage**:
```
RedditPost (raw, 48h TTL)
  ↓ LLM extraction
PainPoint.extracted_text (derived, permanent)
```

When `source_deleted=true`, pain point remains but loses evidence links.

---

## Database Schema (PostgreSQL)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keyword VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    search_count INTEGER DEFAULT 0
);

CREATE TABLE search_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    time_range VARCHAR(20) NOT NULL CHECK (time_range IN ('24h', '7days', '30days', '90days', '1year', 'all')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    pain_points_count INTEGER DEFAULT 0,
    error_message TEXT
);

CREATE TABLE search_run_topics (
    search_run_id UUID NOT NULL REFERENCES search_runs(id) ON DELETE CASCADE,
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (search_run_id, topic_id)
);

CREATE TABLE reddit_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reddit_id VARCHAR(20) UNIQUE NOT NULL,
    subreddit VARCHAR(50) NOT NULL,
    author VARCHAR(50),
    title TEXT NOT NULL,
    text TEXT,
    url VARCHAR(2048) NOT NULL,
    score INTEGER NOT NULL,
    comment_count INTEGER NOT NULL,
    created_utc TIMESTAMP NOT NULL,
    fetched_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    is_nsfw BOOLEAN DEFAULT FALSE
);

CREATE TABLE pain_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    search_run_id UUID NOT NULL REFERENCES search_runs(id) ON DELETE CASCADE,
    extracted_text TEXT NOT NULL CHECK (char_length(extracted_text) <= 500),
    relevance_score DECIMAL(5,4) NOT NULL CHECK (relevance_score >= 0 AND relevance_score <= 1),
    sentiment_score DECIMAL(3,2) NOT NULL CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
    source_reddit_post_ids JSONB NOT NULL,
    source_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_topics_keyword ON topics(keyword);
CREATE INDEX idx_search_runs_user_id ON search_runs(user_id);
CREATE INDEX idx_search_runs_status ON search_runs(status);
CREATE INDEX idx_reddit_posts_reddit_id ON reddit_posts(reddit_id);
CREATE INDEX idx_reddit_posts_expires_at ON reddit_posts(expires_at);
CREATE INDEX idx_pain_points_search_run ON pain_points(search_run_id);
CREATE INDEX idx_pain_points_score ON pain_points(relevance_score DESC);
```

---

## Redis Cache Schema

**Key Pattern**: `reddit:post:{reddit_id}`

**Value**: JSON-serialized RedditPost model

**TTL**: 48 hours (172800 seconds)

**Example**:
```json
{
  "reddit_id": "t3_abc123",
  "subreddit": "AppIdeas",
  "author": "username",
  "title": "Need an app that tracks...",
  "text": "I've been looking for...",
  "url": "https://reddit.com/r/AppIdeas/comments/abc123",
  "score": 42,
  "comment_count": 15,
  "created_utc": "2025-10-04T10:30:00Z",
  "fetched_at": "2025-10-04T14:00:00Z",
  "is_nsfw": false
}
```

---

## Migration Strategy

1. **Phase 1**: Create User, Topic, SearchRun, RedditPost tables
2. **Phase 2**: Create PainPoint table with foreign keys
3. **Phase 3**: Add indexes (can run concurrently with Phase 2)
4. **Phase 4**: Create join table search_run_topics

**Alembic Migration**: `alembic revision -m "add_reddit_pain_point_discovery"`

---

**Status**: ✅ Complete - Ready for contract generation
