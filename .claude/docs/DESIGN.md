# Project Design Document

> This document tracks design decisions made during conversations.
> Updated automatically by the `design-tracker` skill.

## Overview

<!-- Project purpose and goals -->
This monorepo contains TypeScript/Express.js services deployed on Kubernetes (AWS EKS).
Health endpoints are used for Kubernetes liveness/readiness probes.

Proposed product scope: Cross-platform productivity & health tracker (time tracking, goals, health logs, calorie tracking) with offline-first PWA and optional mobile/desktop shells.

## Architecture

<!-- System structure, components, data flow -->

```
[Component diagram or description here]
```

Product architecture (proposed):
- Monorepo (Turborepo + pnpm workspaces) with apps: web (React/Vite PWA), api (Express), shared (types/validation).
- Offline-first: IndexedDB persistence with sync outbox and service worker (Workbox).
- Mobile/desktop shells: Capacitor (iOS/Android) and Electron (post-MVP).

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
| User-mediated LinkedIn ingestion | Safe LinkedIn signal capture | Email alerts parsing, CSV import, manual URL capture, optional extension; no automated scraping |
| Dependency health checks with timeouts | Readiness validation | Per-service healthCheck with short timeouts |
| Simple liveness probe | Avoid restart loops | No dependency checks in liveness |
| Per-service status + latency | Troubleshooting | Response includes status + latency |
| Offline outbox + idempotent sync | Reliable offline-first data capture | Queue writes locally; replay on reconnect |
| Conflict handling by timestamp + audit | Simple MVP merge policy | Keep server timestamps; preserve raw history |

### Libraries & Roles

<!-- Libraries and their responsibilities -->

| Library | Role | Version | Notes |
|---------|------|---------|-------|
| React 18 + Vite | Web app + PWA shell | | SPA build with PWA plugin |
| Zustand | Client state | | UI state and local-only preferences |
| TanStack Query | Server state | | Caching, retries, optimistic updates |
| Tailwind CSS + shadcn/ui | UI system | | Rapid UI development |
| React Hook Form + Zod | Forms + validation | | Typed validation |
| Recharts | Visualization | | Charts for time/health data |
| Node.js + Express.js | API server | | REST API required by project rules |
| PostgreSQL | Primary database | | Relational storage |
| Prisma | ORM + migrations | | Schema-driven model + Studio |
| JWT + bcrypt | Auth | | Access + refresh tokens |
| Workbox (via vite-plugin-pwa) | Service worker | | Offline caching and sync |
| IndexedDB | Local persistence | | Offline data cache |
| Capacitor | Mobile shell | | iOS/Android packaging |
| Electron | Desktop shell | | Windows/macOS/Linux packaging |
| Turborepo + pnpm | Monorepo tooling | | Workspace orchestration |

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
| Recommendation (pending): Use Vite for main app UI; use Next.js only for marketing/SEO needs | Vite is a frontend build tool; Next adds server rendering and Server Components that aren't required for the core offline-first app | Full Next.js app | 2026-02-05 |
| Recommendation (pending): Prefer Prisma for server data access unless SQL-first/low-level control is required; choose Drizzle when SQL-like access and minimal dependencies are priorities | Prisma provides schema-driven ORM with Client and Migrate; Drizzle is a lightweight SQL-like ORM | Drizzle or Prisma (opposite choice) | 2026-02-05 |
| Decision: Use Zustand for UI/local state + persistence and TanStack Query for server cache; keep canonical offline data in IndexedDB | Lightweight client state with persistence and dedicated server-cache layer align with local-first storage | Redux Toolkit + RTK Query | 2026-02-05 |
| Decision: Food data source is market-dependent (US-only → USDA FDC; global/barcode-heavy → Open Food Facts; hybrid only if ODbL share-alike acceptable) | USDA provides authoritative US nutrients with clear public-domain licensing; Open Food Facts provides global barcode coverage with share-alike obligations | USDA-only, Open Food Facts-only, or hybrid without licensing review | 2026-02-05 |
| Proposed: Use Vite + React for MVP (no SSR) | Lowest complexity for 1-2 devs; revisit SSR later | Next.js | 2026-02-05 |
| Proposed: Prisma for ORM + migrations | Schema-driven workflow and tooling | Drizzle ORM | 2026-02-05 |
| Decision: Offline sync uses IndexedDB outbox + Workbox caching; Background Sync is best-effort with manual/online retry fallback | Background Sync support is limited; outbox + retries ensure reliable capture | Rely solely on Background Sync or online-only writes | 2026-02-05 |
| Decision: Implementation order builds offline foundation with auth/backend, then time tracking, goals, health/calories, and cross-platform last | Offline-first affects data model and sync; vertical slices reduce rework | Feature-first without offline foundation | 2026-02-05 |
| Recommendation (pending): For job automation systems, avoid LinkedIn scraping; prefer compliant sources (official APIs/partnerships) | LinkedIn policy restricts automated access; compliance risk outweighs low-volume scraping | Scraping with rate limiting | 2026-02-08 |
| Recommendation (pending): Use hybrid job-match scoring (embeddings + lexical signals + rules) | Embeddings capture semantic similarity; lexical/rules improve precision and explainability | TF-IDF only, embeddings only | 2026-02-08 |
| Recommendation (pending): For on-device cover letter generation on 8GB RAM, constrain model size/quantization and measure SLO; consider server-side fallback | 8GB is minimum for 7B; tighter headroom needs constraints and benchmarking | Larger models without constraints | 2026-02-08 |
| Recommendation (pending): Add resilience patterns for job ingestion/apply flows (timeouts, retries with backoff+jitter, circuit breaker, DLQ) | External dependencies are failure-prone; controlled retries and isolation reduce cascading failures | Best-effort retries only | 2026-02-08 |
| Recommendation (pending): Use user-mediated LinkedIn ingestion (email alerts, CSV export, manual URL, optional extension), no automated scraping | Minimizes account/ToS risk while capturing high-value LinkedIn signals | Direct scraping with rate limits | 2026-02-08 |


## TODO
<!-- Features to implement -->

- [ ] Implement LinkedIn import adapters (email alerts parsing, CSV import, manual URL capture) with explicit consent UX

- [ ] Implement per-service healthCheck() methods with timeouts
- [ ] Update readiness endpoint to aggregate dependency checks
- [ ] Decide timeout values and optional caching window
- [ ] Remove duplicate /health route if unused by probes/ingress
- [ ] Define routing decision matrix with confidence thresholds and manual override
- [ ] Add cross-agent observability (correlation IDs, tool logs, artifact indexing)
- [ ] Add quality gates and failure handling (schema validation, retries, fallback paths)
- [ ] Define offline sync protocol (outbox schema, retry/backoff, idempotency keys)
- [ ] Define conflict resolution policy per domain (time entries, goals, health logs)
- [ ] Decide auth token storage (cookie vs header) and refresh strategy
- [ ] Decide MVP platform scope (PWA only vs include mobile/desktop)
- [ ] Define approved job data sources and permission workflow (no LinkedIn scraping without consent)
- [ ] Define matching evaluation set + metrics (precision/recall, human review)
- [ ] Define Ollama model selection, latency budget, and output length limits for cover letters
- [ ] Define resilience requirements for ingestion (rate limiting/backoff, parser-change detection, dead-letter queue, manual review)
- [ ] Define incremental delivery phases for job automation features

## Open Questions

<!-- Unresolved issues, things to investigate -->

- [ ] What timeout values should be used for each dependency?
- [ ] Should readiness results be cached to reduce load?
- [ ] Should detailed health output be restricted to internal callers?
- [ ] What retry/backoff policy should be used between agents and hooks?
- [ ] What observability (traces, metrics, prompt logs) is required for multi-agent debugging?
- [ ] How should routing confidence thresholds and manual overrides be handled?
- [ ] Do we need SSR/SSG for SEO or shareable pages?
- [ ] Which food data source is acceptable for MVP (USDA vs Open Food Facts) and licensing implications?
- [ ] What offline conflict resolution rules are acceptable to users?
- [ ] What level of cross-platform parity is required at MVP launch?
- [ ] Provide the full Job Automation System requirements list (IDs, priorities, estimates) to complete analysis
- [ ] Confirm in-scope job sources and compliance path (official APIs, partnerships, ATS/RSS feeds)
- [ ] Define target latency/quality SLOs for match scoring and cover letter generation
- [ ] Clarify privacy/compliance requirements for handling resumes, credentials, and user data


## Changelog

| Date | Changes |
| 2026-02-08 | Added job automation requirements analysis recommendations and open questions |
| 2026-02-08 | Added LinkedIn-safe ingestion decision and todo for user-mediated imports |
| 2026-02-05 | Recorded MVP decisions for food data source, phase order, offline stack, and state management |
|------|---------|
| 2026-02-05 | Recorded productivity app architecture recommendations (pending confirmation) |
| 2026-02-04 | Recorded health check design approach and open questions |
| 2026-02-04 | Documented current multi-agent AI workflow orchestration setup |
| 2026-02-04 | Added multi-agent workflow architecture decisions and open questions |
| 2026-02-04 | Added proposed improvement priorities for multi-agent workflow |
| 2026-02-05 | Recorded architecture review recommendations for cross-platform productivity app |