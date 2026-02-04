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

Health check flow:
- Liveness endpoint: process-alive check only.
- Readiness endpoint: checks Postgres, cache, and MongoDB dependencies.

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
| Readiness checks all critical deps (Postgres/Cache/Mongo) | Route traffic only when dependencies are reachable | Skip deps in readiness | 2026-02-04 |
| Liveness remains process-only | Avoid kubelet restarts during downstream outages | Include deps in liveness | 2026-02-04 |
| Health responses include per-service latency | Faster triage when readiness fails | Binary ready/unready only | 2026-02-04 |

## TODO

<!-- Features to implement -->

- [ ] Implement per-service healthCheck() methods with timeouts
- [ ] Update readiness endpoint to aggregate dependency checks
- [ ] Decide timeout values and optional caching window
- [ ] Remove duplicate /health route if unused by probes/ingress

## Open Questions

<!-- Unresolved issues, things to investigate -->

- [ ] What timeout values should be used for each dependency?
- [ ] Should readiness results be cached to reduce load?
- [ ] Should detailed health output be restricted to internal callers?

## Changelog

| Date | Changes |
|------|---------|
| 2026-02-04 | Recorded health check design approach and open questions |
