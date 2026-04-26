"""End-to-end tests for the Vision Agent using synthetic fixtures.

Costs real Anthropic API tokens. Skips cleanly if ANTHROPIC_API_KEY is not set,
so `npm run test:agents` is safe to run on CI without leaking credentials or
billing noise.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from agents.vision import VisionAgent
from agents.vision.agent import VisionOutput

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "vision"

# --- Fixture 1: original synthetic Rebagliati denial ---
FIXTURE_PATH = FIXTURE_DIR / "synthetic_denial.png"
GENERATOR = FIXTURE_DIR / "generate_synthetic.py"

# --- Fixture 2: EsSalud Almenara / Abner Rivera denial ---
FIXTURE_ABNER_PATH = FIXTURE_DIR / "fixture_abner_denial.png"

# --- Fixture 3: MINSA / Rosa Elena Mamani denial ---
FIXTURE_MINSA_PATH = FIXTURE_DIR / "fixture_minsa_denial.png"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_abner_inline() -> None:
    """Render the Abner fixture using Pillow without spawning a subprocess."""
    from PIL import Image, ImageDraw, ImageFont

    width, height = 900, 600
    margin = 60

    def _font(size: int) -> ImageFont.ImageFont:
        for name in ("arial.ttf", "Arial.ttf", "consola.ttf", "DejaVuSans.ttf"):
            try:
                return ImageFont.truetype(name, size=size)
            except OSError:
                continue
        return ImageFont.load_default()

    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    title_font = _font(22)
    sub_font = _font(16)
    body_font = _font(20)
    label_font = _font(18)
    small_font = _font(13)

    lines: list[tuple[str, str]] = [
        ("Paciente:", "ABNER RIVERA QUISPE"),
        ("DNI:", "45678901"),
        ("Fecha de emision:", "15/04/2026"),
        ("Fecha de atencion solicitada:", "20/04/2026"),
        ("Especialidad:", "TRAUMATOLOGIA"),
        ("Motivo de denegacion:", "SIN CUPO DISPONIBLE"),
    ]

    y = margin
    draw.text((margin, y), "ESSALUD — HOSPITAL NACIONAL GUILLERMO ALMENARA IRIGOYEN", fill=(10, 10, 10), font=title_font)
    y += 32
    draw.text((margin, y), "DEPARTAMENTO DE ADMISION Y CITAS MEDICAS", fill=(60, 60, 60), font=sub_font)
    y += 28
    draw.line([(margin, y), (width - margin, y)], fill=(80, 80, 80), width=2)
    y += 16
    draw.text((margin, y), "CONSTANCIA DE DENEGACION DE CITA", fill=(10, 10, 10), font=title_font)
    y += 44

    for label, value in lines:
        draw.text((margin, y), label, fill=(90, 90, 90), font=label_font)
        draw.text((margin + 290, y), value, fill=(10, 10, 10), font=body_font)
        y += 38

    y += 20
    draw.line([(margin, y), (margin + 240, y)], fill=(120, 120, 120), width=1)
    draw.text((margin, y + 6), "Sello y firma del responsable de admision", fill=(120, 120, 120), font=small_font)

    draw.rectangle(
        [(margin, height - margin - 26), (width - margin, height - margin - 6)],
        outline=(200, 0, 0),
        width=2,
    )
    draw.text(
        (margin + 8, height - margin - 24),
        "DOCUMENTO SINTETICO / NO REAL - USO DE PRUEBA UNICAMENTE",
        fill=(200, 0, 0),
        font=small_font,
    )

    img.save(FIXTURE_ABNER_PATH, format="PNG")


def _generate_minsa_inline() -> None:
    """Render the MINSA fixture using Pillow without spawning a subprocess."""
    from PIL import Image, ImageDraw, ImageFont

    width, height = 900, 600
    margin = 60

    def _font(size: int) -> ImageFont.ImageFont:
        for name in ("arial.ttf", "Arial.ttf", "consola.ttf", "DejaVuSans.ttf"):
            try:
                return ImageFont.truetype(name, size=size)
            except OSError:
                continue
        return ImageFont.load_default()

    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    title_font = _font(22)
    sub_font = _font(16)
    body_font = _font(20)
    label_font = _font(18)
    small_font = _font(13)

    lines: list[tuple[str, str]] = [
        ("Paciente:", "ROSA ELENA MAMANI CONDORI"),
        ("DNI:", "71234567"),
        ("Fecha de emision:", "10/04/2026"),
        ("Especialidad solicitada:", "MEDICINA GENERAL"),
        ("Motivo de denegacion:", "NO HAY MEDICO DISPONIBLE HOY"),
    ]

    y = margin
    draw.text((margin, y), "MINSA / SIS — CENTRO DE SALUD SAN JUAN DE MIRAFLORES", fill=(10, 10, 10), font=title_font)
    y += 32
    draw.text((margin, y), "OFICINA DE ADMISION Y REGISTROS MEDICOS", fill=(60, 60, 60), font=sub_font)
    y += 28
    draw.line([(margin, y), (width - margin, y)], fill=(80, 80, 80), width=2)
    y += 16
    draw.text((margin, y), "CONSTANCIA DE DENEGACION DE ATENCION", fill=(10, 10, 10), font=title_font)
    y += 44

    for label, value in lines:
        draw.text((margin, y), label, fill=(90, 90, 90), font=label_font)
        draw.text((margin + 290, y), value, fill=(10, 10, 10), font=body_font)
        y += 38

    y += 20
    draw.line([(margin, y), (margin + 240, y)], fill=(120, 120, 120), width=1)
    draw.text((margin, y + 6), "Sello y firma del responsable de admision", fill=(120, 120, 120), font=small_font)

    draw.rectangle(
        [(margin, height - margin - 26), (width - margin, height - margin - 6)],
        outline=(200, 0, 0),
        width=2,
    )
    draw.text(
        (margin + 8, height - margin - 24),
        "DOCUMENTO SINTETICO / NO REAL - USO DE PRUEBA UNICAMENTE",
        fill=(200, 0, 0),
        font=small_font,
    )

    img.save(FIXTURE_MINSA_PATH, format="PNG")


# ---------------------------------------------------------------------------
# pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def fixture_image() -> bytes:
    if not FIXTURE_PATH.exists():
        subprocess.run(
            [sys.executable, str(GENERATOR)], check=True, capture_output=True
        )
    assert FIXTURE_PATH.exists(), "Synthetic fixture was not generated."
    return FIXTURE_PATH.read_bytes()


@pytest.fixture(scope="module")
def fixture_abner() -> bytes:
    if not FIXTURE_ABNER_PATH.exists():
        _generate_abner_inline()
    assert FIXTURE_ABNER_PATH.exists(), "Abner fixture was not generated."
    return FIXTURE_ABNER_PATH.read_bytes()


@pytest.fixture(scope="module")
def fixture_minsa() -> bytes:
    if not FIXTURE_MINSA_PATH.exists():
        _generate_minsa_inline()
    assert FIXTURE_MINSA_PATH.exists(), "MINSA fixture was not generated."
    return FIXTURE_MINSA_PATH.read_bytes()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set; skipping live vision call.",
)
def test_vision_reads_synthetic_denial(fixture_image: bytes) -> None:
    agent = VisionAgent()
    result = agent.read_document(fixture_image, mime_type="image/png")

    assert isinstance(result, VisionOutput)
    assert result.document_type == "appointment_denial", (
        f"Expected appointment_denial, got {result.document_type}. "
        f"Warnings: {result.warnings}"
    )
    assert result.hospital_network == "EsSalud"
    assert result.confidence >= 0.3
    assert isinstance(result.warnings, list)
    # Synthetic slip explicitly mentions Rebagliati; the model should find it.
    assert result.hospital_name and "Rebagliati" in result.hospital_name


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set; skipping live vision call.",
)
def test_vision_reads_abner_denial(fixture_abner: bytes) -> None:
    agent = VisionAgent()
    result = agent.read_document(fixture_abner, mime_type="image/png")

    assert isinstance(result, VisionOutput)
    assert result.document_type == "appointment_denial", (
        f"Expected appointment_denial, got {result.document_type}. "
        f"Warnings: {result.warnings}"
    )
    assert result.hospital_network == "EsSalud", (
        f"Expected EsSalud, got {result.hospital_network}"
    )
    assert result.patient_name is not None and "abner" in result.patient_name.lower(), (
        f"Expected patient name containing 'ABNER', got {result.patient_name!r}"
    )
    assert result.confidence >= 0.7, (
        f"Expected confidence >= 0.7, got {result.confidence}"
    )


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set; skipping live vision call.",
)
def test_vision_reads_minsa_denial(fixture_minsa: bytes) -> None:
    agent = VisionAgent()
    result = agent.read_document(fixture_minsa, mime_type="image/png")

    assert isinstance(result, VisionOutput)
    assert result.document_type == "appointment_denial", (
        f"Expected appointment_denial, got {result.document_type}. "
        f"Warnings: {result.warnings}"
    )
    assert result.hospital_network == "MINSA", (
        f"Expected MINSA, got {result.hospital_network}"
    )
    assert result.confidence >= 0.5, (
        f"Expected confidence >= 0.5, got {result.confidence}"
    )
