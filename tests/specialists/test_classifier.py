"""Tests for hermes.specialists.router — classify() and fetch_kb_context().

Six tests cover:
1. classify() returns an IntentClassification
2. classify() selects a valid specialist name from the config
3. classify() confidence is in [0, 1]
4. classify() routes to default when LLM returns unknown intent
5. fetch_kb_context() returns a string
6. fetch_kb_context() returns empty string when specialist has no kb_sources
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from hermes.specialists.base import (
    IntentClassification,
    RouterConfig,
    SpecialistConfig,
)
from hermes.specialists.router import classify, fetch_kb_context


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

BILLING_SPECIALIST = SpecialistConfig(
    name="billing",
    description="Handles invoices, payments, and subscription questions.",
    triggers=["invoice", "payment", "subscription"],
    kb_sources=["https://kb.example.com/billing"],
)

SUPPORT_SPECIALIST = SpecialistConfig(
    name="technical_support",
    description="Assists with installation, configuration errors, and API issues.",
    triggers=["error", "install", "api"],
    kb_sources=["https://kb.example.com/support"],
)

GENERAL_SPECIALIST = SpecialistConfig(
    name="general",
    description="Fallback for anything that doesn't match another specialist.",
    triggers=[],
    kb_sources=[],
)


@pytest.fixture()
def router_config() -> RouterConfig:
    return RouterConfig(
        specialists=[BILLING_SPECIALIST, SUPPORT_SPECIALIST, GENERAL_SPECIALIST],
        default_specialist="general",
        classifier_model="claude-haiku-4-5-20251001",
        confidence_threshold=0.6,
    )


def _make_llm_response(intent: str, confidence: float, reasoning: str) -> MagicMock:
    """Build a minimal mock that mimics an Anthropic Messages API response."""
    payload = json.dumps(
        {"intent": intent, "confidence": confidence, "reasoning": reasoning}
    )
    content_block = MagicMock()
    content_block.text = payload
    response = MagicMock()
    response.content = [content_block]
    return response


# ---------------------------------------------------------------------------
# Test 1 — classify() returns an IntentClassification instance
# ---------------------------------------------------------------------------


def test_classify_returns_intent_classification(router_config: RouterConfig) -> None:
    mock_response = _make_llm_response("billing", 0.92, "User asked about invoice.")

    with patch("hermes.specialists.router._call_classifier", return_value=mock_response):
        result = classify("How do I get my invoice?", router_config)

    assert isinstance(result, IntentClassification)


# ---------------------------------------------------------------------------
# Test 2 — classify() returns a specialist name present in config
# ---------------------------------------------------------------------------


def test_classify_intent_is_valid_specialist(router_config: RouterConfig) -> None:
    valid_names = {s.name for s in router_config.specialists}
    mock_response = _make_llm_response("billing", 0.88, "Billing query.")

    with patch("hermes.specialists.router._call_classifier", return_value=mock_response):
        result = classify("When will my subscription renew?", router_config)

    assert result.intent in valid_names


# ---------------------------------------------------------------------------
# Test 3 — classify() confidence is within [0, 1]
# ---------------------------------------------------------------------------


def test_classify_confidence_in_range(router_config: RouterConfig) -> None:
    mock_response = _make_llm_response("technical_support", 0.75, "Error message query.")

    with patch("hermes.specialists.router._call_classifier", return_value=mock_response):
        result = classify("My installation keeps crashing.", router_config)

    assert 0.0 <= result.confidence <= 1.0


# ---------------------------------------------------------------------------
# Test 4 — classify() falls back to default when LLM returns unknown intent
# ---------------------------------------------------------------------------


def test_classify_unknown_intent_falls_back_to_default(
    router_config: RouterConfig,
) -> None:
    # LLM hallucinates a specialist name that doesn't exist in config
    mock_response = _make_llm_response("nonexistent_specialist", 0.80, "Unknown intent.")

    with patch("hermes.specialists.router._call_classifier", return_value=mock_response):
        result = classify("Something completely random.", router_config)

    assert result.intent == router_config.default_specialist


# ---------------------------------------------------------------------------
# Test 5 — fetch_kb_context() returns a string
# ---------------------------------------------------------------------------


def test_fetch_kb_context_returns_string(router_config: RouterConfig) -> None:
    with patch(
        "hermes.specialists.router._fetch_url",
        return_value="KB article content here.",
    ):
        result = fetch_kb_context("billing", router_config)

    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Test 6 — fetch_kb_context() returns empty string when no kb_sources
# ---------------------------------------------------------------------------


def test_fetch_kb_context_empty_when_no_sources(router_config: RouterConfig) -> None:
    # "general" specialist has no kb_sources
    result = fetch_kb_context("general", router_config)
    assert result == ""
