# Extensible Multi-Agent Workflow Architecture

> How to integrate multiple LLM providers (Codex, Gemini, Ollama, OpenCode, etc.)

---

## 1. Extended Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 USER                                         │
│                            (Your prompts)                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CLAUDE CODE (Opus 4.5)                              │
│                          ══════════════════════                              │
│                          Main Orchestrator                                   │
│                                                                              │
│   • Receives prompts          • Coordinates all subagents                    │
│   • Reads/writes code         • Synthesizes final responses                  │
│   • Runs commands             • Decides which agent to use                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
              ▼                       ▼                       ▼
┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
│    CLOUD AGENTS     │ │    LOCAL AGENTS     │ │   CUSTOM AGENTS     │
│    ════════════     │ │    ════════════     │ │   ═════════════     │
│                     │ │                     │ │                     │
│  ┌───────────────┐  │ │  ┌───────────────┐  │ │  ┌───────────────┐  │
│  │  Codex CLI    │  │ │  │  Ollama       │  │ │  │  OpenCode     │  │
│  │  (OpenAI)     │  │ │  │  (Local LLMs) │  │ │  │  (OSS)        │  │
│  │               │  │ │  │               │  │ │  │               │  │
│  │  • Design     │  │ │  │  • Fast local │  │ │  │  • Code gen   │  │
│  │  • Debug      │  │ │  │  • Private    │  │ │  │  • Refactor   │  │
│  │  • Review     │  │ │  │  • No cost    │  │ │  │  • Analysis   │  │
│  └───────────────┘  │ │  └───────────────┘  │ │  └───────────────┘  │
│                     │ │                     │ │                     │
│  ┌───────────────┐  │ │  ┌───────────────┐  │ │  ┌───────────────┐  │
│  │  Gemini CLI   │  │ │  │  LM Studio    │  │ │  │  Aider        │  │
│  │  (Google)     │  │ │  │  (Local UI)   │  │ │  │  (Coding)     │  │
│  │               │  │ │  │               │  │ │  │               │  │
│  │  • Research   │  │ │  │  • GUI-based  │  │ │  │  • Pair prog  │  │
│  │  • Multimodal │  │ │  │  • Multiple   │  │ │  │  • Git-aware  │  │
│  │  • Web search │  │ │  │    models     │  │ │  │  • Edits      │  │
│  └───────────────┘  │ │  └───────────────┘  │ │  └───────────────┘  │
│                     │ │                     │ │                     │
│  ┌───────────────┐  │ │  ┌───────────────┐  │ │  ┌───────────────┐  │
│  │  Claude API   │  │ │  │  LocalAI      │  │ │  │  Continue     │  │
│  │  (Anthropic)  │  │ │  │  (OpenAI API) │  │ │  │  (IDE Agent)  │  │
│  └───────────────┘  │ │  └───────────────┘  │ │  └───────────────┘  │
└─────────────────────┘ └─────────────────────┘ └─────────────────────┘
```

---

## 2. Extended Mode System

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SESSION MODES (Current + Extended)                 │
└─────────────────────────────────────────────────────────────────────────────┘

  CURRENT MODES                           EXTENDED MODES (Proposed)
  ═════════════                           ════════════════════════

  ┌─────────┐                             ┌─────────┐
  │  !solo  │  Claude only                │ !ollama │  Ollama only
  └─────────┘                             └─────────┘

  ┌─────────┐                             ┌─────────┐
  │!consult │  Ask before delegating      │!opencode│  OpenCode only
  └─────────┘                             └─────────┘

  ┌─────────┐                             ┌─────────┐
  │  !auto  │  Auto-delegate              │ !local  │  Local models only
  └─────────┘                             └─────────┘

  ┌─────────┐                             ┌─────────┐
  │ !codex  │  Codex only                 │  !fast  │  Fastest available
  └─────────┘                             └─────────┘

  ┌─────────┐                             ┌─────────┐
  │ !gemini │  Gemini only                │ !cheap  │  Lowest cost option
  └─────────┘                             └─────────┘

                                          ┌─────────┐
                                          │!private │  Only local/private
                                          └─────────┘
```

---

## 3. Extended Router Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER PROMPT                                     │
│                     "Help me design an API"                                  │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AGENT ROUTER                                        │
│                     (agent-router.py)                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    STEP 1: Mode Check                                │   │
│   │                    ══════════════════                                │   │
│   │                                                                      │   │
│   │   Read mode.json → Get current mode                                  │   │
│   │                                                                      │   │
│   │   {                                                                  │   │
│   │     "mode": "auto",                                                  │   │
│   │     "first_delegation_done": true,                                   │   │
│   │     "allowed_agents": ["codex", "gemini", "ollama"]  // Extended     │   │
│   │   }                                                                  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                          │
│                                   ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    STEP 2: Intent Classification                     │   │
│   │                    ═════════════════════════════                     │   │
│   │                                                                      │   │
│   │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │   │
│   │   │ LLM Stage   │ ─▶ │  Keyword    │ ─▶ │  Fallback   │             │   │
│   │   │ (Gemini)    │    │  Matching   │    │  Default    │             │   │
│   │   └─────────────┘    └─────────────┘    └─────────────┘             │   │
│   │                                                                      │   │
│   │   Result: { agent: "codex", confidence: 0.75, intent: "design" }     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                          │
│                                   ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    STEP 3: Agent Selection                           │   │
│   │                    ═══════════════════════                           │   │
│   │                                                                      │   │
│   │   Check if suggested agent is allowed in current mode                │   │
│   │                                                                      │   │
│   │   SOLO mode?     → No delegation, exit                               │   │
│   │   Agent allowed? → Proceed                                           │   │
│   │   Agent blocked? → Try alternative or exit                           │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                          │
│                                   ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    STEP 4: Output Generation                         │   │
│   │                    ═════════════════════════                         │   │
│   │                                                                      │   │
│   │   CONSULT mode → [Agent Suggestion] Ask permission                   │   │
│   │   AUTO mode    → [Auto-Routing] Silent delegation                    │   │
│   │                                                                      │   │
│   │   Output: { "additionalContext": "[Auto-Routing] Codex CLI..." }     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Agent Selection Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AGENT SELECTION MATRIX                                │
├──────────────┬─────────┬─────────┬─────────┬─────────┬──────────┬──────────┤
│    TASK      │  Codex  │ Gemini  │ Ollama  │OpenCode │  Local   │  Cloud   │
├──────────────┼─────────┼─────────┼─────────┼─────────┼──────────┼──────────┤
│ Design       │   ★★★   │   ★★    │   ★★    │   ★★    │    ★★    │   ★★★    │
│ Debug        │   ★★★   │   ★★    │   ★★    │   ★★★   │    ★★    │   ★★★    │
│ Research     │   ★★    │   ★★★   │   ★     │   ★     │    ★     │   ★★★    │
│ Code Review  │   ★★★   │   ★★    │   ★★    │   ★★★   │    ★★    │   ★★★    │
│ Multimodal   │   ★     │   ★★★   │   ★     │   ★     │    ★     │   ★★★    │
│ Fast/Simple  │   ★★    │   ★★    │   ★★★   │   ★★    │   ★★★    │    ★★    │
│ Private Data │   ★     │   ★     │   ★★★   │   ★★    │   ★★★    │    ★     │
│ No Cost      │   ★     │   ★     │   ★★★   │   ★★    │   ★★★    │    ★     │
│ Offline      │   ✗     │   ✗     │   ★★★   │   ★★    │   ★★★    │    ✗     │
├──────────────┴─────────┴─────────┴─────────┴─────────┴──────────┴──────────┤
│ ★★★ = Best choice   ★★ = Good   ★ = Limited   ✗ = Not available            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Extended Trigger Keywords

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TRIGGER KEYWORDS                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              → CODEX                                         │
│                         (Cloud - Deep Reasoning)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  design (3)  │  architecture (3)  │  debug (3)  │  review (2)  │  codex (4) │
│  pattern (3) │  trade-off (2)     │  bug (3)    │  compare (2) │  think (4) │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              → GEMINI                                        │
│                        (Cloud - Research/Multimodal)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  research (3) │  docs (2)     │  pdf (4)    │  video (4)  │  gemini (4)     │
│  investigate  │  library (2)  │  audio (4)  │  codebase   │  web search     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              → OLLAMA (Proposed)                             │
│                          (Local - Fast/Private)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  quick (3)   │  fast (3)     │  local (4)  │  private (4) │  ollama (4)    │
│  simple (2)  │  offline (4)  │  free (3)   │  no-cloud    │  llama (4)     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                             → OPENCODE (Proposed)                            │
│                           (OSS - Code Specialist)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  generate (3) │  refactor (3) │  complete (3) │  opencode (4) │  oss (3)    │
│  snippet (2)  │  boilerplate  │  template (2) │  coding (3)   │  opensource │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Complete Flow with Multiple Providers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ USER: "I need to quickly refactor this function, keep it private"           │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            AGENT ROUTER                                      │
│                                                                              │
│  Keywords found:                                                             │
│  • "quickly" → fast (weight: 3) → OLLAMA                                     │
│  • "refactor" → refactor (weight: 3) → CODEX or OPENCODE                     │
│  • "private" → private (weight: 4) → OLLAMA                                  │
│                                                                              │
│  Scores:                                                                     │
│  • Ollama: 7 points (quick + private)                                        │
│  • Codex: 3 points (refactor)                                                │
│  • OpenCode: 3 points (refactor)                                             │
│                                                                              │
│  Winner: OLLAMA (highest score + privacy requirement)                        │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MODE CHECK                                           │
│                                                                              │
│  Current mode: AUTO                                                          │
│  Ollama allowed: YES                                                         │
│                                                                              │
│  Output: [Auto-Routing] Consulting Ollama for fast local processing          │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CLAUDE CODE                                          │
│                                                                              │
│  Sees: "[Auto-Routing] Intent: refactor. Consulting Ollama (local)..."       │
│                                                                              │
│  Action: Spawn subagent to call Ollama                                       │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUBAGENT EXECUTION                                   │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  Task Subagent                                                      │     │
│  │                                                                     │     │
│  │  1. Call Ollama CLI:                                                │     │
│  │     ollama run codellama "Refactor this function: ..."              │     │
│  │                                                                     │     │
│  │  2. Receive local response (fast, no API cost)                      │     │
│  │                                                                     │     │
│  │  3. Save output to: .claude/docs/local/task-xxx.md                  │     │
│  │                                                                     │     │
│  │  4. Return summary to Claude                                        │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FINAL RESPONSE                                       │
│                                                                              │
│  Claude synthesizes Ollama's output and responds to user                     │
│  (Data never left local machine!)                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Provider Configuration (Proposed)

```yaml
# .claude/config/agents.yaml (Proposed)

agents:
  # Cloud Agents
  codex:
    type: cloud
    cli: "codex exec --model gpt-5.2-codex --sandbox read-only --full-auto"
    triggers: [design, architecture, debug, review, trade-off]
    cost: high
    privacy: low
    speed: medium

  gemini:
    type: cloud
    cli: "gemini -p"
    triggers: [research, docs, pdf, video, codebase]
    cost: medium
    privacy: low
    speed: medium

  # Local Agents
  ollama:
    type: local
    cli: "ollama run"
    default_model: "codellama:13b"
    triggers: [quick, fast, local, private, offline]
    cost: free
    privacy: high
    speed: fast

  lmstudio:
    type: local
    cli: "lms chat"
    triggers: [local, private]
    cost: free
    privacy: high
    speed: medium

  # OSS Agents
  opencode:
    type: oss
    cli: "opencode"
    triggers: [generate, refactor, complete, snippet]
    cost: free
    privacy: medium
    speed: fast

  aider:
    type: oss
    cli: "aider --message"
    triggers: [pair, edit, git-aware]
    cost: varies
    privacy: varies
    speed: medium

# Selection Rules
selection:
  privacy_required:
    prefer: [ollama, lmstudio]
    avoid: [codex, gemini]

  offline_mode:
    only: [ollama, lmstudio]

  cost_sensitive:
    prefer: [ollama, opencode]
    limit: [codex, gemini]

  speed_priority:
    prefer: [ollama]
    fallback: [codex, gemini]
```

---

## 8. Mode Transition Diagram

```
                              ┌─────────────────┐
                              │   START/RESET   │
                              └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │   SOLO (Default)│◄─────── !solo
                              │   Claude only   │
                              └────────┬────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
              ▼                        ▼                        ▼
     ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
     │    CONSULT      │◄──── │      AUTO       │◄──── │   AGENT-ONLY    │
     │  Ask permission │      │ Auto-delegate   │      │  (codex/gemini/ │
     │  every time     │      │ silently        │      │   ollama/etc)   │
     └────────┬────────┘      └────────┬────────┘      └────────┬────────┘
              │                        │                        │
              │       !consult         │        !auto           │    !<agent>
              │◄───────────────────────┤◄───────────────────────┤
              │                        │                        │
              └────────────────────────┼────────────────────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │  HYBRID MODES   │
                              │   (Proposed)    │
                              └─────────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
              ▼                        ▼                        ▼
     ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
     │    !local       │      │     !cloud      │      │    !hybrid      │
     │ Only local LLMs │      │ Only cloud LLMs │      │ Best of both    │
     │ (Ollama, etc)   │      │ (Codex, Gemini) │      │ Auto-select     │
     └─────────────────┘      └─────────────────┘      └─────────────────┘
```

---

## 9. CLI Command Examples

```bash
# Current Commands (Working Now)
┌─────────────────────────────────────────────────────────────────────────────┐
│ Codex CLI                                                                    │
│ ──────────                                                                   │
│ codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "..."       │
│                                                                              │
│ Gemini CLI                                                                   │
│ ──────────                                                                   │
│ gemini -p "Research: ..." 2>/dev/null                                        │
└─────────────────────────────────────────────────────────────────────────────┘

# Proposed Commands (To Add)
┌─────────────────────────────────────────────────────────────────────────────┐
│ Ollama CLI                                                                   │
│ ──────────                                                                   │
│ ollama run codellama "Refactor this code: ..."                               │
│ ollama run llama2 "Explain this error: ..."                                  │
│ ollama run mistral "Quick analysis: ..."                                     │
│                                                                              │
│ OpenCode CLI                                                                 │
│ ────────────                                                                 │
│ opencode generate "Create a REST endpoint for..."                            │
│ opencode refactor "Simplify this function..."                                │
│                                                                              │
│ Aider CLI                                                                    │
│ ─────────                                                                    │
│ aider --message "Add error handling to..."                                   │
│                                                                              │
│ LM Studio (via API)                                                          │
│ ───────────────────                                                          │
│ curl http://localhost:1234/v1/chat/completions -d '{"prompt": "..."}'        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Implementation Roadmap

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        IMPLEMENTATION PHASES                                 │
└─────────────────────────────────────────────────────────────────────────────┘

PHASE 1: Current (DONE)
════════════════════════
  ✅ Codex integration
  ✅ Gemini integration
  ✅ Session modes (SOLO/CONSULT/AUTO/CODEX/GEMINI)
  ✅ Intent classification (LLM + keyword)
  ✅ Security fixes (injection, locking, traversal)

PHASE 2: Local Models
════════════════════════
  ⬜ Add Ollama support
     - CLI wrapper: ollama run <model> "<prompt>"
     - Trigger keywords: quick, fast, local, private
     - New mode: !ollama

  ⬜ Add LM Studio support (OpenAI-compatible API)
     - HTTP client for localhost:1234
     - Auto-detect if running

PHASE 3: OSS Tools
════════════════════════
  ⬜ Add OpenCode support
  ⬜ Add Aider support
  ⬜ Configurable agent registry (agents.yaml)

PHASE 4: Smart Selection
════════════════════════
  ⬜ Cost-aware routing
  ⬜ Privacy-aware routing
  ⬜ Speed-aware routing
  ⬜ Fallback chains (if Codex fails → try Ollama)

PHASE 5: Hybrid Modes
════════════════════════
  ⬜ !local mode (only local models)
  ⬜ !cloud mode (only cloud models)
  ⬜ !hybrid mode (auto-select best)
  ⬜ !private mode (never send to cloud)
```

---

## 11. Summary: How It All Fits Together

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│                         THE MULTI-AGENT ECOSYSTEM                            │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                           USER                                       │    │
│  │                      "Your prompt here"                              │    │
│  └───────────────────────────────┬─────────────────────────────────────┘    │
│                                  │                                           │
│                                  ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    AGENT ROUTER (Hook)                               │    │
│  │         Classifies intent + Checks mode + Selects agent              │    │
│  └───────────────────────────────┬─────────────────────────────────────┘    │
│                                  │                                           │
│                                  ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    CLAUDE CODE (Orchestrator)                        │    │
│  │              Sees routing suggestion, decides action                 │    │
│  └───────────────────────────────┬─────────────────────────────────────┘    │
│                                  │                                           │
│          ┌───────────────────────┼───────────────────────┐                  │
│          │                       │                       │                  │
│          ▼                       ▼                       ▼                  │
│  ┌───────────────┐       ┌───────────────┐       ┌───────────────┐         │
│  │    CLOUD      │       │    LOCAL      │       │     OSS       │         │
│  │   AGENTS      │       │   AGENTS      │       │   AGENTS      │         │
│  │               │       │               │       │               │         │
│  │ • Codex       │       │ • Ollama      │       │ • OpenCode    │         │
│  │ • Gemini      │       │ • LM Studio   │       │ • Aider       │         │
│  │ • Claude API  │       │ • LocalAI     │       │ • Continue    │         │
│  └───────┬───────┘       └───────┬───────┘       └───────┬───────┘         │
│          │                       │                       │                  │
│          └───────────────────────┼───────────────────────┘                  │
│                                  │                                           │
│                                  ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    FINDINGS RETURNED                                 │    │
│  │         Subagent returns summary → Claude synthesizes               │    │
│  └───────────────────────────────┬─────────────────────────────────────┘    │
│                                  │                                           │
│                                  ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    FINAL RESPONSE TO USER                            │    │
│  │                 (Seamless - only results shown)                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Document created: 2026-02-05*
*This document outlines both current functionality and proposed extensions.*
