# Quickstart: Reddit Pain Point Discovery

**Feature**: Reddit Pain Point Discovery
**Purpose**: End-to-end validation of search flow, authentication, and privacy enforcement
**Estimated Time**: 5-10 minutes

## Prerequisites

- Docker Compose running (`docker-compose up`)
- API available at `http://localhost:8000`
- Frontend available at `http://localhost:3000`
- Redis and PostgreSQL initialized

## Test Scenario: Complete User Journey

### Step 1: Register New User

**Request**:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123"
  }'
```

**Expected Response** (201 Created):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "test@example.com",
    "created_at": "2025-10-04T10:30:00Z"
  }
}
```

**Validation**:
- ✅ Status code 201
- ✅ JWT token received
- ✅ User ID is valid UUID
- ✅ `Set-Cookie` header present with `access_token` (httponly)

---

### Step 2: Login with Credentials

**Request**:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123"
  }'
```

**Expected Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "test@example.com",
    "created_at": "2025-10-04T10:30:00Z"
  }
}
```

**Validation**:
- ✅ Status code 200
- ✅ Same user ID as registration
- ✅ Cookie saved to `cookies.txt`

---

### Step 3: Create Reddit Search Run

**Request**:
```bash
curl -X POST http://localhost:8000/api/reddit/search \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "topics": ["productivity tools", "automation"],
    "time_range": "7days"
  }'
```

**Expected Response** (201 Created):
```json
{
  "run_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "pending",
  "created_at": "2025-10-04T10:35:00Z"
}
```

**Validation**:
- ✅ Status code 201
- ✅ Run ID is valid UUID
- ✅ Status is "pending"

**Save run_id for next steps**:
```bash
RUN_ID="a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

---

### Step 4: Poll Search Run Status

**Request** (repeat every 2 seconds until status = "completed"):
```bash
curl http://localhost:8000/api/reddit/runs/$RUN_ID \
  -b cookies.txt
```

**Expected Status Progression**:

**Initial** (pending):
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "topics": ["productivity tools", "automation"],
  "time_range": "7days",
  "pain_points_count": 0,
  "created_at": "2025-10-04T10:35:00Z",
  "started_at": null,
  "completed_at": null
}
```

**In Progress**:
```json
{
  "status": "in_progress",
  "started_at": "2025-10-04T10:35:02Z",
  "pain_points_count": 23
}
```

**Completed** (final):
```json
{
  "status": "completed",
  "completed_at": "2025-10-04T10:35:25Z",
  "pain_points_count": 147
}
```

**Validation**:
- ✅ Status transitions: pending → in_progress → completed
- ✅ `started_at` populated when in_progress
- ✅ `completed_at` populated when completed
- ✅ `pain_points_count` increases during processing
- ✅ Total time < 30 seconds (performance SLA)

---

### Step 5: Fetch Pain Points (Paginated)

**Request** (page 1):
```bash
curl "http://localhost:8000/api/reddit/runs/$RUN_ID/pain-points?page=1&limit=50" \
  -b cookies.txt
```

**Expected Response** (200 OK):
```json
{
  "items": [
    {
      "id": "pain-001",
      "extracted_text": "Freelancers need simple time-tracking without complex project management bloat",
      "relevance_score": 0.8734,
      "sentiment_score": -0.42,
      "source_reddit_posts": [
        {
          "reddit_id": "t3_abc123",
          "subreddit": "freelance",
          "title": "What time tracker do you use?",
          "url": "https://reddit.com/r/freelance/comments/abc123",
          "deleted": false
        }
      ],
      "created_at": "2025-10-04T10:35:15Z"
    }
    // ... 49 more items
  ],
  "total": 147,
  "page": 1,
  "pages": 3,
  "per_page": 50
}
```

**Validation**:
- ✅ Status code 200
- ✅ Exactly 50 items returned (page 1)
- ✅ Pain points sorted by `relevance_score` DESC
- ✅ `sentiment_score` between -1 and 1
- ✅ `source_reddit_posts` array not empty
- ✅ Total pages calculated correctly (147 / 50 = 3)

**Request page 2**:
```bash
curl "http://localhost:8000/api/reddit/runs/$RUN_ID/pain-points?page=2&limit=50" \
  -b cookies.txt
```

**Validation**:
- ✅ Different items than page 1
- ✅ Scores continue descending from page 1

---

### Step 6: Test User Privacy (Unauthorized Access)

**Register Second User**:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -c cookies_user2.txt \
  -d '{
    "email": "user2@example.com",
    "password": "SecurePass456"
  }'
```

**Attempt to Access User 1's Run**:
```bash
curl http://localhost:8000/api/reddit/runs/$RUN_ID \
  -b cookies_user2.txt
```

**Expected Response** (403 Forbidden):
```json
{
  "error": "Access denied",
  "detail": "You do not have permission to access this search run"
}
```

**Validation**:
- ✅ Status code 403
- ✅ User 2 cannot access User 1's run
- ✅ Privacy enforcement working

---

### Step 7: Test Empty Results Fallback

**Create Search with Obscure Topic**:
```bash
curl -X POST http://localhost:8000/api/reddit/search \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "topics": ["xyzabc123nonexistent"],
    "time_range": "24h"
  }'
```

**Poll Until Completed** (assume 0 results):
```bash
EMPTY_RUN_ID="..."  # from response
curl http://localhost:8000/api/reddit/runs/$EMPTY_RUN_ID \
  -b cookies.txt
```

**Response**:
```json
{
  "status": "completed",
  "pain_points_count": 0
}
```

**Fetch Pain Points**:
```bash
curl "http://localhost:8000/api/reddit/runs/$EMPTY_RUN_ID/pain-points?page=1&limit=50" \
  -b cookies.txt
```

**Expected Fallback Response**:
```json
{
  "items": [
    {
      "id": "fallback-001",
      "extracted_text": "Popular pain point from last 7 days (any topic)",
      "relevance_score": 0.9120,
      ...
    }
    // ... up to 20 fallback items
  ],
  "total": 20,
  "page": 1,
  "pages": 1,
  "per_page": 50,
  "is_fallback": true
}
```

**Validation**:
- ✅ Returns 20 recent pain points (any topic)
- ✅ `is_fallback: true` flag present
- ✅ Pain points from last 7 days
- ✅ User still gets value despite zero direct results

---

### Step 8: View User Dashboard

**Request**:
```bash
curl http://localhost:8000/api/reddit/dashboard \
  -b cookies.txt
```

**Expected Response**:
```json
{
  "total_searches": 2,
  "recent_runs": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "status": "completed",
      "topics": ["productivity tools", "automation"],
      "pain_points_count": 147,
      "created_at": "2025-10-04T10:35:00Z"
    },
    {
      "id": "...",
      "status": "completed",
      "topics": ["xyzabc123nonexistent"],
      "pain_points_count": 0,
      "created_at": "2025-10-04T10:40:00Z"
    }
  ],
  "recent_pain_points": [
    // Top 20 pain points from all user's searches
  ]
}
```

**Validation**:
- ✅ Shows only User 1's searches (not User 2's)
- ✅ `total_searches` = 2
- ✅ `recent_runs` sorted by `created_at` DESC

---

## Success Criteria

All validations must pass:

- [x] User registration creates account with JWT
- [x] Login authenticates and sets httponly cookie
- [x] Search run created and queued successfully
- [x] Status transitions correctly (pending → in_progress → completed)
- [x] Pain points extracted and ranked within 30 seconds
- [x] Pagination works correctly (50 items/page)
- [x] User 2 cannot access User 1's results (403)
- [x] Empty results return fallback pain points
- [x] Dashboard shows only user's own searches

## Cleanup

```bash
# Delete test users (optional)
curl -X DELETE http://localhost:8000/api/auth/me \
  -b cookies.txt

curl -X DELETE http://localhost:8000/api/auth/me \
  -b cookies_user2.txt

# Or reset database
docker-compose down -v
docker-compose up -d
```

---

**Status**: ✅ Quickstart complete - Feature validated end-to-end
