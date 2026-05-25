"""Tests for hermes.specialists.finance — FinanceSpecialist (T010)."""

import pytest

from hermes.specialists.base import BaseSpecialist
from hermes.specialists.finance import FinanceSpecialist


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def specialist() -> FinanceSpecialist:
    return FinanceSpecialist()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_finance_specialist_is_base_specialist(specialist):
    """FinanceSpecialist must be a concrete subclass of BaseSpecialist."""
    assert isinstance(specialist, BaseSpecialist)


def test_finance_specialist_name(specialist):
    """FinanceSpecialist.name must be 'finance'."""
    assert specialist.name == "finance"


def test_can_handle_budget_query(specialist):
    """can_handle() returns True for a query about budgets."""
    assert specialist.can_handle("How should I manage my quarterly budget?") is True


def test_cannot_handle_coding_query(specialist):
    """can_handle() returns False for a programming query."""
    assert specialist.can_handle("How do I write a Python for-loop?") is False


def test_handle_returns_string_response(specialist):
    """handle() returns a non-empty string for any finance query."""
    result = specialist.handle("What is the ROI on this investment?")
    assert isinstance(result, str)
    assert len(result) > 0
