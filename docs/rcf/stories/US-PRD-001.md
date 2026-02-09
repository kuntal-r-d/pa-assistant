# User Stories - PRD-001

**Zero-Cost Remote Job Search Automation System**

| Field | Value |
|-------|-------|
| PRD ID | PRD-001 |
| Version | 1.2.0 |
| Status | Draft |
| Total Stories | 46 |
| Total Acceptance Criteria | 258 |

---

## Job Discovery Domain

### US-001: Daily Multi-Platform Job Scraping

**Requirement:** REQ-001

**As a** remote job seeker
**I want** the system to automatically scrape jobs from RemoteOK, WeWorkRemotely, Himalayas, and Indeed daily
**So that** I don't have to manually check each platform and can discover all relevant opportunities

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-001 | System scrapes RemoteOK API and retrieves job listings |
| AC-002 | System scrapes WeWorkRemotely and retrieves job listings |
| AC-003 | System scrapes Himalayas API and retrieves job listings |
| AC-004 | System scrapes Indeed with rate limiting and retrieves job listings |
| AC-005 | Scraping completes within 60 minutes for all platforms |

---

### US-002: Scraper Circuit Breaker

**Requirement:** REQ-001

**As a** remote job seeker
**I want** the system to continue scraping other platforms when one fails
**So that** a single platform outage doesn't prevent me from discovering jobs elsewhere

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-006 | After 3 consecutive failures, scraper enters 1-hour cooldown |
| AC-007 | Health check runs before each scraping attempt |
| AC-008 | Other scrapers continue when one is in cooldown |
| AC-009 | Alert email sent when scraper enters cooldown |

---

### US-003: Job Data Extraction

**Requirement:** REQ-002

**As a** remote job seeker
**I want** each job to have complete information extracted
**So that** I can make informed decisions without visiting the original posting

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-010 | Job title is extracted from listing |
| AC-011 | Company name is extracted from listing |
| AC-012 | Location (or 'Remote') is extracted from listing |
| AC-013 | Salary range is extracted when available |
| AC-014 | Full job description text is extracted |
| AC-015 | Technologies/skills are extracted from description |
| AC-016 | Posted date is extracted |
| AC-017 | Application URL is captured |

---

### US-004: Cross-Platform Job Deduplication

**Requirement:** REQ-003

**As a** remote job seeker
**I want** duplicate jobs to be automatically removed
**So that** I don't see the same job multiple times and waste time reviewing duplicates

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-018 | Jobs with same title AND company (case-insensitive) are identified as duplicates |
| AC-019 | The version with most complete data is retained |
| AC-020 | Deduplication runs after each scraping batch |
| AC-021 | Deduplication actions are logged for debugging |

---

### US-005: Job Data Normalization

**Requirement:** REQ-004

**As a** remote job seeker
**I want** job data to be normalized into consistent formats
**So that** I can accurately filter and compare jobs across platforms

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-022 | Country names are standardized (e.g., 'USA' to 'United States') |
| AC-023 | Technology names are mapped to canonical forms (e.g., 'React.js' to 'React') |
| AC-024 | Salary is converted to USD equivalent |
| AC-025 | Experience level is categorized (Junior/Mid/Senior/Lead) |

---

### US-006: Job Filtering by Preferences

**Requirement:** REQ-005

**As a** remote job seeker
**I want** to filter jobs by countries, technologies, salary, and experience level
**So that** I only see jobs that match my criteria

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-026 | Jobs can be filtered by one or more target countries (OR logic) |
| AC-027 | Jobs can be filtered by technologies (must match at least one) |
| AC-028 | Jobs can be filtered by salary range (min/max) |
| AC-029 | Jobs can be filtered by remote-only toggle |
| AC-030 | Jobs can be filtered by experience level |
| AC-031 | Filters can be combined and applied instantly |

---

### US-038: LinkedIn Stealth Job Scraping

**Requirement:** REQ-041

**As a** remote job seeker
**I want** the system to scrape 20-40 LinkedIn jobs daily using stealth automation
**So that** I can discover jobs from the most important professional platform without risking account bans

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-202 | Playwright browser with stealth plugin is used for LinkedIn scraping |
| AC-203 | Browser runs in headed mode (visible window) to mimic real usage |
| AC-204 | System extracts job title, company, location, salary, and description from LinkedIn listings |
| AC-205 | Daily scraping limit is 20-40 jobs to maintain conservative rate |
| AC-206 | Scraping session starts from LinkedIn feed page, not directly at job search |
| AC-207 | System interacts with feed (scrolls, pauses) before navigating to jobs |

---

### US-039: LinkedIn Session Persistence

**Requirement:** REQ-042

**As a** remote job seeker
**I want** my LinkedIn session to persist between scraping runs
**So that** I don't trigger detection by logging in repeatedly

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-208 | Browser profile with cookies and localStorage is persisted to disk |
| AC-209 | Session is resumed on subsequent scraping runs without re-login |
| AC-210 | Session files are stored locally with 7-day rotation |
| AC-211 | Manual re-authentication prompt shown only when session expires |
| AC-212 | Session data is encrypted at rest using user-provided key |

---

### US-040: LinkedIn Human-Like Behavior

**Requirement:** REQ-043

**As a** remote job seeker
**I want** the scraper to behave like a real human browsing LinkedIn
**So that** LinkedIn's behavioral analysis cannot detect automation

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-213 | Delays between actions follow Gamma distribution (8s ± 4s mean) |
| AC-214 | Session length varies between 15-25 minutes per run |
| AC-215 | Mouse movements are simulated with realistic bezier curves |
| AC-216 | Scroll behavior varies (speed, pauses, direction changes) |
| AC-217 | Scraping only occurs during business hours (9 AM - 6 PM local time) |
| AC-218 | Random 'reading' pauses (5-15s) occur when viewing job details |

---

### US-041: LinkedIn Detection Monitoring

**Requirement:** REQ-044

**As a** remote job seeker
**I want** the system to detect when LinkedIn suspects automation and pause automatically
**So that** my account is protected from bans

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-219 | CAPTCHA challenges are detected and trigger immediate pause |
| AC-220 | Rate limit responses (429) trigger immediate pause |
| AC-221 | Unusual redirects (security checkpoint) are detected |
| AC-222 | Account warning messages in DOM are detected |
| AC-223 | Initial pause duration is 24 hours after first detection |
| AC-224 | Exponential backoff (24h to 48h to 96h) on repeated detections |
| AC-225 | Email alert sent to user when detection pause is triggered |

---

### US-042: LinkedIn Browser Fingerprint Injection

**Requirement:** REQ-045

**As a** remote job seeker
**I want** my browser fingerprint to appear unique and human-like
**So that** LinkedIn's fingerprinting detection cannot identify the automation

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-226 | Canvas fingerprint is randomized using fingerprint-generator |
| AC-227 | WebGL renderer string is varied realistically |
| AC-228 | Font enumeration is masked to a common subset |
| AC-229 | Timezone matches user profile location |
| AC-230 | Browser language matches user profile preferences |
| AC-231 | Screen resolution is set to common desktop values |
| AC-232 | Fingerprint remains consistent within a session, varies between sessions |

---

### US-043: LinkedIn Email Alert Integration

**Requirement:** REQ-046

**As a** remote job seeker
**I want** to import jobs from my LinkedIn email alerts
**So that** I have a zero-risk backup when stealth scraping is paused

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-233 | System connects to email via IMAP with user credentials |
| AC-234 | LinkedIn job alert emails are identified and parsed |
| AC-235 | Job URLs are extracted from email content |
| AC-236 | Job titles and companies are extracted from email |
| AC-237 | Posting dates are extracted when available |
| AC-238 | Duplicate jobs (already in system) are skipped |
| AC-239 | Email parsing runs automatically when stealth scraping is paused |

---

### US-044: LinkedIn Manual URL Import

**Requirement:** REQ-047

**As a** remote job seeker
**I want** to paste LinkedIn job URLs and have them imported
**So that** I can still track LinkedIn jobs when automation is unavailable

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-240 | Text input accepts one or more LinkedIn job URLs |
| AC-241 | URLs are validated as LinkedIn job posting format |
| AC-242 | Full job details are fetched from provided URLs |
| AC-243 | Rate limiting of 1 request per 30 seconds is enforced |
| AC-244 | Progress indicator shows import status |
| AC-245 | Imported jobs are marked with 'Manual Import' source tag |

---

## Intelligent Matching Domain

### US-007: CV Upload and Parsing

**Requirement:** REQ-006

**As a** remote job seeker
**I want** to upload my CV and have the system extract my skills and experience
**So that** the system can match me with relevant jobs

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-032 | PDF files up to 5MB can be uploaded |
| AC-033 | DOCX files up to 5MB can be uploaded |
| AC-034 | Text is extracted with 95%+ accuracy |
| AC-035 | Technical skills are identified and listed |
| AC-036 | Years of experience are calculated from dates |
| AC-037 | Education and certifications are extracted |
| AC-038 | User can manually edit extracted data |

---

### US-008: Job Search Preferences Setup

**Requirement:** REQ-007

**As a** remote job seeker
**I want** to set my target countries, technologies, salary expectations, and experience level
**So that** the system knows what jobs to prioritize for me

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-039 | User can select multiple target countries |
| AC-040 | User can select preferred technologies with autocomplete |
| AC-041 | User can set minimum and maximum salary |
| AC-042 | User can select currency (USD, EUR, GBP) |
| AC-043 | User can set experience level preference |
| AC-044 | Preferences auto-save on change |

---

### US-009: Hybrid Job Match Scoring

**Requirement:** REQ-008

**As a** remote job seeker
**I want** each job to have a match score showing how well it fits my profile
**So that** I can prioritize the most relevant opportunities

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-045 | Match score is calculated as 0-100% |
| AC-046 | TF-IDF text similarity contributes 30% to score |
| AC-047 | Skill overlap contributes 40% to score |
| AC-048 | Experience match contributes 20% to score |
| AC-049 | Semantic embeddings contribute 10% to score |
| AC-050 | Scoring completes within 10 seconds per job |
| AC-051 | Scores are cached and recalculated only when CV changes |

---

### US-010: Skill Gap Identification

**Requirement:** REQ-009

**As a** remote job seeker
**I want** to see matched skills, missing skills, and extra skills for each job
**So that** I can assess my fit and identify areas for improvement

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-052 | Matched skills (in CV AND job) are listed |
| AC-053 | Missing skills (in job NOT in CV) are listed |
| AC-054 | Extra skills (in CV NOT in job) are listed |
| AC-055 | Match percentage is calculated |
| AC-056 | Fuzzy matching handles synonyms (e.g., 'JS' matches 'JavaScript') |

---

### US-011: AI Gap Analysis Report

**Requirement:** REQ-010

**As a** remote job seeker
**I want** AI-generated analysis with strengths, gaps, and improvement suggestions
**So that** I get actionable advice beyond simple skill matching

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-057 | Analysis includes 3-5 strengths |
| AC-058 | Analysis includes 3-5 missing skills |
| AC-059 | Analysis includes 3-5 actionable improvement suggestions |
| AC-060 | Analysis includes overall assessment (2-3 sentences) |
| AC-061 | Analysis is generated using Ollama within 15 seconds |
| AC-062 | Analysis is cached for 30 days |

---

## Content Generation Domain

### US-012: Cover Letter Generation

**Requirement:** REQ-011

**As a** remote job seeker
**I want** to generate 3 different cover letter styles for each job
**So that** I can choose the style that best fits the company culture

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-063 | Conservative variant is professional and formal |
| AC-064 | Aggressive variant is bold and confident |
| AC-065 | Story-driven variant focuses on narrative and mission alignment |
| AC-066 | Each variant is 300-400 words with 3-4 paragraphs |
| AC-067 | Cover letters include user name and job details |
| AC-068 | Cover letters highlight relevant experience from CV |
| AC-069 | All 3 variants generate within 90 seconds each |

---

### US-013: Cover Letter Polish with Claude

**Requirement:** REQ-012

**As a** remote job seeker
**I want** to polish my cover letter with Claude API for important applications
**So that** I get professional-quality cover letters for jobs I really want

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-070 | Polish is auto-triggered for jobs with match >= 85% |
| AC-071 | User can manually request polish for any job |
| AC-072 | Polish improves grammar, clarity, and tone |
| AC-073 | Polish completes within 10 seconds |
| AC-074 | Both draft and polished versions are stored |

---

### US-014: CV Tailoring

**Requirement:** REQ-013

**As a** remote job seeker
**I want** to generate a tailored CV that highlights relevant experience
**So that** my CV resonates with the specific job requirements

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-075 | Bullet points are reordered by relevance to job |
| AC-076 | 'Key Skills Match' section is added at top |
| AC-077 | Matching technologies are highlighted (bold) |
| AC-078 | Tailored CV can be exported as Markdown or PDF |
| AC-079 | User can edit before downloading |

---

### US-015: AI Cost Tracking

**Requirement:** REQ-014

**As a** remote job seeker
**I want** to see my AI API usage and get alerts near budget limits
**So that** I don't exceed my monthly budget

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-080 | Ollama calls are tracked (unlimited) |
| AC-081 | Claude API calls are tracked with cost estimation |
| AC-082 | Alert shown when approaching $10 monthly budget |
| AC-083 | System falls back to Ollama-only when budget exceeded |

---

## Application Tracking Domain

### US-016: Application Status Tracking

**Requirement:** REQ-015

**As a** remote job seeker
**I want** to track each application through its lifecycle
**So that** I know which applications need attention and can follow up appropriately

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-084 | Applications can be marked as Saved |
| AC-085 | Applications can be marked as Reviewing |
| AC-086 | Applications can be marked as Applied with date |
| AC-087 | Applications can be marked as Interviewing |
| AC-088 | Applications can be marked as Rejected |
| AC-089 | Applications can be marked as Offered |
| AC-090 | Status changes record timestamps |
| AC-091 | Statuses can only move forward (except Rejected) |

---

### US-017: Application Notes

**Requirement:** REQ-016

**As a** remote job seeker
**I want** to add notes to each application
**So that** I can track important details for interviews and follow-ups

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-092 | Freeform text can be added to any application |
| AC-093 | Rich text formatting (bold, italic, lists) is supported |
| AC-094 | Notes auto-save with 2-second debounce |
| AC-095 | Note count badge shown on application card |

---

### US-018: Automated Follow-Up Reminders

**Requirement:** REQ-017

**As a** remote job seeker
**I want** automatic email reminders 7 days after applying
**So that** I don't forget to follow up on applications

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-096 | Email reminder sent 7 days after 'Applied' status |
| AC-097 | Email includes company name, job title, and days since applied |
| AC-098 | User can snooze reminder (3/7/14 days) |
| AC-099 | User can dismiss reminder |
| AC-100 | Reminder auto-cancelled if status changes to Interviewing/Rejected |

---

### US-019: Application Timeline View

**Requirement:** REQ-018

**As a** remote job seeker
**I want** to see a timeline of my application progress
**So that** I can identify slow-moving applications and bottlenecks

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-101 | Horizontal timeline shows all status stages |
| AC-102 | Days between stages are calculated and displayed |
| AC-103 | Average times shown for comparison |
| AC-104 | Color-coded: green (fast), yellow (average), red (slow) |

---

## User Interface Domain

### US-020: Job List Dashboard

**Requirement:** REQ-019

**As a** remote job seeker
**I want** to see all discovered jobs in a clean, filterable dashboard
**So that** I can quickly find and review relevant opportunities

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-105 | Jobs displayed in card layout (3 columns on desktop) |
| AC-106 | Each card shows title, company, location, salary, match %, technologies |
| AC-107 | Pagination with 20 jobs per page |
| AC-108 | Sort by match %, posted date, or salary |
| AC-109 | Filter panel on left sidebar |
| AC-110 | Dashboard loads within 2 seconds for 1000 jobs |

---

### US-021: Job Detail View

**Requirement:** REQ-020

**As a** remote job seeker
**I want** to see all details about a job in one place
**So that** I can make informed application decisions

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-111 | Header shows title, company, location, salary, posted date |
| AC-112 | Large match score card with color coding |
| AC-113 | Tabs for Description, Requirements, Gap Analysis, Cover Letters, CV |
| AC-114 | Requirements checklist shows matched and missing skills |
| AC-115 | 3 cover letter variants shown side-by-side |
| AC-116 | Tailored CV preview with download button |
| AC-117 | Action buttons: Save, Generate Cover Letter, Track, Open URL |

---

### US-022: Kanban Application Board

**Requirement:** REQ-021

**As a** remote job seeker
**I want** to manage my applications on a visual Kanban board
**So that** I can easily see and update application statuses

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-118 | Columns for each status: Saved, Reviewing, Applied, Interviewing, Rejected, Offered |
| AC-119 | Jobs can be dragged between columns |
| AC-120 | Each card shows title, company, match %, days in stage |
| AC-121 | Card count displayed per column |
| AC-122 | Filter by date range (Last 7/30/90 days) |

---

## Analytics Domain

### US-023: Analytics Dashboard

**Requirement:** REQ-022

**As a** remote job seeker
**I want** to see analytics about my job search performance
**So that** I can optimize my strategy based on data

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-123 | Application funnel chart (Discovered to Applied to Interview to Offer) |
| AC-124 | Conversion rates between stages displayed |
| AC-125 | Source performance table (Platform, Jobs, Applied, Response rate) |
| AC-126 | Match score distribution histogram |
| AC-127 | Weekly activity chart |
| AC-128 | Export to CSV button |

---

### US-024: Daily Job Digest Email

**Requirement:** REQ-023

**As a** remote job seeker
**I want** to receive a daily email with the best new job matches
**So that** I stay informed without logging in every day

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-129 | Email sent at 9:00 AM daily |
| AC-130 | Only sent if new jobs with match >= 70% exist |
| AC-131 | Contains top 10 jobs sorted by match score |
| AC-132 | Each job shows title, company, match %, dashboard link |
| AC-133 | HTML formatted and mobile-responsive |
| AC-134 | Unsubscribe link in footer |

---

### US-025: Weekly Analytics Report Email

**Requirement:** REQ-024

**As a** remote job seeker
**I want** to receive a weekly email summarizing my job search progress
**So that** I can track my progress and stay motivated

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-135 | Email sent every Sunday at 9:00 PM |
| AC-136 | Contains jobs discovered this week |
| AC-137 | Contains applications submitted |
| AC-138 | Contains interviews scheduled |
| AC-139 | Contains conversion rates |
| AC-140 | Contains top trending technologies |

---

## Automation Domain

### US-026: Scheduled Daily Scraping

**Requirement:** REQ-025

**As a** remote job seeker
**I want** job scraping to run automatically every day
**So that** I always have fresh job data without manual intervention

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-141 | n8n workflow triggers at 8:00 AM daily |
| AC-142 | Workflow calls scraper API for all platforms |
| AC-143 | Scraping completes within 60 minutes |
| AC-144 | Failed platforms retry 3 times |
| AC-145 | Alert email sent if zero jobs scraped |

---

### US-027: Automated Match Scoring

**Requirement:** REQ-026

**As a** remote job seeker
**I want** new jobs to be automatically scored after scraping
**So that** I can immediately see relevant matches

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-146 | Scoring triggers after daily scraping completes |
| AC-147 | Only new jobs (no existing score) are processed |
| AC-148 | Jobs processed in batches of 10 |
| AC-149 | 300 jobs scored within 50 minutes |

---

## System Reliability Domain

### US-028: Scraper Circuit Breaker Implementation

**Requirement:** REQ-027

**As a** system administrator
**I want** circuit breakers to prevent cascade failures
**So that** one failing platform doesn't affect the entire system

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-150 | Each scraper has independent circuit breaker |
| AC-151 | 3 consecutive failures trigger cooldown |
| AC-152 | Cooldown lasts 1 hour |
| AC-153 | Health check runs before scraping attempt |
| AC-154 | Graceful degradation when platform unavailable |

---

### US-029: Retry Logic with Exponential Backoff

**Requirement:** REQ-028

**As a** system administrator
**I want** automatic retries with exponential backoff
**So that** transient failures are handled gracefully

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-155 | First retry after 1 second |
| AC-156 | Second retry after 2 seconds |
| AC-157 | Third retry after 4 seconds |
| AC-158 | Maximum backoff of 30 seconds |
| AC-159 | Maximum 3 retries by default (configurable) |

---

### US-030: Service Health Check Endpoints

**Requirement:** REQ-029

**As a** system administrator
**I want** health check endpoints for each service
**So that** I can monitor system health and set up alerts

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-160 | Scraper API exposes /health endpoint |
| AC-161 | PostgreSQL connection can be tested |
| AC-162 | Ollama model availability can be checked |
| AC-163 | n8n workflow status can be queried |
| AC-164 | Health checks run every 5 minutes |
| AC-165 | Alert email sent after 3 consecutive failures |

---

### US-031: Centralized Error Logging

**Requirement:** REQ-030

**As a** system administrator
**I want** centralized, structured error logs
**So that** I can debug issues and track incidents

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-166 | All services log to ./logs/ directory |
| AC-167 | Logs use JSON structured format |
| AC-168 | Logs include timestamp, service, severity, message, context |
| AC-169 | Logs rotate daily |
| AC-170 | Last 30 days of logs retained |

---

## Infrastructure Domain

### US-032: Automated Database Backup

**Requirement:** REQ-031

**As a** system administrator
**I want** automatic daily database backups
**So that** I can recover from data loss

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-171 | Backup runs at 2:00 AM daily |
| AC-172 | Backups stored in ./backups/ directory |
| AC-173 | Filename format: backup_YYYYMMDD.sql |
| AC-174 | Last 7 days of backups retained |
| AC-175 | Backups are compressed (gzip) |
| AC-176 | Restore is tested monthly (automated) |

---

### US-033: Data Retention Policy

**Requirement:** REQ-032

**As a** system administrator
**I want** automatic cleanup of old data
**So that** the database doesn't grow unboundedly

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-177 | Unsaved jobs deleted after 90 days |
| AC-178 | Saved jobs retained indefinitely |
| AC-179 | Generated content deleted after 30 days |
| AC-180 | Raw analytics aggregated monthly, deleted after 6 months |
| AC-181 | Cleanup runs weekly (Sunday midnight) |

---

### US-034: Docker Deployment

**Requirement:** REQ-033

**As a** system administrator
**I want** to deploy the entire system with one command
**So that** setup is simple and reproducible

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-182 | docker-compose.yml defines all services |
| AC-183 | Scraper API container configured |
| AC-184 | PostgreSQL container configured with volume |
| AC-185 | Ollama container configured |
| AC-186 | n8n container configured |
| AC-187 | Web frontend container configured |
| AC-188 | Single 'docker-compose up' starts entire system |

---

### US-045: Cloud Backup Sync to Google Drive

**Requirement:** REQ-048

**As a** remote job seeker
**I want** my backups to be automatically synced to Google Drive
**So that** I can recover my data even if my local machine fails

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-246 | rclone is configured to sync with Google Drive (or configurable provider) |
| AC-247 | Backup files are encrypted before upload using user-provided key |
| AC-248 | Cloud sync runs automatically after each daily local backup |
| AC-249 | Cloud storage retains 90 days of backups |
| AC-250 | Sync failures trigger email alert to user |
| AC-251 | Cloud backup can be disabled via configuration |

---

### US-046: Docker Volume Data Persistence

**Requirement:** REQ-049

**As a** system administrator
**I want** all data to persist even when containers are recreated or updated
**So that** I never lose data due to container operations

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-252 | PostgreSQL data uses named volume (postgres_data) |
| AC-253 | Backup directory uses named volume (backups) |
| AC-254 | LinkedIn session data uses named volume (linkedin_sessions) |
| AC-255 | User uploads use named volume (uploads) |
| AC-256 | Data persists after docker-compose down followed by docker-compose up |
| AC-257 | Data persists after container image updates |
| AC-258 | Volume backup script is provided for manual volume export |

---

## Security Domain

### US-035: Local Data Storage

**Requirement:** REQ-038

**As a** privacy-conscious job seeker
**I want** all my data to stay on my local machine
**So that** my job search activity remains private

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-189 | CV stored only in local PostgreSQL |
| AC-190 | Preferences stored only locally |
| AC-191 | Application history stored only locally |
| AC-192 | No data transmitted externally except optional Claude API |
| AC-193 | Claude API calls only contain job description + cover letter draft |

---

### US-036: Secure API Key Management

**Requirement:** REQ-039

**As a** system administrator
**I want** API keys stored securely in environment variables
**So that** credentials are not exposed in code or logs

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-194 | API keys stored in .env file |
| AC-195 | API keys never appear in code |
| AC-196 | API keys never appear in logs |
| AC-197 | .env.example provided with documentation |
| AC-198 | Startup validation checks required env vars |

---

## Usability Domain

### US-037: Single-User Local Setup

**Requirement:** REQ-040

**As a** remote job seeker
**I want** a simple setup without login requirements
**So that** I can start using the system immediately

#### Acceptance Criteria

| ID | Description |
|----|-------------|
| AC-199 | One-time profile setup on first launch |
| AC-200 | No authentication required for local access |
| AC-201 | Profile data persists between sessions |

---

## Traceability Matrix

| Story ID | Requirement ID | Domain |
|----------|---------------|--------|
| US-001 | REQ-001 | Job Discovery |
| US-002 | REQ-001 | Job Discovery |
| US-003 | REQ-002 | Job Discovery |
| US-004 | REQ-003 | Job Discovery |
| US-005 | REQ-004 | Job Discovery |
| US-006 | REQ-005 | Job Discovery |
| US-038 | REQ-041 | Job Discovery (LinkedIn) |
| US-039 | REQ-042 | Job Discovery (LinkedIn) |
| US-040 | REQ-043 | Job Discovery (LinkedIn) |
| US-041 | REQ-044 | Job Discovery (LinkedIn) |
| US-042 | REQ-045 | Job Discovery (LinkedIn) |
| US-043 | REQ-046 | Job Discovery (LinkedIn) |
| US-044 | REQ-047 | Job Discovery (LinkedIn) |
| US-007 | REQ-006 | Intelligent Matching |
| US-008 | REQ-007 | Intelligent Matching |
| US-009 | REQ-008 | Intelligent Matching |
| US-010 | REQ-009 | Intelligent Matching |
| US-011 | REQ-010 | Intelligent Matching |
| US-012 | REQ-011 | Content Generation |
| US-013 | REQ-012 | Content Generation |
| US-014 | REQ-013 | Content Generation |
| US-015 | REQ-014 | Content Generation |
| US-016 | REQ-015 | Application Tracking |
| US-017 | REQ-016 | Application Tracking |
| US-018 | REQ-017 | Application Tracking |
| US-019 | REQ-018 | Application Tracking |
| US-020 | REQ-019 | User Interface |
| US-021 | REQ-020 | User Interface |
| US-022 | REQ-021 | User Interface |
| US-023 | REQ-022 | Analytics |
| US-024 | REQ-023 | Analytics |
| US-025 | REQ-024 | Analytics |
| US-026 | REQ-025 | Automation |
| US-027 | REQ-026 | Automation |
| US-028 | REQ-027 | System Reliability |
| US-029 | REQ-028 | System Reliability |
| US-030 | REQ-029 | System Reliability |
| US-031 | REQ-030 | System Reliability |
| US-032 | REQ-031 | Infrastructure |
| US-033 | REQ-032 | Infrastructure |
| US-034 | REQ-033 | Infrastructure |
| US-045 | REQ-048 | Infrastructure (Backup) |
| US-046 | REQ-049 | Infrastructure (Docker) |
| US-035 | REQ-038 | Security |
| US-036 | REQ-039 | Security |
| US-037 | REQ-040 | Usability |

---

*Generated: 2026-02-08 | Updated: 2026-02-08 (v1.2.0 - LinkedIn + Cloud Backup + Docker Persistence)*
