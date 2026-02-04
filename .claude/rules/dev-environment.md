# Development Environment

Project development environment and toolchain for TypeScript/Express.js.

## Package Management: npm/pnpm

**Use npm or pnpm for package management.**

```bash
# Add packages
npm install <package>
npm install --save-dev <package>    # Dev dependency

# Or with pnpm (faster)
pnpm add <package>
pnpm add -D <package>    # Dev dependency

# Install dependencies
npm install
pnpm install

# Run scripts
npm run <script>
pnpm run <script>
npx <command>
```

### package.json

Manage dependencies in `package.json`:

```json
{
  "name": "project-name",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js",
    "lint": "eslint src/",
    "lint:fix": "eslint src/ --fix",
    "format": "prettier --write src/",
    "format:check": "prettier --check src/",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage"
  },
  "dependencies": {
    "express": "^4.18.0"
  },
  "devDependencies": {
    "@types/express": "^4.17.0",
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0",
    "tsx": "^4.0.0",
    "eslint": "^9.0.0",
    "prettier": "^3.0.0",
    "vitest": "^2.0.0"
  }
}
```

## TypeScript Configuration

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "resolveJsonModule": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

## Linting & Formatting: ESLint + Prettier

```bash
# Check
npm run lint
npm run format:check

# Auto-fix
npm run lint:fix
npm run format
```

### ESLint Configuration (eslint.config.js)

```javascript
import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  eslint.configs.recommended,
  ...tseslint.configs.strictTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        project: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      '@typescript-eslint/explicit-function-return-type': 'warn',
      '@typescript-eslint/no-explicit-any': 'error',
    },
  },
  {
    ignores: ['dist/', 'node_modules/', '*.config.js'],
  }
);
```

### Prettier Configuration (.prettierrc)

```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100
}
```

## Type Checking: TypeScript

```bash
# Run type check
npm run typecheck
# or
npx tsc --noEmit
```

### TypeScript Features

- **Strict mode**: Enables all strict type-checking options
- **Modern ECMAScript**: Targets ES2022 for modern features
- **Node.js ready**: Configured for Node.js module resolution

## Express.js Setup

### Basic Express Application

```typescript
// src/index.ts
import express, { type Request, type Response, type NextFunction } from 'express';

const app = express();
const PORT = process.env.PORT ?? 3000;

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.get('/health', (_req: Request, res: Response) => {
  res.json({ status: 'ok' });
});

// Error handler
app.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Internal Server Error' });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

## Development Server

```bash
# Development with hot reload
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

### tsx Features

- **Fast execution**: Uses esbuild for instant startup
- **Watch mode**: Auto-restarts on file changes
- **TypeScript native**: No separate compilation step needed

## Task Runner

Manage scripts in `package.json`:

```json
{
  "scripts": {
    "lint": "eslint src/ && prettier --check src/",
    "format": "eslint src/ --fix && prettier --write src/",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "all": "npm run lint && npm run typecheck && npm run test"
  }
}
```

## Common Commands

```bash
# Initialize
npm init -y
npm install typescript tsx @types/node --save-dev
npx tsc --init

# Install dependencies
npm install

# Quality check (all)
npm run lint && npm run typecheck && npm run test

# Or combined
npm run all

# Development
npm run dev
```

## Pre-commit Checklist

- [ ] `npm run lint` passes
- [ ] `npm run format:check` passes
- [ ] `npm run typecheck` passes
- [ ] `npm run test` passes
