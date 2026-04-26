"""Violation Agent — maps vision output to Ley 29414 violations.

See /agents/violation/prompt.md for the system prompt (Spanish) and
/agents/violation/schema.json for the strict output schema.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Literal


def _extract_json(text: str) -> str:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if fence:
        return fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text

from anthropic import Anthropic
from pydantic import BaseModel, Field, ValidationError

AGENT_DIR = Path(__file__).parent
PROMPT_PATH = AGENT_DIR / "prompt.md"
SCHEMA_PATH = AGENT_DIR / "schema.json"

MODEL_ID = "claude-opus-4-7"
MAX_TOKENS = 4096

ViolationType = Literal["confirmada", "posible", "no_aplica"]
Severity = Literal["alta", "media", "baja"]


_ITEM_ALIASES: dict[str, str] = {
    "description": "explanation",
    "detalle": "explanation",
    "explicacion": "explanation",
    "text_excerpt": "article_text_excerpt",
    "excerpt": "article_text_excerpt",
    "fragmento": "article_text_excerpt",
    "gravedad": "severity",
    "tipo": "violation_type",
    "type": "violation_type",
}


def _normalize_violation_item(item: dict) -> dict:  # type: ignore[type-arg]
    for alias, canonical in _ITEM_ALIASES.items():
        if alias in item and canonical not in item:
            item[canonical] = item.pop(alias)
    item.setdefault("article_text_excerpt", "")
    item.setdefault("explanation", item.get("description", ""))
    item.setdefault("severity", "media")
    return item


class ViolationItem(BaseModel):
    """A single identified or possible legal violation."""

    model_config = {"extra": "ignore"}

    article: str
    article_text_excerpt: str
    violation_type: ViolationType
    explanation: str
    severity: Severity


class ViolationOutput(BaseModel):
    """Strict output contract. Mirrors /agents/violation/schema.json."""

    model_config = {"extra": "ignore"}

    violations: list[ViolationItem]
    summary: str
    recommended_channel: str
    complaint_viable: bool
    confidence: float = Field(ge=0.0, le=1.0)


class ViolationAgent:
    """Analyzes structured vision output and returns Ley 29414 violations.

    The agent loads its system prompt from prompt.md, sends the vision JSON
    to Opus 4.7 via the Anthropic API, and validates the response against the
    Pydantic schema above before returning.
    """

    def __init__(self, client: Anthropic | None = None) -> None:
        if client is None:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "ANTHROPIC_API_KEY is not set. Define it in .env.local."
                )
            client = Anthropic(api_key=api_key)
        self._client = client
        self._system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    def analyze(self, vision_output: dict[str, object]) -> ViolationOutput:
        """Identify Ley 29414 violations from structured vision output.

        Args:
            vision_output: Dict produced by VisionAgent.read_document(), or any
                dict matching the vision output schema.

        Returns:
            ViolationOutput — validated against schema.json.

        Raises:
            ValueError: if the model response is not valid JSON or fails validation.
        """
        user_text = (
            "Analiza la siguiente salida del Agente de Visión y devuelve únicamente "
            "el JSON del esquema de violaciones. Sin markdown, sin comentarios.\n\n"
            + json.dumps(vision_output, ensure_ascii=False, indent=2)
        )

        response = self._client.messages.create(
            model=MODEL_ID,
            max_tokens=MAX_TOKENS,
            system=self._system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_text,
                },
            ],
        )

        parts = [b.text for b in response.content if getattr(b, "type", "") == "text"]
        raw = _extract_json("".join(parts))

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Violation Agent returned non-JSON response: {e}\n---\n{raw[:500]}"
            ) from e

        if isinstance(data.get("violations"), list):
            data["violations"] = [_normalize_violation_item(v) for v in data["violations"]]

        try:
            return ViolationOutput.model_validate(data)
        except ValidationError as e:
            raise ValueError(
                f"Violation Agent response failed schema validation: {e}"
            ) from e
