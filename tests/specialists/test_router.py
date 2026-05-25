"""Tests for hermes.specialists.router — Router (T012)."""

import pytest

from hermes.specialists.finance import FinanceSpecialist
from hermes.specialists.router import DEFAULT_MAX_DEPTH, Router
from hermes.specialists.trading import TradingSpecialist


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def trading() -> TradingSpecialist:
    return TradingSpecialist()


@pytest.fixture()
def finance() -> FinanceSpecialist:
    return FinanceSpecialist()


@pytest.fixture()
def router(trading, finance) -> Router:
    return Router([trading, finance])


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_router_init(trading, finance):
    """Router stores the provided specialists list."""
    r = Router([trading, finance])
    assert r.specialists == [trading, finance]


def test_router_default_max_depth(trading):
    """Router uses DEFAULT_MAX_DEPTH when max_depth is not supplied."""
    r = Router([trading])
    assert r.max_depth == DEFAULT_MAX_DEPTH


def test_route_to_trading_specialist(router):
    """route() dispatches a stock-price query to TradingSpecialist."""
    result = router.route("What is the stock price of GOOG?")
    assert "[Trading]" in result


def test_route_to_finance_specialist(router):
    """route() dispatches a budget query to FinanceSpecialist."""
    result = router.route("Can you help me review my annual budget?")
    assert "[Finance]" in result


def test_route_unmatched_query_returns_fallback(router):
    """route() returns a non-empty fallback string when no specialist matches."""
    result = router.route("Tell me a joke about penguins.")
    assert isinstance(result, str)
    assert len(result) > 0


def test_handle_followup_with_specialist_context(router):
    """handle_followup() uses the specialist named in context, skipping routing."""
    context = {"specialist": "trading"}
    result = router.handle_followup("What about MSFT?", context)
    assert "[Trading]" in result


def test_handle_followup_without_context_routes(router):
    """handle_followup() falls back to route() when context has no specialist."""
    result = router.handle_followup("What is the current tax rate?", context={})
    assert "[Finance]" in result


def test_depth_guard_raises_on_exceeded_depth(trading):
    """route() raises RecursionError when routing depth exceeds max_depth."""
    r = Router([trading], max_depth=0)
    with pytest.raises(RecursionError):
        r.route("buy AAPL")


def test_first_matching_specialist_wins(trading, finance):
    """When multiple specialists match, the first one in the list handles it."""
    # Give finance a keyword that also exists in trading to force a tie.
    finance.keywords = ["stock"]
    r = Router([trading, finance])
    result = r.route("stock market outlook")
    # TradingSpecialist is first — it must win.
    assert "[Trading]" in result
