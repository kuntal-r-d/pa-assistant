#!/usr/bin/env python3
"""
Post-tool hook: Run formatter and type checker on TypeScript files after Edit/Write.

Triggered after Edit or Write tools modify files.
Runs ESLint, Prettier, and TypeScript compiler on TypeScript files.
"""

import json
import os
import subprocess
import sys

# Input validation constants
MAX_PATH_LENGTH = 4096


def validate_path(file_path: str) -> bool:
    """Validate file path for security."""
    if not file_path or len(file_path) > MAX_PATH_LENGTH:
        return False
    # Check for path traversal
    if ".." in file_path:
        return False
    return True


def get_file_path() -> str | None:
    """Extract file path from tool input."""
    tool_input = os.environ.get("CLAUDE_TOOL_INPUT", "")
    if not tool_input:
        return None

    try:
        data = json.loads(tool_input)
        return data.get("file_path")
    except json.JSONDecodeError:
        return None


def is_typescript_file(path: str) -> bool:
    """Check if the file is a TypeScript or JavaScript file."""
    return path.endswith((".ts", ".tsx", ".js", ".jsx", ".mts", ".cts"))


def run_command(cmd: list[str], cwd: str) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except FileNotFoundError:
        return 1, "", f"Command not found: {cmd[0]}"


def main() -> None:
    file_path = get_file_path()
    if not file_path:
        return

    # Validate input
    if not validate_path(file_path):
        return

    if not is_typescript_file(file_path):
        return

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

    # Determine relative path for display
    if file_path.startswith(project_dir):
        rel_path = os.path.relpath(file_path, project_dir)
    else:
        rel_path = file_path

    issues: list[str] = []

    # Run Prettier format
    ret, stdout, stderr = run_command(
        ["npx", "prettier", "--write", file_path],
        cwd=project_dir,
    )
    if ret != 0:
        issues.append(f"prettier format failed:\n{stderr or stdout}")

    # Run ESLint with auto-fix
    ret, stdout, stderr = run_command(
        ["npx", "eslint", "--fix", file_path],
        cwd=project_dir,
    )
    if ret != 0:
        # Show remaining issues that couldn't be auto-fixed
        output = stdout or stderr
        if output.strip():
            issues.append(f"eslint issues:\n{output}")

    # Run TypeScript type check (only for .ts/.tsx files)
    if file_path.endswith((".ts", ".tsx", ".mts", ".cts")):
        ret, stdout, stderr = run_command(
            ["npx", "tsc", "--noEmit", "--skipLibCheck"],
            cwd=project_dir,
        )
        if ret != 0:
            output = stdout or stderr
            if output.strip():
                issues.append(f"tsc type check issues:\n{output}")

    # Report results
    if issues:
        print(f"[lint-on-save] Issues found in {rel_path}:", file=sys.stderr)
        for issue in issues:
            print(issue, file=sys.stderr)
        print(
            "\nPlease review and fix these issues.",
            file=sys.stderr,
        )
    else:
        print(f"[lint-on-save] OK: {rel_path} passed all checks")


if __name__ == "__main__":
    main()
