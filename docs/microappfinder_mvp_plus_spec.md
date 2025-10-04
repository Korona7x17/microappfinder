# MicroAppFinder — MVP+ System Specification

## 🎯 Core Principle
Start lean, safe, and fast. Build MVP with text-first, API-friendly sources. Avoid risky scraping (TikTok, Twitter).

**Primary Sources (MVP):**
- Reddit API (official)
- Hacker News (Algolia API)
- Product Hunt (GraphQL API)
- Indie Hackers (SERP-first discovery + polite fetch)

---

## ✅ Data Flow

```
Topics → Providers → Fetch → Normalize → Signals
→ Deduplicate → Cluster → Score → Briefs
→ Feedback → Export
```

---

## 🔑 Key Improvements (from feedback)

### 1. IndieHackers Strategy
- Use **SERP-first discovery**: Google/Bing queries like `site:indiehackers.com "what should I build"`.
- Fetch only selected threads (10–20 at a time).
- Add polite User-Agent with contact info.
- Monitor 403/429 errors, back off immediately.
- Optional: poll `/newest` page for recent posts.

### 2. Deduplication
- Multi-level dedupe:  
  1. **By URL** (fast exact match).  
  2. **By embeddings** (semantic merge across platforms).  
- Merge duplicates → keep the highest-engagement signal.  
- Store combined proof links + metrics.

### 3. Clustering
- Use **embeddings** (OpenAI text-embedding-3-small or similar).  
- Try **HDBSCAN** if ≥50 signals.  
- Fallback: **K-means** (optimal k via elbow method).  
- Constraints: min 5 signals/cluster, max 20 clusters.  
- Label clusters with cheap LLM (“≤5 word theme”).  

### 4. Brief Generation
- Use **premium LLM only for top 3 clusters**.  
- Strong guardrail prompt:  
  - ≤3 screens  
  - <1 week build  
  - One job-to-be-done only  
  - No AI/ML, blockchain, complex integrations  
- Validation function auto-checks briefs for:  
  - Screen count > 3  
  - Red-flag keywords (“machine learning”, “multi-tenant”)  

### 5. Scoring
- Rebalanced rubric (0–100):  
  - Pain intensity (30%)  
  - Frequency (20%)  
  - WTP hint (20%)  
  - Pull evidence (15%)  
  - Social validation (10%)  
  - Urgency (5%)  
  - + Recency bonus (<7 days = +5, <24h = +10)  
- Pain intensity scored via cheap LLM (0–100).  

### 6. Confidence Score
Each signal has `confidence: 0.0–1.0` based on:  
- Engagement (upvotes, comments)  
- Pull evidence  
- JTBD clarity  
- Recency  

### 7. Feedback Loop
- Schema: `brief_feedback` with thumbs_up, thumbs_down, flags, export count.  
- API endpoint: `/api/briefs/{id}/feedback`.  
- Analytics view: top briefs, most exported, most flagged.  

### 8. Market Size & Competition (V1+)
- Estimate market size from subreddit size + engagement.  
- Quick competition check via Product Hunt + Google search.  
- Add to brief template as optional enrichment:  
  - **Market size hint:** Niche/Small/Medium/Large  
  - **Competition:** None/Low/Moderate/High + competitor names  

---

## 🗂️ Data Contracts

**Signal (normalized):**
```ts
interface Signal {
  id: string;
  run_id: string;
  source: "reddit"|"hn"|"producthunt"|"indiehackers";
  url: string;
  audience_guess: string;
  job_to_be_done: string;
  pain_snippet: string;
  frequency: "daily"|"weekly"|"irregular";
  evidence_pull: boolean;
  workaround?: string;
  wtp_hint: "none"|"low"|"medium"|"high";
  metrics: Record<string, any>;
  proof_urls: string[];
  confidence: number; // 0.0–1.0
  created_at: string;
}
```

**Brief (output):**
```md
## [App Name - ≤3 words]

**Who hurts:** [audience]
**Job-to-be-done:** [1 sentence JTBD]
**Killer feature:** [1 sentence]
**MVP (≤3 screens):**
1. [Screen name]: [description]
2. [Screen name]: [description]
3. [Screen name]: [description]

**Mechanics:**
- Input: ...
- Process: ...
- Output: ...

**North star metric:** ...
**Monetization hint:** ...
**Risks:**
- [Risk 1]
- [Risk 2]

**Proof:** [Top 3 signal URLs]

**Market size hint (optional):** ...
**Competition (optional):** ...
```

---

## 📋 Revised 12-Day Timeline

| Day | Task |
|-----|------|
| 1–2 | Reddit API integration + normalization |
| 3 | HN Algolia API integration |
| 4 | Product Hunt GraphQL integration |
| 5 | IndieHackers SERP discovery + fetch |
| 6 | Deduplication (URL + embeddings) |
| 7 | Clustering (HDBSCAN + fallback) |
| 8 | Scoring + recency booster |
| 9 | Brief generation + validation |
| 10 | Exports + feedback UI |
| 11 | Market size + competition (optional) |
| 12 | Buffer: debugging, tuning, deploy |

---

## 🚀 Priority Fixes Before Ship
1. IndieHackers → SERP-first fetch (polite).  
2. Deduplication → add embeddings step.  
3. Clustering → fallback plan.  
4. Brief prompt → guardrails + validator.  
5. Scoring → rebalanced weights + recency booster.  
6. Add confidence score.  
7. Implement feedback DB + API.  

---

**End of MVP+ spec.**
