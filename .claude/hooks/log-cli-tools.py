#!/usr/bin/env python3
"""
PostToolUse hook: Log Codex/Gemini CLI input/output to JSONL file.

Triggers after Bash tool calls containing 'codex' or 'gemini' commands.
Logs are stored in .claude/logs/cli-tools.jsonl

All agents (Claude Code, subagents, Codex, Gemini) can read this log.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Setup logging for errors
LOG_DIR = Path(__file__).parent.parent / "logs"
ERROR_LOG_FILE = LOG_DIR / "hook-errors.log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(ERROR_LOG_FILE),
    level=logging.WARNING,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("log-cli-tools")

# CLI tools log file
LOG_FILE = LOG_DIR / "cli-tools.jsonl"


def extract_codex_prompt(command: str) -> str | None:
    """Extract prompt from codex exec command."""
    # Pattern: codex exec ... "prompt" or codex exec ... 'prompt'
    patterns = [
        r'codex\s+exec\s+.*?--full-auto\s+"([^"]+)"',
        r"codex\s+exec\s+.*?--full-auto\s+'([^']+)'",
        r'codex\s+exec\s+.*?"([^"]+)"\s*2>/dev/null',
        r"codex\s+exec\s+.*?'([^']+)'\s*2>/dev/null",
    ]
    for pattern in patterns:
        match = re.search(pattern, command, re.DOTALL)
        if match:
            return match.group(1).strip()
    return None


def extract_gemini_prompt(command: str) -> str | None:
    """Extract prompt from gemini command."""
    # Pattern: gemini -p "prompt" or gemini -p 'prompt'
    patterns = [
        r'gemini\s+-p\s+"([^"]+)"',
        r"gemini\s+-p\s+'([^']+)'",
    ]
    for pattern in patterns:
        match = re.search(pattern, command, re.DOTALL)
        if match:
            return match.group(1).strip()
    return None


def extract_model(command: str) -> str | None:
    """Extract model name from command."""
    match = re.search(r"--model\s+(\S+)", command)
    return match.group(1) if match else None


def truncate_text(text: str, max_length: int = 2000) -> str:
    """Truncate text if too long."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + f"... [truncated, {len(text)} total chars]"


# Patterns for sensitive data filtering (compiled for performance)
SENSITIVE_PATTERNS = [
    # API keys (common formats)
    (re.compile(r'(?i)(api[_-]?key|apikey)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?'), r'\1="[REDACTED]"'),
    # Secrets, passwords
    (re.compile(r'(?i)(secret|password|passwd|pwd)["\s:=]+["\']?([^\s"\']{4,})["\']?'), r'\1="[REDACTED]"'),
    # Bearer tokens
    (re.compile(r'(?i)(bearer\s+)([a-zA-Z0-9_\-\.]{10,})'), r'\1[REDACTED]'),
    # JWT tokens (three base64 segments)
    (re.compile(r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*'), '[REDACTED_JWT]'),
    # Environment variable secrets
    (re.compile(r'([A-Z_]*(?:SECRET|TOKEN|KEY|PASSWORD|PASSWD)[A-Z_]*)[=\s]+["\']?([^\s"\']{4,})'), r'\1=[REDACTED]'),
    # Connection strings with credentials
    (re.compile(r'(?i)(mongodb\+srv|postgres|mysql|redis)://[^@]+@'), r'\1://[REDACTED]@'),
    # AWS keys
    (re.compile(r'(?i)(aws[_-]?access[_-]?key[_-]?id)["\s:=]+["\']?([A-Z0-9]{16,})["\']?'), r'\1="[REDACTED]"'),
    (re.compile(r'(?i)(aws[_-]?secret[_-]?access[_-]?key)["\s:=]+["\']?([a-zA-Z0-9/+=]{30,})["\']?'), r'\1="[REDACTED]"'),
]


def filter_sensitive_data(text: str) -> str:
    """Remove sensitive data patterns from text."""
    if not text:
        return text
    result = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


# Log rotation settings
MAX_LOG_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_BACKUP_FILES = 5


def rotate_log_if_needed() -> None:
    """Rotate log file if it exceeds size limit."""
    if not LOG_FILE.exists():
        return

    try:
        if LOG_FILE.stat().st_size < MAX_LOG_SIZE_BYTES:
            return

        # Rotate: .1 -> .2 -> .3 -> .4 -> .5 (delete oldest)
        for i in range(MAX_BACKUP_FILES - 1, 0, -1):
            old_backup = LOG_FILE.with_suffix(f".jsonl.{i}")
            new_backup = LOG_FILE.with_suffix(f".jsonl.{i + 1}")
            if old_backup.exists():
                if i + 1 >= MAX_BACKUP_FILES:
                    old_backup.unlink()  # Delete oldest
                else:
                    old_backup.rename(new_backup)

        # Move current to .1
        backup_1 = LOG_FILE.with_suffix(".jsonl.1")
        LOG_FILE.rename(backup_1)
        logger.info(f"Rotated log file to {backup_1}")

    except Exception as e:
        logger.warning(f"Log rotation failed: {e}")


def log_entry(entry: dict) -> None:
    """Append entry to JSONL log file with rotation."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    rotate_log_if_needed()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> None:
    # Generate trace ID for request correlation
    trace_id = str(uuid.uuid4())[:8]
    start_time = datetime.now(timezone.utc)

    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        logger.error(f"[{trace_id}] Invalid JSON input: {e}")
        return

    # Only process Bash tool calls
    tool_name = hook_input.get("tool_name", "")
    if tool_name != "Bash":
        return

    # Get command and output
    tool_input = hook_input.get("tool_input", {})
    tool_response = hook_input.get("tool_response", {})

    command = tool_input.get("command", "")
    output = tool_response.get("stdout", "") or tool_response.get("content", "")

    # Check if this is a codex or gemini command
    is_codex = "codex" in command.lower()
    is_gemini = "gemini" in command.lower() and "codex" not in command.lower()

    if not (is_codex or is_gemini):
        return

    # Extract prompt based on tool type
    if is_codex:
        tool = "codex"
        prompt = extract_codex_prompt(command)
        model = extract_model(command) or "gpt-5.2-codex"
    else:
        tool = "gemini"
        prompt = extract_gemini_prompt(command)
        model = "gemini-3-pro-preview"

    if not prompt:
        # Could not extract prompt, skip logging
        return

    # Determine success
    exit_code = tool_response.get("exit_code", 0)
    success = exit_code == 0 and bool(output)

    # Calculate latency
    end_time = datetime.now(timezone.utc)
    latency_ms = int((end_time - start_time).total_seconds() * 1000)

    # Get session ID from environment if available
    session_id = os.environ.get("CLAUDE_SESSION_ID", "unknown")

    # Create log entry with trace_id and latency
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": trace_id,
        "session_id": session_id,
        "tool": tool,
        "model": model,
        "prompt": truncate_text(filter_sensitive_data(prompt)),
        "response": truncate_text(filter_sensitive_data(output)) if output else "",
        "success": success,
        "exit_code": exit_code,
        "latency_ms": latency_ms,
    }

    try:
        log_entry(entry)
    except Exception as e:
        logger.error(f"[{trace_id}] Failed to write log entry: {e}", exc_info=True)

    # Output notification (shown to user via hook output)
    print(
        json.dumps(
            {
                "result": "continue",
                "message": f"[LOG] {tool.capitalize()} call logged (trace: {trace_id})",
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Hook error: {e}", exc_info=True)
        sys.exit(0)
