"""Abstract base class for Hermes specialists."""

from abc import ABC, abstractmethod


class BaseSpecialist(ABC):
    """Abstract base for all Hermes domain specialists.

    Subclasses declare a ``name``, ``description``, and a list of
    ``keywords`` that determine whether this specialist can handle a query.
    They must also implement ``handle()`` to produce a response.
    """

    name: str = ""
    description: str = ""
    keywords: list[str] = []

    def can_handle(self, query: str) -> bool:
        """Return True if this specialist can handle *query*.

        The default implementation does a case-insensitive substring search
        for any keyword in the query text.
        """
        q = query.lower()
        return any(kw in q for kw in self.keywords)

    @abstractmethod
    def handle(self, query: str) -> str:
        """Process *query* and return a plain-text response."""
        ...
