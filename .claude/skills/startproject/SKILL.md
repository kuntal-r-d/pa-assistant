---
name: startproject
description: |
  Start a new project/feature implementation with multi-agent collaboration.
  Includes multi-session review workflow for quality assurance.
metadata:
  short-description: Project kickoff with multi-agent collaboration
---

# Start Project

**Start a project with multi-agent collaboration.**

## Overview

This skill coordinates three agents (Claude, Codex, Gemini) to cover project initiation through post-implementation review.

## Workflow

```
Phase 1: Research (Gemini via Subagent)
    ↓
Phase 2: Requirements & Planning (Claude)
    ↓
Phase 3: Design Review (Codex via Subagent)
    ↓
Phase 4: Task Creation (Claude)
    ↓
Phase 5: CLAUDE.md Update (Claude)
    ↓
[Implementation...]
    ↓
Phase 6: Multi-Session Review (New Session + Codex)
```

---

## Phase 1: Gemini Research (Background)

**Use Task tool to spawn subagent and analyze repository with Gemini.**

```
Task tool parameters:
- subagent_type: "general-purpose"
- run_in_background: true
- prompt: |
    Research for: {feature}

    1. Call Gemini CLI:
       gemini -p "Analyze this repository for: {feature}

       Provide:
       1. Repository structure and architecture
       2. Relevant existing code and patterns
       3. Library recommendations
       4. Technical considerations
       " --include-directories . 2>/dev/null

    2. Save full output to: .claude/docs/research/{feature}.md

    3. Return CONCISE summary (5-7 bullet points)
```

---

## Phase 2: Requirements Gathering (Claude)

**Ask user questions to clarify requirements.**

Ask:

1. **Goal**: What do you want to achieve?
2. **Scope**: What to include/exclude?
3. **Technical requirements**: Specific libraries, constraints?
4. **Success criteria**: How do we know it's complete?

**Draft implementation plan based on Gemini research + user answers.**

---

## Phase 3: Codex Design Review (Background)

**Use Task tool to spawn subagent and review plan with Codex.**

```
Task tool parameters:
- subagent_type: "general-purpose"
- run_in_background: true
- prompt: |
    Review plan for: {feature}

    Draft plan: {plan from Phase 2}

    1. Call Codex CLI:
       codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "
       Review this implementation plan:
       {plan}

       Analyze:
       1. Approach assessment
       2. Risk analysis
       3. Implementation order
       4. Improvements
       " 2>/dev/null

    2. Return CONCISE summary:
       - Top 3-5 recommendations
       - Key risks
       - Suggested order
```

---

## Phase 4: Task Creation (Claude)

**Integrate subagent summaries and create task list.**

Use TodoWrite to create tasks:

```python
{
    "content": "Implement {specific feature}",
    "activeForm": "Implementing {specific feature}",
    "status": "pending"
}
```

---

## Phase 5: CLAUDE.md Update (IMPORTANT)

**Add project-specific information to CLAUDE.md.**

Add to CLAUDE.md:

```markdown
---

## Current Project: {feature}

### Context
- Goal: {1-2 sentences}
- Key files: {list}
- Dependencies: {list}

### Decisions
- {Decision 1}: {rationale}
- {Decision 2}: {rationale}

### Notes
- {Important constraints or considerations}
```

**This ensures context persists across sessions.**

---

## Phase 6: Multi-Session Review (Post-Implementation)

**After implementation, conduct review in a separate session.**

### Option A: New Claude Session

1. Start new Claude Code session
2. Run: `git diff main...HEAD` to see all changes
3. Ask Claude to review the implementation

### Option B: Codex Review (via Subagent)

```
Task tool parameters:
- subagent_type: "general-purpose"
- prompt: |
    Review implementation for: {feature}

    1. Run: git diff main...HEAD
    2. Call Codex CLI:
       codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "
       Review this implementation:
       {diff output}

       Check:
       1. Code quality and patterns
       2. Potential bugs
       3. Missing edge cases
       4. Security concerns
       " 2>/dev/null

    3. Return findings and recommendations
```

### Why Multi-Session Review?

- **Fresh perspective**: New session has no bias from implementation
- **Different context**: Can focus purely on review, not implementation details
- **Codex strength**: Deep analysis without context pollution

---

## User Confirmation

Present final plan to user:

```markdown
## Project Plan: {feature}

### Research Results (Gemini)
{Key findings - 3-5 bullet points}

### Design Approach (Codex Reviewed)
{Approach with refinements}

### Task List ({N} items)
{Task list}

### Risks and Notes
{From Codex analysis}

### Next Steps
1. Should we proceed with this plan?
2. Post-implementation review will be conducted in a separate session

---
Should we proceed with this plan?
```

---

## Output Files

| File | Purpose |
|------|---------|
| `.claude/docs/research/{feature}.md` | Gemini research output |
| `CLAUDE.md` | Updated with project context |
| Task list (internal) | Progress tracking |

---

## Tips

- **All Codex/Gemini work through subagents** to preserve main context
- **Update CLAUDE.md** to persist context across sessions
- **Use multi-session review** for better quality assurance
- **Ctrl+T**: Toggle task list visibility
