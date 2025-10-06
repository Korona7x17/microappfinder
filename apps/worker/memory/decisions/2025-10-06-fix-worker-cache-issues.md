# Session: Fix Worker Python Cache Issues

**Date**: 2025-10-06  
**Status**: ✅ Resolved

## Problem Summary
Multi-source search intermittently failed with `'source_platform' is an invalid keyword argument for PainPoint` despite the field existing in both model and database schema.

## Root Cause
Multiple RQ worker processes running simultaneously with stale Python bytecode cache (`__pycache__`). Workers cached different versions of the PainPoint model:
- Old workers: PainPoint without `source_platform` field
- New workers: PainPoint with `source_platform` field

When jobs distributed across workers, some succeeded (new worker) and some failed (old worker).

## Issues Fixed

### 1. AttributeError: 'selftext' and 'num_comments'
**Files**: 
- `apps/api/app/services/unified_search_service.py:67,71`
- `apps/api/app/services/deduplication_service.py:247,250`

**Changes**:
```python
# Before
"text": post.selftext
"comments": post.num_comments

# After
"text": post.text
"comment_count": post.comment_count
```

**Reason**: RedditPost model uses database field names, not PRAW library field names.

### 2. Intermittent 'source_platform' Invalid Keyword Error
**Cause**: Multiple workers with stale cached models competing for jobs

**Solution**:
1. Cleared all Python cache: `find . -type d -name __pycache__ -exec rm -rf {} +`
2. Killed all old worker processes: `ps aux | grep "Python worker.py" | awk '{print $2}' | xargs kill -9`
3. Started single fresh worker with `PYTHONDONTWRITEBYTECODE=1`

### 3. UI Text Update
**File**: `apps/web/src/components/search/RunStatus.tsx:154`

**Changes**:
```typescript
// Before
'Searching Reddit & HackerNews...'

// After (first iteration)
'Searching across communities...'

// After (final - user feedback)
'Searching and extracting pain points...'
```

**Reason**: User wanted generic text not tied to specific platforms.

## Solution Implementation

### Worker Management Protocol
**Always follow when restarting worker after code changes:**

1. **Clear Python cache**:
   ```bash
   find /Users/sutiteeraniti/dev/microappfinder -type d -name __pycache__ -exec rm -rf {} +
   ```

2. **Kill all existing workers**:
   ```bash
   ps aux | grep "Python worker.py" | awk '{print $2}' | xargs kill -9
   ```

3. **Start single worker with cache disabled**:
   ```bash
   cd /Users/sutiteeraniti/dev/microappfinder/apps/worker
   PYTHONDONTWRITEBYTECODE=1 \
   OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES \
   DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/microappfinder" \
   REDDIT_CLIENT_ID="VE-dSkrSanfWKmndGfivcA" \
   REDDIT_CLIENT_SECRET="McsEWvtlYnd3n8-tK7XMUzdAj_HCPw" \
   REDDIT_USER_AGENT="MicroAppFinder:v1.0 (by /u/Worldly_Post5439)" \
   PYTHONPATH=../api:$PYTHONPATH \
   python worker.py
   ```

4. **Verify single worker**:
   ```bash
   ps aux | grep "Python worker.py" | grep -v grep
   # Should show only ONE process
   ```

## Verification
- ✅ First search (7 day range): SUCCESS
- ✅ Second search (all time): SUCCESS  
- ✅ Subsequent searches: Consistent SUCCESS

## Key Takeaways

1. **Single Worker**: Always run exactly ONE worker process to avoid cache state conflicts
2. **Cache Hygiene**: Clear `__pycache__` after model schema changes
3. **PYTHONDONTWRITEBYTECODE**: Use this flag during development to prevent cache issues
4. **Field Name Consistency**: Always use database field names from SQLAlchemy models, not source library names

## Files Modified
- `apps/api/app/services/unified_search_service.py`
- `apps/api/app/services/deduplication_service.py`
- `apps/web/src/components/search/RunStatus.tsx`
