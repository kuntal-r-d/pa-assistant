#!/usr/bin/env python3
"""
UserPromptSubmit hook: Route to appropriate agent based on user intent.

Uses LLM-based classification (Gemini) with fallback to keyword matching.
Respects session mode settings (!solo, !consult, !auto, !codex, !gemini).

Modes:
- !solo (default): Claude + Claude subagents, no Codex/Gemini CLI
- !consult: Ask permission before consulting Codex/Gemini
- !auto: Auto-delegate to Codex/Gemini without prompts
- !codex: Only Codex consultation allowed
- !gemini: Only Gemini consultation allowed

Routing decisions:
- Codex: Design, debugging, code review, trade-off analysis
- Gemini: Research, documentation, codebase analysis, multimodal
- Perplexity: Only when explicitly mentioned (web research with citations)
"""

from __future__ import annotations

import json
import logging
import sys
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

# Add lib directory to path for imports
LIB_DIR = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(LIB_DIR))

try:
    from session_mode import (
        AgentMode,
        get_mode,
        set_mode,
        parse_mode_command,
        get_mode_description,
    )
    from intent_classifier import IntentClassifier, SuggestedAgent
    MODULES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Failed to import modules: {e}")
    MODULES_AVAILABLE = False


def get_confidence_label(confidence: float) -> str:
    """Get human-readable confidence label."""
    if confidence >= 0.7:
        return "high"
    elif confidence >= 0.5:
        return "medium"
    else:
        return "low"


def strip_mode_command(prompt: str) -> str:
    """Remove mode command prefix from prompt."""
    mode_prefixes = ["!solo", "!consult", "!auto", "!codex", "!gemini", "!ollama", "!local"]
    prompt_lower = prompt.lower().strip()

    for prefix in mode_prefixes:
        if prompt_lower.startswith(prefix):
            # Remove prefix and leading whitespace
            return prompt[len(prefix):].lstrip()

    return prompt


def create_confirmation_output(
    agent: str,
    confidence: float,
    detected_intent: str,
    reasoning: str,
    source: str,
) -> dict:
    """Create output that asks user for permission (CONSULT mode)."""
    confidence_label = get_confidence_label(confidence)

    if agent == "codex":
        agent_desc = "Codex for design/architecture recommendations"
    elif agent == "ollama":
        agent_desc = "Ollama (local model) for private/offline processing"
    else:
        agent_desc = "Gemini for research/documentation"

    confirmation_prompt = (
        f"[Agent Suggestion] This looks like a {detected_intent} task. "
        f"Would you like me to consult {agent_desc}? "
        f"(Confidence: {confidence_label}, {confidence:.0%}. Source: {source})\n\n"
        f"Options:\n"
        f"- Say 'yes' to consult {agent.capitalize()}\n"
        f"- Say 'no' to handle directly\n"
        f"- Use '!solo' to switch to solo mode (no more prompts)"
    )

    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": confirmation_prompt,
        }
    }


def create_auto_delegate_output(
    agent: str,
    confidence: float,
    detected_intent: str,
    reasoning: str,
    source: str,
) -> dict:
    """Create output for auto-delegation (AUTO mode)."""
    confidence_label = get_confidence_label(confidence)

    if agent == "codex":
        suggestion = (
            f"[Auto-Routing] Intent: {detected_intent}. "
            f"Consulting Codex CLI for recommendations. "
            f"(Confidence: {confidence_label}, {confidence:.0%}. Source: {source}. "
            f"Reason: {reasoning})"
        )
    elif agent == "ollama":
        suggestion = (
            f"[Auto-Routing] Intent: {detected_intent}. "
            f"Consulting Ollama (local model) for private processing. "
            f"(Confidence: {confidence_label}, {confidence:.0%}. Source: {source}. "
            f"Reason: {reasoning})"
        )
    else:
        suggestion = (
            f"[Auto-Routing] Intent: {detected_intent}. "
            f"Consulting Gemini CLI for research. "
            f"(Confidence: {confidence_label}, {confidence:.0%}. Source: {source}. "
            f"Reason: {reasoning})"
        )

    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": suggestion,
        }
    }


def create_mode_change_output(mode: AgentMode) -> dict:
    """Create output confirming mode change."""
    description = get_mode_description(mode)

    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": f"[Mode Changed] {description}",
        }
    }


def main():
    try:
        data = json.load(sys.stdin)
        prompt = data.get("prompt", "")

        # Skip very short prompts
        if len(prompt) < 5:
            sys.exit(0)

        # Check if modules are available
        if not MODULES_AVAILABLE:
            logger.warning("Modules not available, skipping routing")
            sys.exit(0)

        # Step 1: Check for mode command
        new_mode = parse_mode_command(prompt)
        if new_mode is not None:
            # Set the new mode
            set_mode(new_mode)

            # Output mode change confirmation
            output = create_mode_change_output(new_mode)
            print(json.dumps(output))

            # If prompt only contains mode command, exit
            remaining_prompt = strip_mode_command(prompt)
            if len(remaining_prompt) < 5:
                sys.exit(0)

            # Continue processing remaining prompt
            prompt = remaining_prompt

        # Step 2: Get current mode
        mode_config = get_mode()

        # Step 3: If SOLO mode, skip routing (no external LLM delegation)
        if mode_config.mode == AgentMode.SOLO:
            # No output needed - Claude handles with Claude subagents
            sys.exit(0)

        # Step 4: Classify intent (LLM with keyword fallback)
        classifier = IntentClassifier(timeout=3.5)
        classification = classifier.classify(prompt)

        # Step 5: Check if we should suggest delegation (0.12 = ~3 weight points)
        if not classification.should_delegate(min_confidence=0.12):
            # No strong signal, skip suggestion
            sys.exit(0)

        # Step 6: Check if suggested agent is allowed in current mode
        agent_name = classification.suggested_agent.value if classification.suggested_agent else None

        if agent_name and not mode_config.is_agent_allowed(agent_name):
            # Agent not allowed in current mode
            # Check if we should suggest the allowed agent instead
            if mode_config.mode == AgentMode.CODEX:
                agent_name = "codex"
            elif mode_config.mode == AgentMode.GEMINI:
                agent_name = "gemini"
            elif mode_config.mode in (AgentMode.OLLAMA, AgentMode.LOCAL):
                agent_name = "ollama"
            else:
                sys.exit(0)

        if not agent_name:
            sys.exit(0)

        # Step 7: Generate output based on mode
        if mode_config.should_ask_permission():
            # CONSULT mode or first delegation in CODEX/GEMINI mode
            output = create_confirmation_output(
                agent=agent_name,
                confidence=classification.confidence,
                detected_intent=classification.detected_intent,
                reasoning=classification.reasoning,
                source=classification.source,
            )

            # Mark first delegation done for single-agent modes
            if mode_config.mode in (AgentMode.CODEX, AgentMode.GEMINI, AgentMode.OLLAMA, AgentMode.LOCAL):
                mode_config.mark_first_delegation_done()

        else:
            # AUTO mode or subsequent delegations in CODEX/GEMINI mode
            output = create_auto_delegate_output(
                agent=agent_name,
                confidence=classification.confidence,
                detected_intent=classification.detected_intent,
                reasoning=classification.reasoning,
                source=classification.source,
            )

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
