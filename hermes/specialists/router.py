"""Hermes Specialist Router — LLM-powered intent classification and KB retrieval.

Public API
----------
classify(user_message, config)  → IntentClassification
fetch_kb_context(intent, config) → str

Internal helpers (patched in tests)
------------------------------------
_call_classifier(prompt, model)  → Anthropic Messages API response object
_fetch_url(url)                  → str
"""

from __future__ import annotations

import json
import logging
from typing import Any

from hermes.specialists.base import IntentClassification, RouterConfig, SpecialistConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Classifier prompt
# ---------------------------------------------------------------------------

CLASSIFIER_PROMPT = """\
You are a routing assistant.  Given a user message and a list of specialists,
return a JSON object (with no additional text) that selects the most appropriate
specialist.

Specialists:
{specialists_block}

User message:
{user_message}

Respond with ONLY a JSON object in this exact format:
{{
  "intent": "<specialist name>",
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<one-sentence explanation>"
}}
"""

# ---------------------------------------------------------------------------
# Internal helpers — these thin wrappers exist so unit tests can patch them
# ---------------------------------------------------------------------------


def _call_classifier(prompt: str, model: str) -> Any:
    """Call the Anthropic Messages API and return the raw response object.

    Isolated into its own function so tests can replace it with a mock
    without needing a real API key.
    """
    try:
        import anthropic  # type: ignore[import]
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "The 'anthropic' package is required for classify().  "
            "Install it with: pip install anthropic"
        ) from exc

    client = anthropic.Anthropic()
    return client.messages.create(
        model=model,
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )


def _fetch_url(url: str) -> str:
    """Fetch text content from a URL or local path.

    Isolated for easy mocking in tests.
    """
    import urllib.request

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310
            return resp.read().decode("utf-8", errors="replace")
    except Exception as exc:  # pragma: no cover
        logger.warning("fetch_kb_context: could not fetch %r: %s", url, exc)
        return ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _build_specialists_block(specialists: list[SpecialistConfig]) -> str:
    """Render the specialists list for injection into CLASSIFIER_PROMPT."""
    lines: list[str] = []
    for spec in specialists:
        lines.append(f"- name: {spec.name}")
        lines.append(f"  description: {spec.description}")
        if spec.triggers:
            lines.append(f"  triggers: {', '.join(spec.triggers)}")
    return "\n".join(lines)


def _parse_classifier_response(
    response: Any,
    config: RouterConfig,
) -> IntentClassification:
    """Extract and validate IntentClassification from the LLM response."""
    raw_text = response.content[0].text.strip()

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        logger.warning(
            "classify: LLM returned non-JSON response, falling back to default. "
            "Raw text: %r",
            raw_text,
        )
        return IntentClassification(
            intent=config.default_specialist or "general",
            confidence=0.0,
            reasoning="LLM response was not valid JSON.",
        )

    intent: str = str(data.get("intent", "")).strip()
    reasoning: str = str(data.get("reasoning", "")).strip()

    # Clamp confidence to [0, 1]
    try:
        confidence = float(data.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    # Validate that the returned intent is a known specialist
    valid_names = {s.name for s in config.specialists}
    if intent not in valid_names:
        logger.warning(
            "classify: LLM returned unknown intent %r, falling back to default %r",
            intent,
            config.default_specialist,
        )
        intent = config.default_specialist or "general"
        confidence = 0.0

    return IntentClassification(
        intent=intent,
        confidence=confidence,
        reasoning=reasoning,
    )


def classify(user_message: str, config: RouterConfig) -> IntentClassification:
    """Classify *user_message* into one of the specialists defined in *config*.

    The function builds a prompt from :data:`CLASSIFIER_PROMPT`, calls the
    Anthropic Messages API via :func:`_call_classifier`, parses the JSON
    response, and validates the returned intent against the configured
    specialists.

    If the LLM returns an intent that is not in *config.specialists*, or if the
    response is not valid JSON, the function falls back to
    ``config.default_specialist``.

    Args:
        user_message: The raw text message from the user.
        config: Router configuration, including the list of specialists and the
            classifier model name.

    Returns:
        An :class:`~hermes.specialists.base.IntentClassification` with the
        selected intent, a confidence score in ``[0, 1]``, and the model's
        reasoning.
    """
    specialists_block = _build_specialists_block(config.specialists)
    prompt = CLASSIFIER_PROMPT.format(
        specialists_block=specialists_block,
        user_message=user_message,
    )

    response = _call_classifier(prompt, config.classifier_model)
    return _parse_classifier_response(response, config)


def fetch_kb_context(intent: str, config: RouterConfig) -> str:
    """Retrieve knowledge-base context for the given *intent*.

    Looks up the :class:`~hermes.specialists.base.SpecialistConfig` whose
    ``name`` matches *intent*, then fetches each URL listed in
    ``kb_sources``, joining the results with a double newline separator.

    If *intent* is not found in *config.specialists*, or if the matched
    specialist has no ``kb_sources``, an empty string is returned.

    When ``config.kb_base_url`` is set, it is prepended to any source path
    that does not already start with a URL scheme (``http://`` / ``https://``).

    Args:
        intent: The canonical specialist name (matches
            :attr:`~hermes.specialists.base.SpecialistConfig.name`).
        config: Router configuration.

    Returns:
        A string of retrieved KB content, or ``""`` when no sources are
        configured or all fetches fail.
    """
    # Find the matching specialist
    matched: SpecialistConfig | None = None
    for spec in config.specialists:
        if spec.name == intent:
            matched = spec
            break

    if matched is None or not matched.kb_sources:
        return ""

    snippets: list[str] = []
    for source in matched.kb_sources:
        url = source
        if (
            config.kb_base_url
            and not source.startswith("http://")
            and not source.startswith("https://")
        ):
            url = config.kb_base_url.rstrip("/") + "/" + source.lstrip("/")

        content = _fetch_url(url)
        if content:
            snippets.append(content)

    return "\n\n".join(snippets)
