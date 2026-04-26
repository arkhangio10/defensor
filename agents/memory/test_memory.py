"""Tests for the Memory Agent.

No API key required — all tests are pure file I/O.
"""

from __future__ import annotations

from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Test 1 — save and load round-trip
# ---------------------------------------------------------------------------


def test_memory_save_and_load(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import agents.memory.agent as memory_module

    monkeypatch.setattr(memory_module, "CASES_DIR", tmp_path)

    from agents.memory.agent import MemoryAgent

    agent = MemoryAgent()
    case_id = "test-case-001"
    data = {
        "case_id": case_id,
        "created_at": "2026-04-25T00:00:00+00:00",
        "vision": {"hospital_name": "Hospital Test", "patient_name": "PACIENTE TEST"},
        "analysis": None,
        "events": [],
        "status": "pending",
    }

    agent.save_case(case_id, data)
    loaded = agent.load_case(case_id)

    assert loaded is not None
    assert loaded["case_id"] == case_id
    assert loaded["vision"]["hospital_name"] == "Hospital Test"
    assert loaded["status"] == "pending"


# ---------------------------------------------------------------------------
# Test 2 — append event
# ---------------------------------------------------------------------------


def test_memory_append_event(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import agents.memory.agent as memory_module

    monkeypatch.setattr(memory_module, "CASES_DIR", tmp_path)

    from agents.memory.agent import FollowUpEvent, MemoryAgent

    agent = MemoryAgent()
    case_id = "test-case-002"
    agent.save_case(
        case_id,
        {
            "case_id": case_id,
            "created_at": "2026-04-25T00:00:00+00:00",
            "vision": {"hospital_name": "Hospital Test"},
            "events": [],
            "status": "pending",
        },
    )

    event = FollowUpEvent(
        event_type="sent",
        timestamp="2026-04-25T10:00:00+00:00",
        channel="EsSalud Defensoría del Asegurado",
        notes="Carta enviada por correo certificado.",
    )
    agent.append_event(case_id, event)

    loaded = agent.load_case(case_id)
    assert loaded is not None
    events = loaded.get("events", [])
    assert len(events) == 1
    assert events[0]["event_type"] == "sent"
    assert events[0]["channel"] == "EsSalud Defensoría del Asegurado"


# ---------------------------------------------------------------------------
# Test 3 — list cases
# ---------------------------------------------------------------------------


def test_memory_list_cases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import agents.memory.agent as memory_module

    monkeypatch.setattr(memory_module, "CASES_DIR", tmp_path)

    from agents.memory.agent import MemoryAgent

    agent = MemoryAgent()

    for case_id in ("case-aaa", "case-bbb"):
        agent.save_case(
            case_id,
            {
                "case_id": case_id,
                "created_at": "2026-04-25T00:00:00+00:00",
                "vision": {},
                "events": [],
                "status": "pending",
            },
        )

    result = agent.list_cases()
    assert "case-aaa" in result
    assert "case-bbb" in result
