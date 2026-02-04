#!/usr/bin/env python3
"""
PostToolUse hook: Suggest Codex analysis after test/build failures.

Analyzes test and build output and suggests Codex consultation
for debugging complex failures.
"""

import json
import sys
import re

# Commands that run tests or builds
TEST_BUILD_COMMANDS = [
    "npm test",
    "npm run test",
    "npm run build",
    "npm run lint",
    "npm run typecheck",
    "npx vitest",
    "npx jest",
    "npx tsc",
    "npx eslint",
    "pnpm test",
    "pnpm run test",
    "pnpm run build",
    "yarn test",
    "yarn run test",
    "yarn run build",
    "bun test",
    "bun run test",
    "make test",
    "make build",
]

# Patterns indicating failures that need debugging
FAILURE_PATTERNS = [
    r"FAILED",
    r"ERROR",
    r"error\[",
    r"Error:",
    r"failed",
    r"error:",
    r"TypeError",
    r"ReferenceError",
    r"SyntaxError",
    r"Cannot find module",
    r"Cannot find name",
    r"TS\d{4}:",  # TypeScript errors like TS2304:
    r"AssertionError",
    r"expect\(.+\)\..+\(.+\)",  # Jest/Vitest assertion failures
    r"FAIL\s+",  # Jest test failures
    r"✖|×",  # Test failure markers
    r"ERR!",  # npm errors
]

# Simple errors that don't need Codex
SIMPLE_ERRORS = [
    "Cannot find module",  # Usually just need to install
    "command not found",
    "No such file or directory",
    "ENOENT",
    "npm ERR! missing script",
]


def is_test_or_build_command(command: str) -> bool:
    """Check if the command runs tests or builds."""
    command_lower = command.lower()
    return any(cmd in command_lower for cmd in TEST_BUILD_COMMANDS)


def has_complex_failure(output: str) -> tuple[bool, str]:
    """Check if output contains complex failures that need debugging."""
    # Skip if it's a simple error
    for simple in SIMPLE_ERRORS:
        if simple in output:
            return False, ""

    # Count failure patterns
    failure_count = 0
    matched_patterns = []
    for pattern in FAILURE_PATTERNS:
        matches = re.findall(pattern, output, re.IGNORECASE)
        if matches:
            failure_count += len(matches)
            matched_patterns.append(pattern)

    # Multiple failures or complex errors suggest need for Codex
    if failure_count >= 3:
        return True, f"Multiple failures detected ({failure_count} issues)"

    # Single failure in test output
    if failure_count >= 1 and any(
        p in output.lower() for p in ["expect(", "assertion", "typeerror", "ts2"]
    ):
        return True, "Test failure or type error"

    return False, ""


def main():
    try:
        data = json.load(sys.stdin)
        tool_name = data.get("tool_name", "")

        # Only process Bash tool
        if tool_name != "Bash":
            sys.exit(0)

        tool_input = data.get("tool_input", {})
        tool_output = data.get("tool_output", "")
        command = tool_input.get("command", "")

        # Check if it's a test/build command
        if not is_test_or_build_command(command):
            sys.exit(0)

        # Check for complex failures
        has_failure, reason = has_complex_failure(tool_output)

        if has_failure:
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": (
                        f"[Codex Debug Suggestion] {reason}. "
                        "Consider consulting Codex for debugging analysis. "
                        "**Recommended**: Use Task tool with subagent_type='general-purpose' "
                        "to consult Codex with full error context and preserve main context."
                    ),
                }
            }
            print(json.dumps(output))

        sys.exit(0)

    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
