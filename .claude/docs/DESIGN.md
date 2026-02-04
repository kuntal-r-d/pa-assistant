# Project Design Document

> This document tracks design decisions made during conversations.
> Updated automatically by the `design-tracker` skill.

## Overview

<!-- Project purpose and goals -->
This monorepo contains TypeScript/Express.js services deployed on Kubernetes (AWS EKS).
Health endpoints are used for Kubernetes liveness/readiness probes.

## Architecture

<!-- System structure, components, data flow -->

```
[Component diagram or description here]
```

AI workflow orchestration (developer tooling):
- Claude Code as main orchestrator with hooks on Edit/Write/Bash/Task.
- Codex CLI for deep reasoning (design decisions, debugging, code review).
- Gemini CLI for research (large context analysis, Google Search, multimodal).
- Subagent pattern for heavy reasoning/research via CLI calls.
- Shared context via `.claude/rules/` and `.claude/docs/`.
- Hook structure: UserPromptSubmit (routing), PreToolUse (consult before writes), PostToolUse (review/tests/lint).

Health check flow:
- Liveness endpoint: process-alive check only.
- Readiness endpoint: checks Postgres, cache, and MongoDB dependencies.

### AI Workflow Orchestration (Claude/Codex/Gemini)

- Orchestrator: Claude Code with hooks (UserPromptSubmit, PreToolUse, PostToolUse).
- Deep reasoning: Codex CLI for design/debug/review tasks.
- Research: Gemini CLI for large-context analysis and web-grounded research.
- Subagent pattern: Claude spawns general-purpose subagents to call Codex/Gemini CLIs.
- Shared context: All agents access `.claude/rules/` and `.claude/docs/`.
- Hook behaviors: user prompt routing, pre-write consultation checks, post-plan review, lint-on-save, post-implementation review.
- Config: model selection and permissions managed per agent.
## Implementation Plan

### Patterns & Approaches

<!-- Design patterns, architectural approaches -->

| Pattern | Purpose | Notes |
|---------|---------|-------|
| Dependency health checks with timeouts | Readiness validation | Per-service healthCheck with short timeouts |
| Simple liveness probe | Avoid restart loops | No dependency checks in liveness |
| Per-service status + latency | Troubleshooting | Response includes status + latency |

### Libraries & Roles

<!-- Libraries and their responsibilities -->

| Library | Role | Version | Notes |
|---------|------|---------|-------|
| | | | |

### Key Decisions

<!-- Important decisions and their rationale -->

| Decision | Rationale | Alternatives Considered | Date |
|----------|-----------|------------------------|------|
| Claude Code as orchestrator with hooks for routing/guardrails | Centralized control over tool use and workflow | Fully autonomous per-agent workflows | 2026-02-04 |
| Codex CLI specialized for deep reasoning tasks | Higher quality design/debugging decisions | Single-model generalist | 2026-02-04 |
| Gemini CLI specialized for research/large-context analysis | Better grounding and multimodal support | Rely on Codex for research | 2026-02-04 |
| Readiness checks all critical deps (Postgres/Cache/Mongo) | Route traffic only when dependencies are reachable | Skip deps in readiness | 2026-02-04 |
| Liveness remains process-only | Avoid kubelet restarts during downstream outages | Include deps in liveness | 2026-02-04 |
| Health responses include per-service latency | Faster triage when readiness fails | Binary ready/unready only | 2026-02-04 |

## TODO

<!-- Features to implement -->

- [ ] Implement per-service healthCheck() methods with timeouts
- [ ] Update readiness endpoint to aggregate dependency checks
- [ ] Decide timeout values and optional caching window
- [ ] Remove duplicate /health route if unused by probes/ingress
- [ ] Define routing decision matrix with confidence thresholds and manual override
- [ ] Add cross-agent observability (correlation IDs, tool logs, artifact indexing)
- [ ] Add quality gates and failure handling (schema validation, retries, fallback paths)

## Open Questions

<!-- Unresolved issues, things to investigate -->

- [ ] What timeout values should be used for each dependency?
- [ ] Should readiness results be cached to reduce load?
- [ ] Should detailed health output be restricted to internal callers?
- [ ] What retry/backoff policy should be used between agents and hooks?
- [ ] What observability (traces, metrics, prompt logs) is required for multi-agent debugging?
- [ ] How should routing confidence thresholds and manual overrides be handled?

## Changelog

| Date | Changes |
|------|---------|
| 2026-02-04 | Recorded health check design approach and open questions |
| 2026-02-04 | Documented current multi-agent AI workflow orchestration setup |
| 2026-02-04 | Added multi-agent workflow architecture decisions and open questions |
| 2026-02-04 | Added proposed improvement priorities for multi-agent workflow |
