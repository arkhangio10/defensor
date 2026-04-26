"""Tests for the Channel Agent.

Tests 1-3 are offline (no API key required) — they exercise the deterministic
routing table directly via _load_country_config.
Test 4 requires ANTHROPIC_API_KEY and is skipped when it is absent.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from agents.channel.agent import ChannelAgent, _load_country_config

_FIXTURES = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "channel"
_NEED_KEY = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live API test",
)


def _load(filename: str) -> dict:  # type: ignore[type-arg]
    return json.loads((_FIXTURES / filename).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Test 1 — offline: EsSalud → Defensoría del Asegurado
# ---------------------------------------------------------------------------


def test_channel_essalud_routes_to_defensoria() -> None:
    """EsSalud must route to 'EsSalud Defensoría del Asegurado' per Peru config."""
    config = _load_country_config("peru")
    networks = config["networks"]
    assert networks["EsSalud"]["primary_channel"] == "EsSalud Defensoría del Asegurado"


# ---------------------------------------------------------------------------
# Test 2 — offline: MINSA → SUSALUD
# ---------------------------------------------------------------------------


def test_channel_minsa_routes_to_susalud() -> None:
    """MINSA must route to 'SUSALUD' as primary channel per Peru config."""
    config = _load_country_config("peru")
    networks = config["networks"]
    assert networks["MINSA"]["primary_channel"] == "SUSALUD"


# ---------------------------------------------------------------------------
# Test 3 — offline: Colombia EPS → Supersalud
# ---------------------------------------------------------------------------


def test_channel_colombia_routes_to_supersalud() -> None:
    """Colombia EPS must route to 'Supersalud' as primary channel."""
    config = _load_country_config("colombia")
    networks = config["networks"]
    assert networks["EPS"]["primary_channel"] == "Supersalud"


# ---------------------------------------------------------------------------
# Test 4 — live: full route() call with LLM explanation
# ---------------------------------------------------------------------------


@_NEED_KEY
def test_channel_live_explanation() -> None:
    """Live route() for EsSalud must return correct channel and a real explanation."""
    fixture = _load("input_essalud.json")
    agent = ChannelAgent()
    result = agent.route(
        hospital_network=fixture["hospital_network"],
        violations=fixture["violations"],
        country=fixture["country"],
    )

    assert result.primary_channel == "EsSalud Defensoría del Asegurado"
    assert len(result.explanation) > 20, (
        f"Explanation too short: {result.explanation!r}"
    )
    assert result.estimated_response_days > 0
