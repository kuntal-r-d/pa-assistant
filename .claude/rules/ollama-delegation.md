# Ollama Delegation Rule

**Ollama provides free, private, local AI processing with no cloud dependency.**

## Context Management (CRITICAL)

**Be mindful of context consumption when using Ollama.** For large expected outputs, use subagent.

| Situation | Recommended Method |
|-----------|-------------------|
| Short question/answer | Direct call OK |
| Complex analysis | Via subagent |
| Code generation | Via subagent |
| Multiple questions | Via subagent |

```
┌──────────────────────────────────────────────────────────┐
│  Main Claude Code                                        │
│  → Direct call OK for short questions                    │
│  → Use subagent for large expected output                │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Subagent (general-purpose)                         │ │
│  │  → Calls Ollama CLI                                 │ │
│  │  → Saves full output to .claude/docs/local/         │ │
│  │  → Returns key insights only                        │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

## About Ollama

Ollama runs open-source LLMs locally on your machine:
- **Complete privacy** — Data never leaves your machine
- **No API costs** — Free to use after setup
- **Works offline** — No internet required
- **Many models** — Llama, Mistral, CodeLlama, DeepSeek, Qwen, and more

Think of Ollama as your private, free assistant for tasks where privacy matters.

**When you need privacy/offline processing → Delegate to subagent → Subagent consults Ollama.**

## Ollama vs Cloud Agents: Choose the Right Tool

| Task | Codex | Gemini | Ollama |
|------|-------|--------|--------|
| Design decisions | ✓ | | |
| Debugging | ✓ | | ✓ |
| Code implementation | ✓ | | ✓ |
| Large codebase analysis | | ✓ | |
| Research with web access | | ✓ | |
| Multimodal (PDF/video/audio) | | ✓ | |
| Privacy-sensitive data | | | ✓ |
| Offline work | | | ✓ |
| Cost-free processing | | | ✓ |
| Air-gapped environments | | | ✓ |

## When to Consult Ollama

ALWAYS consult Ollama BEFORE working with:

1. **Confidential data** - Sensitive information that shouldn't leave your machine
2. **Offline requirements** - Air-gapped or no-internet environments
3. **Cost control** - When avoiding API costs matters
4. **Privacy-first tasks** - Personal or proprietary code review

### Trigger Phrases (User Input)

Consult Ollama when user says:

- "Use local model" "Use Ollama"
- "Keep this private" "Confidential"
- "Process offline" "No cloud"
- "Use llama/mistral/codellama"
- "Self-hosted" "On-device"

## When NOT to Consult Ollama

Skip Ollama for:

- Tasks requiring web search or latest information (use Gemini)
- Complex design decisions needing frontier models (use Codex)
- Multimodal processing like PDF/video/audio (use Gemini)
- Tasks where cloud quality matters more than privacy

## Available Ollama Models

| Model | Best For | Size |
|-------|----------|------|
| `llama3.2` | General tasks | 3B/11B |
| `llama3.1` | Reasoning, coding | 8B/70B |
| `codellama` | Code generation | 7B/13B/34B |
| `mistral` | General tasks | 7B |
| `deepseek-coder` | Code analysis | 6.7B/33B |
| `qwen2.5-coder` | Code tasks | 7B/32B |
| `phi3` | Fast, lightweight | 3.8B |
| `gemma2` | General tasks | 9B/27B |

## How to Consult (via Subagent)

**IMPORTANT: Use subagent to preserve main context.**

If Ollama runs in Docker on this machine, the host CLI must have `OLLAMA_HOST=http://localhost:11434` (or use `docker exec <container> ollama run ...` in the prompt).

### Recommended: Subagent Pattern

Use Task tool with `subagent_type: "general-purpose"`:

```
Task tool parameters:
- subagent_type: "general-purpose"
- run_in_background: true (for parallel work)
- prompt: |
    {Task description}

    CONSTRAINTS:
    - ONLY write to .claude/docs/local/ (for output files)
    - Do NOT modify any other files
    - Return concise summary to orchestrator

    Call Ollama CLI:
    ollama run llama3.2 "{Question}" 2>/dev/null

    For code tasks, use:
    ollama run codellama "{Code question}" 2>/dev/null

    Return CONCISE summary:
    - Key findings
    - Recommendations
    - Any limitations noted
```

### Subagent Patterns by Task Type

**Code Review Pattern (Private):**
```
prompt: |
  Review this code privately using local model.

  ollama run codellama "Review this code for issues:
  {code}" 2>/dev/null

  Save to .claude/docs/local/{filename}-review.md
  Return key issues found.
```

**Analysis Pattern (Offline):**
```
prompt: |
  Analyze this data offline.

  ollama run llama3.2 "Analyze: {data}" 2>/dev/null

  Save to .claude/docs/local/analysis.md
  Return summary of findings.
```

## Ollama CLI Commands Reference

For use within subagents:

```bash
# Basic query (default model)
ollama run llama3.2 "{question}" 2>/dev/null

# Code-specific model
ollama run codellama "{code question}" 2>/dev/null

# Reasoning tasks
ollama run llama3.1 "{complex question}" 2>/dev/null

# Fast lightweight tasks
ollama run phi3 "{simple question}" 2>/dev/null

# List available models
ollama list

# Pull a new model
ollama pull mistral
```

## Setup Requirements

Ollama must be installed and running (locally or in Docker).

### Option A: Native install

```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama service
ollama serve

# Pull recommended models
ollama pull llama3.2
ollama pull codellama
```

### Option B: Ollama in Docker

If Ollama runs in a Docker container:

1. **Use the Ollama CLI on the host** (recommended): Install the CLI on the host and point it at the container:
   ```bash
   # Install CLI (macOS)
   brew install ollama

   # Tell the CLI to use the container (default port 11434)
   export OLLAMA_HOST=http://localhost:11434

   # Then ollama run / ollama list work as usual
   ollama run llama3.2 "your question"
   ```
   Ensure the container exposes port 11434 (e.g. `docker run -d -p 11434:11434 ollama/ollama`).

2. **Or call into the container** if you don’t use the host CLI:
   ```bash
   docker exec <container_name> ollama run llama3.2 "your question"
   ```
   Subagent prompts that use the Ollama CLI should then use this `docker exec` form, or the host CLI with `OLLAMA_HOST` set.

## Why Subagent Pattern?

- **Context preservation**: Main orchestrator stays lightweight
- **Full capture**: Subagent can save entire Ollama output to file
- **Concise handoff**: Main only receives key findings
- **Privacy maintained**: All processing stays local

**Use Ollama (via subagent) for privacy, Codex for design, Gemini for research, Claude for orchestration.**

## Subagent Constraints (CRITICAL)

**General-purpose subagents have FULL tool access.** Without explicit constraints,
they may modify files unexpectedly. Always include these constraints:

```markdown
SUBAGENT CONSTRAINTS:
- ONLY write to .claude/docs/local/ (to save outputs)
- Do NOT modify any other files
- Return analysis as TEXT to main orchestrator
- Only use Bash for calling Ollama CLI
```

### When Subagent CAN Write

| Task Type | Write Allowed | Constraint |
|-----------|---------------|------------|
| Private analysis | `.claude/docs/local/` only | Save findings there |
| Code review (local) | `.claude/docs/local/` only | Save review there |
| Other files | NO | Return text only |

## Mode Commands

- `!ollama` - Switch to Ollama-only mode
- `!local` - Alias for Ollama mode
- `!auto` - Auto-delegate (may choose Ollama based on triggers)
- `!consult` - Ask permission before delegating

## Privacy Considerations

When using Ollama:
- ✅ Data stays on your machine
- ✅ No API keys required
- ✅ Works without internet
- ✅ Full control over model and data
- ⚠️ Quality may vary by model size
- ⚠️ Requires local compute resources
