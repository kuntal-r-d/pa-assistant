#!/usr/bin/env python3
"""
UserPromptSubmit hook: Route to appropriate agent based on user intent.

Analyzes user prompts and suggests the most appropriate agent
(Codex for design/debug, Gemini for research/multimodal).
"""

import json
import sys

# Triggers for Codex (design, debugging, deep reasoning)
CODEX_TRIGGERS = [
    "design", "architecture", "architect",
    "debug", "error", "bug", "not working", "fails",
    "compare", "trade-off", "tradeoff", "which is better",
    "how to implement", "implementation",
    "refactor", "simplify",
    "review", "check this",
    "think", "analyze", "deeply",
]

# Triggers for Gemini (research, multimodal, large context)
GEMINI_TRIGGERS = [
    "research", "investigate", "look up", "find out",
    "pdf", "video", "audio", "image",
    "entire codebase", "whole repository",
    "latest", "documentation", "docs",
    "library", "package", "framework",
]


def detect_agent(prompt: str) -> tuple[str | None, str]:
    """Detect which agent should handle this prompt."""
    prompt_lower = prompt.lower()

    # Check Codex triggers
    for trigger in CODEX_TRIGGERS:
        if trigger in prompt_lower:
            return "codex", trigger

    # Check Gemini triggers
    for trigger in GEMINI_TRIGGERS:
        if trigger in prompt_lower:
            return "gemini", trigger

    return None, ""


def main():
    try:
        data = json.load(sys.stdin)
        prompt = data.get("prompt", "")

        # Skip short prompts
        if len(prompt) < 10:
            sys.exit(0)

        agent, trigger = detect_agent(prompt)

        if agent == "codex":
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": (
                        f"[Agent Routing] Detected '{trigger}' - this task may benefit from "
                        "Codex CLI's deep reasoning capabilities. Consider: "
                        "`codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "
                        '"{task description}"` for design decisions, debugging, or complex analysis.'
                    )
                }
            }
            print(json.dumps(output))

        elif agent == "gemini":
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": (
                        f"[Agent Routing] Detected '{trigger}' - this task may benefit from "
                        "Gemini CLI's research capabilities. Consider: "
                        '`gemini -p "Research: {topic}" 2>/dev/null` '
                        "for documentation, library research, or multimodal content."
                    )
                }
            }
            print(json.dumps(output))

        sys.exit(0)

    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
