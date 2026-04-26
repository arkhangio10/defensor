"""Memory Agent — thin wrapper over tmp/cases/<uuid>.json case files.

Provides a clean interface so other agents can read/update case state
without calling the Anthropic API. Pure file I/O via pathlib.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

# Resolve repo root: agents/memory/ -> agents/ -> repo root
CASES_DIR = Path(__file__).parent.parent.parent / "tmp" / "cases"


class FollowUpEvent(BaseModel):
    """A single event in the 25-day follow-up timeline."""

    model_config = {"extra": "forbid"}

    event_type: Literal["sent", "reminder", "response_received", "escalated", "closed"]
    timestamp: str  # ISO 8601
    channel: str
    notes: str


class StoredCaseData(BaseModel):
    """Shape of every tmp/cases/<uuid>.json file."""

    model_config = {"extra": "allow"}  # allow legacy fields written by VisionAgent

    case_id: str
    created_at: str  # ISO 8601
    vision: dict  # type: ignore[type-arg]
    analysis: dict | None = None  # type: ignore[type-arg]
    events: list[FollowUpEvent] = Field(default_factory=list)
    status: Literal["pending", "filed", "following_up", "resolved", "closed"] = "pending"


class MemoryAgent:
    """Read/write case files from tmp/cases/.

    No API calls — pure file I/O.
    """

    def __init__(self) -> None:
        CASES_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def load_case(self, case_id: str) -> dict | None:  # type: ignore[type-arg]
        """Read tmp/cases/<case_id>.json and return the raw dict, or None."""
        path = self._path(case_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save_case(self, case_id: str, data: dict) -> None:  # type: ignore[type-arg]
        """Write (or merge into) tmp/cases/<case_id>.json.

        If the file already exists the new dict is merged on top of the
        existing data — existing keys not present in ``data`` are kept.
        """
        path = self._path(case_id)
        existing: dict = {}  # type: ignore[type-arg]
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
        existing.update(data)
        path.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def append_event(self, case_id: str, event: FollowUpEvent) -> None:
        """Append a FollowUpEvent to the events list of an existing case.

        Raises:
            FileNotFoundError: if the case file does not exist yet.
        """
        path = self._path(case_id)
        if not path.exists():
            raise FileNotFoundError(
                f"Caso no encontrado: {case_id}. "
                "Llame a save_case() antes de agregar eventos."
            )
        raw = json.loads(path.read_text(encoding="utf-8"))
        events: list[dict] = raw.get("events", [])  # type: ignore[type-arg]
        events.append(event.model_dump())
        raw["events"] = events
        path.write_text(
            json.dumps(raw, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def list_cases(self) -> list[str]:
        """Return all case IDs present in tmp/cases/."""
        return [p.stem for p in sorted(CASES_DIR.glob("*.json"))]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _path(self, case_id: str) -> Path:
        return CASES_DIR / f"{case_id}.json"


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()
