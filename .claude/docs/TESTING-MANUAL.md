# Multi-Agent Workflow Testing Manual

> Complete guide for testing all session modes and security features.

---

## Quick Reference

### Mode Commands

| Command | Mode | Behavior |
|---------|------|----------|
| `!solo` | SOLO | Claude only, no external LLM delegation |
| `!consult` | CONSULT | Ask permission before each delegation |
| `!auto` | AUTO | Auto-delegate without prompts |
| `!codex` | CODEX | Only Codex consultation allowed |
| `!gemini` | GEMINI | Only Gemini consultation allowed |
| `!ollama` | OLLAMA | Only local Ollama models allowed (free/private) |
| `!local` | LOCAL | Alias for Ollama - local models only |

### Current Mode Check

```bash
cat .claude/session/mode.json
```

---

## Test Cases by Mode

### 1. SOLO Mode (`!solo`)

**Purpose:** Claude handles everything directly with Claude subagents only. No Codex/Gemini CLI calls.

#### Setup
```
!solo
```

#### Test Prompts & Expected Results

| # | Test Prompt | Expected Behavior |
|---|-------------|-------------------|
| 1 | `Help me design an authentication system` | **No routing suggestion.** Claude handles directly. |
| 2 | `Research best practices for caching` | **No routing suggestion.** Claude handles directly. |
| 3 | `Debug this error in my code` | **No routing suggestion.** Claude handles directly. |
| 4 | `!codex review this code` | **Mode change to CODEX**, not a Codex call. |

#### What You Should See
- No `[Agent Suggestion]` or `[Auto-Routing]` messages
- Claude responds directly without mentioning Codex/Gemini
- Claude may use its own subagents (Task tool) but won't call CLI tools

---

### 2. CONSULT Mode (`!consult`)

**Purpose:** Ask user permission before each external LLM delegation.

#### Setup
```
!consult
```

#### Test Prompts & Expected Results

| # | Test Prompt | Expected Output |
|---|-------------|-----------------|
| 1 | `Help me design a REST API` | `[Agent Suggestion] ... Would you like me to consult Codex for design/architecture recommendations?` |
| 2 | `Research React 19 features` | `[Agent Suggestion] ... Would you like me to consult Gemini for research/documentation?` |
| 3 | `Fix the typo on line 42` | **No suggestion** (simple task, low confidence) |
| 4 | `Compare Redis vs Memcached` | `[Agent Suggestion] ... Codex for design/architecture...` |

#### What You Should See
```
[Agent Suggestion] This looks like a {intent} task. Would you like me to consult {Agent} for {purpose}?
(Confidence: {level}, {%}. Source: {llm/keyword})

Options:
- Say 'yes' to consult {Agent}
- Say 'no' to handle directly
- Use '!solo' to switch to solo mode (no more prompts)
```

#### Response Options
- **"yes"** - Claude spawns subagent to consult Codex/Gemini
- **"no"** - Claude handles directly
- **"!solo"** - Switch to SOLO mode

---

### 3. AUTO Mode (`!auto`)

**Purpose:** Automatically delegate to appropriate agent without asking permission.

#### Setup
```
!auto
```

#### Test Prompts & Expected Results

| # | Test Prompt | Expected Output |
|---|-------------|-----------------|
| 1 | `Design a microservices architecture` | `[Auto-Routing] Intent: keyword_match. Consulting Codex CLI for recommendations.` |
| 2 | `Research Kubernetes best practices 2026` | `[Auto-Routing] Intent: keyword_match. Consulting Gemini CLI for research.` |
| 3 | `Review my authentication code` | `[Auto-Routing] ... Consulting Codex CLI...` |
| 4 | `Analyze this PDF document` | `[Auto-Routing] ... Consulting Gemini CLI...` (multimodal) |
| 5 | `Run the tests` | **No routing** (simple command) |

#### What You Should See
```
[Auto-Routing] Intent: {intent}. Consulting {Agent} CLI for {purpose}.
(Confidence: {level}, {%}. Source: {llm/keyword}. Reason: {explanation})
```

#### Key Behaviors
- No permission prompts
- Claude silently spawns subagent
- Only final results shown to user (per MEMORY.md preferences)

---

### 4. CODEX Mode (`!codex`)

**Purpose:** Only Codex consultation allowed. Asks permission once, then auto-delegates.

#### Setup
```
!codex
```

#### Test Prompts & Expected Results

| # | Test Prompt | First Time? | Expected Output |
|---|-------------|-------------|-----------------|
| 1 | `Design an API` | Yes | `[Agent Suggestion] ... Would you like me to consult Codex?` |
| 2 | `Debug this error` | No (after 1st delegation) | `[Auto-Routing] ... Consulting Codex CLI...` |
| 3 | `Research caching` | No | `[Auto-Routing] ... Consulting Codex CLI...` (forced to Codex, not Gemini) |

#### What You Should See
- **First delegation:** Permission prompt like CONSULT mode
- **Subsequent delegations:** Auto-routing like AUTO mode
- **Research prompts:** Routed to Codex (not Gemini) since only Codex is allowed

---

### 5. GEMINI Mode (`!gemini`)

**Purpose:** Only Gemini consultation allowed. Asks permission once, then auto-delegates.

#### Setup
```
!gemini
```

#### Test Prompts & Expected Results

| # | Test Prompt | First Time? | Expected Output |
|---|-------------|-------------|-----------------|
| 1 | `Research OAuth best practices` | Yes | `[Agent Suggestion] ... Would you like me to consult Gemini?` |
| 2 | `Look up React documentation` | No (after 1st) | `[Auto-Routing] ... Consulting Gemini CLI...` |
| 3 | `Design an authentication system` | No | `[Auto-Routing] ... Consulting Gemini CLI...` (forced to Gemini, not Codex) |

#### What You Should See
- **First delegation:** Permission prompt
- **Subsequent delegations:** Auto-routing
- **Design prompts:** Routed to Gemini (not Codex) since only Gemini is allowed

---

### 6. OLLAMA Mode (`!ollama` or `!local`)

**Purpose:** Only local Ollama models allowed. Free, private, offline processing.

#### Setup
```
!ollama
```
or
```
!local
```

#### Test Prompts & Expected Results

| # | Test Prompt | First Time? | Expected Output |
|---|-------------|-------------|-----------------|
| 1 | `Analyze this with a local model` | Yes | `[Agent Suggestion] ... Would you like me to consult Ollama (local model)?` |
| 2 | `Use llama to review this code` | No (after 1st) | `[Auto-Routing] ... Consulting Ollama (local model)...` |
| 3 | `Design an API` | No | `[Auto-Routing] ... Consulting Ollama (local model)...` (forced to Ollama) |
| 4 | `Process this confidential data` | No | `[Auto-Routing] ... Consulting Ollama (local model)...` |

#### What You Should See
- **First delegation:** Permission prompt
- **Subsequent delegations:** Auto-routing
- **All prompts:** Routed to Ollama (not Codex/Gemini) since only local is allowed

#### Use Cases for Ollama Mode
- **Privacy-sensitive tasks:** Confidential data processing
- **Offline work:** Air-gapped or no-internet environments
- **Cost control:** Free local processing
- **Self-hosted:** Complete control over model

---

## Trigger Keywords Reference

### Codex Triggers (Design/Debug/Review)

| Keyword | Weight | Category |
|---------|--------|----------|
| `design` | 3 | Design |
| `architecture` | 3 | Design |
| `debug` | 3 | Debug |
| `bug` | 3 | Debug |
| `error` | 2 | Debug |
| `fix` | 2 | Debug |
| `review` | 2 | Review |
| `compare` | 2 | Analysis |
| `trade-off` | 2 | Analysis |
| `implement` | 2 | Implementation |
| `build` | 2 | Implementation |
| `think deeper` | 4 | Explicit |
| `codex` | 4 | Explicit |
| `second opinion` | 4 | Explicit |

### Gemini Triggers (Research/Multimodal)

| Keyword | Weight | Category |
|---------|--------|----------|
| `research` | 3 | Research |
| `investigate` | 3 | Research |
| `look up` | 3 | Research |
| `documentation` | 2 | Docs |
| `docs` | 2 | Docs |
| `library` | 2 | Docs |
| `pdf` | 4 | Multimodal |
| `video` | 4 | Multimodal |
| `audio` | 4 | Multimodal |
| `entire codebase` | 4 | Large Context |
| `whole repository` | 4 | Large Context |
| `gemini` | 4 | Explicit |

### Ollama Triggers (Local/Privacy/Free)

| Keyword | Weight | Category |
|---------|--------|----------|
| `ollama` | 4 | Explicit |
| `local model` | 4 | Local |
| `no cloud` | 4 | Privacy |
| `air-gapped` | 4 | Privacy |
| `self-hosted` | 4 | Local |
| `on-device` | 4 | Local |
| `llama` | 4 | Model Name |
| `mistral` | 4 | Model Name |
| `codellama` | 4 | Model Name |
| `deepseek` | 4 | Model Name |
| `qwen` | 4 | Model Name |
| `local` | 3 | Local |
| `private` | 3 | Privacy |
| `offline` | 3 | Privacy |
| `confidential` | 3 | Privacy |
| `free` | 2 | Cost |
| `sensitive` | 2 | Privacy |

---

## Sample Test Session

### Complete Workflow Test

```bash
# 1. Start in SOLO mode
!solo
> "Design an API for user management"
# Expected: Claude handles directly, no routing

# 2. Switch to CONSULT mode
!consult
> "Design an API for user management"
# Expected: [Agent Suggestion] asks for Codex

# 3. Confirm delegation
> "yes"
# Expected: Claude spawns subagent, consults Codex, returns design

# 4. Switch to AUTO mode
!auto
> "Research JWT best practices 2026"
# Expected: [Auto-Routing] automatically consults Gemini

# 5. Test CODEX-only mode
!codex
> "Research caching strategies"
# Expected: Routes to Codex (not Gemini) since only Codex allowed

# 6. Reset to AUTO
!auto
```

---

## Security Test Cases

### 1. Command Injection (Fixed)

**Test:** Verify malicious input doesn't execute shell commands.

```bash
# Test prompt with shell injection attempt
> "; cat /etc/passwd; echo 'test"
```

**Expected:** Normal classification, no command execution. The fix uses list-based subprocess (`shell=False`).

### 2. Path Traversal (Fixed)

**Test:** Verify path traversal attempts are blocked.

```python
# In Python interpreter
from task_coordinator import TaskCoordinator, PathTraversalError

coordinator = TaskCoordinator()

# These should raise PathTraversalError
coordinator.get_research_path("../../../etc/passwd")
coordinator.get_research_path("task/../../../secret")
```

**Expected:** `PathTraversalError` raised for malicious task IDs.

### 3. File Locking (Fixed)

**Test:** Verify concurrent mode changes don't corrupt state.

```python
import threading
from session_mode import set_mode, AgentMode

def writer(mode, n):
    for _ in range(n):
        set_mode(mode)

# Concurrent writers
threads = [
    threading.Thread(target=writer, args=(AgentMode.AUTO, 10)),
    threading.Thread(target=writer, args=(AgentMode.SOLO, 10)),
]
for t in threads: t.start()
for t in threads: t.join()

# File should be valid JSON
cat .claude/session/mode.json
```

**Expected:** Valid JSON file, no corruption.

---

## CLI Testing Commands

### Quick Mode Test

```bash
# Test all modes with a design prompt
for mode in solo consult auto codex gemini ollama local; do
  echo "=== Testing $mode mode ==="
  python3 -c "
import sys; sys.path.insert(0, '.claude/lib')
from session_mode import set_mode, AgentMode
set_mode(AgentMode(\"$mode\"))
"
  echo '{"prompt": "Help me design an API"}' | python3 .claude/hooks/agent-router.py
  echo ""
done
```

### Test Ollama Mode Specifically

```bash
# Test Ollama mode with privacy-focused prompts
python3 -c "
import sys; sys.path.insert(0, '.claude/lib')
from session_mode import set_mode, AgentMode
set_mode(AgentMode.OLLAMA)
"

# These should route to Ollama
echo '{"prompt": "Analyze this confidential data with a local model"}' | python3 .claude/hooks/agent-router.py
echo '{"prompt": "Use llama to review this code"}' | python3 .claude/hooks/agent-router.py
echo '{"prompt": "Process this offline"}' | python3 .claude/hooks/agent-router.py
```

### Security Quick Check

```bash
python3 -c "
import sys; sys.path.insert(0, '.claude/lib')

# Test 1: Command injection protection
from intent_classifier import IntentClassifier
import inspect
source = inspect.getsource(IntentClassifier._classify_with_llm)
print('Command injection fix:', 'PASS' if 'shell=False' in source else 'FAIL')

# Test 2: Path traversal protection
from task_coordinator import TaskCoordinator, PathTraversalError
coord = TaskCoordinator()
try:
    coord.get_research_path('../etc/passwd')
    print('Path traversal fix: FAIL')
except (PathTraversalError, ValueError):
    print('Path traversal fix: PASS')

# Test 3: Protected files
from file_lock import PROTECTED_FILES
print('mode.json protected:', 'PASS' if 'mode.json' in PROTECTED_FILES else 'FAIL')
"
```

---

## Troubleshooting

### No Routing Suggestion Appearing

1. **Prompt too short:** Must be > 10 characters
2. **Low confidence:** Add explicit keywords like "design", "research", "debug"
3. **SOLO mode active:** Check `cat .claude/session/mode.json`

### Wrong Agent Suggested

1. Check trigger keywords in your prompt
2. Use explicit triggers: `!codex` prefix or "codex" keyword
3. Use mode-specific modes (`!codex`, `!gemini`) to force agent

### FileLock Warnings

The warning `FileLock not available` appears in CLI tests due to relative imports. This is normal - the lock works correctly when hooks load the module as a package.

---

## Expected Confidence Levels

| Level | Range | Meaning |
|-------|-------|---------|
| High | 70%+ | Strong keyword match, likely correct |
| Medium | 50-70% | Moderate match, suggestion reasonable |
| Low | 30-50% | Weak match, use judgment |
| None | <30% | No suggestion shown |

---

## File Locations

| File | Purpose |
|------|---------|
| `.claude/session/mode.json` | Current session mode state |
| `.claude/hooks/agent-router.py` | Main routing hook |
| `.claude/lib/session_mode.py` | Mode management |
| `.claude/lib/intent_classifier.py` | Intent classification |
| `.claude/lib/task_coordinator.py` | Task path management |
| `.claude/lib/file_lock.py` | File locking |
| `.claude/config/agents.yaml` | Agent configuration (extensibility) |
| `.claude/docs/research/` | Gemini research outputs |
| `.claude/docs/design/` | Codex design outputs |

---

## Agent Summary

| Agent | Type | Use Case | Command |
|-------|------|----------|---------|
| **Codex** | Cloud | Design, debug, review | `!codex` |
| **Gemini** | Cloud | Research, multimodal | `!gemini` |
| **Ollama** | Local | Privacy, offline, free | `!ollama` or `!local` |

---

*Document created: 2026-02-05*
*Last updated: 2026-02-05*
