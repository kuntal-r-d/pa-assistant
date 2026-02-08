"""
LLM-based intent classification for agent routing.

Uses Gemini CLI for fast intent classification with fallback to keyword matching.

Usage:
    from lib.intent_classifier import IntentClassifier

    classifier = IntentClassifier()
    result = classifier.classify("Help me design a new API")

    print(result.suggested_agent)  # "codex"
    print(result.confidence)       # 0.85
    print(result.reasoning)        # "Design task requiring architecture decisions"
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class SuggestedAgent(Enum):
    """Agents that can be suggested for delegation."""
    CODEX = "codex"
    GEMINI = "gemini"
    OLLAMA = "ollama"  # Free/local models
    DIRECT = "direct"  # No delegation needed


@dataclass
class IntentClassification:
    """Result of intent classification."""
    suggested_agent: Optional[SuggestedAgent]
    confidence: float  # 0.0 - 1.0
    reasoning: str
    detected_intent: str
    source: str  # "llm" or "keyword"

    def should_delegate(self, min_confidence: float = 0.5) -> bool:
        """Check if delegation is recommended based on confidence."""
        return (
            self.suggested_agent is not None
            and self.suggested_agent != SuggestedAgent.DIRECT
            and self.confidence >= min_confidence
        )


# Weighted triggers for keyword fallback (from existing agent-router.py)
CODEX_TRIGGERS = {
    # Design & Architecture
    "design": 3, "architecture": 3, "architect": 3, "pattern": 3, "structure": 2,
    # Debugging
    "debug": 3, "error": 2, "bug": 3, "fix": 2, "broken": 2, "not working": 3, "fails": 2,
    # Analysis
    "compare": 2, "trade-off": 2, "tradeoff": 2, "analyze": 2, "which is better": 3,
    # Implementation
    "how to implement": 3, "implementation": 2, "refactor": 2, "simplify": 2,
    # Review
    "review": 2, "check this": 2,
    # Explicit triggers
    "think deeper": 4, "codex": 4, "second opinion": 4, "deeply": 3,
    # New triggers for better detection
    "build": 2, "create": 2, "develop": 2, "implement": 2, "feature": 2,
    "api": 2, "system": 2, "application": 2, "app": 2, "service": 2,
}

GEMINI_TRIGGERS = {
    # Research
    "research": 3, "investigate": 3, "look up": 3, "find out": 2,
    # Documentation
    "documentation": 2, "docs": 2, "library": 2, "package": 2, "framework": 2, "latest": 2,
    # Multimodal
    "pdf": 4, "video": 4, "audio": 4, "image": 3,
    # Large context
    "entire codebase": 4, "whole repository": 4, "all files": 3, "repository": 2,
    # Explicit triggers
    "gemini": 4,
}

OLLAMA_TRIGGERS = {
    # Explicit triggers for local/free models
    "ollama": 4, "local": 3, "local model": 4, "free": 2, "private": 3,
    "offline": 3, "self-hosted": 4, "on-device": 4,
    # Privacy-focused
    "confidential": 3, "sensitive": 2, "no cloud": 4, "air-gapped": 4,
    # Specific local models
    "llama": 4, "mistral": 4, "codellama": 4, "deepseek": 4, "qwen": 4,
    "phi": 3, "gemma": 3, "vicuna": 3, "openchat": 3,
}


class IntentClassifier:
    """
    LLM-based intent classifier using Gemini CLI.

    Falls back to keyword matching if LLM call fails or times out.
    """

    CLASSIFICATION_PROMPT = '''Classify this user request and suggest the best AI agent to consult.

User request: "{prompt}"

Available agents:
- CODEX: Best for design decisions, architecture, debugging, code review, trade-off analysis, implementation planning
- GEMINI: Best for research, documentation lookup, library comparison, codebase analysis, multimodal (PDF/video/audio)
- OLLAMA: Best for privacy-sensitive tasks, offline work, or when user explicitly wants local/free models (llama, mistral, etc.)
- DIRECT: For simple tasks that don't need external consultation (file edits, commands, clear instructions)

Respond with JSON only (no other text):
{{"suggested_agent": "CODEX" or "GEMINI" or "OLLAMA" or "DIRECT", "confidence": 0.0 to 1.0, "reasoning": "brief explanation (max 15 words)", "detected_intent": "design" or "debug" or "research" or "implement" or "review" or "analyze" or "private" or "simple"}}'''

    def __init__(self, timeout: float = 3.5, use_circuit_breaker: bool = True):
        """
        Initialize classifier.

        Args:
            timeout: Timeout for Gemini CLI call in seconds
            use_circuit_breaker: Whether to use circuit breaker for resilience
        """
        self.timeout = timeout
        self.circuit_breaker = None

        if use_circuit_breaker:
            try:
                from .circuit_breaker import GEMINI_CIRCUIT
                self.circuit_breaker = GEMINI_CIRCUIT
            except ImportError:
                logger.warning("Circuit breaker not available, proceeding without")

    def classify(self, prompt: str) -> IntentClassification:
        """
        Classify user intent.

        Tries LLM classification first, falls back to keyword matching on failure.

        Args:
            prompt: User's input prompt

        Returns:
            IntentClassification with suggested agent and confidence
        """
        # Skip very short prompts
        if len(prompt.strip()) < 10:
            return IntentClassification(
                suggested_agent=None,
                confidence=0.0,
                reasoning="Prompt too short for classification",
                detected_intent="none",
                source="skip",
            )

        # Try LLM classification if circuit is closed
        if self.circuit_breaker is None or self.circuit_breaker.is_closed:
            try:
                result = self._classify_with_llm(prompt)
                if result:
                    if self.circuit_breaker:
                        # Record success
                        pass  # Circuit breaker handles this internally
                    return result
            except Exception as e:
                logger.warning(f"LLM classification failed: {e}")
                if self.circuit_breaker:
                    self.circuit_breaker._on_failure(e)

        # Fallback to keyword matching
        return self._classify_with_keywords(prompt)

    def _classify_with_llm(self, prompt: str) -> Optional[IntentClassification]:
        """
        Call Gemini CLI for intent classification.

        Args:
            prompt: User's input prompt

        Returns:
            IntentClassification or None on failure
        """
        # Truncate prompt to avoid context issues
        # No shell escaping needed - using list-based subprocess for security
        truncated_prompt = prompt[:500].replace('\n', ' ')

        classification_prompt = self.CLASSIFICATION_PROMPT.format(prompt=truncated_prompt)

        # Use list-based subprocess (secure - no shell injection possible)
        cmd = ["gemini", "-p", classification_prompt]

        try:
            result = subprocess.run(
                cmd,
                shell=False,  # SECURE: No shell interpretation
                capture_output=True,
                text=True,
                timeout=self.timeout,
                stderr=subprocess.DEVNULL,  # Suppress stderr
            )

            if result.returncode != 0:
                logger.debug(f"Gemini returned non-zero: {result.returncode}")
                return None

            response_text = result.stdout.strip()
            if not response_text:
                return None

            # Extract JSON from response
            json_str = self._extract_json(response_text)
            if not json_str:
                logger.debug(f"No JSON found in response: {response_text[:100]}")
                return None

            data = json.loads(json_str)

            # Parse agent
            agent_str = data.get("suggested_agent", "DIRECT").upper()
            if agent_str == "CODEX":
                agent = SuggestedAgent.CODEX
            elif agent_str == "GEMINI":
                agent = SuggestedAgent.GEMINI
            elif agent_str == "OLLAMA":
                agent = SuggestedAgent.OLLAMA
            else:
                agent = SuggestedAgent.DIRECT

            return IntentClassification(
                suggested_agent=agent if agent != SuggestedAgent.DIRECT else None,
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", "LLM classification"),
                detected_intent=data.get("detected_intent", "unknown"),
                source="llm",
            )

        except subprocess.TimeoutExpired:
            logger.warning(f"Gemini classification timed out after {self.timeout}s")
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Gemini response as JSON: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error in LLM classification: {e}")
            return None

    def _extract_json(self, text: str) -> Optional[str]:
        """
        Extract JSON object from text that may contain other content.

        Args:
            text: Response text potentially containing JSON

        Returns:
            JSON string or None
        """
        # Find JSON object boundaries
        start = text.find('{')
        if start == -1:
            return None

        # Find matching closing brace
        depth = 0
        for i, char in enumerate(text[start:], start):
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]

        return None

    def _classify_with_keywords(self, prompt: str) -> IntentClassification:
        """
        Fallback keyword-based classification.

        Uses weighted scoring from existing agent-router logic.

        Args:
            prompt: User's input prompt

        Returns:
            IntentClassification based on keyword matching
        """
        codex_score, codex_triggers = self._calculate_score(prompt, CODEX_TRIGGERS)
        gemini_score, gemini_triggers = self._calculate_score(prompt, GEMINI_TRIGGERS)
        ollama_score, ollama_triggers = self._calculate_score(prompt, OLLAMA_TRIGGERS)

        # Lower threshold since we added more trigger words (0.12 = ~3 weight points)
        MIN_CONFIDENCE = 0.12

        # Find the highest scoring agent
        scores = [
            (ollama_score, SuggestedAgent.OLLAMA, ollama_triggers),  # Ollama first (privacy preference)
            (codex_score, SuggestedAgent.CODEX, codex_triggers),
            (gemini_score, SuggestedAgent.GEMINI, gemini_triggers),
        ]

        # Sort by score (descending)
        scores.sort(key=lambda x: x[0], reverse=True)
        best_score, best_agent, best_triggers = scores[0]

        if best_score >= MIN_CONFIDENCE:
            return IntentClassification(
                suggested_agent=best_agent,
                confidence=best_score,
                reasoning=f"Matched keywords: {', '.join(best_triggers[:3])}",
                detected_intent="keyword_match",
                source="keyword",
            )

        # Check for ties between top 2
        if len(scores) > 1 and scores[0][0] == scores[1][0] and scores[0][0] >= MIN_CONFIDENCE:
            # Tie-breaker: prefer Ollama (privacy) > Codex (implementation) > Gemini
            return IntentClassification(
                suggested_agent=scores[0][1],
                confidence=scores[0][0],
                reasoning="Tie-breaker: defaulting based on priority",
                detected_intent="keyword_match",
                source="keyword",
            )

        return IntentClassification(
            suggested_agent=None,
            confidence=0.0,
            reasoning="No strong signal detected",
            detected_intent="none",
            source="keyword",
        )

    def _calculate_score(
        self, prompt: str, triggers: dict
    ) -> Tuple[float, List[str]]:
        """
        Calculate weighted score for trigger matches.

        Args:
            prompt: User's input prompt
            triggers: Dictionary of trigger words and weights

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
