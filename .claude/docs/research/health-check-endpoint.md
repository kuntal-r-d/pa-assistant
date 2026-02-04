# Health Check Endpoint Research

**Date**: 2026-02-04
**Context**: Implementation of health check endpoint for api-service

## Repository Analysis

### Repository Structure & Architecture

The project is a **monorepo** managed with `pnpm workspaces`. The relevant application is `apps/api-service`, which is a standard Express.js REST API.

- **Entry Point**: `apps/api-service/src/index.ts` initializes the Express app.
- **Routes**: `apps/api-service/src/api/index.ts` aggregates routes.
- **Shared Logic**: `packages/@uat/backend-common` contains the database and cache client implementations (`PostgresService`, `MongoDBService`, `CacheService`).
- **Config**: `apps/api-service/src/config/index.ts` defines connections for PostgreSQL, MongoDB, and Redis.

### Existing Code & Patterns

There is currently a **conflict/duplication** in how health checks are handled:

1. **Root Route (`src/index.ts`)**: A simple inline route exists at `GET /health` that returns a hardcoded `{ status: 'healthy' }`.
2. **API Route (`src/api/routes/health.ts`)**: A dedicated router is mounted at `/api/health` with three endpoints:
   - `GET /api/health/` -> Returns service info.
   - `GET /api/health/live` -> Returns `{ status: 'alive' }`.
   - `GET /api/health/ready` -> Currently returns `{ status: 'ready' }` but contains a `TODO: Check database connections`.

## Technical Considerations

### Dependency Analysis

The system relies on three critical external services. A proper "Readiness" probe must check connectivity to these to ensure the API can actually serve requests.

| Dependency | Purpose | Criticality |
|------------|---------|-------------|
| **PostgreSQL** | Primary data (ACID), exam results | **High** (Readiness should fail if down) |
| **MongoDB** | Application settings | **High** (Readiness should fail if down) |
| **Redis** | Session state, caching | **Medium/High** (Depends on fallback logic) |

### Probe Strategy

- **Liveness Probe (`/live`)**: Should strictly check if the Node.js event loop is running. The current implementation is correct. **Do not** check databases here; doing so can cause k8s/orchestrators to restart the container unnecessarily during temporary DB blips.

- **Readiness Probe (`/ready`)**: Should check if the application is ready to accept traffic. This **must** verify connections to Postgres, MongoDB, and Redis.

## Best Practices for Health Check Endpoints

### Liveness vs Readiness

**Liveness Probe**:
- Purpose: Is the application process alive?
- Should check: Basic application responsiveness
- Should NOT check: External dependencies (databases, caches)
- Response time: Must be fast (< 100ms)
- Failure action: Restart the container

**Readiness Probe**:
- Purpose: Is the application ready to serve traffic?
- Should check: All critical dependencies
- Acceptable response time: < 1-2 seconds
- Failure action: Remove from load balancer pool (do not restart)

### Response Format Standards

```typescript
// Success (200)
{
  status: 'ok',
  timestamp: '2026-02-04T10:30:00Z',
  uptime: 3600,
  details: {
    postgres: 'up',
    mongodb: 'up',
    redis: 'up'
  }
}

// Failure (503)
{
  status: 'down',
  timestamp: '2026-02-04T10:30:00Z',
  uptime: 3600,
  details: {
    postgres: 'down',
    mongodb: 'up',
    redis: 'up'
  }
}
```

## Library Recommendations

### Option 1: @godaddy/terminus (Recommended for Production)

**Pros**:
- Industry standard for Node.js health checks
- Handles graceful shutdown automatically
- Kubernetes-ready out of the box
- Active maintenance and wide adoption

**Usage**:
```typescript
import { createTerminus } from '@godaddy/terminus';

function onHealthCheck() {
  return Promise.all([
    postgres.ping(),
    mongodb.ping(),
    redis.ping()
  ]);
}

createTerminus(server, {
  healthChecks: {
    '/health/live': () => Promise.resolve(),
    '/health/ready': onHealthCheck
  },
  timeout: 1000
});
```

### Option 2: Custom Implementation (Current Approach)

**Pros**:
- Full control over implementation
- No additional dependencies
- Simpler for basic needs
- Already structured in existing codebase

**Cons**:
- Need to implement graceful shutdown manually
- Need to handle edge cases yourself

**Recommendation**: For this project, a **custom implementation is sufficient** since the structure already exists. Focus on implementing proper dependency checks.

## Implementation Plan

### 1. Update `backend-common` Services

Add health check methods to each service:

```typescript
// PostgresService
async healthCheck(): Promise<boolean> {
  try {
    await this.pool.query('SELECT 1');
    return true;
  } catch {
    return false;
  }
}

// MongoDBService
async healthCheck(): Promise<boolean> {
  try {
    await this.client.db().admin().ping();
    return true;
  } catch {
    return false;
  }
}

// CacheService (Redis)
async healthCheck(): Promise<boolean> {
  try {
    await this.client.ping();
    return true;
  } catch {
    return false;
  }
}
```

### 2. Consolidate Routes

Remove duplicate health check from `src/index.ts`:
```typescript
// REMOVE this:
app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});
```

### 3. Implement Readiness Check

Update `health.controller.ts`:

```typescript
export async function getReadinessStatus(
  req: Request,
  res: Response
): Promise<void> {
  const checks = {
    postgres: false,
    mongodb: false,
    redis: false
  };

  try {
    checks.postgres = await postgresService.healthCheck();
    checks.mongodb = await mongoService.healthCheck();
    checks.redis = await cacheService.healthCheck();

    const allHealthy = Object.values(checks).every(v => v);

    res.status(allHealthy ? 200 : 503).json({
      status: allHealthy ? 'ok' : 'down',
      timestamp: new Date().toISOString(),
      details: checks
    });
  } catch (error) {
    res.status(503).json({
      status: 'error',
      timestamp: new Date().toISOString(),
      details: checks
    });
  }
}
```

### 4. Service Initialization

Ensure services are initialized and accessible:

```typescript
// src/index.ts or src/services.ts
export const postgresService = new PostgresService(config.postgres);
export const mongoService = new MongoDBService(config.mongodb);
export const cacheService = new CacheService(config.redis);

// Initialize connections
await Promise.all([
  postgresService.connect(),
  mongoService.connect(),
  cacheService.connect()
]);
```

## Security Considerations

1. **Rate Limiting**: Health check endpoints should have lenient rate limits (they're frequently polled)
2. **Authentication**: Typically health checks are unauthenticated (k8s needs access)
3. **Information Disclosure**: Don't expose sensitive config in health responses
4. **Timeouts**: Set appropriate timeouts (1-2s max) to prevent hanging

## Testing Strategy

```typescript
describe('Health Check Endpoints', () => {
  describe('GET /health/live', () => {
    it('should return 200 when application is alive', async () => {
      const response = await request(app).get('/api/health/live');
      expect(response.status).toBe(200);
      expect(response.body.status).toBe('alive');
    });
  });

  describe('GET /health/ready', () => {
    it('should return 200 when all dependencies are healthy', async () => {
      vi.mocked(postgresService.healthCheck).mockResolvedValue(true);
      vi.mocked(mongoService.healthCheck).mockResolvedValue(true);
      vi.mocked(cacheService.healthCheck).mockResolvedValue(true);

      const response = await request(app).get('/api/health/ready');
      expect(response.status).toBe(200);
      expect(response.body.status).toBe('ok');
    });

    it('should return 503 when any dependency is down', async () => {
      vi.mocked(postgresService.healthCheck).mockResolvedValue(false);
      vi.mocked(mongoService.healthCheck).mockResolvedValue(true);
      vi.mocked(cacheService.healthCheck).mockResolvedValue(true);

      const response = await request(app).get('/api/health/ready');
      expect(response.status).toBe(503);
      expect(response.body.status).toBe('down');
    });
  });
});
```

## Kubernetes Integration

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: api-service
    image: api-service:latest
    livenessProbe:
      httpGet:
        path: /api/health/live
        port: 3000
      initialDelaySeconds: 10
      periodSeconds: 10
      timeoutSeconds: 1
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /api/health/ready
        port: 3000
      initialDelaySeconds: 5
      periodSeconds: 5
      timeoutSeconds: 2
      failureThreshold: 3
```

## References

- [Kubernetes Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [@godaddy/terminus Documentation](https://github.com/godaddy/terminus)
- [Express.js Best Practices](https://expressjs.com/en/advanced/best-practice-performance.html)
