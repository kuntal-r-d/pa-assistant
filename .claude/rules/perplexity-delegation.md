# Perplexity Delegation Rule

**Use Perplexity only when explicitly requested by user.**

## When to Use

Only when user explicitly mentions:
- "Ask Perplexity"
- "Use Perplexity"
- "Consult Perplexity"
- "Check with Perplexity"

**No automatic triggers.** Do not proactively use Perplexity.

## Available Tools

| Tool | Model | Use Case |
|------|-------|----------|
| `perplexity_ask` | Sonar | Quick Q&A |
| `perplexity_reason` | sonar-reasoning-pro | Complex reasoning |
| `perplexity_research` | Deep research | Comprehensive research with citations |

## How to Use

Call the MCP tools directly:

```
mcp__MCP_DOCKER__perplexity_ask
mcp__MCP_DOCKER__perplexity_reason
mcp__MCP_DOCKER__perplexity_research
```

### Message Format

```json
{
  "messages": [
    {"role": "user", "content": "Your question here"}
  ]
}
```

## What Perplexity Excels At

- Web-grounded research with citations
- Latest information (not limited by training cutoff)
- Technology comparisons with current benchmarks
- Documentation and changelog lookup
- Fact-checking with verifiable sources

## Language Protocol

1. Ask Perplexity in **English**
2. Receive response in **English**
3. Report to user in **English**
