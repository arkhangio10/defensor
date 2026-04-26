"""Tests for the Follow-Up Managed Agent.

Requires ANTHROPIC_API_KEY — skipped automatically without it.
"""

from __future__ import annotations

import os
import uuid

import pytest

from agents.follow_up.agent import FollowUpAgent
from agents.memory.agent import FollowUpEvent, MemoryAgent


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live API test",
)
def test_follow_up_start_returns_five_events(tmp_path: pytest.FixturePath) -> None:  # type: ignore[name-defined]
    """start() should produce exactly 5 events, one per schedule step."""
    # Use a fresh tmp_path so the test never touches production cases.
    import agents.memory.agent as mem_module

    original_cases_dir = mem_module.CASES_DIR
    mem_module.CASES_DIR = tmp_path
    try:
        memory = MemoryAgent()
        agent = FollowUpAgent(memory=memory)

        case_id = str(uuid.uuid4())
        events = agent.start(
            case_id=case_id,
            channel="SUSALUD",
            letter_text="Queja de prueba: negativa de cita post-operatoria en EsSalud Rebagliati.",
        )

        # 1. Exactly 5 events (one per schedule step)
        assert len(events) == 5, f"Esperados 5 eventos, recibidos {len(events)}"

        # 2. Each event has a non-empty notes field
        for i, event in enumerate(events):
            assert isinstance(event, FollowUpEvent)
            assert event.notes.strip(), (
                f"Evento {i} no tiene texto en 'notes': {event!r}"
            )

        # 3. Events are also persisted in memory
        replayed = agent.replay_events(case_id)
        assert len(replayed) == 5

    finally:
        mem_module.CASES_DIR = original_cases_dir


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live API test",
)
def test_follow_up_event_types_follow_schedule(tmp_path: pytest.FixturePath) -> None:  # type: ignore[name-defined]
    """Events should follow the expected schedule order."""
    import agents.memory.agent as mem_module

    original_cases_dir = mem_module.CASES_DIR
    mem_module.CASES_DIR = tmp_path
    try:
        memory = MemoryAgent()
        agent = FollowUpAgent(memory=memory)

        case_id = str(uuid.uuid4())
        events = agent.start(
            case_id=case_id,
            channel="Defensoría del Pueblo",
            letter_text="Negativa de cirugía urgente — caso de prueba.",
        )

        expected_types = ["sent", "reminder", "reminder", "escalated", "closed"]
        actual_types = [e.event_type for e in events]
        assert actual_types == expected_types, (
            f"Tipos de evento incorrectos: {actual_types}"
        )

    finally:
        mem_module.CASES_DIR = original_cases_dir


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live API test",
)
def test_follow_up_channel_recorded_in_events(tmp_path: pytest.FixturePath) -> None:  # type: ignore[name-defined]
    """Each event should record the channel that was passed to start()."""
    import agents.memory.agent as mem_module

    original_cases_dir = mem_module.CASES_DIR
    mem_module.CASES_DIR = tmp_path
    try:
        memory = MemoryAgent()
        agent = FollowUpAgent(memory=memory)

        case_id = str(uuid.uuid4())
        channel = "SUSALUD"
        events = agent.start(
            case_id=case_id,
            channel=channel,
            letter_text="Queja de prueba canal.",
        )

        for event in events:
            assert event.channel == channel, (
                f"Canal incorrecto en evento: {event.channel!r} != {channel!r}"
            )

    finally:
        mem_module.CASES_DIR = original_cases_dir
