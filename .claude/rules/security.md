# Security Rules

Security checklist to always verify when writing Node.js/Express.js code.

## Secrets Management

### Never Do

- Hardcode API keys or passwords
- Log sensitive information
- Commit `.env` files

### Required

```typescript
// Good: Get from environment variables
const API_KEY = process.env.API_KEY;

// Good: With existence check
const API_KEY = process.env.API_KEY;
if (!API_KEY) {
  throw new Error('API_KEY environment variable is required');
}

// Good: Type-safe environment with validation
import { z } from 'zod';

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']),
  PORT: z.coerce.number().default(3000),
  DATABASE_URL: z.string().url(),
  API_KEY: z.string().min(1),
});

export const env = envSchema.parse(process.env);
```

## Input Validation

Always validate external input:

```typescript
// Good: Using Zod for validation
import { z } from 'zod';

const userSchema = z.object({
  email: z.string().email(),
  age: z.number().int().min(0).max(150),
  name: z.string().min(1).max(100),
});

type UserInput = z.infer<typeof userSchema>;

function createUser(input: unknown): User {
  const validated = userSchema.parse(input);
  // ...
}

// Good: Express middleware for validation
function validateBody<T>(schema: z.Schema<T>) {
  return (req: Request, res: Response, next: NextFunction) => {
    try {
      req.body = schema.parse(req.body);
      next();
    } catch (error) {
      res.status(400).json({ error: 'Invalid request body' });
    }
  };
}

app.post('/users', validateBody(userSchema), createUserHandler);
```

## SQL Injection Prevention

```typescript
// Bad: String concatenation
const query = `SELECT * FROM users WHERE id = ${userId}`;

// Good: Parameterized query (with pg library)
const result = await pool.query(
  'SELECT * FROM users WHERE id = $1',
  [userId]
);

// Good: Using Prisma (ORM)
const user = await prisma.user.findUnique({
  where: { id: userId },
});

// Good: Using Drizzle (ORM)
const user = await db.select().from(users).where(eq(users.id, userId));
```

## NoSQL Injection Prevention

```typescript
// Bad: Direct user input in query
const user = await collection.findOne({ username: req.body.username });

// Good: Validate and sanitize
const usernameSchema = z.string().min(1).max(50).regex(/^[a-zA-Z0-9_]+$/);
const username = usernameSchema.parse(req.body.username);
const user = await collection.findOne({ username });
```

## XSS Prevention

```typescript
// Bad: Rendering user input directly
res.send(`<h1>Hello ${req.query.name}</h1>`);

// Good: Use template engine with auto-escaping
// (EJS, Handlebars, Pug all escape by default)

// Good: Sanitize for API responses
import DOMPurify from 'dompurify';
const sanitized = DOMPurify.sanitize(userInput);

// Good: Set security headers with Helmet
import helmet from 'helmet';
app.use(helmet());
```

## Error Messages

```typescript
// Bad: Too detailed (gives attackers information)
throw new Error(`Database connection failed: ${connectionString}`);

// Good: Minimal information to client
class AppError extends Error {
  constructor(
    message: string,
    public statusCode: number = 500,
    public isOperational: boolean = true
  ) {
    super(message);
  }
}

throw new AppError('Database connection failed', 500);

// Good: Details go to logs only
logger.error('Database connection failed', {
  connectionString: maskSensitiveData(connectionString),
  error: err.message,
});
res.status(500).json({ error: 'Internal server error' });
```

## Rate Limiting

```typescript
// Good: Implement rate limiting
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests, please try again later',
});

app.use('/api/', limiter);

// Good: Stricter limits for auth endpoints
const authLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 5, // 5 failed attempts per hour
  message: 'Too many login attempts',
});

app.use('/api/auth/login', authLimiter);
```

## CORS Configuration

```typescript
// Bad: Allow all origins
app.use(cors());

// Good: Configure allowed origins
import cors from 'cors';

const corsOptions = {
  origin: (origin: string | undefined, callback: Function) => {
    const allowedOrigins = ['https://myapp.com', 'https://admin.myapp.com'];
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  optionsSuccessStatus: 200,
};

app.use(cors(corsOptions));
```

## Authentication & Authorization

```typescript
// Good: Secure password hashing
import bcrypt from 'bcrypt';

const SALT_ROUNDS = 12;

async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, SALT_ROUNDS);
}

async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

// Good: JWT with proper configuration
import jwt from 'jsonwebtoken';

const JWT_SECRET = env.JWT_SECRET;
const JWT_EXPIRES_IN = '1h';

function generateToken(userId: number): string {
  return jwt.sign({ userId }, JWT_SECRET, { expiresIn: JWT_EXPIRES_IN });
}

function verifyToken(token: string): { userId: number } {
  return jwt.verify(token, JWT_SECRET) as { userId: number };
}
```

## Dependencies

```bash
# Regular vulnerability checks
npm audit
npm audit fix

# Use Snyk for deeper analysis
npx snyk test

# Keep dependencies updated
npm outdated
npm update
```

### package.json Best Practices

```json
{
  "dependencies": {
    "express": "4.18.2"
  }
}
```

- Use exact versions (`4.18.2`) over ranges (`^4.18.0`) for predictability
- Regularly audit and update dependencies
- Remove unused dependencies

## Code Review Checklist

- [ ] No hardcoded secrets
- [ ] External input is validated (Zod, Joi, etc.)
- [ ] SQL/NoSQL queries are parameterized
- [ ] Error messages don't leak sensitive info
- [ ] Logs don't contain sensitive information
- [ ] Rate limiting is implemented for public endpoints
- [ ] CORS is properly configured
- [ ] Security headers are set (Helmet)
- [ ] Authentication tokens are properly handled
- [ ] File uploads are validated and sanitized
