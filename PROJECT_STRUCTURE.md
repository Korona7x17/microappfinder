# MicroAppFinder Project Structure

Complete overview of the scaffolded project.

## 📁 Directory Structure

```
microappfinder/
├── apps/
│   ├── web/                      # Next.js Frontend
│   │   ├── src/
│   │   │   ├── app/             # Next.js App Router
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── page.tsx
│   │   │   │   └── globals.css
│   │   │   ├── components/      # React components
│   │   │   └── lib/             # Utilities
│   │   │       ├── api.ts
│   │   │       └── utils.ts
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── next.config.js
│   │   ├── tailwind.config.ts
│   │   ├── postcss.config.js
│   │   ├── Dockerfile
│   │   └── README.md
│   │
│   ├── api/                      # FastAPI Backend
│   │   ├── app/
│   │   │   ├── main.py          # FastAPI entry point
│   │   │   ├── core/
│   │   │   │   ├── config.py    # Settings
│   │   │   │   └── database.py  # DB connection
│   │   │   ├── models/          # SQLAlchemy models
│   │   │   │   ├── __init__.py
│   │   │   │   ├── run.py
│   │   │   │   ├── signal.py
│   │   │   │   ├── cluster.py
│   │   │   │   └── brief.py
│   │   │   ├── schemas/         # Pydantic schemas
│   │   │   │   └── run.py
│   │   │   ├── routers/         # API endpoints
│   │   │   │   ├── runs.py
│   │   │   │   ├── signals.py
│   │   │   │   ├── clusters.py
│   │   │   │   ├── briefs.py
│   │   │   │   └── exports.py
│   │   │   ├── providers/       # Data providers
│   │   │   │   ├── base.py
│   │   │   │   ├── reddit.py
│   │   │   │   ├── hackernews.py
│   │   │   │   ├── producthunt.py
│   │   │   │   └── indiehackers.py
│   │   │   └── services/        # Business logic
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── README.md
│   │
│   └── worker/                   # Background Worker
│       ├── worker/
│       │   ├── main.py          # Worker entry point
│       │   ├── config.py        # Settings
│       │   ├── pipeline/        # Pipeline logic
│       │   │   └── runner.py
│       │   └── tasks/           # RQ tasks
│       │       ├── __init__.py
│       │       └── run_pipeline.py
│       ├── requirements.txt
│       ├── Dockerfile
│       └── README.md
│
├── packages/                     # Shared Packages
│   ├── types/                   # TypeScript types
│   │   ├── index.ts
│   │   └── package.json
│   └── schemas/                 # Python schemas
│       └── signals.py
│
├── infra/                       # Infrastructure
│   ├── migrations/              # Database migrations
│   │   ├── versions/
│   │   │   └── 001_initial_schema.py
│   │   ├── alembic.ini
│   │   ├── env.py
│   │   └── script.py.mako
│   └── docker/                  # Docker configs
│       └── nginx.conf
│
├── docs/                        # Documentation
│   ├── microappfinder_system_architecture.md
│   ├── microappfinder_pipeline_revised.md
│   ├── microappfinder_mvp_plus_spec.md
│   └── micro_apps_research_assistant.md
│
├── docker-compose.yml           # Docker orchestration
├── Makefile                     # Build commands
├── package.json                 # Root package.json (workspaces)
├── .gitignore
├── .dockerignore
├── .prettierrc
├── .editorconfig
├── README.md
├── CONTRIBUTING.md
└── PROJECT_STRUCTURE.md
```

## 🎯 Key Components

### Frontend (apps/web)
- **Framework**: Next.js 14 with App Router
- **Styling**: Tailwind CSS + shadcn/ui
- **Auth**: Clerk (or Supabase)
- **Data Fetching**: SWR
- **API Client**: Axios

### Backend (apps/api)
- **Framework**: FastAPI
- **Database**: PostgreSQL (SQLAlchemy ORM)
- **Vector DB**: Qdrant (optional)
- **Queue**: Redis + RQ
- **LLM**: OpenAI/Anthropic APIs
- **Providers**: Reddit, HN, Product Hunt, Indie Hackers

### Worker (apps/worker)
- **Queue**: RQ (Redis Queue)
- **Pipeline**: Multi-step processing
  1. Provider Search
  2. Fetch & Parse
  3. Normalize to Signals
  4. Deduplicate
  5. Cluster
  6. Score
  7. Generate Briefs

### Shared
- **Types**: Shared TypeScript types
- **Schemas**: Shared Python Pydantic schemas
- **Migrations**: Alembic migrations
- **Docker**: Multi-service orchestration

## 🚀 Getting Started

### Quick Start (Docker)
```bash
# Start all services
docker-compose up -d

# Run migrations
cd infra/migrations && alembic upgrade head

# View logs
docker-compose logs -f
```

### Local Development
```bash
# Frontend
cd apps/web && npm install && npm run dev

# Backend
cd apps/api && pip install -r requirements.txt && uvicorn app.main:app --reload

# Worker
cd apps/worker && pip install -r requirements.txt && python -m worker.main
```

## 📊 Services

| Service  | Port | Description              |
|----------|------|--------------------------|
| Frontend | 3000 | Next.js web app          |
| API      | 8000 | FastAPI backend          |
| Worker   | -    | Background processing    |
| Postgres | 5432 | Database                 |
| Redis    | 6379 | Queue & cache           |
| Qdrant   | 6333 | Vector database (optional)|

## 🔧 Configuration

All services use environment variables. See `.env.example` files in each app directory.

### Required Variables
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `OPENAI_API_KEY` - For LLM operations
- `REDDIT_CLIENT_ID` - Reddit API
- `REDDIT_CLIENT_SECRET` - Reddit API

## 📝 Next Steps

1. **Fill in environment variables** in each app
2. **Run migrations** to create database schema
3. **Implement provider logic** in `apps/api/app/providers/`
4. **Build frontend components** in `apps/web/src/components/`
5. **Test the pipeline** end-to-end

## 🧪 Testing

```bash
# API tests
cd apps/api && pytest

# Frontend tests
cd apps/web && npm test
```

## 📚 Additional Documentation

See the `docs/` directory for detailed specifications:
- System Architecture
- Data Pipeline
- MVP+ Specification
- Research Assistant Guidelines

---

**Status**: ✅ Fully Scaffolded & Ready for Development
