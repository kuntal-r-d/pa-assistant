# RCF Structure and Packages Reference

**Purpose:** This document describes the structured layout, RCF (Requirements Confidence Framework) artifacts, and package ecosystem maintained in this project. Use it as a **reference to generate a Technical Architecture Document (TAD)** or project setup for another project that will follow the RCF framework for development.

**Version:** 1.0  
**Last Updated:** 2026-02-08

---

## 1. Repository Overview

| Attribute                | Value                           |
| ------------------------ | ------------------------------- |
| **Type**                 | pnpm monorepo (ESM, TypeScript) |
| **Package manager**      | pnpm ≥ 8.0.0                    |
| **Node.js**              | ≥ 24.0.0                        |
| **Workspace definition** | `pnpm-workspace.yaml`           |

```yaml
# pnpm-workspace.yaml
packages:
  - 'packages/@<scope>/*'
  - 'apps/*'
```

---

## 2. Directory Structure (High Level)

```
<repo-root>/
├── apps/                          # Deployable applications
│   ├── api-service/                # Backend API (Express, Node.js)
│   └── spa-admin/                  # Admin SPA (Vue 3, Vite, Vuetify)
├── packages/@<scope>/             # Shared internal libraries (scoped)
│   ├── backend-common/             # Logger, cache, DB clients, exceptions, middleware
│   ├── backend-text-to-data/      # SQL sanitizer, text-to-data utilities
│   └── backend-integration-tests/ # Integration test helpers, fixtures, generators
├── docs/                          # Project documentation
│   ├── rcf/                       # RCF framework artifacts (see Section 3)
│   ├── plans/                     # Technical plans, SPI/design docs
│   ├── configs/                   # Sample configs, SQL, etc.
│   └── *.md                       # Guides (KEYCLOAK, FRONTEND_SPEC, etc.)
├── tests/                         # Cross-cutting tests (not per-app)
│   ├── integration/               # RCF-aligned integration specs (US-xxx / AC-xxx)
│   ├── e2e/                       # Playwright E2E (fixtures, configs, specs)
│   └── data/                      # Test data, fixtures
├── scripts/                       # Shell/Node scripts (dev, Keycloak, Docker, etc.)
├── distribution/                  # Distribution scripts (sh/bat), docs
├── .claude/                       # Claude agents and commands (RCF stages, etc.)
├── .cursor/                       # Cursor-specific commands
├── .github/                       # CI/CD workflows
├── .husky/                        # Git hooks (e.g. pre-commit)
├── package.json                   # Root scripts, devDependencies, lint-staged
├── pnpm-workspace.yaml
├── tsconfig.json                  # Base TypeScript config
├── eslint.config.js               # ESLint flat config
├── .prettierrc.json
├── .c8rc.json                     # Coverage (c8)
├── docker-compose.yml             # Core + dev/prod profiles
├── Dockerfile
├── CLAUDE.md                      # AI/dev guidance, RCF commands, patterns index
└── .cursorrules                   # Cursor rules (format, exceptions, API, tests)
```

**Build order:** Packages are built first, then apps. Root script:  
`pnpm build` → `packages/*` build → `apps/*` build.

---

## 3. RCF Framework Structure (`docs/rcf/`)

All RCF artifacts live under `docs/rcf/`. The **single source of truth** for what exists is `docs/rcf/rcf.manifest.json`.

### 3.1 RCF Manifest (`rcf.manifest.json`)

Central index: one entry per PRD, with pointers to stories, TAD, build sequences (BS), and FBS.

**Top-level fields (conceptual):**

- `version`, `projectName`, `description`
- `activePrdId` (e.g. `PRD-001`)
- `prds[]`: each has `id`, `name`, `path`, and arrays:
  - `stories[]` → user story document(s)
  - `tad[]` → Technical Architecture Document(s)
  - `bs[]` → Build Sequence JSON files
  - `fbs[]` → Feature Build Specs (id, path, name, bsId)

**Use when generating TAD for a new project:** Create or update the manifest so every PRD has consistent `prds[].stories`, `prds[].tad`, `prds[].bs`, and `prds[].fbs` paths.

### 3.2 Product Requirements Document (PRD)

- **Location:** `docs/rcf/prds/<PRD-ID>.json` (e.g. `PRD-001.json`)
- **Role:** Product scope, problem statement, users, objectives, in/out of scope, constraints, and a list of **requirements** (id, title, description, category, domain, priority, rationale, tags).

**Typical PRD JSON shape:**

- `prdId`, `productName`, `version`, `status`
- `executiveSummary`, `problemStatement`, `targetUsers[]`, `objectives[]`
- `inScope[]`, `outOfScope[]`, `constraints[]`
- `requirements[]`: `id`, `title`, `description`, `category`, `domain`, `priority`, `rationale`, `tags`

### 3.3 User Stories

- **Location:** `docs/rcf/user-stories/<STORY-DOC>.json` (e.g. `US-PRD-001.json` – one file per PRD or story set)
- **Role:** User stories and acceptance criteria (AC) linked to requirements; used for traceability and integration tests.

**Typical story document shape:**

- `prdId`, `version`, `status`
- `stories[]`: each story has `id`, `reqId`, `title`, `description`, `asA`, `iWant`, `soThat`
- `acceptanceCriteria[]`: `id`, `description`, `testable`

**Traceability:** PRD → REQ → US → AC. Integration tests are organised by US and AC (e.g. `tests/integration/.../US-xxx/AC-xxx.spec.ts`).

### 3.4 Technical Architecture Document (TAD)

- **Location:** `docs/rcf/tad/<TAD-ID>.json` (e.g. `TAD-001.json`)
- **Role:** Extracted product context, functional/non-functional requirements, and architectural implications (for design and implementation).

**Typical TAD JSON shape (high level):**

- `tadId`, `prdId`, `version`, `status`
- `extractedConcerns.sourceDocuments` (PRD, user stories, versions)
- `extractedConcerns.productContext`: `productName`, `problemStatement`, `targetUsers[]`, `scope` (inScope, outOfScope)
- `extractedConcerns.functionalRequirements[]`: `reqId`, `title`, `description`, `category`, `priority`, `architecturalImplications[]`
- `extractedConcerns.nonFunctionalRequirements[]`: `reqId`, `title`, `category`, `targets`, `constraints`, `architecturalImplications[]`
- (Additional sections may include components, data flows, technology choices, etc.)

**Use for another project:** Use this repo’s TAD structure and sections as the template when generating a new TAD (same top-level keys and nesting).

### 3.5 Build Sequence (BS)

- **Location:** `docs/rcf/build-sequence/<PRD-ID>/<BS-ID>.json` (e.g. `PRD-001/BS-001.json`)
- **Role:** Ordered list of FBS items for a PRD (or a part of it). Each entry defines the feature slice, dependencies, testable outcomes, status, risk, domain.

**Typical BS JSON shape:**

- `bsId`, `prdId`, `version`, `status`, `title`
- `buildPhilosophy`, `generationStrategy` (e.g. vertical-slice)
- `buildSequence[]`: each item has:
  - `id` (FBS-ID), `title`, `summary`
  - `storyScope` (e.g. US-xxx(AC-xxx,...))
  - `dependencies[]` (other FBS-IDs)
  - `testableOutcomes[]`
  - `status`, `riskLevel`, `domain`

An **index** (e.g. `docs/rcf/build-sequence/PRD-001/index.md`) can summarise FBS id, title, BS, status, risk, domain, dependencies in a table.

### 3.6 Feature Build Specification (FBS)

- **Location:** `docs/rcf/fbs/<FBS-ID>.md` (e.g. `FBS-001.md`)
- **Role:** Single feature slice: scope, requirements, user stories, AC, testable outcomes, domain model, API contracts, and verification notes. Drives the RCF 5-stage workflow.

**Typical FBS markdown sections:**

- **Header:** FBS-ID, title, version, date, status, Parent TAD, Build Sequence (and position), domain, risk level
- **Document control** (version history)
- **Overview:** feature summary, build sequence position, RCF traceability (REQ, US, AC)
- **Story grouping validation:** user-facing value, testable AC, dependencies
- **Testable outcomes:** integration test outcomes, user story verification, AC coverage table
- **Domain model / API:** types, endpoints, config (as needed)
- **Verification:** how to verify (CLI, API, UI)

**RCF workflow:** Each FBS is executed through DEFINE → BUILD → REVIEW → TEST → FINALISE (see Section 6).

### 3.7 Patterns

- **Location:** `docs/rcf/patterns/*.md`
- **Role:** Reusable design and implementation patterns (backend, frontend, testing, infra). Referenced from CLAUDE.md and .cursorrules for consistent implementation.

**Example pattern files:**

- Backend: `api-structure.md`, `exception-handling.md`, `server-logging.md`, `caching-patterns.md`, `circuit-breaker.md`, `redis-service.md`, `mongodb-service.md`, `postgres-service.md`, `litellm-integration.md`, `authorization-access-control.md`, `api-security.md`, `sql-sanitisation.md`
- Frontend: `spa-pages.md`, `spa-data-tables.md`, `spa-pinia-stores.md`, `spa-chatbot.md`, `session-state.md`
- Shared: `typescript.md`, `code-quality.md`, `monorepo.md`, `unit-testing.md`, `rcf-test-patterns.md`
- Other: `keycloak-setup.md`, `websocket-realtime.md`

**Use for TAD:** In a new project TAD, list which of these (or project-specific) patterns apply and where they are documented.

### 3.8 Prompts and Other RCF Assets

- **Location:** `docs/rcf/prompts/` (e.g. add-fbs-to-build-sequence prompts)
- Optional: other RCF-specific docs (glossaries, conventions) under `docs/rcf/` as needed.

---

## 4. Packages and Dependencies

### 4.1 Root `package.json` (Workspace Root)

**Scripts (conceptual):**

- **Dev:** `dev`, `dev:api`, `dev:spa`, `dev:api:debug`, `dev:local`, `dev:local:stop`
- **Build:** `build` (packages then apps)
- **Test:** `test`, `test:unit`, `test:unit:watch`, `test:coverage`, `test:fbs`, `test:e2e`, `test:e2e:headed`, `test:e2e:ui`
- **Quality:** `format`, `format:check`, `lint`, `type-check`, `outdated`, `quality`
- **Docker:** `docker:ecr-login`, `docker:build`, `docker:run`, `docker:down`, `docker:local:up`, etc.
- **Other:** `clean`, `postman:generate`, `prepare` (husky)

**Root devDependencies (examples):**

- TypeScript, ESLint, Prettier, typescript-eslint, c8, tsx, tsup
- Playwright, Sinon, mongodb (for tests), husky, lint-staged
- Workspace packages used at root: e.g. `@wsd-ai-services-wespa/backend-common`, `backend-integration-tests` (for tooling/tests)

**Engines:** `node`: `>=24.11.1`, `pnpm`: `>=8.0.0`

### 4.2 Apps

| App             | Description                        | Key dependencies                                                                                                                                                                           |
| --------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **api-service** | Main backend API (Express)         | `@wsd-ai-services-wespa/backend-common`, `backend-text-to-data`, express, dotenv, mongodb, pg, redis, jsonwebtoken, jwks-rsa, swagger-jsdoc, swagger-ui-express, express-validator, multer |
| **spa-admin**   | Admin SPA (Vue 3 + Vite + Vuetify) | Vue, Vue Router, Pinia, Vuetify, Axios, Chart.js, vue-chartjs, markdown-it, highlight.js, dompurify, jwt-decode, @vueuse/core, etc.                                                        |

**Conventions:**

- Apps depend on workspace packages via `workspace:*`.
- API service builds with tsup (ESM); SPA builds with Vue/Vite.
- Unit tests live inside each app (e.g. `api-service/test/unit/`). E2E and shared integration tests live under `tests/`.

### 4.3 Shared Packages (`packages/@<scope>/`)

| Package                       | Purpose                                                                                                                                                                                       | Key dependencies                                                                                                                 |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **backend-common**            | Logger, cache, MongoDB/Postgres/Redis clients, exceptions, middleware (CORS, rate limit, security headers, request logger), validators, utils (env, sanitisation, UUID, recovery, PII masker) | express, mongodb, pg, redis, pino, cors, helmet, express-rate-limit, dotenv, uuid; optionally `backend-text-to-data` (workspace) |
| **backend-text-to-data**      | SQL sanitisation, text-to-data utilities                                                                                                                                                      | pgsql-ast-parser                                                                                                                 |
| **backend-integration-tests** | Helpers, fixtures, test DB, test server, JWT/rate-limit/data-source utilities, coverage analyser, test generators                                                                             | (dev/test focused; may depend on backend-common or app)                                                                          |

**Conventions:**

- Packages export ESM + CJS and types (`exports` in package.json with `types`, `import`, `require`).
- Built with tsup. Unit tests under `test/unit/`; run via `tsx --test` and c8 for coverage.
- Internal dependency chain: e.g. `backend-common` may depend on `backend-text-to-data`; apps depend on both.

### 4.4 Dependency Rules for a New Project

- Use **scoped package names** (e.g. `@wsd-ai-services-wespa/<name>`).
- Use **`workspace:*`** for intra-repo dependencies.
- Build order: no app should build before the packages it depends on; root `build` script enforces this.
- Document in the **TAD** which packages exist, their responsibilities, and dependency graph.

---

## 5. Testing Structure (RCF-Aligned)

- **Unit tests:** Per package or app (e.g. `packages/*/test/unit/**/*.test.ts`, `apps/api-service/test/unit/**/*.test.ts`). Node `node:test` + Sinon; c8 for coverage.
- **Integration tests:** Under `tests/integration/`. Organised by **User Story** and **Acceptance Criterion** to match RCF:
  - Path pattern: `tests/integration/<area>/US-<id>/AC-<id>.spec.ts`
  - Example areas: `api-service/`, `backend/`, `tooling/`
- **E2E tests:** Under `tests/e2e/` (Playwright). Configs may be at repo root or in `tests/e2e/`. SPA may have additional Playwright configs for integration/docker.
- **FBS test run:** `test:fbs` runs integration specs then e2e (as defined in root package.json).

**Use for TAD:** In the new project’s TAD, define the same test layers (unit, integration by US/AC, e2e) and where they live (per-app vs `tests/`).

---

## 6. RCF Build Workflow (5 Stages)

Each FBS is executed through five stages (orchestrated e.g. by `/rcf-execute-fbs <FBS-ID> [--from STAGE]`):

| Stage        | Purpose                                                | Typical outcome            |
| ------------ | ------------------------------------------------------ | -------------------------- |
| **DEFINE**   | Lock scope, AC, test cases, and contracts for the FBS  | Commit with DEFINE summary |
| **BUILD**    | Implement feature to satisfy AC; add/update unit tests | Commit with BUILD summary  |
| **REVIEW**   | Functional/code review against FBS and patterns        | Commit with REVIEW summary |
| **TEST**     | Run integration + E2E and verify testable outcomes     | Commit with TEST summary   |
| **FINALISE** | PR prep, docs, final checks                            | Commit + PR                |

Agents/commands under `.claude/agents/` and `.claude/commands/` implement each stage and the orchestrator. Use this 5-stage model in the new project’s TAD and tooling.

---

## 7. Conventions Summary (for TAD / New Project)

- **Monorepo:** pnpm workspaces; `packages/<scope>/*` and `apps/*`.
- **TypeScript:** Strict mode; ESM with `.js` extensions in imports; NodeNext.
- **Code quality:** Prettier + ESLint (zero warnings); format/lint/type-check at root and per package.
- **Errors:** Centralised exception conversion and standard error classes (e.g. from backend-common).
- **Logging:** Global logger; no sensitive data; structured (e.g. JSON) and levels.
- **API:** Controllers as named exports; routes import controller namespace; Swagger on routes; no URL versioning.
- **Git:** Pre-commit hooks (format + lint); conventional branch/commit usage for RCF (e.g. branch per FBS, commit per stage).

---

## 8. Checklist for Generating TAD for Another RCF Project

Use this when creating a TAD (or project setup) for a new project that will follow RCF:

1. **Repository layout**
   - [ ] Same top-level folders: `apps/`, `packages/<scope>/`, `docs/rcf/`, `tests/integration/`, `tests/e2e/`, `scripts/`.
   - [ ] `pnpm-workspace.yaml` and root `package.json` with equivalent scripts and quality gates.

2. **RCF artifact structure**
   - [ ] `docs/rcf/rcf.manifest.json` with `prds[]` and for each PRD: `stories`, `tad`, `bs`, `fbs`.
   - [ ] `docs/rcf/prds/<PRD-ID>.json` (requirements, scope, constraints).
   - [ ] `docs/rcf/user-stories/<STORY-DOC>.json` (stories and AC linked to REQ).
   - [ ] `docs/rcf/tad/<TAD-ID>.json` (same sections as this project: product context, functional/non-functional requirements, architectural implications).
   - [ ] `docs/rcf/build-sequence/<PRD-ID>/<BS-ID>.json` and optional `index.md`.
   - [ ] `docs/rcf/fbs/<FBS-ID>.md` (same section template: overview, traceability, testable outcomes, domain/API).
   - [ ] `docs/rcf/patterns/*.md` (reuse or adapt from this repo; reference in TAD).

3. **Packages and apps**
   - [ ] List apps and shared packages; document in TAD with responsibilities and dependency graph.
   - [ ] Use scoped names and `workspace:*`; document build order.

4. **Testing**
   - [ ] Unit tests per package/app; integration tests under `tests/integration/` by US/AC; E2E under `tests/e2e/`.
   - [ ] In TAD, describe test strategy and how it ties to RCF (FBS, AC, testable outcomes).

5. **Workflow and tooling**
   - [ ] Adopt 5-stage FBS workflow (DEFINE → BUILD → REVIEW → TEST → FINALISE).
   - [ ] Document in TAD how FBS execution and quality gates (lint, type-check, test) are run.

6. **Conventions**
   - [ ] In TAD, reference TypeScript, formatting, linting, error handling, logging, and API conventions (or point to pattern docs).

---

## 9. Document History

| Version | Date       | Changes                                                          |
| ------- | ---------- | ---------------------------------------------------------------- |
| 1.0     | 2026-02-08 | Initial RCF structure and packages reference for TAD generation. |
