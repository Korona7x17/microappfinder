# 🧠 Claude-Memory System
**Guidelines & Implementation Instructions for LLM-Based Projects (Claude Code, Cursor Sub‑Agents, Spec‑Kit, Genesis Engine)**

> Drop this file into your repo as `memory/CLAUDE_MEMORY_GUIDELINES.md` (or `docs/CLAUDE_MEMORY_GUIDELINES.md`).  
> This system is file‑based, deterministic, git‑friendly, and model‑agnostic (works with Claude, GPT, Llama).

---

## 1) Purpose & Principles

**Purpose.** Provide *persistent project context* without relying on model-native memory or expensive vector calls.  
**Principles.**
- **Human‑readable first**, **machine‑parsable second** (markdown + tiny JSON side‑indexes).
- **Token frugal**: summaries are terse, diff‑oriented, and reference artifacts by `path@hash`.
- **Explicit control**: no hidden “auto‑memory”; everything is saved intentionally and reviewed in Git.
- **Composable**: sub‑agents load *slices* of memory (not the whole history).

---

## 2) Quick Start (TL;DR)

1. Create `/memory` with the structure below.  
2. Add the **pre‑commit** hook to enforce size/format.  
3. Start a session → log transcript → run the **Summarizer** to produce a Brief (≤250 tokens).  
4. At day’s end, create `daily_summary_YYYY‑MM‑DD.md` and update `project_snapshot.md`.  
5. Sub‑agents read `project_snapshot.md`, last `daily_summary`, and relevant `/decisions/*.md`.  
6. Weekly, generate `weekly_compact.md` (decisions + active constraints + unresolved Q/→).

---

## 3) Folder Structure

```
/memory
 ├─ sessions/
 │   ├─ 2025-10-04_session-01.md
 │   └─ 2025-10-04_session-02.md
 ├─ summaries/
 │   ├─ daily_summary_2025-10-04.md
 │   ├─ weekly_compact_2025-W40.md
 │   └─ project_snapshot.md
 ├─ decisions/
 │   ├─ design_decisions.md
 │   ├─ tech_stack_choices.md
 │   ├─ rejected_ideas.md
 │   └─ naming_history.md
 ├─ state/
 │   ├─ active_context.json
 │   ├─ recent_topics.json
 │   └─ subagent_state.json
 ├─ subagents/
 │   ├─ product_manager_context.md
 │   ├─ researcher_context.md
 │   └─ designer_context.md
 ├─ archive/          # optional rotations
 └─ CLAUDE_MEMORY_RULES.md
```

**Git rules.**
- Commit everything under `/memory` (unless sensitive—then encrypt `/sessions` only).
- Use conventional commits: `chore(memory): add daily_summary_2025-10-04`.

---

## 4) Roles & Files (What goes where)

- **/sessions/** – Raw transcripts per dev block. You can paste transcripts, major commands, outcomes.
- **/summaries/** – Terse, token-budgeted context (daily, weekly, snapshot).
- **/decisions/** – Append‑only logs of accepted/superseded choices with 1‑line rationale.
- **/state/** – Machine‑oriented JSON describing the *current* active topics, owners, due dates.
- **/subagents/** – Narrow context files for each agent to read/write (kept tiny, ≤2 KB each).

---

## 5) Runtime Loading Policy

**Short task** → `project_snapshot.md` + last daily summary + any relevant decision file(s).  
**Deep refactor/architecture** → above + last 2–3 session logs.  
**Writer/Researcher sub‑agents** → its `/subagents/{role}_context.md` + `project_snapshot.md`.  
**Token ceilings** (soft caps you can change):
- Brief carry‑over memory ≤ **250 tokens**
- Full carry‑over memory ≤ **900 tokens**
- Sub‑agent context files ≤ **2 KB**

---

## 6) Session Template (paste into each `/sessions/*.md`)

```md
# Session Log – 2025-10-04_01
Tags: [API][Auth]  |  Repo: web@a82e77  |  Context loaded: project_snapshot.md, design_decisions.md

## Notes
- Fixed auth flow edge case on token refresh
- Agreed on FastAPI over Flask (see decisions)

## Exchanges
- User: “Add /users pagination and tests.”
- Agent: “Implemented GET /users?limit&cursor … see api/routes.py@c1a9f2”

## Artifacts
- PR #134  web@a82e77
- api/routes.py@c1a9f2
```

---

## 7) **Session Summarization & Token Optimization**

> **Use line lists; avoid prose. Prefer diffs and references.**

### 7.1 TL;DR Rules
- No paragraphs—**one‑line bullets** with fixed prefixes.
- Cap **Brief ≤250 tokens**, **Full ≤900 tokens**.
- Order: **Constraints → Decisions → Δ Changes → Open Q → Next**.
- Reference by `path@hash`, never paste large code.

### 7.2 Formats

**Tier A — Brief (≤250 tokens)**
```
# BRIEF_SUMMARY (YYYY-MM-DD HH:MM)
C: <top-3 constraints>
D: <top-3 decisions>
Δ: <top-3 changes>
Q: <top-2 questions>
→: <top-3 next actions>
```

**Tier B — Full (≤900 tokens)**
```
CONSTRAINTS
- C1: …

DECISIONS
- D1: <Decision> | Rationale=<short> | Status=Accepted | Ref=<file@hash|#issue>

CHANGES
- Δ api/routes.py@c1a9f2: +/users GET pagination; -legacy cursor

RISKS
- R1: <risk> | L=<L/M/H> | I=<L/M/H> | Mitigation=<short>

OPEN_QUESTIONS
- Q1: <question> | Owner=@alice | Due=2025-10-06

NEXT_ACTIONS
- → A1: <action> | Owner=@john | Due=2025-10-05
```

**Tier C — Ultra (≤120 tokens)**
```
C:[c1;c2] D:[d1;d2] Δ:[f@h:chg;g@h:chg] Q:[q1] →:[a1;a2]
```

### 7.3 Summarizer Prompts

**SYSTEM (Summarizer Agent):**
> Compress the dev session to preserve constraints, decisions, external‑facing changes, blockers, and next actions. Output **Tier A** unless `mode:full`. No prose, no quotes, no code blocks. Reference artifacts as `path@hash`. ≤250 tokens (or ≤900 in full). Prefer actionability over completeness.

**USER Inputs:** `last_full_summary.md`, `current_session_transcript.md`, optional diff list, `mode: brief|full|ultra`.

### 7.4 JSON Side‑Index (machine‑parsable, ≤2 KB)
```json
{
  "ts": "2025-10-04T13:45:00Z",
  "constraints": ["FastAPI", "SSR only"],
  "decisions": [{"id":"D-20251004-1","title":"Adopt HDBSCAN","rationale":"stable clusters small corpora","status":"Accepted","ref":"research/notebook@7fd3b1"}],
  "changes": [{"path":"api/routes.py","hash":"c1a9f2","summary":"+users GET pagination;-cursor"}],
  "risks":[{"title":"PH API rate limits","likelihood":"M","impact":"H"}],
  "open_questions":[{"q":"Self-host Algolia?","owner":"@john","due":"2025-10-06"}],
  "next_actions":[{"a":"Implement retry/backoff","owner":"@john","due":"2025-10-05"}]
}
```

---

## 8) Decision Logging (append‑only)

Each material choice is a one‑liner with rationale and status.

```md
## D‑2025‑10‑04‑01 — Use FastAPI for backend
Rationale: async‑first, better ecosystem; aligns with SSR constraint  
Status: Accepted  |  Date: 2025‑10‑04  |  Ref: backend/stack@e312bc
```

When superseded:
```
Status: Superseded → D‑2025‑11‑02‑03
```

---

## 9) State Files (schemas)

`/state/active_context.json`
```json
{
  "active_topics": ["API pagination", "Docker"],
  "owners": {"api":"@john","ui":"@mindy"},
  "last_daily_summary": "2025-10-04",
  "linked_agents": ["ProductManager","Researcher"]
}
```

`/state/subagent_state.json`
```json
{
  "ProductManager": {"last_run":"2025-10-04T11:22:33Z","needs":["design_decisions.md"]},
  "Researcher": {"last_run":"2025-10-04T12:03:11Z","scope":["Reddit","HN"]}
}
```

---

## 10) Integration Patterns

### 10.1 Claude Code
- **Session start:** load `project_snapshot.md` + last daily summary + relevant decisions.
- **Session end:** save `/sessions/*.md` → run Summarizer → update `/summaries/*` → update `/state/*`.

### 10.2 Cursor Sub‑Agents
- Give each agent a tiny context file under `/subagents/…`.  
- Agents must *only* append to their file and `/state/subagent_state.json`.

### 10.3 Spec‑Kit
- Place `/memory` beside `/spec` and reference in specs:
  - `context_files: ["memory/summaries/project_snapshot.md", "memory/decisions/design_decisions.md"]`

### 10.4 Genesis Engine
- Register a “Memory Intake” step before agent execution that:
  1) Concatenates Tier‑A brief + active decisions,  
  2) Clips to 250–500 tokens,  
  3) Emits `context_bundle.md` to the active job folder.

---

## 11) Automation (n8n or scripts)

### 11.1 Daily Rotation (pseudo‑flow)
- Trigger at 18:00 → Collect today’s `BRIEF_SUMMARY` → Write `daily_summary_YYYY‑MM‑DD.md`  
- Update `project_snapshot.md` (merge constraints + accepted decisions + unresolved Q/→)  
- Commit with `chore(memory): daily rotation`

### 11.2 Weekly Compact
- Sunday 17:00 → Build `weekly_compact_YYYY‑Www.md` from latest decisions + active constraints + unresolved Q/→.

### 11.3 Pre‑Commit Quality Gate (bash)
```bash
#!/usr/bin/env bash
set -euo pipefail
files=$(git diff --cached --name-only | grep '^memory/')
fail=0

check_summary () {
  f="$1"
  # Must include at least one of the required prefixes
  if ! grep -Eq '^(C:|D:|Δ:|->|→:|Q:)' "$f"; then
    echo "✗ $f missing required summary prefixes (C/D/Δ/Q/→)"
    fail=1
  fi
  # Rough token cap: 1 token ≈ 4 chars → enforce 1000 char brief files
  if [[ "$(basename "$f")" == BRIEF_* ]] && [ "$(wc -c < "$f")" -gt 1000 ]; then
    echo "✗ $f exceeds brief size cap (~250 tokens)"
    fail=1
  fi
}

for f in $files; do
  case "$f" in
    memory/summaries/*|memory/subagents/*) check_summary "$f" ;;
  esac
done

[ $fail -eq 0 ] || { echo "Commit blocked by memory quality gate."; exit 1; }
```

Add with:
```
chmod +x .git/hooks/pre-commit
```

---

## 12) Minimal CLI Helpers (optional)

`memory/tools/summarize.py` (skeleton)
```python
#!/usr/bin/env python3
import sys, json, pathlib, re
from datetime import datetime

def brief(lines, now=None):
    # naive rules: pick lines prefixed with markers or synthesize from transcript
    C,D,CH,Q,N = [],[],[],[],[]
    for ln in lines:
        s = ln.strip()
        if s.startswith("C:"): C.append(s[2:].strip())
        if s.startswith("D:"): D.append(s[2:].strip())
        if s.startswith("Δ:"): CH.append(s[2:].strip())
        if s.startswith("Q:"): Q.append(s[2:].strip())
        if s.startswith("→:") or s.startswith("->"): N.append(s[2:].strip())
    now = now or datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    out = [f"# BRIEF_SUMMARY ({now})"]
    if C: out.append("C: " + "; ".join(C[:3]))
    if D: out.append("D: " + "; ".join(D[:3]))
    if CH: out.append("Δ: " + "; ".join(CH[:3]))
    if Q: out.append("Q: " + "; ".join(Q[:2]))
    if N: out.append("→: " + "; ".join(N[:3]))
    text = "\n".join(out)
    # truncate to ~250 tokens ~ 1000 chars
    return text[:1000]

if __name__ == "__main__":
    transcript = sys.stdin.read().splitlines()
    print(brief(transcript))
```

---

## 13) Security & Privacy

- Keep **PII and secrets out of `/sessions`**; if unavoidable, encrypt that subfolder (git‑crypt/age).
- Memory files live in Git; use PR reviews to audit context changes.
- For external sharing, include only `/summaries`, `/decisions`, `/state`—omit `/sessions`.

---

## 14) Working Agreements (team/solo)

- Summaries are **append‑only**; never rewrite history—mark with `Status: Superseded`.
- Keep each memory file **small and focused** (aim ≤2 KB for sub‑agent files).
- Prefer **issue/PR links** over inline code or screenshots.

---

## 15) FAQ

**Q: Why not vectors?**  
A: This covers 80% of day‑to‑day continuity at near‑zero cost. You can add vectors later for search across `/sessions`.

**Q: How do sub‑agents avoid drift?**  
A: They read `project_snapshot.md` and their own `/subagents/{role}_context.md`, and must update `/state/subagent_state.json` after runs.

**Q: What if the project explodes in size?**  
A: Increase rotation frequency; keep only last 1–2 weeks of `/sessions/` locally and move older logs to `/archive/` (or object storage).

---

## 16) Copy‑Paste: `CLAUDE_MEMORY_RULES.md` (starter)

```md
# CLAUDE MEMORY RULES (Runtime)
- Load: project_snapshot + last daily summary + relevant decision files.
- Prefer Tier‑A Brief unless `mode:full` is specified.
- Use line lists; avoid prose and code blocks.
- Reference artifacts by path@hash; no large pastes.
- Return at least one of: C: D: Δ: Q: →: in outputs.
- Respect caps: Brief ≤250 tokens, Full ≤900.
```
