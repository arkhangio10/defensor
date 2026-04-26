"""Channel Agent — determines which authority to file a healthcare complaint with.

Routing is fully deterministic (no LLM needed for the decision).
The LLM is called once, cheaply, only to generate a plain-Spanish explanation
for the patient.

See /agents/channel/prompt.md for the system prompt and
/agents/channel/schema.json for the strict output schema.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

from anthropic import Anthropic
from pydantic import BaseModel

AGENT_DIR = Path(__file__).parent
PROMPT_PATH = AGENT_DIR / "prompt.md"
_COUNTRY_MODULES_DIR = AGENT_DIR.parent.parent / "country-modules"
_SUPPORTED_COUNTRIES = {"peru", "colombia", "mexico"}


def _load_country_config(country: str) -> dict[str, Any]:
    key = country.lower()
    if key not in _SUPPORTED_COUNTRIES:
        key = "peru"
    path = _COUNTRY_MODULES_DIR / key / "config.json"
    return json.loads(path.read_text(encoding="utf-8"))

MODEL_ID = "claude-opus-4-7"
MAX_TOKENS = 512

HospitalNetwork = Literal["EsSalud", "MINSA", "EPS", "private", "unknown"]
FilingMethod = Literal["presencial", "virtual", "ambos"]

# ---------------------------------------------------------------------------
# Output model
# ---------------------------------------------------------------------------


class ChannelOutput(BaseModel):
    """Strict output contract. Mirrors /agents/channel/schema.json."""

    model_config = {"extra": "forbid"}

    primary_channel: str
    secondary_channel: str | None
    channel_url: str | None
    explanation: str
    filing_method: FilingMethod
    estimated_response_days: int


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class ChannelAgent:
    """Determines where a complaint should be filed, then explains it in Spanish.

    Routing logic is purely deterministic — no API call required for the
    decision.  One cheap API call generates the patient-facing explanation.
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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def route(
        self,
        hospital_network: str,
        violations: list[dict],  # type: ignore[type-arg]
        country: str = "peru",
    ) -> ChannelOutput:
        """Determine the filing channel and generate a Spanish explanation.

        Args:
            hospital_network: One of EsSalud / MINSA / EPS / private / unknown.
            violations: List of violation dicts from ViolationAgent.
            country: ISO country name; only "peru" is fully supported today.

        Returns:
            ChannelOutput — validated Pydantic model.
        """
        routing = self._resolve_routing(hospital_network, country)
        explanation = self._generate_explanation(
            hospital_network=hospital_network,
            violations=violations,
            primary_channel=str(routing["primary"]),
            secondary_channel=routing["secondary"],  # type: ignore[arg-type]
        )

        return ChannelOutput(
            primary_channel=str(routing["primary"]),
            secondary_channel=routing["secondary"],  # type: ignore[assignment]
            channel_url=routing["url"],  # type: ignore[assignment]
            explanation=explanation,
            filing_method=str(routing["filing_method"]),  # type: ignore[assignment]
            estimated_response_days=int(routing["estimated_response_days"]),  # type: ignore[arg-type]
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_routing(
        self,
        hospital_network: str,
        country: str,
    ) -> dict[str, Any]:
        """Return a routing dict for the given network and country.

        Loads the country config via country_modules (falls back to peru for
        unsupported countries).  Falls back to "unknown" for unrecognised
        networks within the config.
        """
        config = _load_country_config(country)
        networks: dict[str, Any] = config["networks"]

        key = hospital_network if hospital_network in networks else "unknown"
        # Some country configs may not have an "unknown" fallback entry;
        # in that case fall back to the first available network row.
        if key not in networks:
            key = next(iter(networks))

        row = networks[key]
        return {
            "primary": row["primary_channel"],
            "secondary": row.get("secondary_channel"),
            "url": row["url"],
            "filing_method": "ambos",
            "estimated_response_days": row["response_days"],
        }

    def _generate_explanation(
        self,
        hospital_network: str,
        violations: list[dict],  # type: ignore[type-arg]
        primary_channel: str,
        secondary_channel: str | None,
    ) -> str:
        """Call the LLM once to produce a plain-Spanish patient explanation."""
        violation_summary = ", ".join(
            v.get("article_label", v.get("violation_type", "infracción"))
            for v in violations
        ) or "incumplimiento de sus derechos como paciente"

        user_message = (
            f"Red hospitalaria: {hospital_network}\n"
            f"Infracciones identificadas: {violation_summary}\n"
            f"Canal principal: {primary_channel}\n"
            f"Canal secundario: {secondary_channel or 'ninguno'}\n\n"
            "Explica al paciente dónde y por qué debe presentar su queja."
        )

        response = self._client.messages.create(
            model=MODEL_ID,
            max_tokens=MAX_TOKENS,
            system=self._system_prompt,
            messages=[
                {"role": "user", "content": user_message},
            ],
        )

        parts = [
            block.text
            for block in response.content
            if getattr(block, "type", "") == "text"
        ]
        return "".join(parts).strip()
