"""Follow-Up Managed Agent — autonomous 25-day complaint follow-up loop.

In production this would run as a Managed Agent with the
``managed-agents-2026-04-01`` beta header, persisting across sessions.
For the demo, ``start()`` simulates the full schedule synchronously and
``replay_events()`` returns the stored history for 100x-speed replay.

See /agents/follow_up/prompt.md for the Spanish system prompt and
/agents/follow_up/schema.json for the strict output schema.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from anthropic import Anthropic
from pydantic import BaseModel, Field, ValidationError

from agents.memory.agent import FollowUpEvent, MemoryAgent

AGENT_DIR = Path(__file__).parent
PROMPT_PATH = AGENT_DIR / "prompt.md"
SCHEMA_PATH = AGENT_DIR / "schema.json"

MODEL_ID = "claude-opus-4-7"
MAX_TOKENS = 2048

# Follow-up schedule: (day, step_type)
_SCHEDULE: list[tuple[int, Literal["confirmacion", "recordatorio", "escalacion", "cierre"]]] = [
    (1, "confirmacion"),
    (7, "recordatorio"),
    (15, "recordatorio"),
    (20, "escalacion"),
    (25, "cierre"),
]

# Map step type → FollowUpEvent event_type
_STEP_TO_EVENT: dict[
    Literal["confirmacion", "recordatorio", "escalacion", "cierre"],
    Literal["sent", "reminder", "response_received", "escalated", "closed"],
] = {
    "confirmacion": "sent",
    "recordatorio": "reminder",
    "escalacion": "escalated",
    "cierre": "closed",
}


def _extract_json(text: str) -> str:
    """Extract the first JSON object from a model response."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if fence:
        return fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


class FollowUpOutput(BaseModel):
    """Strict output contract. Mirrors /agents/follow_up/schema.json."""

    model_config = {"extra": "forbid"}

    message_type: Literal["confirmacion", "recordatorio", "escalacion", "cierre"]
    message_text: str
    recommended_action: str
    days_elapsed: int = Field(ge=0)


class FollowUpAgent:
    """Runs the autonomous follow-up loop for a filed complaint.

    In prod: Would run as a Managed Agent with managed-agents-2026-04-01 beta.
    In demo: replay_events() shows the full 25-day history at 100x speed.
    """

    def __init__(self, memory: MemoryAgent, client: Anthropic | None = None) -> None:
        self._memory = memory
        if client is None:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "ANTHROPIC_API_KEY is not set. Define it in .env.local."
                )
            client = Anthropic(api_key=api_key)
        self._client = client
        self._system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def start(
        self,
        case_id: str,
        channel: str,
        letter_text: str,
    ) -> list[FollowUpEvent]:
        """Simulate the full 25-day follow-up schedule.

        Makes one API call to claude-opus-4-7 per schedule step to generate
        the appropriate Spanish message. Saves each event to memory via
        MemoryAgent.append_event().

        Args:
            case_id:     UUID of the case already stored in tmp/cases/.
            channel:     Filing channel, e.g. "SUSALUD", "Defensoría del Pueblo".
            letter_text: Short summary of the complaint letter for context.

        Returns:
            List of all FollowUpEvent objects created (5 events for the demo).
        """
        # Ensure the case file exists; create a minimal stub if not.
        existing = self._memory.load_case(case_id)
        if existing is None:
            self._memory.save_case(
                case_id,
                {
                    "case_id": case_id,
                    "created_at": _now_iso(),
                    "vision": {},
                    "analysis": None,
                    "events": [],
                    "status": "filed",
                },
            )

        events: list[FollowUpEvent] = []

        for day, step in _SCHEDULE:
            output = self._call_model(
                case_id=case_id,
                channel=channel,
                case_summary=letter_text,
                step=step,
                days_elapsed=day,
            )
            event = FollowUpEvent(
                event_type=_STEP_TO_EVENT[step],
                timestamp=_now_iso(),
                channel=channel,
                notes=output.message_text,
            )
            self._memory.append_event(case_id, event)
            events.append(event)

        # Mark case as following_up after the loop
        self._memory.save_case(case_id, {"status": "following_up"})

        return events

    def replay_events(self, case_id: str) -> list[FollowUpEvent]:
        """Return all stored events for demo replay."""
        raw = self._memory.load_case(case_id)
        if raw is None:
            return []
        return [FollowUpEvent.model_validate(e) for e in raw.get("events", [])]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _call_model(
        self,
        *,
        case_id: str,
        channel: str,
        case_summary: str,
        step: Literal["confirmacion", "recordatorio", "escalacion", "cierre"],
        days_elapsed: int,
    ) -> FollowUpOutput:
        """Call claude-opus-4-7 to generate a Spanish follow-up message."""
        user_message = json.dumps(
            {
                "days_elapsed": days_elapsed,
                "channel": channel,
                "case_summary": case_summary,
                "step": step,
                "case_id": case_id,
            },
            ensure_ascii=False,
        )

        response = self._client.messages.create(
            model=MODEL_ID,
            max_tokens=MAX_TOKENS,
            system=self._system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
        )

        parts = [b.text for b in response.content if getattr(b, "type", "") == "text"]
        raw = _extract_json("".join(parts))

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Follow-Up Agent returned non-JSON response: {e}\n---\n{raw[:500]}"
            ) from e

        try:
            return FollowUpOutput.model_validate(data)
        except ValidationError as e:
            raise ValueError(
                f"Follow-Up Agent response failed schema validation: {e}"
            ) from e
