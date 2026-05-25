"""Finance specialist for financial analysis and accounting queries."""

from hermes.specialists.base import BaseSpecialist


class FinanceSpecialist(BaseSpecialist):
    """Handles queries about finance, budgeting, and accounting."""

    name = "finance"
    description = "Handles financial analysis, budgeting, accounting, and investment queries"
    keywords = [
        "finance",
        "financial",
        "budget",
        "budgeting",
        "tax",
        "taxes",
        "accounting",
        "investment",
        "revenue",
        "profit",
        "loss",
        "earnings",
        "expense",
        "expenses",
        "income",
        "cash flow",
        "balance sheet",
        "ledger",
        "audit",
        "fiscal",
        "roi",
        "return on investment",
    ]

    def handle(self, query: str) -> str:
        """Return a finance-domain response for *query*."""
        return f"[Finance] {query}"
