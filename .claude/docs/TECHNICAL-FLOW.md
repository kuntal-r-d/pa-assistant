# Multi-Agent Workflow Technical Flow

> Step-by-step explanation of how the multi-agent system works internally

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INPUT                                      │
│                         "Help me debug this error"                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HOOK: UserPromptSubmit                               │
│                         (.claude/hooks/agent-router.py)                      │
│                                                                              │
│  1. Receive user prompt                                                      │
│  2. Check for manual overrides (!codex, !gemini, !direct)                   │
│  3. Calculate weighted scores for Codex and Gemini triggers                 │
│  4. Return routing suggestion with confidence level                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CLAUDE CODE                                       │
│                     (Main Orchestrator - Opus 4.5)                          │
│                                                                              │
│  Sees: User prompt + Routing suggestion                                      │
│  Decides: Handle directly OR delegate to Codex/Gemini                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
            ┌───────────┐    ┌───────────┐    ┌───────────┐
            │  Direct   │    │   Codex   │    │  Gemini   │
            │ Execution │    │    CLI    │    │    CLI    │
            └───────────┘    └───────────┘    └───────────┘
```

---

## Step-by-Step Flow

### Step 1: User Submits Prompt

User types a message in Claude Code:
```
"Help me debug this authentication error in the login flow"
```

---

### Step 2: UserPromptSubmit Hook Fires

**File:** `.claude/hooks/agent-router.py`

**Trigger:** Every user message

**Process:**

```python
# 1. Check for manual override
if prompt.startswith("!codex"):
    return RoutingDecision(agent="codex", confidence=1.0)
if prompt.startswith("!gemini"):
    return RoutingDecision(agent="gemini", confidence=1.0)
if prompt.startswith("!direct"):
    return RoutingDecision(agent=None)  # Skip suggestion

# 2. Calculate Codex score
codex_triggers = {"debug": 3, "error": 2, "bug": 3, "design": 3, ...}
codex_score = sum(weight for trigger, weight in codex_triggers.items()
                  if trigger in prompt.lower())

# 3. Calculate Gemini score
gemini_triggers = {"research": 3, "docs": 2, "pdf": 4, ...}
gemini_score = sum(weight for trigger, weight in gemini_triggers.items()
                   if trigger in prompt.lower())

# 4. Determine winner (if above threshold)
if codex_score > gemini_score and codex_score >= MIN_CONFIDENCE:
    return RoutingDecision(agent="codex", confidence=normalized_score)
```

**Output (to Claude):**
```
[Agent Routing] Matched 2 Codex trigger(s) (confidence: medium, 55%).
Triggers: debug, error.
This task may benefit from Codex CLI's deep reasoning.
Consider: `codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "..."`
Override with !direct to skip.
```

---

### Step 3: Claude Receives Context

Claude Code now sees:
1. Original user prompt
2. Routing suggestion from hook
3. Project rules (from `.claude/rules/`)

Claude decides whether to:
- Handle the task directly
- Spawn a subagent to call Codex
- Spawn a subagent to call Gemini

---

### Step 4a: Direct Execution Path

If Claude handles directly:

```
Claude → Uses Read/Edit/Write/Bash tools → Returns result to user
```

No additional hooks fire beyond standard tool hooks.

---

### Step 4b: Codex Delegation Path

If Claude decides to consult Codex:

```python
# Claude spawns a subagent
Task(
    subagent_type="general-purpose",
    prompt="""
    SUBAGENT CONSTRAINTS:
    - Do NOT modify any files
    - Return analysis as TEXT ONLY

    Consult Codex about debugging authentication errors:

    codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "
    Analyze this authentication error and suggest root cause...
    " 2>/dev/null

    Return concise summary.
    """
)
```

**Subagent executes Bash command:**
```bash
codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "..."
```

---

### Step 5: PreToolUse Hooks Fire (if editing files)

When Claude/subagent tries to Edit or Write a file:

**Hook 1:** `check-file-lock.py`
```
┌─────────────────────────────────────────────────────┐
│  PreToolUse: Edit/Write                              │
│                                                      │
│  1. Is this a protected file? (DESIGN.md, etc.)     │
│  2. Check .claude/locks/ for existing lock          │
│  3. If locked → BLOCK operation, return error       │
│  4. If not locked → ALLOW operation                 │
└─────────────────────────────────────────────────────┘
```

**Hook 2:** `check-codex-before-write.py`
```
┌─────────────────────────────────────────────────────┐
│  PreToolUse: Edit/Write                              │
│                                                      │
│  1. Analyze file path and content                   │
│  2. Check for design indicators (architecture, etc.)│
│  3. If design-critical → Suggest Codex review       │
│  4. Return suggestion (advisory, non-blocking)      │
└─────────────────────────────────────────────────────┘
```

---

### Step 6: Tool Executes

The actual tool (Read, Edit, Write, Bash) executes.

---

### Step 7: PostToolUse Hooks Fire

**For Bash commands (Codex/Gemini calls):**

**Hook:** `log-cli-tools.py`
```
┌─────────────────────────────────────────────────────┐
│  PostToolUse: Bash                                   │
│                                                      │
│  1. Check if command contains 'codex' or 'gemini'   │
│  2. Extract prompt from command                     │
│  3. Filter sensitive data (API keys, passwords)     │
│  4. Check log size, rotate if needed                │
│  5. Append to .claude/logs/cli-tools.jsonl          │
└─────────────────────────────────────────────────────┘

Log Entry:
{
  "timestamp": "2026-02-04T10:30:00Z",
  "trace_id": "a1b2c3d4",
  "session_id": "unknown",
  "tool": "codex",
  "model": "gpt-5.2-codex",
  "prompt": "Analyze this authentication error...",
  "response": "The root cause appears to be...",
  "success": true,
  "exit_code": 0,
  "latency_ms": 2500
}
```

**For Edit/Write operations:**

**Hook:** `lint-on-save.py`
```
┌─────────────────────────────────────────────────────┐
│  PostToolUse: Edit/Write                             │
│                                                      │
│  1. Check if file is TypeScript/JavaScript          │
│  2. Run ESLint on the file                          │
│  3. Run Prettier on the file                        │
│  4. Report any issues found                         │
└─────────────────────────────────────────────────────┘
```

**Hook:** `post-implementation-review.py`
```
┌─────────────────────────────────────────────────────┐
│  PostToolUse: Edit/Write                             │
│                                                      │
│  1. Track cumulative lines changed                  │
│  2. If significant changes → Suggest Codex review   │
└─────────────────────────────────────────────────────┘
```

---

### Step 8: Result Returns to User

```
Subagent result → Claude (main) → Formats response → User sees output
```

---

## File Locking Flow

### When Lock is Acquired

```
┌─────────────────────────────────────────────────────┐
│  FileLock.acquire()                                  │
│                                                      │
│  1. Create .claude/locks/ directory if needed       │
│  2. Open lock file: DESIGN.md.lock                  │
│  3. Try fcntl.flock(fd, LOCK_EX | LOCK_NB)         │
│  4. If success:                                     │
│     - Write metadata: PID, file, timestamp, proc_start│
│     - Return True                                   │
│  5. If blocked:                                     │
│     - Check if stale (process dead, PID reused)    │
│     - If stale → cleanup and retry                  │
│     - If not stale → wait and retry                 │
│     - If timeout → Return False                     │
└─────────────────────────────────────────────────────┘
```

### Lock File Format

```
.claude/locks/DESIGN.md.lock
├── Line 1: PID (e.g., 12345)
├── Line 2: File path
├── Line 3: Lock timestamp (Unix epoch)
└── Line 4: Process start time (for PID reuse detection)
```

### Stale Lock Detection

```python
def _is_stale_lock():
    # 1. Process dead?
    try:
        os.kill(pid, 0)  # Check if process exists
    except OSError:
        return True  # Process dead → stale

    # 2. PID reused? (different process with same PID)
    if current_proc_start != lock_proc_start:
        return True  # Different process → stale

    # 3. Timeout exceeded?
    if time.time() - lock_time > 60:
        return True  # Too old → stale

    return False
```

---

## Sensitive Data Filtering Flow

```
┌─────────────────────────────────────────────────────┐
│  filter_sensitive_data(text)                         │
│                                                      │
│  Input: "Use API_KEY=sk-1234567890abcdef"           │
│                                                      │
│  Patterns checked:                                  │
│  ├── API keys: api[_-]?key → [REDACTED]            │
│  ├── Passwords: password|secret → [REDACTED]        │
│  ├── Bearer tokens: bearer xyz → [REDACTED]         │
│  ├── JWT: eyJ...eyJ...sig → [REDACTED_JWT]         │
│  ├── AWS keys: aws_access_key → [REDACTED]         │
│  └── Connection strings: postgres://user:pass@     │
│                                                      │
│  Output: "Use API_KEY=[REDACTED]"                   │
└─────────────────────────────────────────────────────┘
```

---

## Log Rotation Flow

```
┌─────────────────────────────────────────────────────┐
│  rotate_log_if_needed()                              │
│                                                      │
│  1. Check cli-tools.jsonl size                      │
│  2. If size < 50MB → do nothing                     │
│  3. If size >= 50MB:                                │
│     ├── cli-tools.jsonl.4 → cli-tools.jsonl.5      │
│     ├── cli-tools.jsonl.3 → cli-tools.jsonl.4      │
│     ├── cli-tools.jsonl.2 → cli-tools.jsonl.3      │
│     ├── cli-tools.jsonl.1 → cli-tools.jsonl.2      │
│     ├── cli-tools.jsonl → cli-tools.jsonl.1        │
│     └── (cli-tools.jsonl.5 deleted if exists)      │
└─────────────────────────────────────────────────────┘
```

---

## Hook Execution Order

### For User Prompt

```
1. UserPromptSubmit
   └── agent-router.py (routing suggestion)
```

### For Edit/Write Operations

```
1. PreToolUse
   ├── check-file-lock.py (BLOCKING if locked)
   └── check-codex-before-write.py (advisory)

2. [Tool Executes]

3. PostToolUse
   ├── lint-on-save.py (runs linter)
   └── post-implementation-review.py (review suggestion)
```

### For Bash Operations

```
1. PreToolUse
   └── (none currently)

2. [Tool Executes]

3. PostToolUse
   ├── post-test-analysis.py (if test/build command)
   └── log-cli-tools.py (if codex/gemini command)
```

### For Task Operations

```
1. PreToolUse
   └── (none currently)

2. [Tool Executes]

3. PostToolUse
   └── check-codex-after-plan.py (review suggestion)
```

### For WebSearch/WebFetch

```
1. PreToolUse
   └── suggest-gemini-research.py (advisory)

2. [Tool Executes]

3. PostToolUse
   └── (none currently)
```

---

## Configuration Files

### .claude/settings.json

```json
{
  "hooks": {
    "UserPromptSubmit": [...],
    "PreToolUse": [
      { "matcher": "Edit|Write", "hooks": [...] },
      { "matcher": "WebSearch|WebFetch", "hooks": [...] }
    ],
    "PostToolUse": [
      { "matcher": "Task", "hooks": [...] },
      { "matcher": "Bash", "hooks": [...] },
      { "matcher": "Edit|Write", "hooks": [...] }
    ]
  },
  "permissions": {
    "allow": [...],
    "deny": [".env", "*.pem", "*.key", ...]
  }
}
```

### .claude/rules/

```
.claude/rules/
├── codex-delegation.md    # When/how to use Codex
├── gemini-delegation.md   # When/how to use Gemini
├── security.md            # Security guidelines
├── coding-principles.md   # Code style rules
├── testing.md             # Testing guidelines
└── dev-environment.md     # Dev setup
```

### .claude/lib/

```
.claude/lib/
├── __init__.py           # Exports: FileLock, with_retry, CircuitBreaker
├── file_lock.py          # Advisory file locking
├── retry.py              # Exponential backoff retry
└── circuit_breaker.py    # Circuit breaker pattern
```

---

## Data Flow Diagram

```
┌──────────┐     ┌─────────────┐     ┌─────────────┐     ┌──────────┐
│   User   │────▶│ Hook:Router │────▶│ Claude Code │────▶│  Result  │
└──────────┘     └─────────────┘     └─────────────┘     └──────────┘
                                            │
                       ┌────────────────────┼────────────────────┐
                       ▼                    ▼                    ▼
                 ┌──────────┐         ┌──────────┐         ┌──────────┐
                 │ Subagent │         │ Subagent │         │  Direct  │
                 │ (Codex)  │         │ (Gemini) │         │  Tools   │
                 └──────────┘         └──────────┘         └──────────┘
                       │                    │                    │
                       ▼                    ▼                    ▼
                 ┌──────────┐         ┌──────────┐         ┌──────────┐
                 │ Bash:    │         │ Bash:    │         │ Read/    │
                 │ codex    │         │ gemini   │         │ Edit/    │
                 │ exec ... │         │ -p "..." │         │ Write    │
                 └──────────┘         └──────────┘         └──────────┘
                       │                    │                    │
                       └────────────────────┼────────────────────┘
                                            ▼
                                    ┌──────────────┐
                                    │ PostToolUse  │
                                    │ Hooks        │
                                    │ (logging,    │
                                    │  linting)    │
                                    └──────────────┘
                                            │
                                            ▼
                                    ┌──────────────┐
                                    │ .claude/logs │
                                    │ cli-tools.   │
                                    │ jsonl        │
                                    └──────────────┘
```

---

## Error Handling

### Hook Errors

All hooks follow this pattern:
```python
try:
    # Hook logic
    ...
except Exception as e:
    logger.error(f"Hook error: {e}", exc_info=True)
    sys.exit(0)  # Don't block on errors
```

- Errors are logged to `.claude/logs/hook-errors.log`
- Hooks exit with code 0 to not block operations
- Only `check-file-lock.py` can block (exits with code 1)

### CLI Tool Errors

If Codex/Gemini CLI fails:
1. Error captured in `tool_response.exit_code`
2. Logged with `success: false` in cli-tools.jsonl
3. Claude receives error and can retry or fallback

---

## Performance Characteristics

| Operation | Typical Latency |
|-----------|-----------------|
| UserPromptSubmit hook | ~5ms |
| PreToolUse hooks | ~10ms each |
| PostToolUse hooks | ~10-50ms each |
| Codex CLI call | 2-10 seconds |
| Gemini CLI call | 1-5 seconds |
| File lock acquire | ~1ms |
| Log rotation | ~50ms |

---

## Security Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│  Claude Code (Full Access)                                       │
│  ├── Read/Write project files                                   │
│  ├── Execute bash commands                                      │
│  └── Spawn subagents                                            │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Subagent (Constrained by Prompt)                           ││
│  │  ├── Should NOT modify files (advisory)                     ││
│  │  └── Can call Codex/Gemini CLI                              ││
│  │                                                              ││
│  │  ┌─────────────────────────────────────────────────────────┐││
│  │  │  Codex CLI (Sandboxed)                                  │││
│  │  │  ├── --sandbox read-only: Can only read files           │││
│  │  │  └── --sandbox workspace-write: Can write project files │││
│  │  └─────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting Flow Issues

### Hook Not Firing

1. Check `.claude/settings.json` has hook registered
2. Verify hook file is executable: `chmod +x hook.py`
3. Check hook timeout (default 5-10s)
4. Look for errors in `.claude/logs/hook-errors.log`

### Routing Not Working

1. Check prompt length (> 10 chars required)
2. Verify trigger keywords present
3. Check confidence threshold (30% minimum)
4. Use manual override: `!codex` or `!gemini`

### Lock Not Releasing

1. Check if process died: `ps aux | grep <pid>`
2. Wait 60s for auto-cleanup
3. Manually remove: `rm .claude/locks/*.lock`
4. Check for stale lock in logs
