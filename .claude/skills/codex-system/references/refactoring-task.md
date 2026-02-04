# Refactoring Task for Codex

When delegating refactoring to Codex, use this prompt template.

## Prompt Template

```
Refactor the following code for improved readability and maintainability.

## Target Code
{file path and content}

## Libraries Used
{list of libraries with constraints from .claude/docs/libraries/}

## Refactoring Goals
{specific goals or "General simplification"}

---

Core Principles:

### Pursuit of Simplicity
- Readable code over complex code
- 1 function = 1 responsibility
- Keep nesting shallow (early return)
- Eliminate magic numbers/strings

### Preserving Library Functionality
- Maintain all library constraints
- Don't change library usage patterns unless necessary
- Verify async/sync requirements

### TypeScript Best Practices
- Use proper type annotations
- Prefer interfaces over type aliases for objects
- Use generics where appropriate
- Avoid `any` type

---

Refactoring Patterns to Apply:

### Extract Function
- Break long functions into smaller, focused functions
- Each function should do one thing

### Early Return
- Replace nested if-else with guard clauses
- Return early for error/edge cases

### Add Type Annotations
- Add explicit return types to all functions
- Use proper generic types
- Define interfaces for complex objects

### Remove Duplication
- Extract common logic to shared functions
- Use appropriate abstractions (but don't over-abstract)

---

Provide:
1. Refactored code
2. Explanation of changes
3. Verification that library constraints are preserved
```

## Example Invocation

```bash
codex exec --model gpt-5.2-codex --sandbox workspace-write --full-auto "
Refactor this code for simplicity:

## Target Code
File: src/services/llm-client.ts
$(cat src/services/llm-client.ts)

## Libraries Used
- openai: async client, retry with exponential backoff
- zod: validation schemas

## Refactoring Goals
- Reduce function length
- Add proper error handling
- Improve naming
- Add TypeScript types

[Principles and patterns as above...]
" 2>/dev/null
```

## Checklist

### Before Refactoring
- [ ] Tests exist and all pass
- [ ] Library constraints understood
- [ ] Impact scope identified

### During Refactoring
- [ ] Proceed in small steps
- [ ] Run tests at each step
- [ ] Verify library usage unchanged

### After Refactoring
- [ ] All tests pass
- [ ] Behavior unchanged
- [ ] Code is simpler
- [ ] Type annotations are appropriate
- [ ] ESLint/Prettier pass

## When to Use

- When code becomes hard to read/maintain
- When user says "refactor this", "simplify this"
- Before adding new features to complex code
- When code review identifies complexity issues
