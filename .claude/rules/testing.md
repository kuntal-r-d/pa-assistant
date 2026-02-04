# Testing Rules

Guidelines for writing tests in TypeScript with Vitest.

## Core Principles

- **TDD recommended**: Write tests first
- **Coverage target**: 80% or higher
- **Execution speed**: Unit tests should be fast (< 100ms per test)

## Test Structure

### AAA Pattern

```typescript
describe('createUser', () => {
  it('should create a user with valid data', () => {
    // Arrange
    const userData = { name: 'Alice', email: 'alice@example.com' };

    // Act
    const user = createUser(userData);

    // Assert
    expect(user.name).toBe('Alice');
    expect(user.email).toBe('alice@example.com');
  });
});
```

### Naming Convention

```typescript
// describe: Module/function name
// it: should {expected behavior} when {condition}
describe('createUser', () => {
  it('should return user when valid data is provided', () => {
    // ...
  });

  it('should throw error when email is invalid', () => {
    // ...
  });
});
```

## Test Case Coverage

For each feature, consider:

1. **Happy path**: Basic functionality
2. **Boundary values**: Min, max, empty
3. **Error cases**: Invalid input, error conditions
4. **Edge cases**: null, undefined, empty string, special characters

## Mocking

Mock external dependencies:

```typescript
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { fetchUser } from './api';

vi.mock('./api');

describe('UserService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should handle API response', async () => {
    vi.mocked(fetchUser).mockResolvedValue({ id: 1, name: 'Test' });

    const result = await getUserById(1);

    expect(result.name).toBe('Test');
    expect(fetchUser).toHaveBeenCalledWith(1);
  });
});
```

### Mocking Express Request/Response

```typescript
import { describe, it, expect, vi } from 'vitest';
import type { Request, Response } from 'express';

describe('UserController', () => {
  it('should return user on GET /users/:id', async () => {
    const req = {
      params: { id: '1' },
    } as unknown as Request;

    const res = {
      json: vi.fn(),
      status: vi.fn().mockReturnThis(),
    } as unknown as Response;

    await getUserHandler(req, res);

    expect(res.json).toHaveBeenCalledWith(
      expect.objectContaining({ id: 1 })
    );
  });
});
```

## Test Setup

### vitest.config.ts

```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['src/**/*.test.ts', 'tests/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      exclude: ['node_modules/', 'dist/', '**/*.config.ts'],
    },
  },
});
```

### Setup Files

```typescript
// tests/setup.ts
import { beforeAll, afterAll, beforeEach } from 'vitest';

beforeAll(async () => {
  // Global setup (e.g., start test database)
});

afterAll(async () => {
  // Global teardown
});

beforeEach(() => {
  // Reset state before each test
});
```

## Fixtures and Factories

Create reusable test data:

```typescript
// tests/factories/user.factory.ts
import type { User } from '../../src/types';

export function createTestUser(overrides: Partial<User> = {}): User {
  return {
    id: 1,
    name: 'Test User',
    email: 'test@example.com',
    createdAt: new Date(),
    ...overrides,
  };
}

// Usage in tests
const user = createTestUser({ name: 'Custom Name' });
```

## Integration Tests with Supertest

```typescript
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import request from 'supertest';
import { app } from '../src/app';

describe('GET /api/users', () => {
  it('should return list of users', async () => {
    const response = await request(app)
      .get('/api/users')
      .expect('Content-Type', /json/)
      .expect(200);

    expect(response.body).toBeInstanceOf(Array);
  });

  it('should return 404 for non-existent user', async () => {
    await request(app)
      .get('/api/users/999')
      .expect(404);
  });
});
```

## Commands

```bash
# All tests
npm run test

# Watch mode
npm run test:watch

# Specific file
npx vitest run src/services/user.test.ts

# Specific test by name
npx vitest run -t "should create user"

# With coverage
npm run test:coverage

# Stop on first failure
npx vitest run --bail
```

## Testing Async Code

```typescript
describe('async operations', () => {
  it('should handle promises', async () => {
    const result = await asyncFunction();
    expect(result).toBe('expected');
  });

  it('should handle rejected promises', async () => {
    await expect(failingAsyncFunction()).rejects.toThrow('Error message');
  });

  it('should handle timeouts', async () => {
    vi.useFakeTimers();

    const promise = delayedFunction();
    vi.advanceTimersByTime(1000);

    const result = await promise;
    expect(result).toBe('done');

    vi.useRealTimers();
  });
});
```

## Checklist

- [ ] Happy path is tested
- [ ] Error cases are tested
- [ ] Boundary values are tested
- [ ] Tests are independent (no order dependency)
- [ ] External dependencies are mocked
- [ ] Tests run fast
- [ ] No console.log statements in tests
- [ ] Proper cleanup in afterEach/afterAll
