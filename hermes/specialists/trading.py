"""Trading specialist for market and trade-related queries."""

from hermes.specialists.base import BaseSpecialist


class TradingSpecialist(BaseSpecialist):
    """Handles queries about trading, stocks, and financial markets."""

    name = "trading"
    description = "Handles trading, stock market, and financial instrument queries"
    keywords = [
        "trade",
        "trading",
        "stock",
        "stocks",
        "market",
        "markets",
        "buy",
        "sell",
        "price",
        "ticker",
        "forex",
        "crypto",
        "equity",
        "equities",
        "share",
        "shares",
        "exchange",
        "broker",
        "portfolio",
        "dividend",
        "futures",
        "options",
    ]

    def handle(self, query: str) -> str:
        """Return a trading-domain response for *query*."""
        return f"[Trading] {query}"
