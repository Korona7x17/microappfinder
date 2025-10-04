# MicroAppFinder 🔍

A lean, fast-to-ship system for discovering unmet demand for **micro apps**, clustering & scoring opportunities, and outputting shippable briefs.

## 🎯 What It Does

1. **Discovers Signals** - Scans Reddit, Hacker News, Product Hunt, and Indie Hackers for unmet demand
2. **Normalizes Data** - Extracts pain points, jobs-to-be-done, and demand signals
3. **Clusters Opportunities** - Groups similar signals into themes
4. **Scores & Ranks** - Evaluates opportunity strength with weighted rubric
5. **Generates Briefs** - Creates actionable micro-app briefs with proof

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Next.js    │────▶│   FastAPI    │────▶│   Worker    │
│  Frontend   │     │   Backend    │     │  Pipeline   │
└─────────────┘     └──────────────┘     └─────────────┘
                           │                     │
                           ▼                     ▼
                    ┌──────────────┐     ┌─────────────┐
                    │  PostgreSQL  │     │    Redis    │
                    │   + Qdrant   │     │    Queue    │
                    └──────────────┘     └─────────────┘
```

## 📁 Project Structure

```
microappfinder/
├── apps/
│   ├── web/              # Next.js frontend
│   ├── api/              # FastAPI backend
│   └── worker/           # Background worker
├── packages/
│   ├── types/            # Shared TypeScript types
│   └── schemas/          # Shared Python schemas
├── infra/
│   ├── migrations/       # Database migrations
│   └── docker/           # Docker configs
├── docs/                 # Documentation
└── docker-compose.yml    # Docker orchestration
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local frontend dev)
- Python 3.11+ (for local backend dev)

### 1. Clone & Setup

```bash
git clone <repo>
cd microappfinder

# Copy environment files
cp apps/api/.env.example apps/api/.env
cp apps/worker/.env.example apps/worker/.env
cp apps/web/.env.example apps/web/.env.local
```

### 2. Start Services

```bash
# Start all services with Docker
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

Services will be available at:
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 3. Run Migrations

```bash
# From project root
cd infra/migrations
alembic upgrade head
```

## 💻 Development

### Frontend (Next.js)

```bash
cd apps/web
npm install
npm run dev
```

### Backend (FastAPI)

```bash
cd apps/api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Worker

```bash
cd apps/worker
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m worker.main
```

## 🔑 Environment Variables

### API & Worker

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/microappfinder
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-...
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
```

### Frontend

```env
API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...
CLERK_SECRET_KEY=...
```

## 📊 Data Flow

1. User creates topics → Start run
2. API creates run record → Enqueue job
3. Worker pipeline:
   - Provider search → URLs
   - Fetch via crawl4ai
   - Normalize → Signals
   - Cluster signals
   - Score clusters
   - Generate briefs
4. Frontend displays report

## 🛠️ Tech Stack

- **Frontend**: Next.js 14, Tailwind CSS, shadcn/ui, Clerk
- **Backend**: FastAPI, SQLAlchemy, Redis
- **Worker**: RQ, crawl4ai, scikit-learn
- **Database**: PostgreSQL, Qdrant (vector DB)
- **LLM**: OpenAI GPT-4, Claude
- **Infra**: Docker, Docker Compose

## 📝 API Endpoints

- `POST /api/runs` - Create new analysis run
- `GET /api/runs/{id}` - Get run status
- `GET /api/runs/{id}/report` - Get full report
- `GET /api/signals/{run_id}` - Get signals
- `GET /api/clusters/{run_id}` - Get clusters
- `GET /api/briefs/{run_id}` - Get briefs
- `POST /api/exports/{id}` - Export report

## 🧪 Testing

```bash
# API tests
cd apps/api
pytest

# Frontend tests
cd apps/web
npm test
```

## 📚 Documentation

See the `docs/` directory for detailed documentation:
- [System Architecture](docs/microappfinder_system_architecture.md)
- [Pipeline Spec](docs/microappfinder_pipeline_revised.md)
- [MVP+ Spec](docs/microappfinder_mvp_plus_spec.md)

## 🚢 Deployment

### Production (Docker)

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Hosting Options

- **Frontend**: Vercel
- **Backend + Worker**: Hetzner VPS, Railway, Render
- **Database**: Supabase, Neon
- **Redis**: Upstash, Redis Cloud

## 📈 Roadmap

- [x] Core pipeline (Reddit, HN, PH, IH)
- [x] Signal normalization
- [x] Clustering & scoring
- [x] Brief generation
- [ ] Frontend dashboard
- [ ] Export to MD/PDF
- [ ] Notion integration
- [ ] Topic monitors
- [ ] Team collaboration

## 📄 License

MIT

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

---

Built with ❤️ for micro app builders
