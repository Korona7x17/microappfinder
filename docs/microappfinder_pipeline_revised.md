# MicroAppFinder — Data Search & Scraping Pipeline (Revised MVP Spec)

A lean, safe, and fast-to-ship pipeline using **text-heavy, API-friendly sources**:  
- Reddit API  
- Hacker News (Algolia API)  
- Product Hunt (GraphQL API)  
- Indie Hackers (scrape or SERP)  

TikTok is **excluded from MVP**. Future expansion only.

---

## 1) Goals & Non‑Goals

**Goals**
- Capture unmet demand signals from 4 strong, ToS-safe sources.
- Normalize results into **Signals → Clusters → Briefs**.
- Avoid scraping-sensitive or high-risk platforms (TikTok).
- Keep costs low and MVP scope tight.

**Non‑Goals**
- No TikTok, Twitter, or LinkedIn in MVP.
- No storing raw HTML long-term (only normalized signals).
- No firehose ingestion.

---

## 2) High‑Level Flow

```
Topics → Source Providers (Reddit, HN, PH, IH)
→ URL/API Fetch → Clean Text
→ Normalize → Signals
→ Deduplicate + Vector Search
→ Cluster + Score
→ Generate Briefs
→ Export (MD/PDF)
```

---

## 3) Source Strategies

### 3.1 Reddit API (Primary)
- **Discovery:** Google/Bing `site:reddit.com` queries for candidate threads.  
- **Hydration:** Reddit API (free tier).  
- **Why:** Pain points expressed clearly; upvotes = validation.  
- **Subs to watch:** r/SomebodyMakeThis, r/AppIdeas, r/Productivity, r/PersonalFinance.

**Example queries:**
- `"I wish there was an app for" site:reddit.com <topic>`
- `"is there an app that" site:reddit.com <topic>`
- `"how do you track" site:reddit.com <topic>`

---

### 3.2 Hacker News (Ask HN + Show HN)
- **API:** Algolia HN Search API (https://hn.algolia.com/api).  
- **Why:** Developer/maker audience; great for unmet tool needs.  
- **Signals:**  
  - “Ask HN: Looking for a tool that…”  
  - “Ask HN: Does anyone know an app for…”  
  - Complaints or frustrations.  

**Example query:** `"Ask HN" + "tool"`

---

### 3.3 Product Hunt (Launch Signals)
- **API:** Public GraphQL API (https://api.producthunt.com/v2/docs).  
- **Why:**  
  - Track what’s being launched.  
  - Comments reveal gaps/unmet demand.  
  - Upvotes indicate traction.  
- **Integration:**  
  - Fetch daily launches.  
  - Collect title, tagline, comments, upvote count.

---

### 3.4 Indie Hackers (Founder Pain)
- **Access:** Public forums (HTML scrape or SERP `site:indiehackers.com`).  
- **Why:**  
  - Founders discuss unmet needs & revenue.  
  - “What should I build?” → pure demand signals.  
- **Integration:**  
  - crawl4ai fetch, 1 rps throttle, 48h cache.  
  - Parse post title + first 1–2 paragraphs + comments.

---

## 4) Pipeline Components

- **Queue:** Redis (RQ/Celery).  
- **DB:** Postgres (Supabase/Neon).  
- **Vector (optional):** Qdrant.  
- **Storage:** S3/R2 for exports.  
- **Crawler:** crawl4ai (for Indie Hackers only).  
- **APIs:** Reddit API, HN Algolia, PH GraphQL.

---

## 5) Data Contracts

**RawItem (provider output):**
```ts
type Source = "reddit" | "hn" | "producthunt" | "indiehackers";

interface RawItem {
  source: Source;
  url: string;
  title?: string | null;
  text?: string | null;
  meta?: Record<string, any>; // upvotes, comments, etc.
}
```

**Signal (normalized):**
```ts
interface Signal {
  id: string;
  run_id: string;
  source: Source;
  url: string;
  audience_guess: string;
  job_to_be_done: string;
  pain_snippet: string;
  frequency: "daily" | "weekly" | "irregular";
  evidence_pull: boolean;
  workaround?: string;
  wtp_hint: "none" | "low" | "medium" | "high";
  metrics: Record<string, any>; // e.g., upvotes, karma
  created_at: string;
}
```

---

## 6) Deduplication & Clustering

- **Deduplication:** by URL + SimHash on snippet.  
- **Clustering (MVP):** TF‑IDF vectors + HDBSCAN (unsupervised).  
- **Labeling:** Cheap LLM generates 3–5 word cluster name.  

**Cluster metrics:**  
- Cohesion (avg sim).  
- Support (#signals).  
- Freshness (% <7 days).  

---

## 7) Scoring

**Rubric (0–100):**
- Pain intensity (25%)  
- Frequency (15%)  
- Urgency (10%)  
- WTP hint (15%)  
- Audience size/upvotes (10%)  
- Pull evidence (15%)  
- Competitive gap (10%)  
+ Freshness booster: <7 days = +1, <24h = +2

---

## 8) Brief Generation

- Use **premium LLM only for top 3 clusters**.  
- Guardrail prompt ensures ≤3 screens, single job.  

**Brief template (MD):**
```md
## <Name>
- **Who hurts:** <audience>
- **JTBD:** <job>
- **Killer feature:** <one liner>
- **MVP:** <≤3 screens>
- **Mechanics:** <input/output>
- **North star metric:** <metric>
- **Monetization:** <hint>
- **Risks:** <2 bullets>
- **Proof:** <links>
```

---

## 9) Feedback Loop

- Thumbs up/down on briefs.  
- Export/download count tracking.  
- Flag “not a micro-app opportunity.”  
- Log to refine scoring & clustering.

---

## 10) Plan Limits (Cost Safety)

- **Free:** 1 run/week, max 50 signals, 1 brief.  
- **Starter:** 5 runs/month, 200 signals/run, 3 briefs.  
- **Pro:** 30 runs/month, 1000 signals/run, 3 briefs + monitors.

---

## 11) Data Retention

- Store only normalized signals/clusters/briefs.  
- Redis cache: 48h → purge.  
- Delete run → cascade delete.  
- No usernames; only community labels.  

---

## 12) Deployment Sketch

```yaml
version: "3.9"
services:
  api:
    build: ./apps/api
    env_file: .env
    depends_on: [redis, db]
    ports: ["8000:8000"]

  worker:
    build: ./apps/worker
    env_file: .env
    depends_on: [redis, db]
    command: python -m worker.main

  web:
    build: ./apps/web
    env_file: .env
    ports: ["3000:3000"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: microappfinder
    ports: ["5432:5432"]
```

---

## 13) Rollout Plan

**Days 1–3:** Reddit API + normalization.  
**Days 3–4:** Hacker News API integration.  
**Days 4–5:** Product Hunt GraphQL.  
**Days 5–6:** Indie Hackers crawler.  
**Days 7–8:** Clustering + scoring.  
**Days 9–10:** Brief gen + exports + feedback loop.  

---

## 14) Appendix — Prompt Stubs

**Signal Summarization (cheap LLM):**
```
Extract problem in JSON:
{ "audience_guess": "...",
  "job_to_be_done": "...",
  "frequency": "daily|weekly|irregular",
  "evidence_pull": true|false,
  "workaround": "...",
  "wtp_hint": "none|low|medium|high" }
```

**Brief Writer (premium LLM):**
```
Write a MICRO-APP BRIEF. One job only. ≤3 screens.
Follow this format: Name, Who hurts, JTBD, Killer feature, MVP, Mechanics, Metric, Monetization, Risks, Proof.
```

---

**End of revised spec.**
