# 🧠 Memory System

This directory contains the claude-memory system for persistent project context across LLM sessions.

## 📁 Structure

- **sessions/** - Raw session transcripts and logs
- **summaries/** - Token-optimized context (daily, weekly, project snapshot)
- **decisions/** - Append-only decision logs (design, tech stack, naming)
- **state/** - Machine-readable JSON state files
- **subagents/** - Context files for specialized agents
- **archive/** - Rotated historical logs
- **tools/** - Helper scripts (summarizer)

## 🚀 Quick Start

### Loading Context (Claude/LLM)
Always load these at session start:
1. `summaries/project_snapshot.md`
2. Latest `summaries/daily_summary_*.md` (if exists)
3. Relevant `decisions/*.md` files

### Creating Session Logs
Use the template format:
```md
# Session Log – 2025-10-04_01
Tags: [Feature] [Bug Fix]

## Notes
- Key observations

## Exchanges
- User: "request"
- Agent: "response with refs"

## Artifacts
- PR #123
- file/path@hash
```

### Generating Summaries
```bash
# Brief summary (≤250 tokens)
cat sessions/2025-10-04_session-01.md | python tools/summarize.py > summaries/brief.md

# Full summary (≤900 tokens)
python tools/summarize.py -i sessions/latest.md -m full -o summaries/daily_summary_2025-10-04.md
```

## 📝 Decision Logging

When making important decisions, add to appropriate file:

```md
## D-2025-10-04-01 — Decision title
Rationale: Why this choice
Status: Accepted
Date: 2025-10-04
Ref: file@hash or PR#123
```

## 🔍 Summary Format (Tier-A Brief)

Use these prefixes in summaries:
- **C:** Constraints (tech/design limits)
- **D:** Decisions made
- **Δ:** Changes/artifacts created
- **Q:** Open questions
- **→:** Next actions

Example:
```
C: FastAPI backend; Docker-first deployment
D: Use HDBSCAN for clustering; crawl4ai for scraping
Δ: api/routes.py@c1a9f2 +pagination endpoint
Q: Export format preference?
→: Implement frontend dashboard; Setup CI/CD
```

## 🛡️ Quality Gate

Pre-commit hook validates:
- Summary files have required prefixes (C/D/Δ/Q/→)
- BRIEF_* files stay under ~250 tokens (1000 chars)

## 🔄 Workflow

1. **Session Start:** Load context files
2. **During Work:** Log key decisions in sessions/
3. **Session End:**
   - Save session log
   - Generate summary
   - Update project_snapshot.md if needed
   - Update state/*.json
4. **Daily:** Create daily_summary_YYYY-MM-DD.md
5. **Weekly:** Generate weekly_compact.md

## 📚 Full Documentation

See `docs/CLAUDE_MEMORY_GUIDELINES.md` for complete specifications.

## 🔐 Security Note

Keep PII and secrets out of session logs. Encrypt sessions/ if needed using git-crypt.
