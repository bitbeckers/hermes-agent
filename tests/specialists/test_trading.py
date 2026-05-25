"""Tests for hermes.specialists.trading — TradingSpecialist (T008)."""

import pytest

from hermes.specialists.base import BaseSpecialist
from hermes.specialists.trading import TradingSpecialist


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def specialist() -> TradingSpecialist:
    return TradingSpecialist()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_trading_specialist_is_base_specialist(specialist):
    """TradingSpecialist must be a concrete subclass of BaseSpecialist."""
    assert isinstance(specialist, BaseSpecialist)


def test_trading_specialist_name(specialist):
    """TradingSpecialist.name must be 'trading'."""
    assert specialist.name == "trading"


def test_can_handle_stock_query(specialist):
    """can_handle() returns True for a query about stock prices."""
    assert specialist.can_handle("What is the current stock price of AAPL?") is True


def test_cannot_handle_unrelated_query(specialist):
    """can_handle() returns False for a clearly unrelated query."""
    assert specialist.can_handle("What is the weather in London today?") is False


def test_handle_returns_string_response(specialist):
    """handle() returns a non-empty string for any trading query."""
    result = specialist.handle("Should I buy TSLA shares today?")
    assert isinstance(result, str)
    assert len(result) > 0
