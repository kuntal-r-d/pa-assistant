"""
Task coordinator for parallel agent orchestration.

Manages parallel execution of Codex and Gemini subagents with
findings synchronized via separate files.

Usage:
    from lib.task_coordinator import TaskCoordinator

    coordinator = TaskCoordinator()
    task_id = coordinator.generate_task_id()

    # Paths for agent outputs
    research_path = coordinator.get_research_path(task_id)
    design_path = coordinator.get_design_path(task_id)
    decision_path = coordinator.get_decision_path(task_id)
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Output directories
DOCS_DIR = Path(__file__).parent.parent / "docs"
RESEARCH_DIR = DOCS_DIR / "research"
DESIGN_DIR = DOCS_DIR / "design"
DECISIONS_DIR = DOCS_DIR / "decisions"

# Safe task ID pattern: alphanumeric, hyphens, underscores only
SAFE_TASK_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')


class PathTraversalError(ValueError):
    """Raised when a path traversal attempt is detected."""
    pass


def _validate_task_id(task_id: str) -> str:
    """
    Validate task ID to prevent path traversal attacks.

    Args:
        task_id: The task ID to validate

    Returns:
        The validated task ID

    Raises:
        PathTraversalError: If task ID contains path traversal sequences
        ValueError: If task ID format is invalid
    """
    if not task_id:
        raise ValueError("Task ID cannot be empty")

    # Check for path traversal sequences
    if '..' in task_id:
        raise PathTraversalError(f"Path traversal detected in task ID: {task_id}")

    if '/' in task_id or '\\' in task_id:
        raise PathTraversalError(f"Path separator detected in task ID: {task_id}")

    # Check for null bytes (another injection vector)
    if '\0' in task_id:
        raise PathTraversalError(f"Null byte detected in task ID: {task_id}")

    # Validate format (only alphanumeric, hyphens, underscores)
    if not SAFE_TASK_ID_PATTERN.match(task_id):
        raise ValueError(
            f"Invalid task ID format: {task_id}. "
            f"Must contain only alphanumeric characters, hyphens, and underscores."
        )

    return task_id


def _safe_path(base_dir: Path, task_id: str, suffix: str = ".md") -> Path:
    """
    Construct a safe path within the base directory.

    Args:
        base_dir: The base directory (must be absolute)
        task_id: The task ID (will be validated)
        suffix: File suffix

    Returns:
        Safe path within base_dir

    Raises:
        PathTraversalError: If resulting path escapes base_dir
    """
    # Validate task ID first
    validated_id = _validate_task_id(task_id)

    # Construct path
    target_path = base_dir / f"{validated_id}{suffix}"

    # Resolve to absolute and verify containment (defense in depth)
    resolved_path = target_path.resolve()
    resolved_base = base_dir.resolve()

    # Check that resolved path is within base directory
    try:
        resolved_path.relative_to(resolved_base)
    except ValueError:
        raise PathTraversalError(
            f"Path {resolved_path} escapes base directory {resolved_base}"
        )

    return target_path


@dataclass
class AgentResult:
    """Result from a subagent execution."""
    agent: str  # "codex" or "gemini"
    task_id: str
    output_path: Path
    summary: str
    success: bool
    error: Optional[str] = None


@dataclass
class CoordinatedTask:
    """A coordinated multi-agent task."""
    task_id: str
    user_request: str
    created_at: datetime
    gemini_result: Optional[AgentResult] = None
    codex_result: Optional[AgentResult] = None
    final_decision: Optional[str] = None


class TaskCoordinator:
    """
    Coordinates parallel execution of multiple agent subagents.

    Manages output paths and provides helpers for synthesizing findings.
    """

    def __init__(self):
        """Initialize coordinator and ensure directories exist."""
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure all output directories exist."""
        for directory in [RESEARCH_DIR, DESIGN_DIR, DECISIONS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

    def generate_task_id(self, user_request: Optional[str] = None) -> str:
        """
        Generate unique task ID.

        Args:
            user_request: Optional user request to include in hash

        Returns:
            Unique task ID string (e.g., "task-2026-02-05-a1b2c3d4")
        """
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")

        # Create hash from timestamp and request
        hash_input = f"{timestamp}-{user_request or ''}"
        hash_suffix = hashlib.sha256(hash_input.encode()).hexdigest()[:8]

        return f"task-{timestamp}-{hash_suffix}"

    def get_research_path(self, task_id: str) -> Path:
        """
        Get path for Gemini research output.

        Args:
            task_id: Validated task ID

        Returns:
            Safe path within RESEARCH_DIR

        Raises:
            PathTraversalError: If task_id contains path traversal
            ValueError: If task_id format is invalid
        """
        return _safe_path(RESEARCH_DIR, task_id, ".md")

    def get_design_path(self, task_id: str) -> Path:
        """
        Get path for Codex design output.

        Args:
            task_id: Validated task ID

        Returns:
            Safe path within DESIGN_DIR

        Raises:
            PathTraversalError: If task_id contains path traversal
            ValueError: If task_id format is invalid
        """
        return _safe_path(DESIGN_DIR, task_id, ".md")

    def get_decision_path(self, task_id: str) -> Path:
        """
        Get path for final decision output.

        Args:
            task_id: Validated task ID

        Returns:
            Safe path within DECISIONS_DIR

        Raises:
            PathTraversalError: If task_id contains path traversal
            ValueError: If task_id format is invalid
        """
        return _safe_path(DECISIONS_DIR, task_id, ".md")

    def create_gemini_prompt(
        self, user_request: str, task_id: str
    ) -> str:
        """
        Create prompt for Gemini subagent.

        Args:
            user_request: Original user request
            task_id: Task ID for file naming

        Returns:
            Formatted prompt for subagent
        """
        output_path = self.get_research_path(task_id)

        return f'''Research task: {user_request}

CONSTRAINTS:
- ONLY write to {output_path}
- Do NOT modify any other files
- Return concise summary to orchestrator

Steps:
1. Call Gemini CLI:
   gemini -p "Research: {user_request}. Include best practices, common patterns, library recommendations, and potential pitfalls." 2>/dev/null

2. Save the full research output to: {output_path}

3. Return CONCISE summary (5-7 bullet points):
   - Key findings
   - Recommended approach
   - Important caveats'''

    def create_codex_prompt(
        self,
        user_request: str,
        task_id: str,
        gemini_findings: Optional[str] = None,
    ) -> str:
        """
        Create prompt for Codex subagent.

        Args:
            user_request: Original user request
            task_id: Task ID for file naming
            gemini_findings: Optional research findings from Gemini

        Returns:
            Formatted prompt for subagent
        """
        output_path = self.get_design_path(task_id)

        context = ""
        if gemini_findings:
            context = f"\n\nContext from research:\n{gemini_findings}"

        return f'''Design analysis: {user_request}{context}

CONSTRAINTS:
- ONLY write to {output_path}
- Do NOT modify any other files
- Return concise summary to orchestrator

Steps:
1. Call Codex CLI:
   codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "Analyze and provide design recommendations for: {user_request}. Include architecture decisions, trade-offs, and implementation approach." 2>/dev/null

2. Save the full design analysis to: {output_path}

3. Return CONCISE summary:
   - Recommended architecture
   - Key trade-offs
   - Implementation steps'''

    def create_decision_template(
        self,
        task_id: str,
        user_request: str,
        gemini_summary: Optional[str] = None,
        codex_summary: Optional[str] = None,
    ) -> str:
        """
        Create template for final decision document.

        Args:
            task_id: Task ID
            user_request: Original user request
            gemini_summary: Summary from Gemini
            codex_summary: Summary from Codex

        Returns:
            Markdown template for decision document
        """
        timestamp = datetime.now().isoformat()

        gemini_section = gemini_summary or "_No research findings available_"
        codex_section = codex_summary or "_No design recommendations available_"

        return f'''# Decision: {task_id}

**Created:** {timestamp}
**Request:** {user_request}

## Research Findings (Gemini)

{gemini_section}

## Design Recommendations (Codex)

{codex_section}

## Final Decision

_Claude's synthesis and decision goes here_

## Action Items

- [ ] _Action item 1_
- [ ] _Action item 2_
'''

    def save_decision(
        self,
        task_id: str,
        content: str,
    ) -> Path:
        """
        Save final decision document.

        Args:
            task_id: Task ID
            content: Decision document content

        Returns:
            Path to saved decision file
        """
        decision_path = self.get_decision_path(task_id)
        decision_path.write_text(content)
        logger.info(f"Decision saved to: {decision_path}")
        return decision_path

    def read_agent_output(self, path: Path) -> Optional[str]:
        """
        Read agent output from file.

        Args:
            path: Path to output file

        Returns:
            File contents or None if not found
        """
        try:
            if path.exists():
                return path.read_text()
        except IOError as e:
            logger.warning(f"Failed to read agent output: {e}")
        return None

    def list_recent_tasks(self, limit: int = 10) -> List[str]:
        """
        List recent task IDs.

        Args:
            limit: Maximum number of tasks to return

        Returns:
            List of task IDs (most recent first)
        """
        tasks = set()

        for directory in [RESEARCH_DIR, DESIGN_DIR, DECISIONS_DIR]:
            if directory.exists():
                for file in directory.glob("task-*.md"):
                    task_id = file.stem
                    tasks.add(task_id)

        # Sort by timestamp in task ID (descending)
        sorted_tasks = sorted(tasks, reverse=True)
        return sorted_tasks[:limit]

    def cleanup_old_tasks(self, keep_days: int = 7) -> int:
        """
        Remove task files older than specified days.

        Args:
            keep_days: Number of days to keep

        Returns:
            Number of files removed
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=keep_days)
        removed = 0

        for directory in [RESEARCH_DIR, DESIGN_DIR, DECISIONS_DIR]:
            if directory.exists():
                for file in directory.glob("task-*.md"):
                    try:
                        # Parse date from task ID (task-YYYY-MM-DD-...)
                        parts = file.stem.split("-")
                        if len(parts) >= 4:
                            date_str = f"{parts[1]}-{parts[2]}-{parts[3]}"
                            file_date = datetime.strptime(date_str, "%Y-%m-%d")
                            if file_date < cutoff:
                                file.unlink()
                                removed += 1
                    except (ValueError, IndexError):
                        continue

        if removed > 0:
            logger.info(f"Cleaned up {removed} old task files")

        return removed
