"""Tests for hermes.specialists.config — RouterConfig (T018)."""

import pytest

from hermes.specialists.config import RouterConfig


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_router_config_default_disabled():
    """RouterConfig.enabled defaults to False (feature flag off by default)."""
    cfg = RouterConfig()
    assert cfg.enabled is False


def test_from_config_dict_enabled():
    """RouterConfig.from_config_dict parses specialists.enabled=true correctly."""
    cfg = RouterConfig.from_config_dict({"specialists": {"enabled": True}})
    assert cfg.enabled is True


def test_from_config_dict_disabled():
    """RouterConfig.from_config_dict parses specialists.enabled=false correctly."""
    cfg = RouterConfig.from_config_dict({"specialists": {"enabled": False}})
    assert cfg.enabled is False


def test_from_config_dict_empty_dict_defaults_disabled():
    """RouterConfig.from_config_dict falls back to enabled=False for missing keys."""
    cfg = RouterConfig.from_config_dict({})
    assert cfg.enabled is False
