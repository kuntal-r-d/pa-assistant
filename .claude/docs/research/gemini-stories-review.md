I will read the existing user stories and the Product Requirement Document (PRD) to understand the current scope and identify potential gaps.
I will read the remaining user stories to determine if the specific LinkedIn, security, and edge case requirements are already covered.
I will read lines 2000-4000 of the user stories file to check for LinkedIn-related stories.
I will read lines 6000-8000 of the user stories file to locate the LinkedIn stealth scraping stories and further assess coverage.
I will read lines 8000+ of the user stories file to check for LinkedIn Email Alert integration and Manual URL Import stories.
I will perform a web search to identify industry best practices for handling LinkedIn OTP/2FA in automation and checking for "zombie jobs" to refine my recommendations.
## Gap Analysis: Job Search Automation System

Based on the analysis of your 297 existing user stories and industry best practices for scraping, security, and offline-first applications, here are the critical gaps identified.

### 1. Missing User Stories
The current backlog covers the "happy path" well but lacks coverage for "unhappy paths" and specific user experience scenarios.

| ID | Domain | User Story Title | Why It's Needed |
|----|--------|------------------|-----------------|
| **NEW-001** | **LinkedIn** | **Handle LinkedIn 2FA/OTP Challenges** | *Crucial.* US-210 covers login, but if LinkedIn asks for an SMS/Email code (common for scrapers), the automation will fail. You need a story for "Pause automation and request user manual OTP entry" or "Auto-fill TOTP from secret". |
| **NEW-002** | **Offline** | **View Dashboard Offline** | The system is local-first, but no story explicitly defines the UI state when internet is lost. Users should be able to browse *saved* jobs and view cached CVs without a connection. |
| **NEW-003** | **Offline** | **Queue Actions Offline** | If a user "Saves" a job or "Updates Status" while offline, these actions should queue and sync to the local DB immediately, then trigger any necessary background tasks (like fetching details) once online. |
| **NEW-004** | **Data** | **Detect & Archive "Zombie Jobs"** | Scraped jobs often close within days. You need a periodic "Health Check" story that visits the original URL of *saved* jobs to see if they redirect to a 404 or say "No longer accepting applications," automatically marking them as "Closed". |
| **NEW-005** | **Security** | **Sanitize Job Description HTML** | Jobs are scraped HTML. Storing and rendering them poses a Stored XSS risk. A specific story for "Sanitize HTML content before rendering" is mandatory for security. |
| **NEW-006** | **UX** | **Warm-up Mode for New Accounts** | 20-40 jobs/day (US-211) is safe for established accounts. New LinkedIn accounts need a "Warm-up" story: start at 5 jobs/day, increasing by 2 daily, to avoid immediate flagging. |

### 2. Acceptance Criteria Gaps
Existing ACs focus on *functionality* (it works) rather than *resilience* (it handles failure well).

*   **US-210 (LinkedIn Login):** Needs AC for "Given a 2FA prompt appears, Then send a desktop notification to the user and wait 5 minutes for input."
*   **US-180 (Docker Deploy):** Needs AC for "Given the container starts, Then it runs as a non-root user" (Security best practice).
*   **US-016 (Deduplication):** Needs AC for "Given a job is reposted with a new date but identical ID/Description, Then update the 'Last Seen' date instead of creating a duplicate."

### 3. Security Considerations
*   **Container Security:** Run containers as non-root users (User 1000) to prevent privilege escalation attacks if a container is compromised.
*   **Encrypted Backups:** You have cloud sync (US-251), but ensure the *local* backup file is also encrypted (GPG/Age) before it even touches the disk/rclone, managing keys via environment variables.
*   **Rate Limit Protection (Claude API):** You have a budget cap (US-080), but consider a "Circuit Breaker" for *cost velocity*. If $5 is spent in 10 minutes (bug/loop), kill the process immediately, regardless of the $10 monthly limit.

### 4. Scraping Edge Cases
*   **"Easy Apply" Detection:** Some users manually apply via LinkedIn. The scraper could potentially detect the "Applied" badge on LinkedIn job cards and auto-update the local status to "Applied" (High value feature).
*   **Salary Nuances:** Jobs often list "competitive" or "DOE" instead of numbers. The parser needs to explicitly handle these text values so they don't break numeric filters (e.g., treat as "0" or "Unspecified").
*   **Remote Restrictions:** A job might be "Remote" but description says "US Residents Only". The scraper should try to parse these geo-restrictions to filter out irrelevant "global" remote jobs.

### 5. LinkedIn-Specific Scenarios
*   **Session "Death" Loop:** If a session dies, the system might try to re-login repeatedly, triggering a ban. Need a story: "If login fails 3 times, disable automation for 24h."
*   **CAPTCHA Handling:** You have detection (US-225), but the response is just "stop". A better response is "Pause and alert user to solve manually," then resume.

### 6. Offline/Sync Scenarios
*   **Image Caching:** Job boards use CDN images for logos. These won't load offline. A story to "Cache company logos locally" would improve the offline experience significantly.
*   **LLM Availability:** US-067 uses local Ollama, which is great for offline. But US-070 (Claude Polish) requires internet. The UI needs to gray out "Polish with Claude" when offline.
