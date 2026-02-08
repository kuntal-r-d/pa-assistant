# Job Automation System - Requirements Analysis & Refinement

## Executive Summary

This document provides a comprehensive analysis of the Business Requirements Document (BRD) for the Zero-Cost Remote Job Search Automation System, with recommendations for refinement aligned with the RCF (Requirements Confidence Framework) methodology.

---

## 1. CRITICAL GAPS IDENTIFIED

### 1.1 Technical Feasibility Concerns

| Requirement | Issue | Recommendation |
|-------------|-------|----------------|
| **JD-001: LinkedIn Scraping (50+ jobs)** | LinkedIn actively blocks scrapers with rate limits, CAPTCHAs, and IP bans. 50 jobs/day is optimistic without authentication. | **Downgrade to P1**, use LinkedIn API (with approval) or rely on aggregators. Add fallback strategy. |
| **IM-001: 5 seconds per job scoring** | TF-IDF vectorization + cosine similarity for 300 jobs = significant memory/CPU. May exceed 8GB RAM constraint. | Use **pre-computed embeddings** stored in DB. Process in batches of 50. |
| **CG-001: 30-second cover letter generation** | Ollama mistral:7b on 8GB RAM may take 45-90 seconds. 3 variants = 2-4 minutes total. | Revise to **60 seconds per variant** or use quantized model (mistral:7b-q4). |
| **AS-001: Complete scraping in 30 minutes** | 5 platforms × rate limits × error handling = realistically 45-60 minutes. | Revise to **60 minutes** or parallelize with caution. |

### 1.2 Missing Requirements

| Category | Missing Requirement | Priority | Rationale |
|----------|---------------------|----------|-----------|
| **Error Handling** | Circuit breaker for failed scrapers | P0 | Prevent cascade failures |
| **Error Handling** | Retry strategy with exponential backoff | P0 | Handle transient failures |
| **Security** | API key rotation mechanism | P1 | Anthropic key security |
| **Security** | Rate limit tracking per platform | P1 | Avoid IP bans |
| **Data Quality** | Job posting freshness validation | P1 | Avoid expired listings |
| **Data Quality** | Salary normalization (hourly/yearly/ranges) | P1 | Accurate comparisons |
| **User Experience** | Offline mode for dashboard | P2 | Local-first commitment |
| **User Experience** | Manual job entry fallback | P2 | When scraping fails |
| **Observability** | Scraping success rate metrics | P1 | Monitor health |
| **Observability** | AI response latency tracking | P2 | Performance tuning |

### 1.3 Legal/Compliance Gaps

| Risk | Current Coverage | Recommendation |
|------|------------------|----------------|
| **LinkedIn ToS Violation** | Acknowledged but no mitigation | Add: Disclaimer, rate limiting (1 req/3s), respect robots.txt |
| **GDPR Compliance** | Mentioned local storage | Add: Data deletion capability, no external transmission logging |
| **Job Board Copyright** | Not addressed | Add: Cache expiry (24h), no redistribution clause |

---

## 2. PRIORITY ADJUSTMENTS

### 2.1 Upgrade to P0 (Critical)

| Current | Requirement | Reason |
|---------|-------------|--------|
| P1 → P0 | **AT-001: Application Status Management** | Core value proposition - tracking is essential for MVP |
| P1 → P0 | **AS-003: Daily Job Digest Email** | Primary user notification - drives engagement |

### 2.2 Downgrade from P0

| Current | Requirement | Reason |
|---------|-------------|--------|
| P0 → P1 | **JD-001: LinkedIn Scraping** | Too risky as critical path - other sources more reliable |

### 2.3 Add New P0 Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| **EH-001** | Error Recovery System | Circuit breaker pattern; 3 failures = disable scraper for 1 hour; alert user |
| **SY-001** | Data Synchronization | Offline changes sync when online; conflict resolution strategy |

---

## 3. TECHNICAL CORRECTIONS

### 3.1 AI/ML Approach

**Current:** TF-IDF + Cosine Similarity
**Issue:** TF-IDF is keyword-based, misses semantic meaning ("React" won't match "React.js")

**Recommended Hybrid Approach:**
```
Match Score = (0.3 × TF-IDF) + (0.4 × Skill Overlap) + (0.2 × Experience Match) + (0.1 × Embedding Similarity)
```

**Implementation:**
1. Use `sentence-transformers` for embeddings (runs locally)
2. Pre-compute CV embedding once
3. Store job embeddings during scraping
4. Fall back to TF-IDF if embedding fails

### 3.2 Database Schema Corrections

**Current Issues:**
- No soft delete support
- No version history for generated content
- Missing indexes for common queries

**Recommended Schema Additions:**
```sql
-- Add to all tables
deleted_at TIMESTAMP NULL,
version INT DEFAULT 1,

-- Critical indexes
CREATE INDEX idx_jobs_match_score ON job_matches(match_score DESC);
CREATE INDEX idx_jobs_posted_date ON jobs(posted_date DESC);
CREATE INDEX idx_applications_status ON applications(status, updated_at);
CREATE INDEX idx_jobs_source_date ON jobs(source, posted_date);
```

### 3.3 Scraping Architecture

**Current:** Sequential scraping
**Issue:** Single point of failure, slow

**Recommended: Parallel with Circuit Breakers**
```
┌─────────────────────────────────────────────────────────┐
│                   n8n Orchestrator                       │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ LinkedIn │  │  Indeed  │  │ RemoteOK │  │ Others  │ │
│  │(disabled)│  │ (active) │  │ (active) │  │(active) │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │
│       │ ❌          │ ✓           │ ✓           │ ✓    │
│       ▼             ▼             ▼             ▼       │
│  ┌─────────────────────────────────────────────────┐   │
│  │            Circuit Breaker Layer                 │   │
│  │  • 3 failures = 1 hour cooldown                  │   │
│  │  • Health check before scraping                  │   │
│  │  • Exponential backoff on retry                  │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 4. RCF FRAMEWORK ALIGNMENT

### 4.1 Recommended PRD Structure

For RCF compliance, structure the PRD as follows:

```
PRD
├── REQ-001: Job Discovery & Aggregation
│   ├── US-001: Daily automated job scraping
│   │   ├── AC-001.1: Scrape from 4+ platforms
│   │   ├── AC-001.2: Handle platform failures gracefully
│   │   └── AC-001.3: Complete within 60 minutes
│   ├── US-002: Job deduplication
│   └── US-003: Job normalization
│
├── REQ-002: Intelligent Job Matching
│   ├── US-004: CV parsing and skill extraction
│   ├── US-005: Match score calculation
│   │   ├── AC-005.1: Calculate score 0-100%
│   │   ├── AC-005.2: Complete within 10 seconds per job
│   │   └── AC-005.3: Cache results for 30 days
│   └── US-006: Skill gap analysis
│
├── REQ-003: Content Generation
│   ├── US-007: Cover letter generation
│   ├── US-008: Cover letter polishing (optional)
│   └── US-009: CV tailoring
│
├── REQ-004: Application Tracking
│   ├── US-010: Status management
│   ├── US-011: Follow-up reminders
│   └── US-012: Timeline visualization
│
├── REQ-005: Analytics & Reporting
│   ├── US-013: Application funnel metrics
│   ├── US-014: Source performance analysis
│   └── US-015: Weekly digest reports
│
└── REQ-006: System Reliability
    ├── US-016: Error handling and recovery
    ├── US-017: Data backup and restore
    └── US-018: Health monitoring
```

### 4.2 Traceability Matrix

| Requirement | User Stories | Acceptance Criteria | Test Specs |
|-------------|--------------|---------------------|------------|
| REQ-001 | US-001, US-002, US-003 | AC-001.1 to AC-003.3 | TS-001 to TS-009 |
| REQ-002 | US-004, US-005, US-006 | AC-004.1 to AC-006.3 | TS-010 to TS-018 |
| REQ-003 | US-007, US-008, US-009 | AC-007.1 to AC-009.3 | TS-019 to TS-027 |
| REQ-004 | US-010, US-011, US-012 | AC-010.1 to AC-012.3 | TS-028 to TS-036 |
| REQ-005 | US-013, US-014, US-015 | AC-013.1 to AC-015.3 | TS-037 to TS-045 |
| REQ-006 | US-016, US-017, US-018 | AC-016.1 to AC-018.3 | TS-046 to TS-054 |

---

## 5. FEATURE BUILD SEQUENCE (FBS)

### Phase 1: Foundation (Week 1-2)

| Order | Feature | Dependencies | Deliverable |
|-------|---------|--------------|-------------|
| 1.1 | Database schema setup | None | PostgreSQL tables, indexes |
| 1.2 | CV upload & parsing | 1.1 | Parse PDF/DOCX, extract skills |
| 1.3 | User profile management | 1.1, 1.2 | Store preferences |
| 1.4 | Health check endpoints | 1.1 | /health for all services |

### Phase 2: Core Discovery (Week 2-3)

| Order | Feature | Dependencies | Deliverable |
|-------|---------|--------------|-------------|
| 2.1 | RemoteOK scraper | 1.1 | API-based, most reliable |
| 2.2 | WeWorkRemotely scraper | 1.1, 2.1 | HTML scraping |
| 2.3 | Himalayas scraper | 1.1, 2.1 | API-based |
| 2.4 | Indeed scraper | 1.1, 2.1 | With rate limiting |
| 2.5 | Job deduplication | 2.1-2.4 | Title+company matching |
| 2.6 | Job normalization | 2.5 | Standardize data |

### Phase 3: Intelligence (Week 3-4)

| Order | Feature | Dependencies | Deliverable |
|-------|---------|--------------|-------------|
| 3.1 | TF-IDF scoring | 1.2, 2.6 | Basic matching |
| 3.2 | Skill extraction (Ollama) | 1.2 | NLP-based extraction |
| 3.3 | Match score calculation | 3.1, 3.2 | Weighted formula |
| 3.4 | Gap analysis | 3.3 | Matched/missing skills |

### Phase 4: Generation (Week 4-5)

| Order | Feature | Dependencies | Deliverable |
|-------|---------|--------------|-------------|
| 4.1 | Cover letter draft (Ollama) | 3.4 | 3 style variants |
| 4.2 | Cover letter polish (Claude) | 4.1 | Optional API call |
| 4.3 | CV tailoring | 1.2, 3.4 | Highlight relevant skills |

### Phase 5: Tracking & UI (Week 5-6)

| Order | Feature | Dependencies | Deliverable |
|-------|---------|--------------|-------------|
| 5.1 | Application status management | 2.6 | Kanban states |
| 5.2 | Job list dashboard | 2.6, 3.3 | Card layout with filters |
| 5.3 | Job detail view | 5.2, 3.4, 4.1 | Full information |
| 5.4 | Kanban board | 5.1 | Drag-and-drop |

### Phase 6: Automation (Week 6-7)

| Order | Feature | Dependencies | Deliverable |
|-------|---------|--------------|-------------|
| 6.1 | Daily scraping workflow | 2.1-2.4 | n8n scheduled job |
| 6.2 | Auto match scoring | 3.3, 6.1 | Post-scraping trigger |
| 6.3 | Daily digest email | 6.2 | High-match notifications |
| 6.4 | Follow-up reminders | 5.1 | 7-day automated emails |

### Phase 7: Polish (Week 7-8)

| Order | Feature | Dependencies | Deliverable |
|-------|---------|--------------|-------------|
| 7.1 | Analytics dashboard | 5.1 | Funnel, conversion rates |
| 7.2 | Weekly reports | 7.1 | Email summaries |
| 7.3 | Data export | All | CSV/JSON download |
| 7.4 | Backup automation | 1.1 | Daily SQL dumps |

---

## 6. RISK ASSESSMENT

### High Risk

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LinkedIn blocks scraping | 90% | High | Rely on other sources; add manual entry |
| Ollama too slow on 8GB RAM | 60% | Medium | Use quantized models; batch processing |
| n8n workflow complexity | 40% | Medium | Start simple; add features incrementally |

### Medium Risk

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Job boards change structure | 50% | Medium | Monitor for changes; modular scraper design |
| Database grows too large | 30% | Low | Implement data retention policy |
| API cost overrun | 20% | Low | Track usage; set hard limits |

---

## 7. REFINED SUCCESS METRICS

| Metric | Current Target | Revised Target | Rationale |
|--------|----------------|----------------|-----------|
| Time to discover jobs | 30 min | 60 min | More realistic with rate limits |
| Jobs per day | 300+ | 200+ | LinkedIn likely unreliable |
| Match scoring speed | 5s/job | 10s/job | Embedding computation time |
| Cover letter generation | 30s | 90s | Local LLM constraints |
| Response rate improvement | 5x | 3x | Conservative estimate |

---

## 8. RECOMMENDED NEXT STEPS

1. **Validate Technical Constraints**
   - Benchmark Ollama mistral:7b on target hardware
   - Test scraper rate limits on each platform
   - Measure actual TF-IDF + embedding performance

2. **Finalize PRD Structure**
   - Convert to RCF-compliant format
   - Add traceability IDs (REQ-xxx, US-xxx, AC-xxx)
   - Define test specifications for each AC

3. **Prioritize MVP Scope**
   - Focus on reliable platforms first (RemoteOK, Himalayas)
   - Defer LinkedIn until alternative approach validated
   - Implement core matching before polish features

4. **Create Technical Architecture Document (TAD)**
   - Docker compose configuration
   - Service communication diagram
   - Data flow specification

---

*Analysis completed: 2026-02-08*
*Framework: RCF (Requirements Confidence Framework)*
