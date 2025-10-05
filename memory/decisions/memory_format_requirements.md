# Memory Format Requirements

## Daily Summary Format (CRITICAL)

**Issue Discovered:** 2025-10-05
**Context:** Git commit hook blocks commits if daily_summary_*.md doesn't meet format requirements

### Git Hook Requirement
The pre-commit hook checks `memory/summaries/daily_summary_*.md` for required C/D/Δ/Q/→ prefixes.

### Correct Format (Tier-A Brief)

Daily summaries MUST have a **single** `## Brief (Tier-A)` section with ALL prefixes:

```markdown
# Daily Summary – YYYY-MM-DD

Sessions: session-01, session-02
Tags: [tag1][tag2]

## Brief (Tier-A)

C: Context line 1; Context line 2

D: Decision 1; Decision 2

Δ: Change 1; Change 2

Q: Question 1; Question 2

→: Next action 1; Next action 2

## Key Metrics
...

## Refs
...
```

### ❌ INCORRECT Format (Will Block Commits)

DO NOT create multiple Brief sections or subsections with C/D/Δ/Q/→:

```markdown
## Brief (Tier-A)
C: Session 1 context
...

## Session 02: Title
C: Session 2 context  ← Git hook won't recognize this!
...
```

DO NOT use bold syntax for prefixes:

```markdown
## Brief (Tier-A)
**C:** This will fail  ← Git hook expects C: at line start, not **C:**
```

### Rules
1. **One Brief section per file** - consolidate all sessions into single C/D/Δ/Q/→ block
2. **NO bold syntax** - Use `C:`, `D:`, `Δ:`, `Q:`, `→:` at line start (not `**C:**`)
3. **All 5 prefixes required** - C (context), D (decisions), Δ (delta/changes), Q (questions), → (next actions)
4. **Semicolon separators** - Use `;` to separate multiple items on same line

### Multi-Session Daily Summaries

For days with multiple sessions, combine their information:

```markdown
## Brief (Tier-A)

C: Session 1 context; Session 2 context; Common stack info

D: D-YYYY-MM-DD-01 Session 1 decision; D-YYYY-MM-DD-02 Session 1 decision; D-YYYY-MM-DD-03 Session 2 decision; D-YYYY-MM-DD-04 Session 2 decision

Δ: Session 1 changes (file1.py, file2.py); Session 2 changes (file3.py, file4.py); Feature X complete (T001-T024)

Q: Outstanding questions from either session

→: Next actions from final session state
```

Then add detailed breakdowns in subsequent sections (without C/D/Δ/Q/→).

### Why This Matters
- Git pre-commit hook enforces memory quality
- Blocked commits prevent progress
- Daily summaries must be loadable by future sessions
- Format consistency enables automated memory retrieval

### Reference
- Memory rules: `memory/CLAUDE_MEMORY_RULES.md`
- Example: `memory/summaries/daily_summary_2025-10-04.md` (single session, correct format)
- Problem case: `memory/summaries/daily_summary_2025-10-05.md` (multi-session, incorrect format - Session 03 subsection not recognized)
