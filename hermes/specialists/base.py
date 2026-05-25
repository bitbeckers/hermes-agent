"""Core data models and abstract base class for the Hermes Specialist Router."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class IntentClassification:
    """Result of classifying a user message into a routing intent.

    Attributes:
        intent: Canonical intent name matching a SpecialistConfig.name (or
            ``"default"`` when no specialist matched).
        confidence: Float in [0, 1] — model's confidence in the classification.
        reasoning: Free-text explanation produced by the classifier.
    """

    intent: str
    confidence: float
    reasoning: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"confidence must be in [0, 1], got {self.confidence!r}"
            )


@dataclass
class HandoffPacket:
    """Data bundle passed from the router to a specialist.

    Attributes:
        user_message: The raw user message that triggered routing.
        intent: Classifier output for this message.
        kb_context: Knowledge-base text retrieved for the intent (may be empty).
        history: Prior conversation turns as a list of ``{"role": ..., "content": ...}``
            dicts (most-recent-last ordering).
        metadata: Arbitrary key/value pairs for specialist-specific context.
    """

    user_message: str
    intent: IntentClassification
    kb_context: str = ""
    history: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SpecialistResult:
    """Response produced by a specialist after handling a HandoffPacket.

    Attributes:
        response: The specialist's textual reply to the user.
        specialist_name: Name of the specialist that handled the request.
        metadata: Arbitrary key/value pairs for downstream consumption.
    """

    response: str
    specialist_name: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SpecialistConfig:
    """Static configuration for a single specialist.

    Attributes:
        name: Unique identifier used as the ``intent`` value returned by the
            classifier (e.g. ``"billing"``, ``"technical_support"``).
        description: Human-readable description shown to the classifier prompt
            so the LLM understands when to route here.
        triggers: Optional list of keyword hints.  These supplement the
            description but are *not* used for hard keyword matching.
        kb_sources: List of knowledge-base source URLs or file paths that
            ``fetch_kb_context()`` should query for this specialist.
    """

    name: str
    description: str
    triggers: list[str] = field(default_factory=list)
    kb_sources: list[str] = field(default_factory=list)


@dataclass
class RouterConfig:
    """Top-level configuration for the Hermes Specialist Router.

    Attributes:
        specialists: Ordered list of specialist configurations.
        default_specialist: Name of the fallback specialist when confidence is
            below ``confidence_threshold``, or ``None`` to return the low-
            confidence result as-is.
        classifier_model: Model identifier used by ``classify()``.
        confidence_threshold: Minimum confidence required to route to a
            specialist rather than the default.
        kb_base_url: Optional base URL prepended to relative ``kb_sources``
            entries.
    """

    specialists: list[SpecialistConfig] = field(default_factory=list)
    default_specialist: str | None = None
    classifier_model: str = "claude-haiku-4-5-20251001"
    confidence_threshold: float = 0.6
    kb_base_url: str | None = None


class BaseSpecialist(ABC):
    """Abstract base class that every specialist must extend.

    Subclasses implement :meth:`handle` to process a
    :class:`HandoffPacket` and return a :class:`SpecialistResult`.
    """

    def __init__(self, config: SpecialistConfig) -> None:
        self.config = config

    @property
    def name(self) -> str:
        """Shortcut for ``self.config.name``."""
        return self.config.name

    @abstractmethod
    def handle(self, packet: HandoffPacket) -> SpecialistResult:
        """Process a routed request and produce a response.

        Args:
            packet: The :class:`HandoffPacket` assembled by the router.

        Returns:
            A :class:`SpecialistResult` containing the specialist's reply.
        """
