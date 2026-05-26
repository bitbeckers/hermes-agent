"""Configuration for the Hermes specialist router."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RouterConfig:
    """Configuration for the specialist router.

    Attributes:
        enabled: Master feature flag.  When ``False`` (the default) the
                 router is a no-op and the gateway processes every message
                 through the normal agent pipeline unchanged.
    """

    enabled: bool = False

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_config_dict(cls, d: dict[str, Any]) -> "RouterConfig":
        """Build a :class:`RouterConfig` from a raw config mapping.

        Reads the ``specialists`` key from *d* (e.g. loaded from
        ``~/.hermes/config.yaml``) and maps its sub-keys to the
        corresponding dataclass fields.

        Example config.yaml snippet::

            specialists:
              enabled: true

        Args:
            d: Top-level config dictionary (the full parsed YAML mapping).

        Returns:
            A :class:`RouterConfig` instance.  Missing keys use their
            dataclass defaults (``enabled=False``).
        """
        specialists_cfg: dict[str, Any] = {}
        if isinstance(d, dict):
            specialists_cfg = d.get("specialists") or {}
        if not isinstance(specialists_cfg, dict):
            specialists_cfg = {}

        enabled = bool(specialists_cfg.get("enabled", False))
        return cls(enabled=enabled)
