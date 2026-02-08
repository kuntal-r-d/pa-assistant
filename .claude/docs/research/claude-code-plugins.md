# Claude Code Plugin/Skill System Research (2025-2026)

**Research Date:** 2026-02-06
**Sources:** Gemini CLI Research + Local Project Analysis

---

## Executive Summary

The Claude Code CLI extensibility system (2025-2026) provides three primary extension mechanisms:
1. **Skills** - Reusable procedural workflows defined in markdown
2. **MCP (Model Context Protocol) Servers** - External tools/data sources exposed as CLI commands
3. **Hooks** - Event-driven scripts that intercept and modify workflow lifecycle

These components work together to create an "Agentic DevOps" architecture where specialized agents coordinate tasks while preserving the main orchestrator's context.

---

## 1. Claude Code Skills & Plugins System

### What Are Skills?

Skills are the primary unit of extensibility, allowing users to define reusable capabilities that Claude can "learn" and invoke autonomously or manually. They serve as "standard operating procedures" for the AI.

**Key Characteristics:**
- **Location:** `.claude/skills/<skill-name>/SKILL.md` (project-specific) or `~/.claude/skills/` (global)
- **Format:** Single Markdown file with YAML frontmatter + procedural instructions
- **Invocation:**
  - **Automatic:** Claude uses the skill description to decide when to run it
  - **Manual:** Users invoke via `/slash-commands` (e.g., `/tdd`, `/startproject`)
  - **Agentic:** Skills can spawn sub-agents for complex multi-step workflows

### Skill Manifest Format (`SKILL.md`)

```markdown
---
name: my-skill-name          # Command trigger (e.g., /my-skill-name)
description: |               # Used by Claude to understand WHEN to use this
  One or two sentences describing the goal.
  Specific keywords help matching.
disable-model-invocation: false # Set 'true' if skill just outputs text/docs
dependencies:                # (Optional) Required system tools
  - python>=3.10
  - node
allowed-tools:               # (Optional) Restrict what the skill can use
  - Bash
  - Read
  - Edit
metadata:                    # (Optional) Additional metadata
  short-description: Brief summary for listings
---

# Human-Readable Title

## Usage
Explain how to use this skill.

## Procedure
1. Step one instructions...
2. Step two instructions...
3. Call specialized tools as needed
```

### Example: Checkpointing Skill

```yaml
---
name: checkpointing
description: |
  Save session context to agent configuration files or create full checkpoint files.
  Supports three modes: session history (default), full checkpoint (--full),
  and skill analysis (--full --analyze).
metadata:
  short-description: Checkpoint session context with skill extraction support
---
```

### How Skills Work (Lifecycle)

1. **Loading Phase:**
   - Claude Code reads all `SKILL.md` files from `.claude/skills/`
   - Parses YAML frontmatter to understand purpose, triggers, and constraints
   - Indexes skills by name and description keywords

2. **Matching Phase:**
   - User prompt analyzed for intent matching skill descriptions
   - Manual invocation via `/skill-name` command
   - Hook-based routing can force-select specific skills

3. **Execution Phase:**
   - Skill instructions passed to Claude as context
   - Claude follows procedural steps in the skill body
   - May execute underlying scripts (e.g., `checkpoint.py`, `gemini -p ...`)
   - Complex skills spawn sub-agents to preserve main context

4. **Sub-agent Coordination:**
   - Skills often delegate to specialized agents (defined in `.claude/agents/`)
   - Example: `startproject` skill calls Gemini for research, then Codex for design
   - Sub-agents work in isolated context, return only summaries

### `disable-model-invocation` Flag

**Purpose:** Controls whether Claude actively executes the skill vs. just providing guidance.

- `false` (default): Skill is executable - Claude runs commands/scripts
- `true`: Skill is procedural guide - Claude follows instructions but doesn't automate

**Use Case Example (TDD Skill):**
```yaml
---
name: tdd
description: Test-Driven Development workflow guide
disable-model-invocation: true
---
```
This serves as a strict procedural guide for the Red-Green-Refactor cycle rather than an automated script.

---

## 2. Model Context Protocol (MCP) Servers

### What is MCP?

The Model Context Protocol (MCP) is the standard for connecting AI models to external data and tools. In Claude Code CLI, MCP servers run as local processes exposing capabilities via CLI commands.

### Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Claude Code (Orchestrator)                             │
│  - Main routing and context management                  │
│  - Opus 4.5 / Sonnet 4.5                                │
└──────────────┬──────────────────────────────────────────┘
               │
               ├──> MCP Server: Codex CLI (Deep Reasoning)
               │    • Design decisions
               │    • Debugging analysis
               │    • Code implementation
               │
               ├──> MCP Server: Gemini CLI (Research)
               │    • Library research
               │    • Codebase analysis
               │    • Multimodal (PDF/video/audio)
               │
               └──> MCP Server: Ollama (Local/Private)
                    • Privacy-sensitive processing
                    • Offline work
                    • Cost-free operations
```

### Agent Configuration (`agents.yaml`)

```yaml
agents:
  codex:
    type: "cloud"
    cli_command: "codex exec --model gpt-5.2-codex"
    triggers:
      high_weight: ["design", "debug", "implement", "fix"]
      medium_weight: ["review", "refactor"]
    capabilities:
      - "deep-reasoning"
      - "code-implementation"
    sandbox_modes:
      - "read-only"    # Analysis only
      - "workspace-write"  # Can modify files

  gemini:
    type: "cloud"
    cli_command: "gemini -p"
    triggers:
      high_weight: ["research", "docs", "analyze", "pdf"]
      medium_weight: ["investigate", "explore"]
    capabilities:
      - "large-context"  # 1M tokens
      - "multimodal"     # Video, audio, PDF
      - "web-search"

  ollama:
    type: "local"
    cli_command: "ollama run {model}"
    triggers:
      high_weight: ["local", "private", "offline", "confidential"]
    capabilities:
      - "privacy-first"
      - "offline-processing"
```

### How Skills Interact with MCP Servers

**Example: Research Skill Calling Gemini**

```markdown
---
name: research-library
description: Research best practices for a given library or framework
---

# Library Research Skill

## Procedure

1. **Spawn Research Sub-agent:**
   ```bash
   # Sub-agent will call Gemini CLI
   gemini -p "Research {library_name} best practices 2025-2026.
   Include: recommended patterns, common pitfalls, latest features,
   breaking changes, and alternatives." 2>/dev/null
   ```

2. **Save Full Output:**
   - Write complete research to `.claude/docs/research/{library_name}.md`

3. **Return Summary:**
   - Extract 5-7 key bullet points
   - Highlight recommended approach
   - Note important caveats
```

**Mechanism:** Instead of raw socket connections, this architecture wraps MCP capabilities in CLI commands that sub-agents invoke via Bash tool.

---

## 3. Claude Code Hooks System

### What Are Hooks?

Hooks are event-driven scripts that intercept and modify Claude Code's workflow at specific lifecycle events. They're distinct from skills but often work together.

### Hook Types & Events

| Event Type | When It Fires | Use Case |
|------------|---------------|----------|
| `UserPromptSubmit` | Before processing user input | Intent classification, routing |
| `PreToolUse` | Before any tool execution | Permission checks, logging |
| `PostToolUse` | After tool completes | Result logging, error handling |
| `SessionStart` | When session begins | Environment setup, mode loading |
| `SessionEnd` | When session ends | Cleanup, checkpointing |

### Hook Implementation

**Location:** `.claude/hooks/`

**Format:** Executable scripts (Python, Bash) that:
- **Input:** Receive JSON from `stdin`
- **Process:** Execute custom logic
- **Output:** Write JSON to `stdout` with instructions for Claude

### Example: Agent Router Hook (`agent-router.py`)

**Purpose:** Intercept user prompts and route to specialized agents based on intent.

**Workflow:**
```python
# 1. Input (from stdin)
{
  "event": "UserPromptSubmit",
  "prompt": "Research React 19 features",
  "context": {...}
}

# 2. Processing Logic
# Check session mode
mode = load_session_mode()  # e.g., "auto", "consult", "solo"

# Classify intent
intent = classify_intent(prompt)  # "research" detected

# Determine routing
if mode == "auto" and intent == "research":
    agent = "gemini"
elif mode == "consult":
    agent = prompt_user_for_confirmation()
else:
    agent = "claude"  # Solo mode

# 3. Output (to stdout)
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "[Auto-Routing] Intent: research. Consulting Gemini...",
    "route_to_agent": "gemini"
  }
}
```

### Hook + Skill + MCP Integration Flow

**Complete Example:**

```
1. User Input:
   "Research React 19 features"

2. Hook: agent-router.py (UserPromptSubmit)
   - Detects "research" intent
   - Session mode is "auto"
   - Injects context: "Use Gemini for research"

3. Orchestrator (Claude):
   - Receives routed prompt
   - Identifies relevant skill: `research-library`
   - Spawns sub-agent (general-purpose agent)

4. Sub-agent Execution:
   - Reads skill instructions
   - Calls MCP server: `gemini -p "Research React 19..."`
   - Saves output to `.claude/docs/research/react-19-features.md`

5. PostToolUse Hook: log-cli-tools.py
   - Logs Gemini invocation to `.claude/logs/cli-tools.jsonl`
   - Filters sensitive data
   - Rotates log if > 50MB

6. Result:
   - Sub-agent returns concise summary to main orchestrator
   - User receives findings without context pollution
```

---

## 4. Creating Custom Skills

### Step-by-Step Guide

**1. Create Skill Directory:**
```bash
mkdir -p .claude/skills/my-new-skill
```

**2. Create Skill Manifest:**
```bash
touch .claude/skills/my-new-skill/SKILL.md
```

**3. Define Skill Content:**
```markdown
---
name: my-new-skill
description: |
  Brief description of what this skill does.
  Include trigger keywords that users might say.
dependencies:
  - node>=18
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
---

# My New Skill

## Overview
Detailed explanation of the skill's purpose.

## Usage
How to invoke: `/my-new-skill` or say "do the thing"

## Procedure

1. **Step 1: Preparation**
   - Check prerequisites
   - Validate inputs

2. **Step 2: Execution**
   ```bash
   # Example command
   npm run build
   ```

3. **Step 3: Verification**
   - Check results
   - Report status

## Notes
Important considerations and edge cases.
```

**4. Test the Skill:**
```bash
# Restart Claude Code or reload context
claude code

# Test invocation
/my-new-skill

# Or via natural language
"Please do the thing"
```

### Best Practices for Custom Skills

**Context Preservation:**
- For heavy operations, spawn sub-agents
- Return only summaries to main orchestrator
- Save detailed output to `.claude/docs/`

**Security:**
- Specify `allowed-tools` to restrict capabilities
- Use sandbox modes for CLI invocations
- Sanitize inputs in skill scripts

**Reusability:**
- Make skills parameterizable
- Document dependencies clearly
- Use generic language, not project-specific

**Performance:**
- Run background tasks with `run_in_background: true`
- Parallelize independent operations
- Cache results when appropriate

---

## 5. Best Practices for Extending Claude Code

### Architecture Patterns

**1. Agentic Workflows**
Coordinate multiple specialized agents for complex tasks:

```
Main Orchestrator (Claude)
  ├─> Research Sub-agent (Gemini)
  │   └─> Output: .claude/docs/research/
  ├─> Design Sub-agent (Codex)
  │   └─> Output: .claude/docs/design/
  └─> Implementation (Claude + Skills)
      └─> Output: Source code
```

**2. Context Management**
Use subagents to preserve main context:

```markdown
Task tool parameters:
- subagent_type: "general-purpose"
- run_in_background: true
- prompt: |
    CONSTRAINTS:
    - ONLY write to .claude/docs/research/
    - Do NOT modify source files
    - Return CONCISE summary (5-7 bullets)
```

**3. Security Layers**

**File Locking (Concurrent Access):**
```python
from file_lock import FileLock

# Protected files
PROTECTED_FILES = [
    '.claude/docs/DESIGN.md',
    '.claude/docs/CLAUDE.md',
    '.claude/docs/AGENTS.md'
]

with FileLock('.claude/docs/DESIGN.md'):
    # Safe to edit - lock auto-released
    pass
```

**Input Sanitization (Hooks):**
```python
import shlex

def sanitize_prompt(prompt: str) -> str:
    """Prevent shell injection in CLI calls"""
    return shlex.quote(prompt)
```

**Sandbox Modes (CLI Tools):**
```bash
# Read-only: Analysis/review tasks
codex exec --sandbox read-only --full-auto "Review this code"

# Workspace-write: Implementation tasks
codex exec --sandbox workspace-write --full-auto "Fix the bug"
```

### Configuration Best Practices

**1. Centralized Agent Definitions**
Keep all agent configs in `.claude/config/agents.yaml`:
- Easy to update when new agents added
- Version control friendly
- Single source of truth

**2. Mode-Based Routing**
Support multiple delegation modes:
- `!auto` - Silent delegation based on intent
- `!consult` - Ask permission before delegating
- `!solo` - Claude only (no external agents)
- `!codex` - Codex only
- `!gemini` - Gemini only
- `!ollama` - Local/private only

**3. Logging & Observability**
Track all CLI tool invocations:
```jsonl
{"timestamp": "2026-02-06T10:30:00Z", "tool": "gemini", "prompt": "Research...", "status": "success"}
{"timestamp": "2026-02-06T10:31:00Z", "tool": "codex", "prompt": "Design...", "status": "success"}
```

**4. Privacy & Security**
- Filter logs for API keys, passwords, tokens
- Rotate logs when exceeding 50MB
- Exclude logs from git (`.gitignore`)
- Never commit secrets to skills or configs

---

## 6. How Extension Points Work Together

### Real-World Scenario: "Implement Feature X"

**Input:** User says "Implement authentication system"

**Flow:**

```
1. UserPromptSubmit Hook (agent-router.py)
   ├─> Load session mode: "auto"
   ├─> Classify intent: "implement" + "design" keywords
   ├─> Decision: Complex task, needs research + design
   └─> Output: Route to multi-agent workflow

2. Main Orchestrator (Claude)
   ├─> Identifies relevant skill: /startproject
   └─> Spawns sub-agents in parallel

3. Sub-agent 1: Research (Gemini)
   ├─> Skill: research-library
   ├─> MCP Call: gemini -p "Research auth best practices 2025-2026"
   ├─> PostToolUse Hook: Logs invocation
   └─> Output: .claude/docs/research/auth-research.md + summary

4. Sub-agent 2: Design (Codex)
   ├─> Skill: design-review
   ├─> MCP Call: codex exec --sandbox read-only "Design auth system"
   ├─> PostToolUse Hook: Logs invocation
   └─> Output: .claude/docs/DESIGN.md update + summary

5. Main Orchestrator (Claude)
   ├─> Receives summaries from both sub-agents
   ├─> Synthesizes findings
   ├─> Selects implementation skill: /implement-feature
   └─> Executes implementation steps

6. Implementation (Claude + Skills)
   ├─> Generate code files
   ├─> Write tests
   ├─> Update documentation
   └─> Commit changes (if approved)

7. Result
   └─> User receives complete implementation with context preserved
```

### Key Interactions

**Hooks ↔ Skills:**
- Hooks can force-select specific skills
- Skills trigger hooks during tool execution (PreToolUse, PostToolUse)
- Hooks can inject context that modifies skill behavior

**Skills ↔ MCP Servers:**
- Skills invoke MCP servers via CLI commands
- Skills structure prompts for optimal agent performance
- Skills handle MCP server outputs (save, summarize, return)

**MCP Servers ↔ Hooks:**
- PostToolUse hooks log all MCP invocations
- Hooks can filter/transform MCP outputs
- Hooks enforce security (sandbox modes, input sanitization)

---

## 7. Advanced Topics

### Skill Composition

Skills can call other skills:

```markdown
---
name: full-feature-workflow
description: Complete feature development workflow
---

# Full Feature Workflow

## Procedure

1. **Research Phase:** Call `/research-library {topic}`
2. **Design Phase:** Call `/design-review`
3. **Implementation Phase:** Call `/implement-feature`
4. **Testing Phase:** Call `/tdd`
5. **Documentation Phase:** Call `/update-docs`
```

### Dynamic Skill Loading

Skills can be loaded from external sources:

```yaml
# .claude/config/plugins.yaml
plugins:
  - name: "community-skills"
    source: "https://github.com/community/claude-skills"
    skills:
      - "code-review"
      - "refactoring-guide"
```

### MCP Registry Integration

2025-2026 ecosystem relies on centralized MCP registries:

```yaml
# .claude/config/mcp-servers.yaml
registry: "https://registry.mcp.tools"
servers:
  - name: "github-mcp"
    version: ">=2.0.0"
    capabilities: ["issues", "pulls", "repos"]
  - name: "postgres-mcp"
    version: ">=1.5.0"
    capabilities: ["query", "schema"]
```

### Skill Versioning

Track skill versions for compatibility:

```yaml
---
name: my-skill
version: "2.1.0"
min-claude-version: "1.5.0"
description: |
  Version 2.1.0 changes:
  - Added support for parallel execution
  - Improved error handling
---
```

---

## 8. Troubleshooting & Debugging

### Common Issues

**Issue: Skill not being auto-invoked**
- **Solution:** Check skill description has clear trigger keywords
- **Debug:** Add explicit keywords user might say

**Issue: Sub-agent consuming too much context**
- **Solution:** Add output constraints in skill instructions
- **Debug:** Use "return CONCISE summary" in skill procedure

**Issue: Hook not firing**
- **Solution:** Verify hook is executable (`chmod +x`)
- **Debug:** Check `.claude/logs/hooks.log` for errors

**Issue: MCP server not responding**
- **Solution:** Test CLI command directly in terminal
- **Debug:** Check `allowed-tools` includes `Bash`

### Debug Commands

```bash
# List all skills
ls -la .claude/skills/

# Test skill manually
/skill-name

# Check hook execution
cat .claude/logs/hooks.log

# Test MCP server
gemini -p "test prompt"
codex exec --sandbox read-only "test prompt"

# Verify session mode
cat .claude/session/mode.json
```

---

## 9. Security Considerations

### Skill Security

**Constraints:**
Always specify constraints for sub-agents:

```markdown
SUBAGENT CONSTRAINTS:
- ONLY write to .claude/docs/research/
- Do NOT modify source files
- Do NOT use Edit or Write tools on protected files
- Return analysis as TEXT only
```

**Protected Files:**
```python
PROTECTED_FILES = [
    '.claude/docs/DESIGN.md',
    '.claude/docs/CLAUDE.md',
    '.claude/docs/AGENTS.md',
    '.claude/docs/GEMINI.md'
]
```

### Hook Security

**Input Validation:**
```python
import json
import shlex

def validate_hook_input(stdin_data: str) -> dict:
    """Validate and sanitize hook input"""
    try:
        data = json.loads(stdin_data)
        # Sanitize string fields
        if 'prompt' in data:
            data['prompt'] = shlex.quote(data['prompt'])
        return data
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON input")
```

**Secrets Filtering:**
```python
import re

SECRETS_PATTERNS = [
    r'(api[_-]?key|password|secret|token)["\s:=]+([^\s"\']+)',
    r'sk-[a-zA-Z0-9]{32,}',  # OpenAI keys
    r'ghp_[a-zA-Z0-9]{36}',  # GitHub tokens
]

def filter_secrets(text: str) -> str:
    """Remove secrets from text"""
    for pattern in SECRETS_PATTERNS:
        text = re.sub(pattern, r'\1: [REDACTED]', text)
    return text
```

### MCP Server Security

**Sandbox Modes:**
- Use `--sandbox read-only` for analysis tasks
- Only use `--sandbox workspace-write` when necessary
- Never use write permissions for untrusted input

**Permission Boundaries:**
```json
{
  "allowed-tools": ["Bash"],
  "bash-allowlist": [
    "gemini -p*",
    "codex exec --sandbox read-only*"
  ],
  "bash-denylist": [
    "rm -rf*",
    "sudo*",
    "> /etc/*"
  ]
}
```

---

## 10. Summary: 2025-2026 Ecosystem Trends

### Agentic DevOps
The shift toward coordinating multiple specialized agents:
- **Main Orchestrator:** Claude Code (context management, routing)
- **Specialists:** Codex (reasoning), Gemini (research), Ollama (privacy)
- **Coordination:** Skills + Hooks manage agent handoffs

### MCP Registry
Centralized discovery for portable skills:
- Skills can depend on standard MCP servers
- Users install MCP servers from registry
- Skills work across environments with same servers

### Context Preservation
Heavy emphasis on context management:
- Sub-agents handle large operations
- Main orchestrator stays lightweight
- Summaries over full outputs

### Security by Default
"Seatbelt" mechanisms built-in:
- File locking for concurrent access
- Input sanitization in hooks
- Sandbox modes for CLI tools
- Secrets filtering in logs

### Community-Driven
Extensibility enables sharing:
- Skills shared via GitHub
- MCP servers published to registry
- Hooks for custom workflows
- Plugins bundle capabilities

---

## References & Resources

### Official Documentation
- Claude Code CLI: https://docs.anthropic.com/claude/docs/claude-code
- MCP Protocol: https://modelcontextprotocol.io/
- Anthropic API: https://docs.anthropic.com/

### Community Resources
- MCP Registry: https://registry.mcp.tools
- Claude Skills Repository: https://github.com/anthropic/claude-skills
- Community Forums: https://discuss.anthropic.com/

### Local Project Examples
- `.claude/skills/` - Example skills (checkpointing, startproject, tdd)
- `.claude/hooks/` - Example hooks (agent-router, log-cli-tools)
- `.claude/config/agents.yaml` - Agent configuration
- `.claude/lib/` - Utility libraries (file_lock, intent_classifier)

---

## Appendix: Complete Skill Template

```markdown
---
# === REQUIRED FIELDS ===
name: skill-name                    # Slug for /command invocation
description: |                      # Multi-line description for auto-matching
  Clear description of what this skill does.
  Include keywords users might say.
  Be specific about the goal and context.

# === OPTIONAL FIELDS ===
version: "1.0.0"                    # Semantic versioning
disable-model-invocation: false     # true = guidance only, false = executable
min-claude-version: "1.5.0"         # Minimum required Claude version

dependencies:                       # System requirements
  - python>=3.10
  - node>=18
  - docker

allowed-tools:                      # Restrict tool access
  - Bash
  - Read
  - Edit
  - Write
  - Glob
  - Grep

metadata:                           # Additional metadata
  author: "Your Name"
  tags: ["development", "testing"]
  short-description: "Brief one-liner"
---

# Skill Title (Human-Readable)

## Overview
Brief overview of what this skill does and why it exists.

## Prerequisites
- Requirement 1
- Requirement 2

## Usage

### Manual Invocation
```
/skill-name [arguments]
```

### Auto-Invocation
Say: "phrase that triggers this skill"

## Procedure

### Step 1: Preparation
- Task 1
- Task 2

### Step 2: Execution
```bash
# Example commands
npm run build
```

### Step 3: Verification
- Check results
- Report status

## Sub-agent Configuration

If this skill spawns sub-agents:

```markdown
SUBAGENT CONSTRAINTS:
- ONLY write to .claude/docs/[specific-dir]/
- Do NOT modify source files
- Return CONCISE summary (5-7 bullets)
- Only use Bash for CLI invocations
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Error 1 | Cause 1 | Solution 1 |
| Error 2 | Cause 2 | Solution 2 |

## Examples

### Example 1: Basic Usage
```
User: "Do the thing"
Skill: [executes steps 1-3]
Output: "Thing completed successfully"
```

### Example 2: Advanced Usage
```
User: "/skill-name --option=value"
Skill: [executes with custom parameters]
Output: "Custom execution complete"
```

## Notes
- Important consideration 1
- Edge case 2
- Performance tip 3

## Changelog

### v1.0.0 (2026-02-06)
- Initial release
- Features: X, Y, Z

```

---

**End of Research Report**
