"""Drafter Agent — drafts a formal complaint letter from vision + violation data.

See /agents/drafter/prompt.md for the system prompt (Spanish) and
/agents/drafter/schema.json for the strict output schema.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path


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
MAX_TOKENS = 8192

DISCLAIMER = "Defensor no reemplaza a un abogado. Esta es información legal, no asesoría legal."


class DrafterOutput(BaseModel):
    """Strict output contract. Mirrors /agents/drafter/schema.json. extra=ignore for LLM tolerance."""

    model_config = {"extra": "ignore"}

    letter_text: str
    addressee: str
    subject: str = ""
    legal_articles_cited: list[str] = Field(default_factory=list)
    patient_request: str = ""
    estimated_response_days: int = Field(default=30, ge=1)
    disclaimer: str
    warnings: list[str] = Field(default_factory=list)


class DrafterAgent:
    """Drafts a formal complaint letter given vision output, violations, and recommended channel.

    The agent loads its system prompt from prompt.md, builds a structured user
    message from the three inputs, calls Opus 4.7, and validates the response
    against the DrafterOutput Pydantic schema before returning.
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

    def draft(
        self,
        vision_output: dict,
        violations: list[dict],
        recommended_channel: str,
    ) -> DrafterOutput:
        """Draft a formal complaint letter and return structured output.

        Args:
            vision_output: Dict matching VisionOutput fields (hospital_name,
                patient_name, patient_dni, specialty_requested, reason_given,
                date_of_attempted_care, hospital_network, etc.)
            violations: List of violation dicts (article, explanation, severity,
                violation_type) from the Violation Agent.
            recommended_channel: Authority to address the complaint to
                (e.g. "SUSALUD", "EsSalud Defensoría").

        Returns:
            DrafterOutput — validated against schema.json.

        Raises:
            ValueError: if the model response is not valid JSON or fails validation.
        """
        user_payload = json.dumps(
            {
                "vision": vision_output,
                "violations": violations,
                "recommended_channel": recommended_channel,
            },
            ensure_ascii=False,
            indent=2,
        )

        response = self._client.messages.create(
            model=MODEL_ID,
            max_tokens=MAX_TOKENS,
            system=self._system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Redacta la carta de queja formal basándote en los siguientes datos. "
                        "Devuelve únicamente el JSON del esquema. Sin markdown, sin comentarios.\n\n"
                        + user_payload
                    ),
                },
            ],
        )

        parts = [b.text for b in response.content if getattr(b, "type", "") == "text"]
        raw = _extract_json("".join(parts))

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Drafter Agent returned non-JSON response: {e}\n---\n{raw[:500]}"
            ) from e

        # Normalise common field name aliases the model may produce.
        _ALIASES: dict[str, str] = {
            "recipient": "addressee",
            "to": "addressee",
            "destinatario": "addressee",
            "para": "addressee",
            "channel": "addressee",
            "subject_line": "subject",
            "asunto": "subject",
            "titulo": "subject",
            "legal_response_deadline_days": "estimated_response_days",
            "response_deadline_days": "estimated_response_days",
            "dias_respuesta": "estimated_response_days",
            "deadline_days": "estimated_response_days",
            "plazo": "estimated_response_days",
            "articles_cited": "legal_articles_cited",
            "cited_articles": "legal_articles_cited",
            "articulos_citados": "legal_articles_cited",
            "articulos": "legal_articles_cited",
            "articles": "legal_articles_cited",
            "legal_basis": "legal_articles_cited",
            "request": "patient_request",
            "petitorio": "patient_request",
            "solicitud": "patient_request",
            "pedido": "patient_request",
            "advertencias": "warnings",
            "notas": "warnings",
        }
        for alias, canonical in _ALIASES.items():
            if alias in data and canonical not in data:
                data[canonical] = data.pop(alias)

        # Guarantee legal_articles_cited — use input violations as authoritative source.
        if not data.get("legal_articles_cited"):
            from_violations = [v["article"] for v in violations if isinstance(v.get("article"), str)]
            if not from_violations:
                letter = data.get("letter_text", "")
                from_violations = re.findall(r"Ley\s+\d+[\w\s]*(?:,\s*Art\.?\s*\d+\w*)?", letter)
            data["legal_articles_cited"] = list(dict.fromkeys(from_violations))

        # Enforce the fixed disclaimer regardless of what the model returned.
        data["disclaimer"] = DISCLAIMER

        try:
            return DrafterOutput.model_validate(data)
        except ValidationError as e:
            raise ValueError(
                f"Drafter Agent response failed schema validation: {e}"
            ) from e
