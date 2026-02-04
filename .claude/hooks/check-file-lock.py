#!/usr/bin/env python3
"""
PreToolUse hook: Check file lock before Edit/Write operations.

Prevents concurrent writes to protected files (DESIGN.md, CLAUDE.md, etc.)
by checking if a lock is held by another process.

Protected files:
- DESIGN.md - Architecture decisions
- CLAUDE.md - Project context
- AGENTS.md - Codex context
- GEMINI.md - Gemini context
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# Setup logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOG_DIR / "hook-errors.log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.WARNING,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("check-file-lock")

# Import shared FileLock from lib
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))
from file_lock import FileLock, is_protected_file


def check_lock(file_path: str) -> tuple[bool, str]:
    """
    Check if file is locked by another process.

    Returns:
        (is_locked, reason) - True if locked, with reason string
    """
    if not is_protected_file(file_path):
        return False, ""

    lock = FileLock(file_path)

    # Check for stale lock and clean up
    if lock._is_stale_lock():
        lock._cleanup_stale_lock()
        logger.info(f"Cleaned up stale lock for {file_path}")
        return False, ""

    # Check if currently locked
    if lock.is_locked():
        info = lock.get_lock_info()
        if info:
            age = int(info.get("age_seconds", 0))
            pid = info.get("pid", "unknown")
            return True, f"Locked by PID {pid} ({age}s ago)"
        return True, "Lock file exists"

    return False, ""


def main():
    try:
        data = json.load(sys.stdin)
        tool_input = data.get("tool_input", {})
        file_path = tool_input.get("file_path", "")

        if not file_path:
            sys.exit(0)

        is_locked, reason = check_lock(file_path)

        if is_locked:
            filename = Path(file_path).name
            output = {
                "decision": "block",
                "reason": (
                    f"[File Lock] {filename} is currently locked: {reason}. "
                    f"Another process is editing this file. "
                    f"Wait for the lock to be released or check .claude/locks/ for details."
                )
            }
            print(json.dumps(output))
            logger.warning(f"Blocked write to locked file: {file_path} ({reason})")
            sys.exit(1)  # Block the operation

        sys.exit(0)  # Allow the operation

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON input: {e}")
        sys.exit(0)  # Don't block on input errors

    except Exception as e:
        logger.error(f"Hook error: {e}", exc_info=True)
        sys.exit(0)  # Don't block on errors


if __name__ == "__main__":
    main()
