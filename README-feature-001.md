# Reddit Pain Point Discovery - Feature 001

## Overview

Complete implementation of Reddit pain point discovery feature with:
- Reddit API integration (PRAW)
- Pain point extraction and scoring
- User authentication with JWT
- Background job processing with RQ
- 48-hour cache compliance (Reddit ToS)

## Quick Start

### 1. Prerequisites

```bash
# Python 3.10+
python --version

# PostgreSQL
psql --version

# Redis
redis-cli --version

# Node.js 18+
node --version
```

### 2. Setup Database

```bash
# Run database migrations
./scripts/setup-database.sh
```

### 3. Configure Environment

```bash
# API (.env)
cp apps/api/.env.example apps/api/.env

# Required variables:
# - REDDIT_CLIENT_ID
# - REDDIT_CLIENT_SECRET
# - REDDIT_USER_AGENT
# - JWT_SECRET_KEY
# - DATABASE_URL
# - REDIS_HOST
```

### 4. Install Dependencies

```bash
# API
cd apps/api
pip install -r requirements.txt

# Worker
cd ../worker
pip install -r requirements.txt

# Web
cd ../web
npm install
```

### 5. Run Services

```bash
# Terminal 1: API
cd apps/api
uvicorn app.main:app --reload

# Terminal 2: Worker
cd apps/worker
python worker.py

# Terminal 3: Scheduler (for deletion sync)
cd apps/worker
python worker.py scheduler

# Terminal 4: Web
cd apps/web
npm run dev
```

### 6. Validate Installation

```bash
# Run quickstart validation
./scripts/quickstart-validation.sh

# Run performance tests
./scripts/performance-validation.sh
```

## Testing

### Unit Tests

```bash
# Worker pipeline tests
cd apps/worker
pytest tests/unit/test_scorer.py -v
pytest tests/unit/test_filter.py -v

# API tests (TDD - will fail until implementation)
cd apps/api
pytest tests/contract/ -v
pytest tests/integration/ -v
```

### Test Coverage

- **T004-T010**: Contract tests (7 endpoints)
- **T011-T014**: Integration tests (4 flows)
- **T047**: Scorer unit tests (16 tests)
- **T048**: Filter unit tests (15 tests)

## Architecture

### Backend (FastAPI)
- **Models**: User, Topic, SearchRun, RedditPost, PainPoint
- **Services**: AuthService, RedditAPIClient, DeletionSyncService
- **Endpoints**: `/api/auth/*`, `/api/reddit/*`
- **Middleware**: JWT auth, ownership verification

### Worker (RQ)
- **Tasks**: Reddit search processing
- **Pipeline**: Filter → Extract → Score
- **Jobs**: Daily deletion sync (2:00 AM UTC)

### Frontend (Next.js)
- **Pages**: Login, Register, Dashboard
- **Components**: SearchForm, RunStatus, PainPointsList
- **API Client**: Fetch with cookie auth

### Database (PostgreSQL)
- 6 tables with 8 indexes
- CHECK constraints for data validation
- CASCADE deletes for privacy

### Cache (Redis)
- 48-hour TTL for Reddit posts
- Automatic expiration
- Deletion sync for compliance

## Key Features

### Authentication (T027)
- JWT with httponly cookies
- bcrypt password hashing (cost 12)
- 15-min access token, 7-day refresh token

### Reddit Integration (T025)
- PRAW OAuth2 client
- 14 curated subreddits
- Rate limiting (<60 req/min)
- NSFW/spam filtering

### Pain Point Extraction (T032)
- 8 regex patterns for pain detection
- Max 500 char summaries
- Deduplication via word overlap

### Composite Scoring (T033)
- Formula: `0.3×upvotes + 0.25×comments + 0.25×recency + 0.2×sentiment`
- TextBlob sentiment analysis
- Normalization: upvotes (1000), comments (500), recency (90 days)

### Compliance (T026, T035, T044)
- 48-hour cache TTL
- Daily deletion sync job
- `source_deleted` flag tracking
- Reddit ToS compliant

## Performance Requirements (NFR-001)

- ✓ API health check: <100ms
- ✓ Dashboard load: <1s
- ✓ Search completion: <30s

## File Structure

```
apps/
├── api/
│   ├── app/
│   │   ├── models/          # T015-T020
│   │   ├── schemas/         # T021-T023
│   │   ├── services/        # T024-T026
│   │   ├── routers/         # T027-T028
│   │   ├── core/            # T029-T030
│   │   └── config/          # T044
│   └── tests/
│       ├── contract/        # T004-T010
│       └── integration/     # T011-T014
├── worker/
│   ├── worker/
│   │   ├── tasks/           # T031
│   │   ├── pipeline/        # T032-T034
│   │   └── jobs/            # T035
│   └── tests/unit/          # T047-T048
└── web/
    └── src/
        ├── app/             # T036-T037, T041
        ├── components/      # T038-T040
        └── lib/             # T042-T043

infra/
└── migrations/
    └── versions/            # T003

scripts/
├── setup-database.sh        # T046
├── quickstart-validation.sh # T049
└── performance-validation.sh# T050
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Get profile

### Reddit Search
- `POST /api/reddit/search` - Create search
- `GET /api/reddit/search/{id}` - Get status
- `GET /api/reddit/search/{id}/results` - Get results (paginated)
- `GET /api/reddit/recent` - Get recent pain points (fallback)
- `GET /api/reddit/dashboard` - Get user dashboard

## Environment Variables

### Required
- `REDDIT_CLIENT_ID` - Reddit OAuth2 client ID
- `REDDIT_CLIENT_SECRET` - Reddit OAuth2 client secret
- `REDDIT_USER_AGENT` - Reddit API user agent
- `JWT_SECRET_KEY` - Secret for JWT signing
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_HOST` - Redis host

### Optional
- `REDIS_PORT` - Redis port (default: 6379)
- `REDIS_DB` - Redis database (default: 0)
- `API_BASE_URL` - API URL (default: http://localhost:8000)

## Reddit ToS Compliance

1. **48-hour cache**: All Reddit content expires after 48 hours
2. **Deletion sync**: Daily job checks for deleted posts
3. **Derived content**: Pain points are summarized (not raw copies)
4. **Source tracking**: `source_deleted` flag when source removed

## Next Steps

1. Run migrations: `./scripts/setup-database.sh`
2. Configure Reddit credentials
3. Start all services
4. Run validation: `./scripts/quickstart-validation.sh`
5. Access dashboard: http://localhost:3000/dashboard

## Support

For issues or questions:
- GitHub Issues: https://github.com/your-org/microappfinder/issues
- Docs: specs/001-reddit-pain-point/
