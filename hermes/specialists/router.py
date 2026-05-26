"""Router that dispatches queries to the correct specialist."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional

from hermes.specialists.base import BaseSpecialist

if TYPE_CHECKING:
    from hermes.specialists.config import RouterConfig

# Default maximum routing depth to prevent infinite delegation loops.
DEFAULT_MAX_DEPTH: int = 5


class Router:
    """Route user queries to the most appropriate specialist.

    Attributes:
        specialists: Ordered list of specialists checked for each query.
        max_depth:   Maximum number of nested ``route()`` calls allowed
                     before a :class:`RecursionError` is raised (depth guard).
        config:      Optional :class:`~hermes.specialists.config.RouterConfig`.
                     When provided and ``config.enabled`` is ``False`` the
                     router is a no-op (``route()`` returns ``None``).
                     When *config* is ``None`` the router operates in
                     legacy/standalone mode and returns a fallback string for
                     unmatched queries so existing unit tests stay green.
    """

    def __init__(
        self,
        specialists: list[BaseSpecialist],
        max_depth: int = DEFAULT_MAX_DEPTH,
        config: Optional["RouterConfig"] = None,
    ) -> None:
        self.specialists = list(specialists)
        self.max_depth = max_depth
        self._config = config
        self._depth: int = 0
        # Per-session context: maps session_id → {"specialist": name, ...}
        self._session_contexts: Dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def route(
        self,
        query: str,
        session_id: Optional[str] = None,
        context_turns: int = 0,
    ) -> Optional[str]:
        """Route *query* to the first specialist that can handle it.

        When a :class:`~hermes.specialists.config.RouterConfig` is attached
        and ``config.enabled`` is ``False``, the router is disabled and
        returns ``None`` immediately so the caller can fall through to its
        normal processing pipeline.

        When *config* is ``None`` (standalone / legacy mode) the router
        behaves as before: unmatched queries return a ``"[Unmatched] …"``
        fallback string so legacy call-sites and unit tests continue to work.

        Args:
            query:         The user's message text.
            session_id:    Optional session identifier.  When provided, the
                           router stores specialist context so subsequent
                           calls to :meth:`has_pending_followup` and
                           :meth:`handle_followup` work correctly.
            context_turns: (reserved) Number of prior turns to consider as
                           specialist context.  Not used in this
                           implementation but kept for API compatibility.

        Returns:
            The specialist's response string when a specialist matches,
            ``None`` when the router is disabled or no specialist matches
            (in config-aware mode), or a ``"[Unmatched] …"`` string when
            no specialist matches in standalone / legacy mode.

        Raises:
            RecursionError: If the routing depth exceeds ``max_depth``.
        """
        # Feature-flag guard: disabled router → no-op
        if self._config is not None and not self._config.enabled:
            return None

        if self._depth >= self.max_depth:
            raise RecursionError(
                f"Routing depth {self._depth} exceeds max_depth {self.max_depth}"
            )

        self._depth += 1
        try:
            for specialist in self.specialists:
                if specialist.can_handle(query):
                    result = specialist.handle(query)
                    # Store session context for follow-up detection.
                    if session_id is not None:
                        self._session_contexts[session_id] = {
                            "specialist": specialist.name,
                        }
                    return result

            # No specialist matched.
            if session_id is not None:
                # Clear any stale session context so followup guard resets.
                self._session_contexts.pop(session_id, None)

            if self._config is not None:
                # Config-aware mode: return None so gateway falls through.
                return None
            else:
                # Legacy / standalone mode: return fallback string.
                return f"[Unmatched] {query}"
        finally:
            self._depth -= 1

    def has_pending_followup(self, session_id: str) -> bool:
        """Return ``True`` if there is pending specialist context for *session_id*.

        Used by the gateway to decide whether to route the next message
        directly to the specialist that handled the previous turn rather
        than running the full routing logic.

        Args:
            session_id: The gateway session identifier.

        Returns:
            ``True`` when a prior :meth:`route` call stored context for this
            session, ``False`` otherwise.
        """
        return session_id in self._session_contexts

    def get_session_context(self, session_id: str) -> dict:
        """Return the stored specialist context for *session_id*.

        Returns an empty ``dict`` when no context is stored.
        """
        return dict(self._session_contexts.get(session_id, {}))

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
