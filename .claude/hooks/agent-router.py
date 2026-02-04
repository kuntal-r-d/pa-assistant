#!/usr/bin/env python3
"""
UserPromptSubmit hook: Route to appropriate agent based on user intent.

Uses weighted scoring to determine confidence level for routing suggestions.
Supports manual override patterns (!codex, !gemini, !direct).

Routing decisions:
- Codex: Design, debugging, code review, trade-off analysis
- Gemini: Research, documentation, codebase analysis, multimodal
"""

from __future__ import annotations

import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Setup logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOG_DIR / "hook-errors.log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.WARNING,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("agent-router")


@dataclass
class RoutingDecision:
    """Result of routing analysis."""
    agent: Optional[str]
    confidence: float  # 0.0 - 1.0
    triggers: list[str]
    reason: str


# Weighted triggers for Codex (design, debugging, deep reasoning)
# Higher weight = stronger signal
CODEX_TRIGGERS = {
    # Design & Architecture (weight: 3)
    "design": 3,
    "architecture": 3,
    "architect": 3,
    "pattern": 3,
    "structure": 2,
    # Debugging (weight: 3)
    "debug": 3,
    "error": 2,
    "bug": 3,
    "fix": 2,
    "broken": 2,
    "not working": 3,
    "fails": 2,
    # Analysis (weight: 2)
    "compare": 2,
    "trade-off": 2,
    "tradeoff": 2,
    "analyze": 2,
    "which is better": 3,
    # Implementation (weight: 2)
    "how to implement": 3,
    "implementation": 2,
    "refactor": 2,
    "simplify": 2,
    # Review (weight: 2)
    "review": 2,
    "check this": 2,
    # Explicit triggers (weight: 4)
    "think deeper": 4,
    "codex": 4,
    "second opinion": 4,
    "deeply": 3,
}

# Weighted triggers for Gemini (research, multimodal, large context)
GEMINI_TRIGGERS = {
    # Research (weight: 3)
    "research": 3,
    "investigate": 3,
    "look up": 3,
    "find out": 2,
    # Documentation (weight: 2)
    "documentation": 2,
    "docs": 2,
    "library": 2,
    "package": 2,
    "framework": 2,
    "latest": 2,
    # Multimodal (weight: 4)
    "pdf": 4,
    "video": 4,
    "audio": 4,
    "image": 3,
    # Large context (weight: 3)
    "entire codebase": 4,
    "whole repository": 4,
    "all files": 3,
    "repository": 2,
    # Explicit triggers (weight: 4)
    "gemini": 4,
}

# Override patterns (bypass scoring)
OVERRIDE_PATTERNS = {
    r"^!codex\b": ("codex", "Manual override: !codex"),
    r"^!gemini\b": ("gemini", "Manual override: !gemini"),
    r"^!direct\b": (None, "Manual override: !direct (skip suggestion)"),
}

# Confidence threshold for showing suggestions
MIN_CONFIDENCE = 0.30  # 30%


def calculate_score(prompt: str, triggers: dict) -> tuple[float, list[str]]:
    """
    Calculate weighted score for trigger matches.

    Returns:
        (score, matched_triggers) - Score normalized to 0-1 range
    """
    prompt_lower = prompt.lower()
    total_possible = sum(triggers.values())
    matched_weight = 0
    matched_triggers = []

    for trigger, weight in triggers.items():
        if trigger in prompt_lower:
            matched_weight += weight
            matched_triggers.append(trigger)

    # Normalize score (cap at 1.0)
    # Use 30% of total weight as the max to make scoring more sensitive
    score = min(matched_weight / (total_possible * 0.3), 1.0)
    return score, matched_triggers


def detect_agent(prompt: str) -> RoutingDecision:
    """
    Detect which agent should handle this prompt.

    Uses weighted scoring with confidence levels.
    """
    # Check for manual overrides first
    for pattern, (agent, reason) in OVERRIDE_PATTERNS.items():
        if re.match(pattern, prompt, re.IGNORECASE):
            return RoutingDecision(
                agent=agent,
                confidence=1.0,
                triggers=[],
                reason=reason
            )

    # Calculate scores for each agent
    codex_score, codex_triggers = calculate_score(prompt, CODEX_TRIGGERS)
    gemini_score, gemini_triggers = calculate_score(prompt, GEMINI_TRIGGERS)

    # Determine winner
    if codex_score > gemini_score and codex_score >= MIN_CONFIDENCE:
        return RoutingDecision(
            agent="codex",
            confidence=codex_score,
            triggers=codex_triggers,
            reason=f"Matched {len(codex_triggers)} Codex trigger(s)"
        )
    elif gemini_score > codex_score and gemini_score >= MIN_CONFIDENCE:
        return RoutingDecision(
            agent="gemini",
            confidence=gemini_score,
            triggers=gemini_triggers,
            reason=f"Matched {len(gemini_triggers)} Gemini trigger(s)"
        )
    elif codex_score == gemini_score and codex_score >= MIN_CONFIDENCE:
        # Tie-breaker: prefer Codex for implementation tasks
        return RoutingDecision(
            agent="codex",
            confidence=codex_score,
            triggers=codex_triggers,
            reason="Tie-breaker: defaulting to Codex"
        )

    # No strong signal
    return RoutingDecision(
        agent=None,
        confidence=0.0,
        triggers=[],
        reason="No strong routing signal detected"
    )


def get_confidence_label(confidence: float) -> str:
    """Get human-readable confidence label."""
    if confidence >= 0.7:
        return "high"
    elif confidence >= 0.5:
        return "medium"
    else:
        return "low"


def main():
    try:
        data = json.load(sys.stdin)
        prompt = data.get("prompt", "")

        # Skip very short prompts
        if len(prompt) < 10:
            sys.exit(0)

        decision = detect_agent(prompt)

        # Only suggest if we have a decision with sufficient confidence
        if decision.agent and decision.confidence >= MIN_CONFIDENCE:
            confidence_label = get_confidence_label(decision.confidence)
            confidence_pct = f"{decision.confidence:.0%}"
            triggers_str = ", ".join(decision.triggers[:5])  # Limit to 5 triggers

            if decision.agent == "codex":
                suggestion = (
                    f"[Agent Routing] {decision.reason} "
                    f"(confidence: {confidence_label}, {confidence_pct}). "
                    f"Triggers: {triggers_str}. "
                    f"This task may benefit from Codex CLI's deep reasoning. "
                    f"Consider: `codex exec --model gpt-5.2-codex --sandbox read-only --full-auto \"...\"` "
                    f"Override with !direct to skip."
                )
            else:  # gemini
                suggestion = (
                    f"[Agent Routing] {decision.reason} "
                    f"(confidence: {confidence_label}, {confidence_pct}). "
                    f"Triggers: {triggers_str}. "
                    f"This task may benefit from Gemini CLI's research capabilities. "
                    f"Consider: `gemini -p \"...\" 2>/dev/null` "
                    f"Override with !direct to skip."
                )

            output = {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": suggestion
                }
            }
            print(json.dumps(output))

        sys.exit(0)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON input: {e}")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Hook error: {e}", exc_info=True)
        sys.exit(0)


if __name__ == "__main__":
    main()
