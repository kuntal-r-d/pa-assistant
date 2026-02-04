# Coding Principles

Core coding rules to always follow in TypeScript/Express.js projects.

## Simplicity First

- Choose readable code over complex code
- Avoid over-abstraction
- Prioritize "understandable" over "working"

## Single Responsibility

- One function does one thing only
- One class/module has one responsibility only
- Target 200-400 lines per file (max 800)

## Early Return

```typescript
// Bad: Deep nesting
function process(value: number | null): string | null {
  if (value !== null) {
    if (value > 0) {
      return doSomething(value);
    }
  }
  return null;
}

// Good: Early return
function process(value: number | null): string | null {
  if (value === null) {
    return null;
  }
  if (value <= 0) {
    return null;
  }
  return doSomething(value);
}
```

## Type Safety Required

All functions must have explicit type annotations:

```typescript
// Good: Explicit types
function callLLM(
  prompt: string,
  model: string = 'gpt-4',
  maxTokens: number = 1000
): Promise<string> {
  // ...
}

// Good: Use interfaces for complex types
interface UserData {
  name: string;
  email: string;
  age?: number;
}

function createUser(data: UserData): User {
  // ...
}
```

### Avoid `any`

```typescript
// Bad: Using any
function processData(data: any): any {
  return data.value;
}

// Good: Use proper types or unknown
function processData(data: unknown): string {
  if (typeof data === 'object' && data !== null && 'value' in data) {
    return String(data.value);
  }
  throw new Error('Invalid data');
}

// Good: Use generics
function processData<T extends { value: string }>(data: T): string {
  return data.value;
}
```

## Immutability

Create new objects instead of mutating existing ones:

```typescript
// Bad: Mutating existing object
data.newKey = value;
items.push(newItem);

// Good: Creating new object
const newData = { ...data, newKey: value };
const newItems = [...items, newItem];

// Good: Using Object.freeze for constants
const CONFIG = Object.freeze({
  API_URL: 'https://api.example.com',
  TIMEOUT: 5000,
});
```

## Naming Conventions

- **Variables/Functions**: camelCase (English)
- **Classes/Interfaces/Types**: PascalCase (English)
- **Constants**: UPPER_SNAKE_CASE (English)
- **Files**: kebab-case.ts or camelCase.ts
- **Meaningful names**: `userCount` over `x`

```typescript
// Good naming examples
const MAX_RETRIES = 3;
const userCount = 10;

interface UserService { }
type UserStatus = 'active' | 'inactive';

function getUserById(id: number): User { }
class UserRepository { }
```

## No Magic Numbers

```typescript
// Bad
if (retryCount > 3) {
  // ...
}

// Good
const MAX_RETRIES = 3;
if (retryCount > MAX_RETRIES) {
  // ...
}

// Good: Use enums for related constants
enum HttpStatus {
  OK = 200,
  CREATED = 201,
  BAD_REQUEST = 400,
  NOT_FOUND = 404,
  INTERNAL_ERROR = 500,
}

if (response.status === HttpStatus.NOT_FOUND) {
  // ...
}
```

## Async/Await Best Practices

```typescript
// Bad: Mixing callbacks and promises
function fetchData(callback: (data: Data) => void) {
  api.fetch().then(data => callback(data));
}

// Good: Use async/await
async function fetchData(): Promise<Data> {
  const data = await api.fetch();
  return data;
}

// Good: Proper error handling
async function fetchDataSafely(): Promise<Data | null> {
  try {
    const data = await api.fetch();
    return data;
  } catch (error) {
    logger.error('Failed to fetch data', { error });
    return null;
  }
}

// Good: Parallel operations when independent
async function fetchAllData(): Promise<[Users, Posts]> {
  const [users, posts] = await Promise.all([
    fetchUsers(),
    fetchPosts(),
  ]);
  return [users, posts];
}
```

## Express.js Best Practices

### Controller Pattern

```typescript
// Good: Separate concerns
// controllers/user.controller.ts
export async function getUser(
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> {
  try {
    const { id } = req.params;
    const user = await userService.findById(Number(id));

    if (!user) {
      res.status(404).json({ error: 'User not found' });
      return;
    }

    res.json(user);
  } catch (error) {
    next(error);
  }
}
```

### Middleware Pattern

```typescript
// Good: Typed middleware
type AsyncHandler = (
  req: Request,
  res: Response,
  next: NextFunction
) => Promise<void>;

function asyncHandler(fn: AsyncHandler): AsyncHandler {
  return async (req, res, next) => {
    try {
      await fn(req, res, next);
    } catch (error) {
      next(error);
    }
  };
}

// Usage
app.get('/users/:id', asyncHandler(getUser));
```

## Null/Undefined Handling

```typescript
// Good: Use nullish coalescing
const port = process.env.PORT ?? 3000;

// Good: Use optional chaining
const userName = user?.profile?.name;

// Good: Type guards
function isUser(value: unknown): value is User {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'email' in value
  );
}
```
