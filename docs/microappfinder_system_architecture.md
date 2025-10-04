# MicroAppFinder — System Architecture (MVP → V1)

A lean, fast-to-ship system for discovering unmet demand for **micro apps**, clustering & scoring opportunities, and outputting shippable briefs. Includes **crawl4ai** ingestion.

---

## 0) Core Promise
**One job:** scan Reddit / IdeaBrowser / TikTok for unmet demand → **normalize** → **cluster** → **score** → output **3 shippable micro‑app briefs** + links + proof.

---

## 1) High-Level Architecture

```
[Next.js Frontend] ──▶ [Next.js API Gateway] ──▶ [FastAPI Backend + Workers]
                                 │                           │
                                 │                           ├─▶ [Ingestion: crawl4ai + fallbacks]
                                 │                           ├─▶ [Normalizer → Signals]
                                 │                           ├─▶ [Scoring + Clustering]
                                 │                           ├─▶ [Brief Generator (LLM)]
                                 │                           └─▶ [Exports (.md/.pdf)]
                                 │
                                 └─▶ [Billing Webhooks]
                                                         
[Postgres (Supabase/Neon)] ◀────── [FastAPI] ───────▶ [Redis Queue] ───────▶ [Workers]
[Object Store (S3/R2)]  ◀─────────┘
[Qdrant Vector DB]* (optional V1)
```

**Frontend (Next.js)**  
- App Router, Tailwind + shadcn/ui  
- Auth (Clerk or Supabase Auth)  
- Pages: Dashboard, Topics, Runs, Reports, Settings, Billing  

**API Gateway (Next.js API routes)**  
- Thin layer that proxies to FastAPI services  
- Webhooks: billing, run-complete

**Backend (FastAPI + Workers)**  
- Ingestors (Reddit, IdeaBrowser, TikTok) using **crawl4ai** (default) with fallback providers  
- Normalizer → common **Signals** schema  
- Scoring + clustering  
- Brief generation (LLM)  
- Exporters (.md, .pdf)

**Data Layer**  
- **Postgres**: users, runs, signals, clusters, briefs  
- **Qdrant** (optional): semantic dedupe & similar-pain search  
- **Object store** (R2/S3): exported reports

**Infra**  
- Hetzner VPS (dockerized): api, worker, redis, qdrant  
- Vercel (frontend) or single VPS behind Caddy/Nginx  
- Observability: Sentry, Uptime Kuma, simple logs

---

## 2) Data Flow (MVP)

```
User → Create Topics → Start Run
→ API creates run (status=pending)
→ Enqueue job(run_id) in Redis
→ Worker pipeline:
   1) Provider Search → list of URLs
   2) Fetch via crawl4ai (HTML→clean text + meta)
   3) Normalize → Signals[]
   4) (Optional) Vectorize for dedupe/similarity
   5) Cluster (algo or LLM labels)
   6) Score clusters (weighted rubric)
   7) Draft 3 Micro‑App Briefs (LLM)
   8) Persist + mark run done + emit event
→ Frontend polls/subscribes → Show Report → Export
```

---

## 3) Providers (with crawl4ai)

**Default fetcher:** `crawl4ai` (JS disabled by default for speed).  
**Fallbacks:** Firecrawl/SerpAPI/Apify **only** on repeated failure or heavy JS pages.

**Sources:**
- **Reddit:** Google/Bing `site:reddit.com` queries → open target threads → parse visible text.  
- **IdeaBrowser:** Public idea pages → parse titles, descriptions, comments.  
- **TikTok:** `site:tiktok.com` result pages → open public video pages → capture caption + like count + a light comment summary.

**Provider Interface (Python):**
```python
class Provider(Protocol):
    def search(self, topics: list[str], limit:int=30) -> list[str]: ...  # return URLs
    def hydrate(self, url: str) -> RawItem: ...                          # fetch + basic parse
```

**Fetcher using crawl4ai (sync wrapper):**
```python
# ingestion/fetcher.py
import asyncio
from crawl4ai import WebCrawler

async def _afetch(url: str, js=False, timeout=20):
    async with WebCrawler() as crawler:
        res = await crawler.arun(url, js=js, timeout=timeout)
        return {"status": res.status, "html": getattr(res, "html", None), "text": getattr(res, "text", None)}

def fetch(url: str, js=False, timeout=20):
    return asyncio.run(_afetch(url, js=js, timeout=timeout))
```

**Caching & Hygiene:**
- Redis URL cache (48h) by URL hash before fetch.  
- Per‑domain throttle `< 1 rps` with jitter.  
- Respect robots/ToS.  
- JS rendering **off** unless required.

---

## 4) Normalized Schema (Postgres)

**signals**
```
id PK, run_id FK, source ENUM('reddit','ideabrowser','tiktok','web'),
audience_guess TEXT, job_to_be_done TEXT, pain_snippet TEXT,
frequency ENUM('daily','weekly','irregular'),
evidence_pull BOOLEAN, workaround TEXT, wtp_hint ENUM('none','low','medium','high'),
url TEXT, metrics JSONB, micro_fit BOOLEAN DEFAULT true,
created_at TIMESTAMPTZ DEFAULT now()
```

**clusters**
```
id PK, run_id FK, theme TEXT, audiences TEXT[],
signals_count INT, pain_intensity_avg NUMERIC,
frequency_mode TEXT, pull_evidence TEXT, gap_summary TEXT,
score_int INT, created_at TIMESTAMPTZ DEFAULT now()
```

**briefs**
```
id PK, run_id FK, cluster_id FK,
name TEXT, who_hurts TEXT, job_to_be_done TEXT,
killer_feature TEXT, scope JSONB, mechanics JSONB,
success_metric TEXT, pricing_hint TEXT,
risks TEXT, validation_plan JSONB,
created_at TIMESTAMPTZ DEFAULT now()
```

**runs**
```
id PK, user_id FK, topic_tags TEXT[], status ENUM('pending','running','done','failed'),
started_at TIMESTAMPTZ, finished_at TIMESTAMPTZ,
counters JSONB, cost_estimate_cents INT
```

---

## 5) Scoring (Deterministic + Simple)

Weights (0–100 total):
- Pain (0–5, w=.25)  
- Frequency (0–5, w=.15)  
- Urgency (0–5, w=.10)  
- WTP (0–5, w=.15)  
- Audience size (0–5, w=.10)  
- Pull evidence (0–5, w=.15)  
- Competitive gap & simplicity (0–5, w=.10)

**Fit Gate (hard):**
- 1 core job, ≤ 3 screens, build < 1 week, ≤ 15s input, $0 infra.

---

## 6) LLM Layer (Provider-Agnostic)

**Abstraction**
```python
class LLM:
    def summarize_signal(self, raw_text:str)->dict: ...
    def cluster_labels(self, sample_texts:list[str])->list[str]: ...
    def craft_brief(self, cluster:dict)->dict: ...
```

- **Models:** Use a cheap model for summaries (GPT‑4o mini / Claude Haiku). Use a higher‑quality model for the **3 briefs only** (GPT‑4o / Claude Sonnet).  
- **Token control:** batch summarize (10–20 signals per call), strict JSON output, short prompts.

**Key Prompts:**  
- Summarize & extract JTBD → JSON only.  
- Cluster naming → 3–5 labels + reasons.  
- Brief writer → fixed template, scope police (no bloat).

---

## 7) API Endpoints

- `POST /api/run` → `{topics: string[], depth: 'quick'|'standard'}` → returns `run_id`  
- `GET /api/run/:id` → status + basic counts  
- `GET /api/run/:id/report` → `{signals[], clusters[], briefs[]}`  
- `POST /api/export/:id` → signed URL for `.md` / `.pdf`  
- Webhooks: `/api/billing/*`

---

## 8) Frontend UX (Fast to Build)

- **Top section:** 3 Brief cards (score, build time, proof links).  
- **Tabs:**  
  - **Signals**: table with source, audience, pain, freq, link.  
  - **Clusters**: badges + scores + supporting signals count.  
  - **Briefs**: copy‑ready MD with export buttons.  
- **Run panel:** pick topics, depth; show ETA & credit cost.  
- **Exports:** `.md`, `.pdf`, “Send to Notion”.

---

## 9) Stack Choices

- **FE:** Next.js (Vercel), Tailwind, shadcn/ui  
- **BE:** FastAPI + Redis Queue (RQ/Celery)  
- **DB:** Postgres (Supabase/Neon)  
- **Vector:** Qdrant (optional V1)  
- **Crawling:** **crawl4ai** (default) + Firecrawl/SerpAPI fallback  
- **Exports:** MD → PDF via WeasyPrint (BE) or jsPDF (FE)  
- **Billing:** Lemon Squeezy (simple) or Stripe

---

## 10) Security & Compliance

- Store **only public content** (URL + short snippets).  
- Respect robots/ToS; throttle requests.  
- Keep API keys server‑side; rotate regularly.  
- Per‑plan rate limits & credit usage.  
- Basic audit log for provider usage per URL.

---

## 11) Deployment (Docker)

**docker-compose.yml** (sketch)
```yaml
version: "3.9"
services:
  api:
    build: ./services/api
    env_file: .env
    depends_on: [redis, db]
    ports: ["8000:8000"]

  worker:
    build: ./services/worker
    env_file: .env
    depends_on: [redis, db]
    command: python -m worker.main

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: microappfinder
    ports: ["5432:5432"]

  qdrant:
    image: qdrant/qdrant:v1.11.0
    ports: ["6333:6333"]
```

**Reverse Proxy:** Caddy (auto TLS) or Nginx.  
**Monitoring:** Sentry + Uptime Kuma.

---

## 12) Build Timeline (Fast)

**Days 1–2**: Repo, auth, billing skeleton; DB migrations.  
**Days 3–5**: Reddit + IdeaBrowser providers; normalizer; first E2E run → JSON.  
**Days 6–7**: Clustering + Brief writer; Report UI; export `.md`.  
**Days 8–10**: TikTok provider; polish UI; plan limits.  
**Days 11–14**: Sentry, uptime, tests; landing page + checkout; soft launch.

---

## 13) 48‑Hour Checklist

- [ ] Monorepo scaffold (frontend, api, worker)  
- [ ] Supabase project + migrations pushed  
- [ ] Next.js + Clerk + Lemon Squeezy wired  
- [ ] FastAPI `/run` + Redis queue + healthcheck  
- [ ] Implement **one** provider → end‑to‑end run  
- [ ] Signals/Clusters/Briefs tables in UI  
- [ ] Export `.md` working

---

## 14) Stretch (V1.1+)

- Topic monitors + **weekly digests**  
- Watchlists (saved audiences)  
- Notion export (create page with report)  
- Team seats + shared runs  
- Simple public API

---

## 15) Public-Facing Methodology (Generic, IP-safe)

1. **Signal Discovery:** scan public conversations across communities (e.g., Reddit, TikTok, idea platforms) for recurring frustrations and unmet needs.  
2. **Pattern Recognition:** extract jobs-to-be-done and cluster similar signals.  
3. **Scoring Framework:** weighted rubric (pain, frequency, WTP, pull, etc.).  
4. **Micro‑App Fit Check:** only problems solvable by a focused, lightweight app pass.  
5. **Actionable Briefs:** concise opportunity briefs with proof snippets and links.
