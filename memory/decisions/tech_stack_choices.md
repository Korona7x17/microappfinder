# Tech Stack Choices

> Append-only log of technology and framework decisions.

## Format
```
## D-YYYY-MM-DD-NN — Technology/Framework choice
Rationale: <short explanation>
Status: Accepted | Superseded | Rejected | Under Review
Date: YYYY-MM-DD
Ref: <file@hash|PR#|issue#>
```

---

## D-2025-10-04-01 — PRAW (Python Reddit API Wrapper) for Reddit Integration
Rationale: Official Python wrapper with built-in OAuth2, rate limiting, and search support; well-maintained and Reddit-community approved
Status: Accepted
Date: 2025-10-04
Ref: specs/001-reddit-pain-point/research.md
Alternative Considered: Direct REST API calls (too much boilerplate), Pushshift (deprecated 2023)

## D-2025-10-04-02 — JWT with httponly Cookies for Authentication
Rationale: Stateless, scalable, prevents XSS attacks; aligns with FastAPI ecosystem (python-jose, passlib)
Status: Accepted
Date: 2025-10-04
Ref: specs/001-reddit-pain-point/research.md
Alternative Considered: Session-based auth (more DB load), OAuth-only (complex for MVP)

## D-2025-10-04-03 — Redis for 48-hour Reddit Content Cache
Rationale: Automatic TTL with EXPIRE command enforces Reddit ToS compliance; <10ms read latency for hot data
Status: Accepted
Date: 2025-10-04
Ref: specs/001-reddit-pain-point/research.md
Alternative Considered: PostgreSQL-only with CRON cleanup (slower, error-prone), S3 (100-200ms latency)

## D-2025-10-04-04 — TextBlob for Sentiment Analysis
Rationale: Lightweight, zero marginal cost, sufficient accuracy for composite scoring component
Status: Accepted
Date: 2025-10-04
Ref: specs/001-reddit-pain-point/research.md
Alternative Considered: OpenAI embeddings ($0.0001/1K tokens adds up), rule-based (less accurate)
