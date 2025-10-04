# Claude Code Instructions

## Memory System
- **Always load:** `memory/summaries/project_snapshot.md` at session start
- **Full spec:** `docs/CLAUDE_MEMORY_GUIDELINES.md`
- **Runtime rules:** `memory/CLAUDE_MEMORY_RULES.md`

## Project Context
- **Stack:** Next.js 14 + FastAPI + RQ worker + PostgreSQL/Qdrant
- **Structure:** Monorepo (apps/web, apps/api, apps/worker)
- **Goal:** Micro app opportunity discovery via Reddit/HN/PH/IH signals

## Development Rules
- Use Docker Compose for all services
- Reference code as `path:line` or `path@hash`
- Log decisions in `memory/decisions/*.md`
- Keep responses token-efficient
