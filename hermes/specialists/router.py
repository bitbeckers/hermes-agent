"""Router that dispatches queries to the correct specialist."""

from __future__ import annotations

from typing import Optional

from hermes.specialists.base import BaseSpecialist

# Default maximum routing depth to prevent infinite delegation loops.
DEFAULT_MAX_DEPTH: int = 5


class Router:
    """Route user queries to the most appropriate specialist.

    Attributes:
        specialists: Ordered list of specialists checked for each query.
        max_depth:   Maximum number of nested ``route()`` calls allowed
                     before a :class:`RecursionError` is raised (depth guard).
    """

    def __init__(
        self,
        specialists: list[BaseSpecialist],
        max_depth: int = DEFAULT_MAX_DEPTH,
    ) -> None:
        self.specialists = list(specialists)
        self.max_depth = max_depth
        self._depth: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def route(self, query: str) -> str:
        """Route *query* to the first specialist that can handle it.

        Returns the specialist's response, or a fallback string when no
        specialist matches.

        Raises:
            RecursionError: If the routing depth exceeds ``max_depth``.
        """
        if self._depth >= self.max_depth:
            raise RecursionError(
                f"Routing depth {self._depth} exceeds max_depth {self.max_depth}"
            )

        self._depth += 1
        try:
            for specialist in self.specialists:
                if specialist.can_handle(query):
                    return specialist.handle(query)
            return f"[Unmatched] {query}"
        finally:
            self._depth -= 1

    def handle_followup(self, query: str, context: dict) -> str:
        """Handle a follow-up question using prior-turn context.

        If *context* contains a ``"specialist"`` key, the query is sent
        directly to the named specialist (bypassing keyword matching).
        Otherwise the query is re-routed normally.

        Args:
            query:   The follow-up question text.
            context: A dict from the prior turn; may include a
                     ``"specialist"`` key naming the previously used
                     specialist.

        Returns:
            The specialist's (or router's) response string.
        """
        specialist_name: Optional[str] = context.get("specialist")
        if specialist_name:
            for specialist in self.specialists:
                if specialist.name == specialist_name:
                    return specialist.handle(query)
        return self.route(query)
