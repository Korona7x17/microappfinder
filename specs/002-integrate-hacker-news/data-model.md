# Data Model: Hacker News Integration

**Feature**: 002-integrate-hacker-news
**Date**: 2025-10-05
**Based on**: research.md findings

## Overview

This feature adds one new model (`HackerNewsItem`) and modifies two existing models (`PainPoint`, `SearchRun`) to support multi-source search aggregation.

---

## New Models

### HackerNewsItem

**Purpose**: 48-hour cache of Hacker News content (mirrors `RedditPost` pattern for consistency).

**Table Name**: `hackernews_items`

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL, default `gen_random_uuid()` | Internal cache ID |
| `hn_id` | String(20) | UNIQUE, NOT NULL, INDEX | HN item ID (e.g., "12345678") from Algolia `objectID` |
| `hn_type` | String(20) | NOT NULL | Item type: "story", "poll", "comment" |
| `author` | String(50) | NULL | HN username (null if account deleted) |
| `title` | Text | NOT NULL | Story title |
| `text` | Text | NULL | Story text (for Ask HN, Show HN with descriptions) |
| `url` | String(2048) | NULL | External URL (null for Ask HN, self posts) |
| `hn_url` | String(2048) | NOT NULL | HN permalink (https://news.ycombinator.com/item?id={hn_id}) |
| `points` | Integer | NOT NULL, CHECK >= 0 | HN score (upvotes) at fetch time |
| `comment_count` | Integer | NOT NULL, CHECK >= 0 | Number of comments at fetch time |
| `created_utc` | TIMESTAMP | NOT NULL | HN item creation timestamp (from `created_at_i`) |
| `fetched_at` | TIMESTAMP | NOT NULL, default NOW() | Cache timestamp |
| `expires_at` | TIMESTAMP | NOT NULL, INDEX | TTL expiry (fetched_at + 48h) |
| `tags` | JSONB | NULL | HN tags array (e.g., ["show_hn", "story"]) |

**Indexes**:
- PRIMARY KEY: `id`
- UNIQUE INDEX: `hn_id`
- INDEX: `expires_at` (for TTL cleanup jobs)
- INDEX: `created_utc` (for time-range queries)

**Constraints**:
- `CHECK (points >= 0)`
- `CHECK (comment_count >= 0)`
- `CHECK (expires_at = fetched_at + INTERVAL '48 hours')` ← enforced in application layer

**Relationships**:
- None (cache model, soft-referenced by `PainPoint.source_post_ids`)

**Lifecycle**:
1. **Fetch**: Hourly background job fetches from Algolia HN API
2. **Store**: Insert with `expires_at = fetched_at + 48h`
3. **Expire**: Daily cleanup job deletes rows where `expires_at < NOW()`
4. **Compliance**: 48h retention matches Reddit pattern (consistency)

**Migration**:
```python
# Alembic migration: add_hackernews_item_model.py
def upgrade():
    op.create_table(
        'hackernews_items',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('hn_id', sa.String(20), nullable=False),
        sa.Column('hn_type', sa.String(20), nullable=False),
        sa.Column('author', sa.String(50), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('url', sa.String(2048), nullable=True),
        sa.Column('hn_url', sa.String(2048), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('comment_count', sa.Integer(), nullable=False),
        sa.Column('created_utc', sa.TIMESTAMP(), nullable=False),
        sa.Column('fetched_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('tags', postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('hn_id'),
        sa.CheckConstraint('points >= 0', name='check_points_positive'),
        sa.CheckConstraint('comment_count >= 0', name='check_comments_positive')
    )
    op.create_index('ix_hackernews_items_hn_id', 'hackernews_items', ['hn_id'])
    op.create_index('ix_hackernews_items_expires_at', 'hackernews_items', ['expires_at'])
    op.create_index('ix_hackernews_items_created_utc', 'hackernews_items', ['created_utc'])
```

---

## Modified Models

### PainPoint

**Changes**: Add multi-source support to track origin platform.

**New Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `source_platform` | String(20) | NOT NULL, default 'reddit' | Origin platform: "reddit" or "hackernews" |

**Modified Fields**:

| Field | Old Type | New Type | Change |
|-------|----------|----------|--------|
| `source_reddit_post_ids` | JSONB | `source_post_ids` (JSONB) | **RENAME** to be platform-agnostic |

**Migration**:
```python
# Alembic migration: add_multi_source_support_to_pain_points.py
def upgrade():
    # Add source_platform column with default 'reddit' for existing rows
    op.add_column('pain_points', sa.Column('source_platform', sa.String(20), server_default='reddit', nullable=False))

    # Rename source_reddit_post_ids to source_post_ids
    op.alter_column('pain_points', 'source_reddit_post_ids', new_column_name='source_post_ids')

    # Update existing rows to set source_platform='reddit' explicitly
    op.execute("UPDATE pain_points SET source_platform = 'reddit' WHERE source_platform IS NULL")

def downgrade():
    op.alter_column('pain_points', 'source_post_ids', new_column_name='source_reddit_post_ids')
    op.drop_column('pain_points', 'source_platform')
```

**Backward Compatibility**:
- Existing `PainPoint` rows get `source_platform='reddit'` by default
- `source_post_ids` preserves existing Reddit IDs (same JSONB array structure)

---

### SearchRun

**Changes**: Add metadata to track which sources were queried.

**New Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `sources_queried` | JSONB | NOT NULL, default '["reddit"]' | Array of sources queried (e.g., ["reddit", "hackernews"]) |
| `hn_items_fetched` | Integer | NULL, CHECK >= 0 | Count of HN items fetched (null if HN not queried) |

**Migration**:
```python
# Alembic migration: add_source_tracking_to_search_runs.py
def upgrade():
    op.add_column('search_runs', sa.Column('sources_queried', postgresql.JSONB(), server_default='["reddit"]', nullable=False))
    op.add_column('search_runs', sa.Column('hn_items_fetched', sa.Integer(), nullable=True))
    op.create_check_constraint('check_hn_items_positive', 'search_runs', 'hn_items_fetched >= 0')

def downgrade():
    op.drop_constraint('check_hn_items_positive', 'search_runs')
    op.drop_column('search_runs', 'hn_items_fetched')
    op.drop_column('search_runs', 'sources_queried')
```

**Backward Compatibility**:
- Existing `SearchRun` rows get `sources_queried='["reddit"]'` by default
- `hn_items_fetched` is nullable (null for Reddit-only runs)

---

## Relationships

```
SearchRun 1──────N PainPoint
     │
     └─ sources_queried: ["reddit", "hackernews"]
                  │
                  ├─ PainPoint (source_platform='reddit')
                  │      └─ source_post_ids: ["t3_abc123", ...]
                  │                │
                  │                └─ RedditPost (soft reference)
                  │
                  └─ PainPoint (source_platform='hackernews')
                         └─ source_post_ids: ["12345678", ...]
                                    │
                                    └─ HackerNewsItem (soft reference)
```

**Notes**:
- `PainPoint.source_post_ids` is a **soft reference** (JSONB array, no FK constraint)
- This allows `RedditPost` and `HackerNewsItem` to be deleted (48h TTL) without cascading to `PainPoint`
- `PainPoint.extracted_text` is derived content (Reddit ToS compliant)

---

## Validation Rules

### HackerNewsItem
- `points >= 0`
- `comment_count >= 0`
- `expires_at = fetched_at + 48h` (application-enforced)
- `hn_id` must match pattern `^\d+$` (digits only)
- `hn_url` must be `https://news.ycombinator.com/item?id={hn_id}`

### PainPoint
- `source_platform` must be in ('reddit', 'hackernews')
- `source_post_ids` must be non-empty JSONB array
- `extracted_text` max 500 characters (existing constraint preserved)

### SearchRun
- `sources_queried` must be non-empty JSONB array
- `hn_items_fetched` nullable but if set, must be >= 0

---

## State Transitions

### HackerNewsItem Lifecycle

```
[Fetch from Algolia] → [Store in DB] → [Cached (48h)] → [Expired] → [Deleted]
                         ↓
                    expires_at = fetched_at + 48h
                         ↓
                    [Daily cleanup job removes expired rows]
```

### PainPoint Multi-Source Flow

```
[SearchRun created]
    ↓
[Background job fetches Reddit + HN in parallel]
    ↓
[Normalize both to unified schema]
    ↓
[Score using CompositeScorer (same formula)]
    ↓
[Deduplicate by URL (MVP) or semantic similarity (Phase 2)]
    ↓
[Top-ranked items → Create PainPoint records]
    ↓
    ├─ source_platform='reddit', source_post_ids=["t3_..."]
    └─ source_platform='hackernews', source_post_ids=["12345678"]
```

---

## Schema Diagram

```
┌─────────────────────┐
│   SearchRun         │
├─────────────────────┤
│ id                  │
│ user_id (FK)        │
│ status              │
│ sources_queried     │ ← NEW: ["reddit", "hackernews"]
│ hn_items_fetched    │ ← NEW: 42
└─────────────────────┘
         │ 1
         │
         │ N
         ▼
┌─────────────────────┐
│   PainPoint         │
├─────────────────────┤
│ id                  │
│ search_run_id (FK)  │
│ extracted_text      │
│ relevance_score     │
│ source_platform     │ ← NEW: 'reddit' | 'hackernews'
│ source_post_ids     │ ← RENAMED from source_reddit_post_ids
└─────────────────────┘
         │
         │ (soft reference via source_post_ids)
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────────────────┐    ┌─────────────────────┐
│   RedditPost        │    │  HackerNewsItem     │ ← NEW MODEL
├─────────────────────┤    ├─────────────────────┤
│ reddit_id           │    │ hn_id               │
│ title               │    │ title               │
│ score               │    │ points              │
│ comment_count       │    │ comment_count       │
│ created_utc         │    │ created_utc         │
│ expires_at          │    │ expires_at          │
└─────────────────────┘    └─────────────────────┘
   (48h TTL cache)          (48h TTL cache)
```

---

## Summary

**New Tables**: 1 (`hackernews_items`)
**Modified Tables**: 2 (`pain_points`, `search_runs`)
**Migrations**: 3 Alembic scripts
**Backward Compatibility**: ✅ All changes preserve existing data

**Next Steps**: Create API contracts and quickstart test scenarios.
