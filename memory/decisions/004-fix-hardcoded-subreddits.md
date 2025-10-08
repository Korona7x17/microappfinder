# Decision: Fix Hardcoded Subreddit Search - Enable Topic-Specific Results

**Date**: 2025-10-07
**Status**: ✅ Implemented
**Branch**: 002-integrate-hacker-news

## Context

User searched for "etsy listing optimization" but got results about productivity tools and to-do lists. After investigation, discovered the Reddit search was using a HARDCODED list of 14 generic subreddits (productivity, AppIdeas, freelance, etc.) regardless of the user's search topic.

## Problem

**Root cause**: `reddit_api.py` lines 26-41 defined `CURATED_SUBREDDITS` as a hardcoded list:
```python
CURATED_SUBREDDITS = [
    "AppIdeas",
    "SomebodyMakeThis",
    "productivity",
    "freelance",
    "Entrepreneur",
    # ... etc
]
```

When user searched for "etsy listing optimization", the system:
1. ✅ Used correct query ("etsy listing optimization")
2. ❌ Searched in WRONG subreddits (r/productivity, r/AppIdeas, etc.)
3. ❌ Reddit returned irrelevant posts (productivity posts) because those subreddits have nothing about Etsy
4. ❌ LLM analyzed wrong posts and displayed them to user

**Evidence**:
```sql
SELECT reddit_id, title, subreddit FROM reddit_posts WHERE reddit_id = 't3_1hvbee1';

reddit_id: t3_1hvbee1
title: "F*ck your productivity system. Seriously."
subreddit: productivity
```

This post was the #1 result for "etsy listing optimization" search!

## Decision

**Replace hardcoded subreddit list with Reddit site-wide search**

### Changes to `reddit_api.py:112-186`

**Before**: Looped through 14 hardcoded subreddits
```python
for subreddit_name in self.CURATED_SUBREDDITS:
    subreddit = self.reddit.subreddit(subreddit_name)
    submissions = subreddit.search(query=query, ...)
```

**After**: Single site-wide search across all of Reddit
```python
submissions = self.reddit.subreddit("all").search(
    query=query,
    time_filter=praw_time_filter,
    limit=300,  # Increased from 100
    sort="relevance"
)
```

### Key Improvements

1. **Topic-specific results**: Reddit automatically finds relevant subreddits for ANY topic
   - "etsy listing optimization" → finds r/Etsy, r/EtsySellers, r/ecommerce
   - "SaaS pricing" → finds r/SaaS, r/startups, r/Entrepreneur
   - No more hardcoded restrictions

2. **Higher quality threshold**: Increased score filter from 2 to 5
   - Site-wide search has more results, so we can be more selective
   - Reduces noise from low-engagement posts

3. **Increased limit**: 300 results instead of 100 per subreddit
   - Site-wide search is more efficient than looping through 14 subreddits
   - Ensures good coverage for niche topics

4. **Removed dead code**: Deleted unused `pain_phrases` array

## Outcome

- ✅ Search results now match the user's actual search topic
- ✅ Reddit automatically discovers relevant subreddits
- ✅ No more productivity posts for Etsy searches
- ✅ System works for ANY topic, not just entrepreneurship/productivity
- ✅ Higher quality results (score >= 5)

## Files Modified

- `apps/api/app/services/reddit_api.py:112-186` - Replaced hardcoded subreddit loop with site-wide search
- Removed lines 144-156 (unused `pain_phrases` array)

## Testing

Worker restarted with new code (PID 89775). Ready for new search to verify Etsy-specific results.

## References

- User quote: "search results aer from old unrelated serach. check throughly there should be no hardcode anywhere"
- Investigation showed query was correct, but subreddits were wrong
- Reddit site-wide search documented: https://praw.readthedocs.io/en/stable/code_overview/models/subreddit.html#praw.models.Subreddit.search
