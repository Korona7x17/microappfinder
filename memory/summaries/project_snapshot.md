# Project Snapshot — MicroAppFinder

**Last Updated:** 2025-10-04
**Project:** MicroAppFinder - Micro app opportunity discovery system

## BRIEF_SUMMARY (2025-10-04)

C: Next.js 14 frontend; FastAPI backend; Docker-first deployment; Token-frugal LLM calls; PostgreSQL + Qdrant for data

D: Monorepo structure (apps/web, apps/api, apps/worker); RQ worker for async pipeline; crawl4ai for scraping; HDBSCAN clustering

Δ: Initial project scaffold complete; Memory system implemented (2025-10-04)

Q: Frontend dashboard implementation priority?; Export format preferences (MD/PDF/Notion)?

→: Implement core pipeline components; Set up frontend dashboard; Configure deployment pipeline

## Active Context

**Stack:**
- Frontend: Next.js 14, Tailwind, shadcn/ui, Clerk auth
- Backend: FastAPI, SQLAlchemy, Redis/RQ
- Worker: crawl4ai, scikit-learn, OpenAI/Claude
- Data: PostgreSQL, Qdrant vector DB
- Infra: Docker, Docker Compose

**Completed:**
- Project structure scaffolding
- Claude-memory system setup
- Documentation foundation

**In Progress:**
- [ ] Core pipeline (Reddit, HN, PH, IH sources)
- [ ] Signal normalization
- [ ] Clustering & scoring
- [ ] Brief generation
- [ ] Frontend dashboard

**Architecture Flow:**
Next.js Frontend → FastAPI Backend → Worker Pipeline → PostgreSQL/Qdrant + Redis Queue

## Reference Files
- Architecture: docs/microappfinder_system_architecture.md
- Pipeline: docs/microappfinder_pipeline_revised.md
- MVP Spec: docs/microappfinder_mvp_plus_spec.md
- Structure: PROJECT_STRUCTURE.md
