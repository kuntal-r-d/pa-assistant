# Human-Like Browser Automation: Stealth Patterns for 2026

**Context**: Personal job search tool for LinkedIn (single user, non-commercial)
**Research Date**: February 2026
**Tech Stack**: TypeScript/Node.js with Playwright/Puppeteer

## Executive Summary

This research covers modern techniques for avoiding bot detection in browser automation, specifically tailored for personal LinkedIn job search. Implementation priority is ordered by effectiveness vs. risk ratio.

### Recommended Implementation Order
1. **Stealth plugins** (puppeteer-extra-plugin-stealth / playwright-stealth) - Foundation
2. **Browser fingerprint randomization** - Critical for long-term sessions
3. **Human-like timing patterns** - Essential behavioral mimicry
4. **Session management** - Maintain realistic user sessions
5. **Mouse movement simulation** - Advanced behavioral layer
6. **Rate limiting patterns** - Avoid triggering velocity checks
7. **Headless detection countermeasures** - Final polish

---

## 1. Browser Fingerprint Randomization

### Overview
Modern detection systems analyze browser fingerprints (canvas, WebGL, fonts, plugins, hardware specs) to identify automation. Randomization creates believable variation without appearing suspicious.

### Implementation Approach

```typescript
// Using playwright with fingerprint randomization
import { chromium } from 'playwright-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import { FingerprintGenerator } from 'fingerprint-generator';
import { FingerprintInjector } from 'fingerprint-injector';

chromium.use(StealthPlugin());

async function launchStealthBrowser() {
  const fingerprintGenerator = new FingerprintGenerator({
    devices: ['desktop'], // Focus on desktop for LinkedIn
    browsers: ['chrome'],
    operatingSystems: ['windows', 'macos'],
  });

  const fingerprint = fingerprintGenerator.getFingerprint({
    locales: ['en-US'],
    screen: {
      minWidth: 1366,
      maxWidth: 1920,
    },
  });

  const browser = await chromium.launch({
    headless: false, // Use headed for better stealth
    args: [
      '--disable-blink-features=AutomationControlled',
      '--disable-features=IsolateOrigins,site-per-process',
      '--disable-dev-shm-usage',
      `--window-size=${fingerprint.screen.width},${fingerprint.screen.height}`,
    ],
  });

  const context = await browser.newContext({
    viewport: fingerprint.screen,
    userAgent: fingerprint.navigator.userAgent,
    locale: 'en-US',
    timezoneId: 'America/New_York', // Match to your actual timezone
    permissions: ['geolocation'],
  });

  // Inject fingerprint
  const page = await context.newPage();
  const injector = new FingerprintInjector();
  await injector.attachFingerprintToPlaywright(page, fingerprint);

  return { browser, context, page };
}
```

### Canvas Fingerprint Randomization

```typescript
// Inject canvas noise to avoid fingerprinting
async function injectCanvasNoise(page: Page) {
  await page.addInitScript(() => {
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    const originalToBlob = HTMLCanvasElement.prototype.toBlob;
    const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;

    // Add subtle noise to canvas
    const noise = () => Math.random() * 0.0001;

    HTMLCanvasElement.prototype.toDataURL = function(...args) {
      const context = this.getContext('2d');
      if (context) {
        const imageData = context.getImageData(0, 0, this.width, this.height);
        for (let i = 0; i < imageData.data.length; i++) {
          imageData.data[i] += noise();
        }
        context.putImageData(imageData, 0, 0);
      }
      return originalToDataURL.apply(this, args);
    };
  });
}
```

### WebGL Fingerprint Randomization

```typescript
async function injectWebGLNoise(page: Page) {
  await page.addInitScript(() => {
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
      // Randomize UNMASKED_VENDOR_WEBGL and UNMASKED_RENDERER_WEBGL
      if (parameter === 37445) { // UNMASKED_VENDOR_WEBGL
        return 'Intel Inc.';
      }
      if (parameter === 37446) { // UNMASKED_RENDERER_WEBGL
        return 'Intel Iris OpenGL Engine';
      }
      return getParameter.call(this, parameter);
    };
  });
}
```

**Effectiveness Rating**: 9/10
**Risk Level**: Low
**Libraries**:
- `fingerprint-generator` + `fingerprint-injector`
- `puppeteer-extra-plugin-stealth`
- `playwright-stealth`

**Best Practices**:
- Use consistent fingerprints per session (don't randomize mid-session)
- Match timezone to actual location
- Keep viewport sizes realistic (1366x768, 1920x1080)
- Don't use exotic browser configurations

**Common Pitfalls**:
- Over-randomization (creates suspicious patterns)
- Mismatched fingerprint components (e.g., macOS with Windows fonts)
- Changing fingerprint during active session

---

## 2. Human-Like Timing Patterns

### Overview
Humans don't interact with pages at constant intervals. Natural behavior includes variable delays, thinking pauses, and realistic scroll speeds.

### Gaussian Distribution Delays

```typescript
// Generate human-like delays using Gaussian distribution
function gaussianRandom(mean: number, stdDev: number): number {
  const u1 = Math.random();
  const u2 = Math.random();
  const z0 = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
  return Math.max(0, z0 * stdDev + mean);
}

function humanDelay(min: number, max: number): number {
  const mean = (min + max) / 2;
  const stdDev = (max - min) / 6;
  return Math.round(gaussianRandom(mean, stdDev));
}

// Usage
async function humanWait(min = 500, max = 2000) {
  const delay = humanDelay(min, max);
  await new Promise(resolve => setTimeout(resolve, delay));
}
```

### Variable Scroll Speed

```typescript
async function humanScroll(page: Page, targetY: number) {
  const startY = await page.evaluate(() => window.scrollY);
  const distance = targetY - startY;
  const duration = humanDelay(800, 1500); // Total scroll time
  const steps = Math.ceil(duration / 16); // 60fps

  for (let i = 0; i <= steps; i++) {
    const progress = i / steps;
    // Easing function for natural deceleration
    const easing = progress < 0.5
      ? 2 * progress * progress
      : 1 - Math.pow(-2 * progress + 2, 2) / 2;

    const currentY = startY + (distance * easing);
    await page.evaluate((y) => window.scrollTo(0, y), currentY);
    await new Promise(resolve => setTimeout(resolve, 16));
  }

  // Add small random micro-scrolls
  if (Math.random() > 0.7) {
    await humanWait(200, 500);
    const microScroll = (Math.random() - 0.5) * 50;
    await page.evaluate((delta) => window.scrollBy(0, delta), microScroll);
  }
}
```

### Reading Time Simulation

```typescript
// Calculate realistic reading time based on content
function calculateReadingTime(text: string): number {
  const wordsPerMinute = 200 + Math.random() * 50; // 200-250 wpm
  const words = text.trim().split(/\s+/).length;
  const readingTimeMs = (words / wordsPerMinute) * 60 * 1000;
  return humanDelay(readingTimeMs * 0.3, readingTimeMs * 0.7);
}

// Usage
const jobDescription = await page.textContent('.job-description');
const readingTime = calculateReadingTime(jobDescription);
await new Promise(resolve => setTimeout(resolve, readingTime));
```

**Effectiveness Rating**: 8/10
**Risk Level**: Low
**Libraries**: Native JavaScript (no external deps needed)

**Best Practices**:
- Use Gaussian distribution for delays (more natural than uniform random)
- Add occasional "thinking pauses" (2-5 seconds)
- Vary scroll patterns (full page vs. incremental)
- Simulate reading time proportional to content length

**Common Pitfalls**:
- Too-fast interactions (< 100ms between actions)
- Perfectly linear scrolling
- Consistent delay patterns
- Not accounting for network latency

---

## 3. Mouse Movement Simulation

### Overview
Bots typically don't move the mouse or click at exact element centers. Human movement follows Bezier curves with micro-adjustments.

### Bezier Curve Mouse Movement

```typescript
import { ghost } from 'ghost-cursor-playwright'; // Or implement your own

async function humanClick(page: Page, selector: string) {
  const cursor = ghost.createCursor(page);

  // Move to element with natural path
  await cursor.move(selector, {
    moveDelay: humanDelay(50, 200),
    maxTries: 3,
    moveSpeed: 500 + Math.random() * 500, // Variable speed
  });

  // Add micro-movements before click
  const microMovements = Math.floor(Math.random() * 3);
  for (let i = 0; i < microMovements; i++) {
    const deltaX = (Math.random() - 0.5) * 10;
    const deltaY = (Math.random() - 0.5) * 10;
    await cursor.moveTo({ x: deltaX, y: deltaY });
    await humanWait(50, 150);
  }

  // Click with realistic timing
  await cursor.click();
}
```

### Custom Bezier Implementation

```typescript
interface Point {
  x: number;
  y: number;
}

function generateBezierPath(start: Point, end: Point, steps = 20): Point[] {
  const path: Point[] = [];

  // Generate random control points for natural curve
  const cp1 = {
    x: start.x + (end.x - start.x) * (0.3 + Math.random() * 0.2),
    y: start.y + (end.y - start.y) * (0.1 + Math.random() * 0.3),
  };
  const cp2 = {
    x: start.x + (end.x - start.x) * (0.7 + Math.random() * 0.2),
    y: start.y + (end.y - start.y) * (0.6 + Math.random() * 0.3),
  };

  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const mt = 1 - t;
    const mt2 = mt * mt;
    const t2 = t * t;

    path.push({
      x: mt2 * mt * start.x +
         3 * mt2 * t * cp1.x +
         3 * mt * t2 * cp2.x +
         t2 * t * end.x,
      y: mt2 * mt * start.y +
         3 * mt2 * t * cp1.y +
         3 * mt * t2 * cp2.y +
         t2 * t * end.y,
    });
  }

  return path;
}

async function moveMouseAlongPath(page: Page, path: Point[]) {
  for (const point of path) {
    await page.mouse.move(point.x, point.y);
    await new Promise(resolve => setTimeout(resolve, 10 + Math.random() * 10));
  }
}
```

### Click Position Randomization

```typescript
async function clickWithOffset(page: Page, selector: string) {
  const element = await page.$(selector);
  if (!element) throw new Error('Element not found');

  const box = await element.boundingBox();
  if (!box) throw new Error('Element has no bounding box');

  // Click at random position within element (avoiding exact center)
  const offsetX = box.width * (0.3 + Math.random() * 0.4);
  const offsetY = box.height * (0.3 + Math.random() * 0.4);

  await page.mouse.click(
    box.x + offsetX,
    box.y + offsetY
  );
}
```

**Effectiveness Rating**: 7/10
**Risk Level**: Low
**Libraries**:
- `ghost-cursor-playwright`
- `puppeteer-real-browser` (includes mouse simulation)

**Best Practices**:
- Use Bezier curves for movement paths
- Add occasional overshoots and corrections
- Random click positions within elements
- Simulate occasional "mouse pauses" while thinking

**Common Pitfalls**:
- Perfectly straight mouse paths
- Clicking exact element centers
- No mouse movement before clicks
- Unrealistic movement speeds (too fast or too slow)

---

## 4. Session Management

### Overview
Maintaining realistic sessions with proper cookie persistence, login state, and session duration patterns.

### Cookie Persistence

```typescript
import { writeFileSync, readFileSync, existsSync } from 'fs';
import { Browser, BrowserContext } from 'playwright';

interface SessionData {
  cookies: any[];
  localStorage: Record<string, string>;
  sessionStorage: Record<string, string>;
  timestamp: number;
}

class SessionManager {
  private sessionFile: string;

  constructor(sessionFile: string) {
    this.sessionFile = sessionFile;
  }

  async saveSession(context: BrowserContext, page: Page): Promise<void> {
    const cookies = await context.cookies();

    const localStorage = await page.evaluate(() => {
      const items: Record<string, string> = {};
      for (let i = 0; i < window.localStorage.length; i++) {
        const key = window.localStorage.key(i);
        if (key) items[key] = window.localStorage.getItem(key) || '';
      }
      return items;
    });

    const sessionStorage = await page.evaluate(() => {
      const items: Record<string, string> = {};
      for (let i = 0; i < window.sessionStorage.length; i++) {
        const key = window.sessionStorage.key(i);
        if (key) items[key] = window.sessionStorage.getItem(key) || '';
      }
      return items;
    });

    const sessionData: SessionData = {
      cookies,
      localStorage,
      sessionStorage,
      timestamp: Date.now(),
    };

    writeFileSync(this.sessionFile, JSON.stringify(sessionData, null, 2));
  }

  async loadSession(context: BrowserContext, page: Page): Promise<boolean> {
    if (!existsSync(this.sessionFile)) return false;

    try {
      const data: SessionData = JSON.parse(readFileSync(this.sessionFile, 'utf-8'));

      // Check if session is too old (> 7 days)
      const daysSinceLastUse = (Date.now() - data.timestamp) / (1000 * 60 * 60 * 24);
      if (daysSinceLastUse > 7) {
        return false;
      }

      // Restore cookies
      await context.addCookies(data.cookies);

      // Navigate to page first
      await page.goto('https://www.linkedin.com');

      // Restore localStorage
      await page.evaluate((items) => {
        for (const [key, value] of Object.entries(items)) {
          window.localStorage.setItem(key, value);
        }
      }, data.localStorage);

      // Restore sessionStorage
      await page.evaluate((items) => {
        for (const [key, value] of Object.entries(items)) {
          window.sessionStorage.setItem(key, value);
        }
      }, data.sessionStorage);

      return true;
    } catch (error) {
      console.error('Failed to load session:', error);
      return false;
    }
  }

  async isSessionValid(page: Page): Promise<boolean> {
    try {
      await page.goto('https://www.linkedin.com/feed');
      await page.waitForTimeout(2000);

      // Check if still logged in
      const isLoggedIn = await page.evaluate(() => {
        return !window.location.href.includes('/login') &&
               document.querySelector('.global-nav__me') !== null;
      });

      return isLoggedIn;
    } catch (error) {
      return false;
    }
  }
}
```

### Realistic Session Lengths

```typescript
interface SessionPattern {
  minDuration: number; // milliseconds
  maxDuration: number;
  jobViewsPerSession: { min: number; max: number };
}

const SESSION_PATTERNS: Record<string, SessionPattern> = {
  morning: {
    minDuration: 10 * 60 * 1000, // 10 minutes
    maxDuration: 30 * 60 * 1000, // 30 minutes
    jobViewsPerSession: { min: 5, max: 15 },
  },
  lunch: {
    minDuration: 5 * 60 * 1000,
    maxDuration: 15 * 60 * 1000,
    jobViewsPerSession: { min: 3, max: 8 },
  },
  evening: {
    minDuration: 15 * 60 * 1000,
    maxDuration: 45 * 60 * 1000,
    jobViewsPerSession: { min: 10, max: 25 },
  },
};

function getSessionPattern(): SessionPattern {
  const hour = new Date().getHours();

  if (hour >= 7 && hour < 10) return SESSION_PATTERNS.morning;
  if (hour >= 12 && hour < 14) return SESSION_PATTERNS.lunch;
  if (hour >= 18 && hour < 22) return SESSION_PATTERNS.evening;

  // Default to random pattern outside typical hours
  const patterns = Object.values(SESSION_PATTERNS);
  return patterns[Math.floor(Math.random() * patterns.length)];
}
```

**Effectiveness Rating**: 9/10
**Risk Level**: Low
**Libraries**: Native Node.js `fs` module

**Best Practices**:
- Persist cookies between sessions
- Maintain consistent session duration patterns
- Save/restore localStorage and sessionStorage
- Implement session expiry (7-14 days)
- Validate session before resuming

**Common Pitfalls**:
- Not clearing expired sessions
- Missing localStorage/sessionStorage restoration
- Session resumption at suspicious hours (3 AM)
- Too frequent logins (looks bot-like)

---

## 5. Viewport and Device Emulation

### Overview
Use realistic desktop viewport configurations that match common user setups.

### Implementation

```typescript
const COMMON_VIEWPORTS = [
  { width: 1920, height: 1080, name: 'Full HD' },
  { width: 1366, height: 768, name: 'HD' },
  { width: 1440, height: 900, name: 'MacBook Pro 15"' },
  { width: 1536, height: 864, name: 'Surface Book' },
  { width: 2560, height: 1440, name: '2K' },
];

async function createRealisticContext(browser: Browser) {
  const viewport = COMMON_VIEWPORTS[Math.floor(Math.random() * COMMON_VIEWPORTS.length)];

  const context = await browser.newContext({
    viewport,
    deviceScaleFactor: [1, 2][Math.floor(Math.random() * 2)], // Regular or Retina
    hasTouch: false, // Desktop doesn't have touch
    isMobile: false,
    locale: 'en-US',
    timezoneId: Intl.DateTimeFormat().resolvedOptions().timeZone,
    colorScheme: 'light', // Or detect system preference
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    permissions: ['geolocation'],
    geolocation: { latitude: 40.7128, longitude: -74.0060 }, // Match your actual location
  });

  return context;
}
```

**Effectiveness Rating**: 8/10
**Risk Level**: Low
**Best Practices**:
- Use common screen resolutions
- Match timezone to actual location
- Consistent viewport per session
- Enable geolocation with realistic coordinates

---

## 6. Proxy/IP Rotation for Single User

### Overview
For personal use, proxies are generally NOT recommended. LinkedIn expects consistent IP addresses from regular users. Rotating IPs is a red flag.

### Recommendation: Residential IP Only

```typescript
// For personal use, use your actual residential IP
// Only consider proxies if:
// 1. You travel frequently (use proxies matching location)
// 2. Your ISP IP is already flagged (rare for personal use)

// If you MUST use a proxy for legitimate reasons:
const PROXY_CONFIG = {
  server: 'http://residential-proxy.example.com:8080',
  username: 'user',
  password: 'pass',
};

const context = await browser.newContext({
  proxy: PROXY_CONFIG,
  // ... other config
});
```

**Effectiveness Rating**: 3/10 (for single user - actually harmful)
**Risk Level**: High (IP rotation triggers flags)

**Best Practices**:
- **Don't use proxies** for personal single-user automation
- If traveling, use local residential proxies
- Stick to one IP per multi-day session

**Common Pitfalls**:
- Rotating IPs within same session (instant ban risk)
- Using datacenter IPs (obvious automation)
- IP geolocation mismatch with timezone

---

## 7. Detection Evasion Libraries

### Recommended Stack (2026)

#### Option 1: Playwright + Stealth (Recommended)

```typescript
import { chromium } from 'playwright-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

// Apply stealth plugin
chromium.use(StealthPlugin());

const browser = await chromium.launch({
  headless: false, // Headed mode is more stealthy
  channel: 'chrome', // Use real Chrome, not Chromium
});
```

**Library**: `playwright-extra` + `puppeteer-extra-plugin-stealth`
**Effectiveness**: 9/10
**Maintenance**: Active (as of 2026)

#### Option 2: Puppeteer Real Browser

```typescript
import puppeteer from 'puppeteer-real-browser';

const { browser, page } = await puppeteer.connect({
  headless: false,
  turnstile: true, // Auto-solve Cloudflare challenges
  customConfig: {
    fingerprint: true,
    proxy: undefined, // Don't use for personal automation
  },
});
```

**Library**: `puppeteer-real-browser`
**Effectiveness**: 8/10
**Features**: Built-in fingerprinting, Cloudflare bypass

#### Option 3: Undetected Chromedriver (Python alternative)

If you need Python:

```python
import undetected_chromedriver as uc

driver = uc.Chrome(
    use_subprocess=True,
    headless=False,
)
```

### Comparison Table

| Library | Language | Headless Support | Fingerprinting | Active Maintenance | LinkedIn Success Rate |
|---------|----------|------------------|----------------|--------------------|----------------------|
| playwright-extra + stealth | TS/JS | Yes | Partial | High | 85% |
| puppeteer-real-browser | TS/JS | Yes | Full | Medium | 80% |
| undetected-chromedriver | Python | Yes | Full | High | 90% |
| selenium-stealth | Python | Yes | Partial | Medium | 75% |
| rebrowser-playwright | TS/JS | Yes | Full | High (2026) | 90% |

**Recommendation**: Use `playwright` with `puppeteer-extra-plugin-stealth` for TypeScript projects.

---

## 8. Rate Limiting Patterns

### Overview
Mimic realistic human browsing velocity to avoid triggering rate limits.

### Implementation

```typescript
interface RateLimiter {
  jobViewsPerHour: number;
  pagesPerSession: number;
  sessionsPerDay: number;
  minTimeBetweenViews: number; // milliseconds
}

const SAFE_RATE_LIMITS: RateLimiter = {
  jobViewsPerHour: 15, // Conservative: real users view 10-30
  pagesPerSession: 12, // Realistic session length
  sessionsPerDay: 3, // Morning, lunch, evening
  minTimeBetweenViews: 2 * 60 * 1000, // 2 minutes minimum
};

class RateLimitManager {
  private viewTimestamps: number[] = [];
  private sessionStartTime: number = 0;
  private viewsInCurrentSession: number = 0;

  async waitBeforeNextView(): Promise<void> {
    // Clean old timestamps (> 1 hour)
    const oneHourAgo = Date.now() - 60 * 60 * 1000;
    this.viewTimestamps = this.viewTimestamps.filter(t => t > oneHourAgo);

    // Check hourly limit
    if (this.viewTimestamps.length >= SAFE_RATE_LIMITS.jobViewsPerHour) {
      const oldestView = Math.min(...this.viewTimestamps);
      const waitTime = (oldestView + 60 * 60 * 1000) - Date.now();
      console.log(`Hourly limit reached. Waiting ${waitTime / 1000}s`);
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }

    // Check time since last view
    if (this.viewTimestamps.length > 0) {
      const lastView = Math.max(...this.viewTimestamps);
      const timeSinceLastView = Date.now() - lastView;

      if (timeSinceLastView < SAFE_RATE_LIMITS.minTimeBetweenViews) {
        const waitTime = SAFE_RATE_LIMITS.minTimeBetweenViews - timeSinceLastView;
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    }

    // Add human-like variance (don't be too consistent)
    await humanWait(1000, 3000);

    this.viewTimestamps.push(Date.now());
    this.viewsInCurrentSession++;
  }

  shouldEndSession(): boolean {
    const sessionDuration = Date.now() - this.sessionStartTime;
    const pattern = getSessionPattern();

    return (
      this.viewsInCurrentSession >= pattern.jobViewsPerSession.max ||
      sessionDuration >= pattern.maxDuration
    );
  }

  startNewSession(): void {
    this.sessionStartTime = Date.now();
    this.viewsInCurrentSession = 0;
  }
}
```

### Daily Activity Pattern

```typescript
async function runDailyJobSearch() {
  const sessions = 3; // Morning, lunch, evening
  const sessionManager = new SessionManager('./.session.json');
  const rateLimiter = new RateLimitManager();

  for (let i = 0; i < sessions; i++) {
    // Wait for appropriate time of day
    await waitForSessionTime(i);

    // Launch browser
    const { browser, page } = await launchStealthBrowser();
    await sessionManager.loadSession(page.context(), page);

    rateLimiter.startNewSession();
    const pattern = getSessionPattern();
    const targetViews = Math.floor(
      Math.random() * (pattern.jobViewsPerSession.max - pattern.jobViewsPerSession.min) +
      pattern.jobViewsPerSession.min
    );

    for (let view = 0; view < targetViews; view++) {
      await rateLimiter.waitBeforeNextView();

      // View job listing
      await viewJobListing(page);

      // Random actions (scroll, click similar jobs, etc.)
      await performRandomActions(page);

      if (rateLimiter.shouldEndSession()) break;
    }

    await sessionManager.saveSession(page.context(), page);
    await browser.close();

    // Wait between sessions
    await new Promise(resolve => setTimeout(resolve, 2 * 60 * 60 * 1000)); // 2 hours
  }
}

function waitForSessionTime(sessionIndex: number): Promise<void> {
  const targetHours = [8, 12, 19]; // 8am, 12pm, 7pm
  const targetHour = targetHours[sessionIndex];

  const now = new Date();
  const target = new Date();
  target.setHours(targetHour, 0, 0, 0);

  if (target <= now) {
    target.setDate(target.getDate() + 1);
  }

  const waitTime = target.getTime() - now.getTime();
  return new Promise(resolve => setTimeout(resolve, waitTime));
}
```

**Effectiveness Rating**: 9/10
**Risk Level**: Low
**Best Practices**:
- Stay well under platform limits (be conservative)
- Add random variance to timing
- Respect time-of-day patterns
- Track views across sessions

**Common Pitfalls**:
- Constant rate (perfectly spaced requests)
- Ignoring time-of-day patterns
- Too many views too quickly
- Not tracking historical rate

---

## 9. Headless Detection Countermeasures

### Overview
Many sites detect headless browsers through JavaScript checks. Modern stealth plugins handle most of these, but here are manual countermeasures.

### Implementation

```typescript
async function applyHeadlessCountermeasures(page: Page) {
  await page.addInitScript(() => {
    // Override navigator.webdriver
    Object.defineProperty(navigator, 'webdriver', {
      get: () => undefined,
    });

    // Add Chrome runtime
    (window as any).chrome = {
      runtime: {},
    };

    // Fake plugins
    Object.defineProperty(navigator, 'plugins', {
      get: () => [
        {
          0: { type: 'application/x-google-chrome-pdf', suffixes: 'pdf', description: 'Portable Document Format' },
          description: 'Portable Document Format',
          filename: 'internal-pdf-viewer',
          length: 1,
          name: 'Chrome PDF Plugin',
        },
        {
          0: { type: 'application/pdf', suffixes: 'pdf', description: '' },
          description: '',
          filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
          length: 1,
          name: 'Chrome PDF Viewer',
        },
      ],
    });

    // Fake languages
    Object.defineProperty(navigator, 'languages', {
      get: () => ['en-US', 'en'],
    });

    // Override permissions query
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters: any) => (
      parameters.name === 'notifications' ?
        Promise.resolve({ state: Cypress ? 'denied' : 'default' }) :
        originalQuery(parameters)
    );
  });
}
```

### Use Headed Mode (Most Effective)

```typescript
// Best practice: Use headed mode for critical sites
const browser = await chromium.launch({
  headless: false, // Run with visible browser
  args: [
    '--disable-blink-features=AutomationControlled',
  ],
});

// If you MUST use headless:
const browser = await chromium.launch({
  headless: true,
  args: [
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage',
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-web-security',
    '--disable-features=IsolateOrigins,site-per-process',
  ],
});
```

**Effectiveness Rating**: 8/10 (with stealth plugins), 4/10 (manual)
**Risk Level**: Medium (for headless), Low (for headed)

**Best Practices**:
- Use headed mode for LinkedIn (low risk, high success)
- If headless, use stealth plugins
- Run browser in XVFB on servers (virtual display)

**Common Pitfalls**:
- Relying only on manual overrides (outdated quickly)
- Not updating stealth plugins regularly
- Using headless for high-security sites

---

## 10. LinkedIn-Specific Detection Patterns

### Overview
LinkedIn has sophisticated bot detection. Here are known patterns and countermeasures.

### Known Detection Methods

1. **Rapid page navigation** - Too many job views in short time
2. **Consistent timing patterns** - Perfect intervals between actions
3. **Missing interactions** - No scrolling, no sidebar clicks
4. **Session anomalies** - IP changes, device changes
5. **Automation signals** - `navigator.webdriver`, headless indicators
6. **Behavioral patterns** - No search refinements, no profile views
7. **Network patterns** - Missing prefetch requests, unusual headers

### Countermeasures

```typescript
async function linkedInStealthSession(page: Page) {
  // 1. Realistic navigation
  await page.goto('https://www.linkedin.com/feed');
  await humanWait(2000, 4000);
  await humanScroll(page, 500);

  // 2. Random interactions before job search
  const randomActions = Math.floor(Math.random() * 3);
  for (let i = 0; i < randomActions; i++) {
    await performRandomLinkedInAction(page);
  }

  // 3. Navigate to jobs
  await page.click('a[href*="/jobs"]');
  await humanWait(1500, 3000);

  // 4. View jobs with realistic behavior
  const jobCards = await page.$$('.job-card-container');

  for (const card of jobCards.slice(0, 5)) {
    await card.scrollIntoViewIfNeeded();
    await humanWait(500, 1500);

    // Sometimes skip jobs (humans don't click everything)
    if (Math.random() > 0.3) {
      await card.click();
      await humanWait(2000, 5000);

      // Read job description
      const description = await page.textContent('.jobs-description');
      const readingTime = calculateReadingTime(description || '');
      await humanWait(readingTime * 0.5, readingTime);

      // Scroll through description
      await humanScroll(page, 300);
      await humanWait(1000, 2000);

      // Sometimes click "Show more"
      if (Math.random() > 0.6) {
        const showMore = await page.$('button:has-text("Show more")');
        if (showMore) {
          await showMore.click();
          await humanWait(1000, 2000);
        }
      }

      // Save job (occasionally)
      if (Math.random() > 0.7) {
        await page.click('button[aria-label*="Save"]');
        await humanWait(500, 1000);
      }
    }
  }
}

async function performRandomLinkedInAction(page: Page) {
  const actions = [
    // View a connection's profile
    async () => {
      const connection = await page.$('.mn-connection-card');
      if (connection) {
        await connection.click();
        await humanWait(2000, 4000);
        await page.goBack();
      }
    },

    // Like a post
    async () => {
      const likeButton = await page.$('button[aria-label*="Like"]');
      if (likeButton) {
        await likeButton.click();
        await humanWait(500, 1500);
      }
    },

    // Search and go back
    async () => {
      await page.click('input[placeholder*="Search"]');
      await humanWait(500, 1000);
      await page.keyboard.type('Software Engineer', { delay: 100 });
      await humanWait(1000, 2000);
      await page.keyboard.press('Escape');
    },
  ];

  const randomAction = actions[Math.floor(Math.random() * actions.length)];
  await randomAction();
}
```

### LinkedIn-Specific Best Practices

1. **Always start from /feed** - Don't go directly to jobs
2. **Interact with feed occasionally** - Like posts, view profiles
3. **Use search refinements** - Change filters, locations
4. **Don't apply to everything** - Only save some jobs
5. **Maintain login sessions** - Don't re-login daily
6. **Match usage patterns** - Search during business hours
7. **Respond to messages** - If you receive recruiter messages

**Effectiveness Rating**: 8/10 (with full strategy)
**Risk Level**: Medium (LinkedIn actively fights automation)

**Common Pitfalls**:
- Going straight to jobs page
- No interaction with feed
- Applying to all jobs (unrealistic)
- Ignoring messages from recruiters
- Session at 3 AM daily

---

## Implementation Strategy

### Phase 1: Foundation (Week 1)
1. Set up Playwright with stealth plugin
2. Implement session management (cookie persistence)
3. Add basic timing delays (Gaussian distribution)
4. Test with headed browser

**Success Metric**: Can maintain logged-in session for 7+ days

### Phase 2: Behavioral Layer (Week 2)
1. Add mouse movement simulation
2. Implement scroll patterns
3. Add reading time calculation
4. Random action injection

**Success Metric**: Session looks natural in browser DevTools timeline

### Phase 3: Fingerprinting (Week 3)
1. Integrate fingerprint-generator
2. Add canvas/WebGL randomization
3. Test fingerprint uniqueness
4. Verify consistency within sessions

**Success Metric**: Fingerprint passes detection tests (browserleaks.com, pixelscan.net)

### Phase 4: Rate Limiting (Week 4)
1. Implement rate limiter
2. Add time-of-day patterns
3. Track historical usage
4. Add session length variance

**Success Metric**: Stay under 20 job views/hour, 3 sessions/day

### Phase 5: LinkedIn-Specific (Week 5)
1. Add feed interactions
2. Implement search refinements
3. Add random navigation patterns
4. Test complete workflow

**Success Metric**: Run for 30 days without account flags

---

## Monitoring and Maintenance

### Detection Monitoring

```typescript
class DetectionMonitor {
  async checkForCaptcha(page: Page): Promise<boolean> {
    const captchaSelectors = [
      'iframe[src*="recaptcha"]',
      'iframe[src*="hcaptcha"]',
      '#px-captcha',
      '.g-recaptcha',
    ];

    for (const selector of captchaSelectors) {
      if (await page.$(selector)) {
        console.error('CAPTCHA detected!');
        return true;
      }
    }
    return false;
  }

  async checkForBlocking(page: Page): Promise<boolean> {
    const url = page.url();
    const blockIndicators = [
      url.includes('checkpoint'),
      url.includes('challenge'),
      url.includes('verify'),
      await page.$('text=unusual activity'),
      await page.$('text=verify you are human'),
    ];

    return blockIndicators.some(indicator => indicator);
  }

  async logSessionMetrics(metrics: {
    duration: number;
    jobViews: number;
    actions: number;
    errors: number;
  }): Promise<void> {
    // Log to file for analysis
    const log = {
      timestamp: new Date().toISOString(),
      ...metrics,
    };

    appendFileSync('./session-logs.jsonl', JSON.stringify(log) + '\n');
  }
}
```

### Update Schedule

- **Weekly**: Check for stealth plugin updates
- **Monthly**: Review fingerprint patterns (sites update detection)
- **Quarterly**: Audit session metrics for anomalies
- **Yearly**: Major refactor based on new detection methods

---

## Legal and Ethical Considerations

### ✅ Acceptable Use (Personal Job Search)
- Viewing publicly accessible job listings
- Saving jobs to your account
- Searching with your authenticated account
- Reasonable automation for personal efficiency

### ❌ Unacceptable Use
- Mass data scraping for resale
- Bypassing paywalls or premium features
- Automated messaging/spamming
- Creating fake accounts
- Circumventing IP bans maliciously

### LinkedIn Terms of Service
From LinkedIn User Agreement (Section 8.2):

> "You agree that you will not use bots, scrapers, or other automated methods to access the Services."

**Reality Check**: This is broadly written, but LinkedIn primarily enforces against:
- Commercial scraping operations
- Fake account automation
- Spam and harassment bots

**For personal job search**: Gray area. Be respectful, stay under rate limits, don't disrupt the platform.

### Risk Mitigation
1. **Use your real account** (don't create fake accounts)
2. **Stay well under rate limits** (act more human than humans)
3. **Don't apply to jobs automatically** (just view/save them)
4. **Be prepared to handle manual verification** (occasional CAPTCHA is okay)
5. **Have a backup plan** (if account flagged, go back to manual browsing)

---

## Testing Your Implementation

### Stealth Testing Sites

1. **Pixelscan.net** - Comprehensive fingerprint analysis
2. **BrowserLeaks.com** - WebRTC, Canvas, Font detection
3. **Bot.Sannysoft.com** - Automation detection tests
4. **Arh.Antoinevastel.com/bots** - Advanced bot detection
5. **Browserbench.org** - Performance profiling (human-like scores)

### Testing Checklist

- [ ] navigator.webdriver is undefined
- [ ] Canvas fingerprint varies between sessions
- [ ] WebGL fingerprint is realistic
- [ ] Plugins list appears normal
- [ ] Mouse movements follow Bezier curves
- [ ] Timing patterns are variable (not constant)
- [ ] Session cookies persist correctly
- [ ] No rapid-fire requests (check DevTools)
- [ ] User-Agent matches other headers
- [ ] Timezone matches geolocation

### Success Metrics

**Technical:**
- Pass all tests on pixelscan.net
- No detection on bot.sannysoft.com
- Fingerprint consistency within sessions

**Behavioral:**
- Average 2-5 minutes between job views
- 10-20 job views per session
- 2-3 sessions per day maximum
- Session duration 15-45 minutes

**Long-term:**
- No CAPTCHAs for 30+ days
- No account warnings
- Consistent access patterns

---

## Recommended Libraries (2026)

### Essential
- `playwright` or `puppeteer` - Browser automation
- `puppeteer-extra-plugin-stealth` - Detection evasion
- `fingerprint-generator` + `fingerprint-injector` - Fingerprint randomization

### Optional
- `ghost-cursor-playwright` - Mouse movement simulation
- `puppeteer-real-browser` - All-in-one stealth solution
- `playwright-extra` - Plugin ecosystem for Playwright

### Installation

```bash
npm install playwright playwright-extra puppeteer-extra-plugin-stealth
npm install fingerprint-generator fingerprint-injector
npm install ghost-cursor-playwright
```

---

## Code Template (Complete Implementation)

```typescript
// See full implementation in separate file
// Location: src/automation/linkedin-stealth.ts

import { chromium } from 'playwright-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import { FingerprintGenerator } from 'fingerprint-generator';
import { FingerprintInjector } from 'fingerprint-injector';
import { SessionManager } from './session-manager';
import { RateLimitManager } from './rate-limit-manager';
import { DetectionMonitor } from './detection-monitor';

chromium.use(StealthPlugin());

async function main() {
  const sessionManager = new SessionManager('./.linkedin-session.json');
  const rateLimiter = new RateLimitManager();
  const monitor = new DetectionMonitor();

  const fingerprintGenerator = new FingerprintGenerator();
  const fingerprint = fingerprintGenerator.getFingerprint();

  const browser = await chromium.launch({
    headless: false,
    channel: 'chrome',
  });

  const context = await browser.newContext({
    viewport: fingerprint.screen,
    userAgent: fingerprint.navigator.userAgent,
    locale: 'en-US',
    timezoneId: Intl.DateTimeFormat().resolvedOptions().timeZone,
  });

  const page = await context.newPage();
  const injector = new FingerprintInjector();
  await injector.attachFingerprintToPlaywright(page, fingerprint);

  // Load session or login
  const sessionLoaded = await sessionManager.loadSession(context, page);
  if (!sessionLoaded) {
    await manualLogin(page); // User logs in manually
    await sessionManager.saveSession(context, page);
  }

  // Run job search session
  rateLimiter.startNewSession();
  await linkedInStealthSession(page, rateLimiter, monitor);

  await sessionManager.saveSession(context, page);
  await browser.close();
}

main().catch(console.error);
```

---

## Summary

**Priority Implementation Order:**
1. Stealth plugins (foundation)
2. Session management (avoid re-logins)
3. Timing patterns (human-like delays)
4. Fingerprint randomization (avoid tracking)
5. Rate limiting (most critical for avoiding bans)
6. Mouse simulation (nice-to-have)
7. LinkedIn-specific behaviors (final polish)

**Key Takeaways:**
- **Use headed mode** for LinkedIn (most reliable)
- **Stay conservative** with rate limits (15 views/hour max)
- **Maintain sessions** (don't re-login daily)
- **Add realistic variance** (don't be perfectly consistent)
- **Monitor for detection** (CAPTCHA, blocks)
- **Be ethical** (personal use only, respect ToS spirit)

**Expected Success Rate**: 85-95% with full implementation, conservative rate limiting, and proper monitoring.

---

**Research completed**: February 2026
**Last updated**: 2026-02-08
**Technologies**: Playwright, TypeScript, Node.js
**Use case**: Personal LinkedIn job search automation
