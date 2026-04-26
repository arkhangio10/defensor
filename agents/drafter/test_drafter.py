"""Tests for the Drafter Agent.

Structural tests run without an API key.
Integration tests are skipped when ANTHROPIC_API_KEY is not set.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "drafter"

_has_api_key = bool(os.environ.get("ANTHROPIC_API_KEY"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load(filename: str) -> dict:
    return json.loads((FIXTURES_DIR / filename).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Test 1 — structural: DrafterOutput has all required fields (no API needed)
# ---------------------------------------------------------------------------


def test_drafter_output_schema() -> None:
    from agents.drafter.agent import DrafterOutput

    fields = DrafterOutput.model_fields
    required = {
        "letter_text",
        "addressee",
        "subject",
        "legal_articles_cited",
        "patient_request",
        "estimated_response_days",
        "disclaimer",
        "warnings",
    }
    for field_name in required:
        assert field_name in fields, f"DrafterOutput is missing field: {field_name}"


# ---------------------------------------------------------------------------
# Test 2 — EsSalud letter integration
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _has_api_key, reason="ANTHROPIC_API_KEY not set")
def test_drafter_essalud_letter() -> None:
    from agents.drafter.agent import DrafterAgent

    fixture = _load("input_essalud_case.json")
    agent = DrafterAgent()
    result = agent.draft(
        vision_output=fixture["vision_output"],
        violations=fixture["violations"],
        recommended_channel=fixture["recommended_channel"],
    )

    assert len(result.letter_text) > 200
    assert "essalud" in result.addressee.lower() or "defensoría" in result.addressee.lower()
    assert (
        result.disclaimer
        == "Defensor no reemplaza a un abogado. Esta es información legal, no asesoría legal."
    )
    assert len(result.legal_articles_cited) >= 1


# ---------------------------------------------------------------------------
# Test 3 — MINSA / SUSALUD letter integration
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _has_api_key, reason="ANTHROPIC_API_KEY not set")
def test_drafter_minsa_letter() -> None:
    from agents.drafter.agent import DrafterAgent

    fixture = _load("input_minsa_case.json")
    agent = DrafterAgent()
    result = agent.draft(
        vision_output=fixture["vision_output"],
        violations=fixture["violations"],
        recommended_channel=fixture["recommended_channel"],
    )

    assert "susalud" in result.addressee.lower()
    assert result.estimated_response_days > 0
    assert (
        result.disclaimer
        == "Defensor no reemplaza a un abogado. Esta es información legal, no asesoría legal."
    )


# ---------------------------------------------------------------------------
# Test 4 — letter contains patient name
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _has_api_key, reason="ANTHROPIC_API_KEY not set")
def test_drafter_letter_contains_patient_name() -> None:
    from agents.drafter.agent import DrafterAgent

    fixture = _load("input_essalud_case.json")
    agent = DrafterAgent()
    result = agent.draft(
        vision_output=fixture["vision_output"],
        violations=fixture["violations"],
        recommended_channel=fixture["recommended_channel"],
    )

    assert "ABNER" in result.letter_text or "RIVERA" in result.letter_text
