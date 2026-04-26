"""Tests for the Violation Agent.

Tests 1 is offline (no API key required).
Tests 2-4 require ANTHROPIC_API_KEY and are skipped when it is absent.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from agents.vision.agent import VisionOutput
from agents.violation.agent import ViolationAgent, ViolationOutput

_FIXTURES = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "violation"
_NEED_KEY = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live API test",
)


def _load(filename: str) -> dict:  # type: ignore[type-arg]
    return json.loads((_FIXTURES / filename).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Test 1 — offline structural validation
# ---------------------------------------------------------------------------


def test_violation_schema_offline() -> None:
    """Input fixture must parse as a valid VisionOutput without any API call."""
    raw = _load("input_essalud_denial.json")
    # Validate the input can be parsed as VisionOutput (what the agent consumes).
    vision = VisionOutput.model_validate(raw)
    assert vision.document_type == "appointment_denial"
    assert vision.hospital_network == "EsSalud"
    assert vision.patient_name == "ABNER RIVERA QUISPE"
    assert vision.confidence == pytest.approx(0.92)

    # Confirm ViolationOutput schema is importable and structurally sound.
    fields = ViolationOutput.model_fields
    assert "violations" in fields
    assert "complaint_viable" in fields
    assert "recommended_channel" in fields
    assert "confidence" in fields


# ---------------------------------------------------------------------------
# Test 2 — live: EsSalud denial
# ---------------------------------------------------------------------------


@_NEED_KEY
def test_violation_essalud_denial() -> None:
    """EsSalud 'SIN CUPO DISPONIBLE' denial must yield at least one violation."""
    data = _load("input_essalud_denial.json")
    result = ViolationAgent().analyze(data)

    assert result.complaint_viable is True
    assert len(result.violations) >= 1
    assert any(
        v.violation_type in ("confirmada", "posible") for v in result.violations
    )
    assert result.recommended_channel.strip() != ""


# ---------------------------------------------------------------------------
# Test 3 — live: MINSA denial with no written reason
# ---------------------------------------------------------------------------


@_NEED_KEY
def test_violation_minsa_no_reason() -> None:
    """Denial without any written reason must still be flagged as viable."""
    data = _load("input_minsa_no_reason.json")
    result = ViolationAgent().analyze(data)

    assert result.complaint_viable is True

    # At least one violation must reference the missing reason OR be non-trivial.
    found_reason_reference = any(
        "motivo" in v.explanation.lower() or "razón" in v.explanation.lower()
        for v in result.violations
    )
    has_non_na_violation = any(
        v.violation_type != "no_aplica" for v in result.violations
    )
    assert found_reason_reference or has_non_na_violation


# ---------------------------------------------------------------------------
# Test 4 — live: EPS private denial — every item must have article + explanation
# ---------------------------------------------------------------------------


@_NEED_KEY
def test_violation_output_has_articles() -> None:
    """Every ViolationItem returned for the EPS case must be fully populated."""
    data = _load("input_eps_private.json")
    result = ViolationAgent().analyze(data)

    assert len(result.violations) >= 1, "Expected at least one violation item"
    for item in result.violations:
        assert item.article.strip() != "", (
            f"Empty article field on violation: {item}"
        )
        assert item.explanation.strip() != "", (
            f"Empty explanation field on violation: {item}"
        )
