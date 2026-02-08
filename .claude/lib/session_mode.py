"""
Session mode management for multi-agent workflow.

Controls which LLM agents are available and whether user confirmation is required.

Modes:
- SOLO (default): Claude + Claude subagents, no Codex/Gemini CLI calls
- CONSULT: Claude can consult Codex/Gemini, asks permission first
- AUTO: Claude auto-delegates to Codex/Gemini, no prompts
- CODEX: Only Codex consultation allowed
- GEMINI: Only Gemini consultation allowed

Usage:
    from lib.session_mode import get_mode, set_mode, AgentMode

    mode = get_mode()
    if mode.should_ask_permission():
        # Show confirmation prompt to user
        pass

    if mode.is_agent_allowed("codex"):
        # Can delegate to Codex
        pass
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Import FileLock for thread-safe file access
try:
    from .file_lock import FileLock
    FILE_LOCK_AVAILABLE = True
except ImportError:
    FILE_LOCK_AVAILABLE = False
    logger.warning("FileLock not available, concurrent access may cause issues")

# Session state directory
SESSION_DIR = Path(__file__).parent.parent / "session"
MODE_FILE = SESSION_DIR / "mode.json"


class AgentMode(Enum):
    """Available agent modes."""
    SOLO = "solo"        # Claude only (default)
    CONSULT = "consult"  # Ask before delegating
    AUTO = "auto"        # Auto-delegate without asking
    CODEX = "codex"      # Only Codex allowed
    GEMINI = "gemini"    # Only Gemini allowed
    OLLAMA = "ollama"    # Only Ollama (local/free) allowed
    LOCAL = "local"      # Alias for Ollama - local models only


@dataclass
class ModeConfig:
    """Configuration for current mode."""
    mode: AgentMode
    delegation_enabled: bool
    ask_permission: bool
    allowed_agents: List[str]
    first_delegation_done: bool = False  # For CODEX/GEMINI modes

    def should_ask_permission(self) -> bool:
        """Check if permission prompt should be shown."""
        if self.mode == AgentMode.SOLO:
            return False  # No delegation = no prompt
        if self.mode == AgentMode.AUTO:
            return False  # Auto-delegate = no prompt
        if self.mode in (AgentMode.CODEX, AgentMode.GEMINI):
            # Ask once, then auto-delegate
            return not self.first_delegation_done
        # CONSULT mode always asks
        return self.ask_permission

    def is_delegation_enabled(self) -> bool:
        """Check if delegation to external LLMs is enabled."""
        return self.delegation_enabled

    def is_agent_allowed(self, agent: str) -> bool:
        """Check if specific agent is allowed in current mode."""
        if not self.delegation_enabled:
            return False
        return agent.lower() in [a.lower() for a in self.allowed_agents]

    def mark_first_delegation_done(self) -> None:
        """Mark that first delegation has been done (for CODEX/GEMINI modes)."""
        self.first_delegation_done = True
        _save_mode_state(self)


# Mode configurations
MODE_CONFIGS = {
    AgentMode.SOLO: ModeConfig(
        mode=AgentMode.SOLO,
        delegation_enabled=False,
        ask_permission=False,
        allowed_agents=[],
    ),
    AgentMode.CONSULT: ModeConfig(
        mode=AgentMode.CONSULT,
        delegation_enabled=True,
        ask_permission=True,
        allowed_agents=["codex", "gemini", "ollama"],
    ),
    AgentMode.AUTO: ModeConfig(
        mode=AgentMode.AUTO,
        delegation_enabled=True,
        ask_permission=False,
        allowed_agents=["codex", "gemini", "ollama"],
    ),
    AgentMode.CODEX: ModeConfig(
        mode=AgentMode.CODEX,
        delegation_enabled=True,
        ask_permission=True,  # Ask once
        allowed_agents=["codex"],
    ),
    AgentMode.GEMINI: ModeConfig(
        mode=AgentMode.GEMINI,
        delegation_enabled=True,
        ask_permission=True,  # Ask once
        allowed_agents=["gemini"],
    ),
    AgentMode.OLLAMA: ModeConfig(
        mode=AgentMode.OLLAMA,
        delegation_enabled=True,
        ask_permission=True,  # Ask once
        allowed_agents=["ollama"],
    ),
    AgentMode.LOCAL: ModeConfig(
        mode=AgentMode.LOCAL,
        delegation_enabled=True,
        ask_permission=True,  # Ask once
        allowed_agents=["ollama"],  # LOCAL is alias for Ollama
    ),
}


def _ensure_session_dir() -> None:
    """Ensure session directory exists."""
    SESSION_DIR.mkdir(parents=True, exist_ok=True)


def _atomic_write_json(file_path: Path, data: dict) -> None:
    """
    Atomically write JSON data using temp-file-then-rename pattern.

    This prevents partial writes from corrupting the file on crash.

    Args:
        file_path: Target file path
        data: Dictionary to write as JSON
    """
    # Write to temp file in same directory (ensures same filesystem for atomic rename)
    temp_fd, temp_path = tempfile.mkstemp(
        dir=file_path.parent,
        prefix=".mode_",
        suffix=".tmp"
    )
    try:
        with os.fdopen(temp_fd, 'w') as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())  # Ensure data hits disk

        # Atomic rename (POSIX guarantees atomicity on same filesystem)
        os.rename(temp_path, file_path)

    except Exception:
        # Clean up temp file on failure
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def _load_mode_state() -> Optional[dict]:
    """
    Load mode state from file with file locking.

    Uses advisory locking to prevent race conditions with concurrent reads/writes.
    """
    if not MODE_FILE.exists():
        return None

    try:
        if FILE_LOCK_AVAILABLE:
            lock = FileLock(str(MODE_FILE), timeout=10)
            if lock.acquire(blocking=True, wait_timeout=5.0):
                try:
                    with open(MODE_FILE, "r") as f:
                        return json.load(f)
                finally:
                    lock.release()
            else:
                # Could not acquire lock, try reading anyway (best effort)
                logger.warning("Could not acquire lock for reading mode.json")
                with open(MODE_FILE, "r") as f:
                    return json.load(f)
        else:
            # No locking available
            with open(MODE_FILE, "r") as f:
                return json.load(f)

    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load mode state: {e}")
    return None


def _save_mode_state(config: ModeConfig) -> None:
    """
    Save mode state to file with locking and atomic write.

    Uses advisory locking to prevent race conditions and atomic writes
    to prevent corruption on crash.
    """
    _ensure_session_dir()

    state = {
        "mode": config.mode.value,
        "first_delegation_done": config.first_delegation_done,
    }

    try:
        if FILE_LOCK_AVAILABLE:
            lock = FileLock(str(MODE_FILE), timeout=30)
            if lock.acquire(blocking=True, wait_timeout=10.0):
                try:
                    _atomic_write_json(MODE_FILE, state)
                finally:
                    lock.release()
            else:
                logger.error("Could not acquire lock for writing mode.json")
                raise IOError("Failed to acquire file lock for mode.json")
        else:
            # No locking available - use atomic write for best-effort safety
            _atomic_write_json(MODE_FILE, state)

    except IOError as e:
        logger.warning(f"Failed to save mode state: {e}")


def get_mode() -> ModeConfig:
    """
    Get current agent mode configuration.

    Returns:
        ModeConfig with current mode settings
    """
    state = _load_mode_state()

    if state:
        try:
            mode = AgentMode(state.get("mode", "solo"))
            config = ModeConfig(
                mode=mode,
                delegation_enabled=MODE_CONFIGS[mode].delegation_enabled,
                ask_permission=MODE_CONFIGS[mode].ask_permission,
                allowed_agents=MODE_CONFIGS[mode].allowed_agents.copy(),
                first_delegation_done=state.get("first_delegation_done", False),
            )
            return config
        except (ValueError, KeyError) as e:
            logger.warning(f"Invalid mode state, using default: {e}")

    # Default to SOLO mode
    return ModeConfig(
        mode=AgentMode.SOLO,
        delegation_enabled=False,
        ask_permission=False,
        allowed_agents=[],
    )


def set_mode(mode: AgentMode) -> ModeConfig:
    """
    Set agent mode.

    Args:
        mode: The AgentMode to set

    Returns:
        ModeConfig for the new mode
    """
    config = ModeConfig(
        mode=mode,
        delegation_enabled=MODE_CONFIGS[mode].delegation_enabled,
        ask_permission=MODE_CONFIGS[mode].ask_permission,
        allowed_agents=MODE_CONFIGS[mode].allowed_agents.copy(),
        first_delegation_done=False,  # Reset on mode change
    )
    _save_mode_state(config)
    logger.info(f"Agent mode set to: {mode.value}")
    return config


def parse_mode_command(prompt: str) -> Optional[AgentMode]:
    """
    Parse mode command from user prompt.

    Args:
        prompt: User's input prompt

    Returns:
        AgentMode if command found, None otherwise

    Examples:
        "!solo" -> AgentMode.SOLO
        "!consult Help me design" -> AgentMode.CONSULT
        "!auto" -> AgentMode.AUTO
    """
    prompt_lower = prompt.lower().strip()

    mode_commands = {
        "!solo": AgentMode.SOLO,
        "!consult": AgentMode.CONSULT,
        "!auto": AgentMode.AUTO,
        "!codex": AgentMode.CODEX,
        "!gemini": AgentMode.GEMINI,
        "!ollama": AgentMode.OLLAMA,
        "!local": AgentMode.LOCAL,
    }

    for command, mode in mode_commands.items():
        if prompt_lower.startswith(command):
            return mode

    return None


def get_mode_description(mode: AgentMode) -> str:
    """Get human-readable description of mode."""
    descriptions = {
        AgentMode.SOLO: "Solo Mode: Claude + Claude subagents (no external CLI)",
        AgentMode.CONSULT: "Consult Mode: Claude can consult external agents (asks first)",
        AgentMode.AUTO: "Auto Mode: Claude auto-delegates to external agents (no prompts)",
        AgentMode.CODEX: "Codex Mode: Only Codex consultation allowed",
        AgentMode.GEMINI: "Gemini Mode: Only Gemini consultation allowed",
        AgentMode.OLLAMA: "Ollama Mode: Only local Ollama models allowed (free/private)",
        AgentMode.LOCAL: "Local Mode: Only local models allowed (Ollama - free/private)",
    }
    return descriptions.get(mode, f"Unknown mode: {mode}")


def clear_mode() -> None:
    """Clear mode state (reset to default SOLO)."""
    try:
        if MODE_FILE.exists():
            MODE_FILE.unlink()
        logger.info("Mode state cleared, reset to SOLO")
    except IOError as e:
        logger.warning(f"Failed to clear mode state: {e}")
