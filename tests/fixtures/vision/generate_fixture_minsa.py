"""Generate a synthetic MINSA/SIS appointment-denial slip for Rosa Elena Mamani Condori.

This is a FAKE document. It exists solely to exercise the Vision Agent
pipeline. Every copy is watermarked SINTÉTICO / NO REAL in the visible
footer so it cannot contaminate the gold-standard test set.

Run: python tests/fixtures/vision/generate_fixture_minsa.py
Output: tests/fixtures/vision/fixture_minsa_denial.png
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_PATH = Path(__file__).parent / "fixture_minsa_denial.png"

WIDTH, HEIGHT = 900, 600
MARGIN = 60

HEADER = "MINSA / SIS — CENTRO DE SALUD SAN JUAN DE MIRAFLORES"
SUBHEADER = "OFICINA DE ADMISION Y REGISTROS MEDICOS"
DOC_TITLE = "CONSTANCIA DE DENEGACION DE ATENCION"

LINES: list[tuple[str, str]] = [
    ("Paciente:", "ROSA ELENA MAMANI CONDORI"),
    ("DNI:", "71234567"),
    ("Fecha de emision:", "10/04/2026"),
    ("Especialidad solicitada:", "MEDICINA GENERAL"),
    ("Motivo de denegacion:", "NO HAY MEDICO DISPONIBLE HOY"),
]

FOOTER_NOTICE = "DOCUMENTO SINTETICO / NO REAL - USO DE PRUEBA UNICAMENTE"


def _font(size: int) -> ImageFont.ImageFont:
    for name in ("arial.ttf", "Arial.ttf", "consola.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def render() -> Path:
    img = Image.new("RGB", (WIDTH, HEIGHT), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    title_font = _font(22)
    sub_font = _font(16)
    body_font = _font(20)
    label_font = _font(18)
    small_font = _font(13)

    y = MARGIN
    draw.text((MARGIN, y), HEADER, fill=(10, 10, 10), font=title_font)
    y += 32
    draw.text((MARGIN, y), SUBHEADER, fill=(60, 60, 60), font=sub_font)
    y += 28
    draw.line([(MARGIN, y), (WIDTH - MARGIN, y)], fill=(80, 80, 80), width=2)
    y += 16
    draw.text((MARGIN, y), DOC_TITLE, fill=(10, 10, 10), font=title_font)
    y += 44

    for label, value in LINES:
        draw.text((MARGIN, y), label, fill=(90, 90, 90), font=label_font)
        draw.text((MARGIN + 290, y), value, fill=(10, 10, 10), font=body_font)
        y += 38

    y += 20
    draw.line([(MARGIN, y), (MARGIN + 240, y)], fill=(120, 120, 120), width=1)
    draw.text(
        (MARGIN, y + 6),
        "Sello y firma del responsable de admision",
        fill=(120, 120, 120),
        font=small_font,
    )

    draw.rectangle(
        [
            (MARGIN, HEIGHT - MARGIN - 26),
            (WIDTH - MARGIN, HEIGHT - MARGIN - 6),
        ],
        outline=(200, 0, 0),
        width=2,
    )
    draw.text(
        (MARGIN + 8, HEIGHT - MARGIN - 24),
        FOOTER_NOTICE,
        fill=(200, 0, 0),
        font=small_font,
    )

    img.save(OUT_PATH, format="PNG")
    return OUT_PATH


if __name__ == "__main__":
    path = render()
    print(f"Wrote {path}")
