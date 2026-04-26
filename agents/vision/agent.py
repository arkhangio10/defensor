"""Vision Agent — reads a Peruvian healthcare document and returns structured fields.

See /agents/vision/prompt.md for the system prompt (Spanish) and
/agents/vision/schema.json for the strict output schema.
"""

from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path
from typing import Literal


def _extract_json(text: str) -> str:
    """Extract the first JSON object from a model response.

    Handles plain JSON, ```json ... ``` blocks, and leading prose.
    """
    text = text.strip()
    # Strip markdown code fence if present
    fence = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if fence:
        return fence.group(1).strip()
    # Find first { ... } span
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

DocumentType = Literal[
    "appointment_denial",
    "prescription",
    "discharge",
    "insurance_card",
    "medical_history",
    "lab_result",
    "other",
]

HospitalNetwork = Literal["EsSalud", "MINSA", "EPS", "private", "unknown"]


class VisionOutput(BaseModel):
    """Strict output contract. Mirrors /agents/vision/schema.json."""

    model_config = {"extra": "forbid"}

    document_type: DocumentType
    hospital_name: str | None
    hospital_network: HospitalNetwork
    patient_name: str | None
    patient_dni: str | None
    date_of_document: str | None
    date_of_attempted_care: str | None
    specialty_requested: str | None
    reason_given: str | None
    reason_given_translated_plain_spanish: str
    raw_text_extracted: str
    confidence: float = Field(ge=0.0, le=1.0)
    warnings: list[str]


class VisionAgent:
    """Reads a document image and returns structured fields.

    The agent loads its system prompt from prompt.md, sends the image to
    Opus 4.7 via the Anthropic API, and validates the response against the
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

    def read_document(self, image_bytes: bytes, mime_type: str) -> VisionOutput:
        """Analyze one document image and return structured fields.

        Args:
            image_bytes: Raw file bytes (JPG, PNG, or PDF page rendered to PNG).
            mime_type: "image/jpeg", "image/png", or "application/pdf".

        Returns:
            VisionOutput — validated against schema.json.

        Raises:
            ValueError: if the model response is not valid JSON or fails validation.
        """
        if mime_type not in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
            raise ValueError(
                f"Unsupported MIME type for vision: {mime_type}. "
                "PDFs must be rendered to PNG before calling this agent."
            )

        b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        response = self._client.messages.create(
            model=MODEL_ID,
            max_tokens=MAX_TOKENS,
            system=self._system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "Analiza este documento y devuelve únicamente "
                                "el JSON del esquema. Sin markdown, sin comentarios."
                            ),
                        },
                    ],
                },
            ],
        )

        parts = [b.text for b in response.content if getattr(b, "type", "") == "text"]
        raw = _extract_json("".join(parts))

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Vision Agent returned non-JSON response: {e}\n---\n{raw[:500]}"
            ) from e

        try:
            return VisionOutput.model_validate(data)
        except ValidationError as e:
            raise ValueError(
                f"Vision Agent response failed schema validation: {e}"
            ) from e
