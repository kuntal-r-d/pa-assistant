"""
Advisory file locking for shared resources.

Prevents concurrent writes to protected files like DESIGN.md, CLAUDE.md, etc.
Uses fcntl for POSIX-compliant advisory locking.

Usage:
    from .file_lock import FileLock

    lock = FileLock('.claude/docs/DESIGN.md')
    if lock.acquire():
        try:
            # Edit the file
            pass
        finally:
            lock.release()
"""

from __future__ import annotations

import fcntl
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional


def _get_process_start_time(pid: int) -> float:
    """
    Get process start time for PID reuse detection.

    Returns the process creation timestamp, or 0.0 if unable to determine.
    Works on macOS and Linux.
    """
    try:
        # macOS: use ps command
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "lstart="],
            capture_output=True,
            text=True,
            timeout=1,
        )
        if result.returncode == 0 and result.stdout.strip():
            # Parse date string like "Mon Jan  1 12:00:00 2024"
            return datetime.strptime(
                result.stdout.strip(), "%a %b %d %H:%M:%S %Y"
            ).timestamp()
    except Exception:
        pass
    return 0.0


class FileLock:
    """
    Advisory file lock for shared resources.

    Args:
        file_path: Path to the file to lock
        lock_dir: Directory to store lock files (default: .claude/locks)
        timeout: Lock timeout in seconds (default: 60)
    """

    DEFAULT_LOCK_DIR = Path(__file__).parent.parent / "locks"
    DEFAULT_TIMEOUT = 60  # seconds

    def __init__(
        self,
        file_path: str,
        lock_dir: Optional[Path] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.file_path = Path(file_path)
        self.lock_dir = lock_dir or self.DEFAULT_LOCK_DIR
        self.timeout = timeout
        self._lock_fd: Optional[int] = None
        self._lock_file: Optional[Path] = None

    @property
    def lock_file(self) -> Path:
        """Get the lock file path for this file."""
        # Use sanitized filename to avoid path issues
        safe_name = self.file_path.name.replace("/", "_").replace("\\", "_")
        return self.lock_dir / f"{safe_name}.lock"

    def acquire(self, blocking: bool = True, wait_timeout: float = 30.0) -> bool:
        """
        Acquire exclusive lock on the file.

        Args:
            blocking: If True, wait for lock. If False, return immediately if locked.
            wait_timeout: Maximum time to wait for lock (only if blocking=True)

        Returns:
            True if lock acquired, False if timeout or non-blocking and locked.
        """
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self._lock_file = self.lock_file

        start_time = time.time()
        while True:
            try:
                # Open lock file
                fd = os.open(str(self._lock_file), os.O_CREAT | os.O_RDWR)

                # Try to acquire exclusive lock (non-blocking to enable timeout handling)
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

                # Write lock metadata (including process start time for PID reuse detection)
                os.ftruncate(fd, 0)
                os.lseek(fd, 0, os.SEEK_SET)
                proc_start = _get_process_start_time(os.getpid())
                metadata = f"{os.getpid()}\n{self.file_path}\n{time.time()}\n{proc_start}\n"
                os.write(fd, metadata.encode())

                self._lock_fd = fd
                return True

            except BlockingIOError:
                os.close(fd)

                if not blocking:
                    return False

                # Check if we should keep waiting
                elapsed = time.time() - start_time
                if elapsed >= wait_timeout:
                    return False

                # Check for stale lock
                if self._is_stale_lock():
                    self._cleanup_stale_lock()
                    continue

                # Wait and retry
                time.sleep(0.5)

            except Exception as e:
                if 'fd' in locals():
                    os.close(fd)
                raise RuntimeError(f"Failed to acquire lock: {e}") from e

    def release(self) -> None:
        """Release the lock."""
        if self._lock_fd is not None:
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
                os.close(self._lock_fd)
            except Exception:
                pass  # Best effort cleanup
            finally:
                self._lock_fd = None

            # Remove lock file
            if self._lock_file and self._lock_file.exists():
                try:
                    self._lock_file.unlink()
                except Exception:
                    pass  # Best effort cleanup

    def _is_stale_lock(self) -> bool:
        """Check if the lock file is stale (process dead, PID reused, or timeout exceeded)."""
        if not self._lock_file or not self._lock_file.exists():
            return False

        try:
            content = self._lock_file.read_text()
            lines = content.strip().split("\n")
            if len(lines) >= 3:
                pid = int(lines[0])
                lock_time = float(lines[2])

                # Check if process is still running
                try:
                    os.kill(pid, 0)  # Signal 0 just checks if process exists
                except OSError:
                    return True  # Process dead

                # Check for PID reuse (if we have process start time in lock file)
                if len(lines) >= 4:
                    lock_proc_start = float(lines[3])
                    current_proc_start = _get_process_start_time(pid)
                    # If current process started at different time, PID was reused
                    if current_proc_start > 0 and abs(current_proc_start - lock_proc_start) > 1.0:
                        return True  # Different process with same PID

                # Check if lock timeout exceeded
                if time.time() - lock_time > self.timeout:
                    return True

            return False
        except Exception:
            return False

    def _cleanup_stale_lock(self) -> None:
        """Remove a stale lock file."""
        if self._lock_file and self._lock_file.exists():
            try:
                self._lock_file.unlink()
            except Exception:
                pass

    def is_locked(self) -> bool:
        """Check if the file is currently locked (by any process)."""
        if not self.lock_file.exists():
            return False

        try:
            fd = os.open(str(self.lock_file), os.O_RDWR)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
                return False  # Was able to acquire, so not locked
            except BlockingIOError:
                os.close(fd)
                return True  # Could not acquire, so locked
        except Exception:
            return False

    def get_lock_info(self) -> Optional[dict]:
        """Get information about the current lock holder."""
        if not self.lock_file.exists():
            return None

        try:
            content = self.lock_file.read_text()
            lines = content.strip().split("\n")
            if len(lines) >= 3:
                return {
                    "pid": int(lines[0]),
                    "file": lines[1],
                    "lock_time": float(lines[2]),
                    "age_seconds": time.time() - float(lines[2]),
                }
        except Exception:
            pass
        return None

    def __enter__(self) -> "FileLock":
        """Context manager support."""
        if not self.acquire():
            raise RuntimeError(f"Could not acquire lock for {self.file_path}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager support."""
        self.release()


# List of protected files that should use locking
PROTECTED_FILES = [
    "DESIGN.md",
    "CLAUDE.md",
    "AGENTS.md",
    "GEMINI.md",
    "mode.json",  # Session mode state file
]


def is_protected_file(file_path: str) -> bool:
    """Check if a file is in the protected list."""
    filename = Path(file_path).name
    return filename in PROTECTED_FILES
