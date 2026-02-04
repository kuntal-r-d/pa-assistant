---
name: tdd
description: Implement features using Test-Driven Development (TDD) with Red-Green-Refactor cycle.
disable-model-invocation: true
---

# Test-Driven Development

Implement $ARGUMENTS using Test-Driven Development (TDD).

## TDD Cycle

```
Repeat: Red → Green → Refactor

1. Red:    Write a failing test
2. Green:  Write minimal code to pass the test
3. Refactor: Clean up code (tests still pass)
```

## Implementation Steps

### Phase 1: Test Design

1. **Confirm Requirements**
   - What is the input
   - What is the output
   - What are the edge cases

2. **List Test Cases**
   ```
   - [ ] Happy path: Basic functionality
   - [ ] Happy path: Boundary values
   - [ ] Error case: Invalid input
   - [ ] Error case: Error handling
   ```

### Phase 2: Red-Green-Refactor

#### Step 1: Write First Test (Red)

```typescript
// src/{module}.test.ts
import { describe, it, expect } from 'vitest';
import { functionName } from './{module}';

describe('functionName', () => {
  it('should handle basic case', () => {
    // Arrange
    const input = { /* test data */ };

    // Act
    const result = functionName(input);

    // Assert
    expect(result).toEqual(expected);
  });
});
```

Run test and **confirm failure**:
```bash
npm run test -- src/{module}.test.ts
```

#### Step 2: Implementation (Green)

Write **minimal** code to pass the test:
- Don't aim for perfection
- Hardcoding is OK
- Just make the test pass

Run test and **confirm success**:
```bash
npm run test -- src/{module}.test.ts
```

#### Step 3: Refactoring (Refactor)

Improve while tests still pass:
- Remove duplication
- Improve naming
- Clean up structure

```bash
npm run test -- src/{module}.test.ts  # Confirm still passes
```

#### Step 4: Next Test

Return to Step 1 with next test case from the list.

### Phase 3: Completion Check

```bash
# Run all tests
npm run test

# Check coverage (target 80%+)
npm run test:coverage
```

## Report Format

```markdown
## TDD Complete: {Feature Name}

### Test Cases
- [x] {test1}: {description}
- [x] {test2}: {description}
...

### Coverage
{Coverage report}

### Implementation Files
- `src/{module}.ts`: {description}
- `src/{module}.test.ts`: {N} tests
```

## Notes

- Write tests **first** (not after)
- Keep each cycle **small**
- Refactor **after** tests pass
- Prioritize **working code** over perfection
