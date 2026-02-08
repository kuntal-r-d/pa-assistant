# Multi-Agent Workflow Diagrams

> Visual guide to understanding the Claude + Codex + Gemini orchestration system.

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              USER                                        │
│                         (You typing prompts)                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLAUDE CODE (Opus 4.5)                           │
│                         ═══════════════════════                          │
│                         Main Orchestrator                                │
│                                                                          │
│  • Receives your prompts                                                 │
│  • Reads/writes code                                                     │
│  • Runs commands                                                         │
│  • Coordinates subagents                                                 │
│  • Synthesizes final responses                                           │
└─────────────────────────────────────────────────────────────────────────┘
                    │                               │
                    ▼                               ▼
    ┌───────────────────────────┐   ┌───────────────────────────┐
    │      CODEX CLI            │   │      GEMINI CLI           │
    │      ══════════           │   │      ══════════           │
    │  Deep Reasoning Expert    │   │  Research Specialist      │
    │                           │   │                           │
    │  • Design decisions       │   │  • Documentation lookup   │
    │  • Architecture review    │   │  • Best practices search  │
    │  • Debugging analysis     │   │  • Large codebase analysis│
    │  • Code review            │   │  • Multimodal (PDF/video) │
    │  • Trade-off analysis     │   │  • Web-grounded answers   │
    └───────────────────────────┘   └───────────────────────────┘
```

---

## 2. Session Mode Flow

```
                              ┌──────────────────┐
                              │   USER PROMPT    │
                              │  "Design an API" │
                              └────────┬─────────┘
                                       │
                                       ▼
                         ┌─────────────────────────┐
                         │   agent-router.py       │
                         │   (UserPromptSubmit)    │
                         └───────────┬─────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
            ┌───────────┐    ┌───────────┐    ┌───────────┐
            │   SOLO    │    │  CONSULT  │    │   AUTO    │
            │   Mode    │    │   Mode    │    │   Mode    │
            └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
                  │                │                │
                  ▼                ▼                ▼
           ┌──────────┐     ┌──────────┐     ┌──────────┐
           │ No       │     │ Ask      │     │ Auto     │
           │ routing  │     │ permission│    │ delegate │
           │          │     │          │     │          │
           │ Claude   │     │ "Would   │     │ Spawn    │
           │ handles  │     │ you like │     │ subagent │
           │ directly │     │ to       │     │ silently │
           │          │     │ consult  │     │          │
           │          │     │ Codex?"  │     │          │
           └──────────┘     └──────────┘     └──────────┘
```

---

## 3. Complete Request Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 1: User Input                                                       │
│ ════════════════════════════════════════════════════════════════════════ │
│                                                                          │
│    User: "Help me design a REST API for user authentication"             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 2: Hook Fires (agent-router.py)                                     │
│ ════════════════════════════════════════════════════════════════════════ │
│                                                                          │
│    ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐  │
│    │ Check Mode      │ ──▶ │ Classify Intent │ ──▶ │ Generate Output │  │
│    │ (mode.json)     │     │ (LLM/keyword)   │     │ (suggestion)    │  │
│    └─────────────────┘     └─────────────────┘     └─────────────────┘  │
│                                                                          │
│    Keywords found: "design", "API" → Suggests CODEX                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 3: Claude Receives Context                                          │
│ ════════════════════════════════════════════════════════════════════════ │
│                                                                          │
│    Claude sees: "[Auto-Routing] Consulting Codex CLI..."                 │
│                                                                          │
│    Claude decides to spawn a subagent for Codex consultation             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 4: Subagent Execution                                               │
│ ════════════════════════════════════════════════════════════════════════ │
│                                                                          │
│    ┌────────────────────────────────────────────────────────────────┐   │
│    │  Task Subagent (general-purpose)                                │   │
│    │  ════════════════════════════════                               │   │
│    │                                                                 │   │
│    │  1. Calls Codex CLI:                                            │   │
│    │     codex exec --sandbox read-only --full-auto "Analyze..."     │   │
│    │                                                                 │   │
│    │  2. Receives Codex response                                     │   │
│    │                                                                 │   │
│    │  3. Saves full output to:                                       │   │
│    │     .claude/docs/design/task-2026-02-05-abc123.md               │   │
│    │                                                                 │   │
│    │  4. Returns CONCISE summary to main Claude                      │   │
│    └────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 5: Claude Synthesizes Response                                      │
│ ════════════════════════════════════════════════════════════════════════ │
│                                                                          │
│    Claude receives summary from subagent:                                │
│    - Recommended architecture: JWT + refresh tokens                      │
│    - Key trade-offs: Stateless vs session-based                          │
│    - Implementation steps: 1) User model, 2) Auth routes...              │
│                                                                          │
│    Claude combines this with its own knowledge and responds to user      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 6: User Sees Final Response                                         │
│ ════════════════════════════════════════════════════════════════════════ │
│                                                                          │
│    "Based on analysis, here's the recommended API design..."             │
│    (User only sees the final synthesized response)                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Mode Comparison

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SESSION MODES                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  !solo          !consult         !auto           !codex        !gemini   │
│    │               │               │               │              │      │
│    ▼               ▼               ▼               ▼              ▼      │
│ ┌──────┐      ┌──────────┐    ┌──────────┐   ┌──────────┐  ┌──────────┐ │
│ │Claude│      │  Claude  │    │  Claude  │   │  Claude  │  │  Claude  │ │
│ │only  │      │    +     │    │    +     │   │    +     │  │    +     │ │
│ │      │      │ Ask first│    │ Auto     │   │ Codex    │  │ Gemini   │ │
│ │      │      │ then     │    │ delegate │   │ only     │  │ only     │ │
│ │      │      │ delegate │    │          │   │          │  │          │ │
│ └──────┘      └──────────┘    └──────────┘   └──────────┘  └──────────┘ │
│                                                                          │
│  No external    Permission      Silent         Forces        Forces      │
│  LLM calls      required        routing        Codex         Gemini      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Intent Classification

```
                         ┌─────────────────────┐
                         │    User Prompt      │
                         │ "Debug this error"  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │     IntentClassifier          │
                    │     ══════════════════        │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
          ┌─────────────────┐             ┌─────────────────┐
          │   LLM Stage     │             │  Keyword Stage  │
          │   (Gemini)      │             │   (Fallback)    │
          │                 │             │                 │
          │  Timeout: 3.5s  │   ──fail──▶ │  Weighted       │
          │  Returns JSON   │             │  scoring        │
          └────────┬────────┘             └────────┬────────┘
                   │                               │
                   └───────────────┬───────────────┘
                                   │
                                   ▼
                    ┌───────────────────────────────┐
                    │     Classification Result     │
                    │     ═════════════════════     │
                    │                               │
                    │  • suggested_agent: CODEX    │
                    │  • confidence: 0.75          │
                    │  • reasoning: "Debug task"   │
                    │  • source: llm/keyword       │
                    └───────────────────────────────┘
```

---

## 6. Keyword Triggers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CODEX TRIGGERS                                   │
│                    (Design / Debug / Review)                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│   │   DESIGN    │  │    DEBUG    │  │   REVIEW    │  │  EXPLICIT   │   │
│   ├─────────────┤  ├─────────────┤  ├─────────────┤  ├─────────────┤   │
│   │ design (3)  │  │ debug (3)   │  │ review (2)  │  │ codex (4)   │   │
│   │ architect(3)│  │ bug (3)     │  │ compare (2) │  │ think       │   │
│   │ pattern (3) │  │ error (2)   │  │ trade-off(2)│  │ deeper (4)  │   │
│   │ structure(2)│  │ fix (2)     │  │ analyze (2) │  │ second      │   │
│   │             │  │ broken (2)  │  │             │  │ opinion (4) │   │
│   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         GEMINI TRIGGERS                                  │
│                   (Research / Multimodal / Large Context)                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│   │  RESEARCH   │  │    DOCS     │  │ MULTIMODAL  │  │   LARGE     │   │
│   ├─────────────┤  ├─────────────┤  ├─────────────┤  ├─────────────┤   │
│   │ research (3)│  │ docs (2)    │  │ pdf (4)     │  │ entire      │   │
│   │ investigate │  │ document(2) │  │ video (4)   │  │ codebase(4) │   │
│   │ (3)         │  │ library (2) │  │ audio (4)   │  │ whole       │   │
│   │ look up (3) │  │ package (2) │  │ image (3)   │  │ repo (4)    │   │
│   │ find out(2) │  │ latest (2)  │  │             │  │ all files(3)│   │
│   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. File Organization

```
.claude/
├── hooks/
│   └── agent-router.py          # Routes prompts to agents
│
├── lib/
│   ├── intent_classifier.py     # LLM + keyword classification
│   ├── session_mode.py          # Mode management (SOLO/CONSULT/AUTO)
│   ├── task_coordinator.py      # Parallel task coordination
│   ├── file_lock.py             # Concurrent access protection
│   ├── circuit_breaker.py       # CLI failure resilience
│   └── retry.py                 # Retry with backoff
│
├── session/
│   └── mode.json                # Current session state
│       {
│         "mode": "auto",
│         "first_delegation_done": true
│       }
│
├── docs/
│   ├── research/                # Gemini outputs
│   │   └── task-2026-02-05-abc123.md
│   ├── design/                  # Codex outputs
│   │   └── task-2026-02-05-def456.md
│   └── decisions/               # Final decisions
│       └── task-2026-02-05-ghi789.md
│
└── rules/
    ├── codex-delegation.md      # When/how to use Codex
    └── gemini-delegation.md     # When/how to use Gemini
```

---

## 8. Security Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       SECURITY LAYERS                                    │
└─────────────────────────────────────────────────────────────────────────┘

     ┌─────────────────────────────────────────────────────────────┐
     │                    USER INPUT                                │
     │                "Help me design..."                           │
     └─────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
     ┌─────────────────────────────────────────────────────────────┐
     │  LAYER 1: Command Injection Prevention                       │
     │  ════════════════════════════════════                        │
     │                                                              │
     │  ✓ List-based subprocess (shell=False)                       │
     │  ✓ No shell interpretation of user input                     │
     │  ✓ Direct argument passing                                   │
     │                                                              │
     │  cmd = ["gemini", "-p", user_prompt]  # SAFE                 │
     │  # NOT: f"gemini -p '{user_prompt}'"  # DANGEROUS            │
     └─────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
     ┌─────────────────────────────────────────────────────────────┐
     │  LAYER 2: Path Traversal Prevention                          │
     │  ═══════════════════════════════════                         │
     │                                                              │
     │  ✓ Task ID validation (alphanumeric only)                    │
     │  ✓ No ".." or "/" in paths                                   │
     │  ✓ Resolve and verify containment                            │
     │                                                              │
     │  "../etc/passwd" → BLOCKED (PathTraversalError)              │
     │  "valid-task-id" → OK                                        │
     └─────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
     ┌─────────────────────────────────────────────────────────────┐
     │  LAYER 3: File Locking                                       │
     │  ══════════════════════                                      │
     │                                                              │
     │  ✓ Advisory locking with fcntl                               │
     │  ✓ Atomic writes (temp + rename)                             │
     │  ✓ Stale lock detection                                      │
     │                                                              │
     │  Protected files: DESIGN.md, CLAUDE.md, mode.json            │
     └─────────────────────────────────────────────────────────────┘
```

---

## 9. Quick Reference Card

```
╔═══════════════════════════════════════════════════════════════════════╗
║                    MULTI-AGENT QUICK REFERENCE                         ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  MODE COMMANDS                                                         ║
║  ────────────                                                          ║
║  !solo     → Claude only, no Codex/Gemini                              ║
║  !consult  → Ask permission before delegating                          ║
║  !auto     → Auto-delegate without asking                              ║
║  !codex    → Only Codex allowed                                        ║
║  !gemini   → Only Gemini allowed                                       ║
║                                                                        ║
║  TRIGGER EXAMPLES                                                      ║
║  ────────────────                                                      ║
║  "design" "architect" "debug" "review"  → Routes to CODEX              ║
║  "research" "docs" "pdf" "codebase"     → Routes to GEMINI             ║
║                                                                        ║
║  OUTPUT LOCATIONS                                                      ║
║  ────────────────                                                      ║
║  .claude/docs/research/  → Gemini findings                             ║
║  .claude/docs/design/    → Codex recommendations                       ║
║  .claude/session/        → Mode state                                  ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

*Created: 2026-02-05*
