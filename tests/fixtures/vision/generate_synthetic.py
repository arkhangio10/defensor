"""Generate a synthetic EsSalud-style appointment-denial slip for Day-1 testing.

This is a FAKE document. It exists solely to exercise the Vision Agent
pipeline before real anonymized fixtures arrive on Day 2. Every copy we
generate is watermarked SINTÉTICO / NO REAL in the visible footer so it
cannot contaminate the gold-standard test set later.

Run: python tests/fixtures/vision/generate_synthetic.py
Output: tests/fixtures/vision/synthetic_denial.png
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_PATH = Path(__file__).parent / "synthetic_denial.png"

WIDTH, HEIGHT = 900, 1200
MARGIN = 60

HEADER = "ESSALUD — RED ASISTENCIAL REBAGLIATI"
SUBHEADER = "CENTRO DE ATENCION PRIMARIA III - SAN ISIDRO"
DOC_TITLE = "CONSTANCIA DE CITA"

LINES: list[tuple[str, str]] = [
    ("Paciente:", "ROSA ELENA MAMANI QUISPE"),
    ("DNI:", "45892137"),
    ("Fecha de emision:", "18/04/2026"),
    ("Fecha solicitada:", "22/04/2026"),
    ("Especialidad:", "CARDIOLOGIA"),
    ("Medico:", "DR. J. TORRES ALVAREZ"),
    ("Estado:", "NO ATENDIDO - SIN CUPO"),
    ("Reprogramacion:", "PROXIMA DISPONIBILIDAD 2026-07-15"),
    ("Observaciones:", "PACIENTE DEBE RETORNAR A SITEDS PARA NUEVA CITA"),
]

FOOTER_LEFT = "Sello y firma del responsable de admision"
FOOTER_RIGHT_NOTICE = "DOCUMENTO SINTETICO / NO REAL - USO DE PRUEBA UNICAMENTE"


def _font(size: int) -> ImageFont.ImageFont:
    for name in ("arial.ttf", "Arial.ttf", "consola.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def render() -> Path:
    img = Image.new("RGB", (WIDTH, HEIGHT), color=(250, 250, 248))
    draw = ImageDraw.Draw(img)

    title_font = _font(28)
    sub_font = _font(18)
    body_font = _font(22)
    label_font = _font(20)
    small_font = _font(14)

    y = MARGIN
    draw.text((MARGIN, y), HEADER, fill=(20, 20, 20), font=title_font)
    y += 38
    draw.text((MARGIN, y), SUBHEADER, fill=(60, 60, 60), font=sub_font)
    y += 36
    draw.line(
        [(MARGIN, y), (WIDTH - MARGIN, y)], fill=(100, 100, 100), width=2
    )
    y += 20
    draw.text((MARGIN, y), DOC_TITLE, fill=(20, 20, 20), font=title_font)
    y += 60

    for label, value in LINES:
        draw.text((MARGIN, y), label, fill=(90, 90, 90), font=label_font)
        draw.text((MARGIN + 230, y), value, fill=(10, 10, 10), font=body_font)
        y += 44

    y += 60
    draw.line(
        [(MARGIN, y), (MARGIN + 260, y)], fill=(120, 120, 120), width=1
    )
    draw.text(
        (MARGIN, y + 8),
        FOOTER_LEFT,
        fill=(120, 120, 120),
        font=small_font,
    )

    draw.rectangle(
        [
            (MARGIN, HEIGHT - MARGIN - 30),
            (WIDTH - MARGIN, HEIGHT - MARGIN - 10),
        ],
        outline=(200, 0, 0),
        width=2,
    )
    draw.text(
        (MARGIN + 8, HEIGHT - MARGIN - 28),
        FOOTER_RIGHT_NOTICE,
        fill=(200, 0, 0),
        font=small_font,
    )

    img.save(OUT_PATH, format="PNG")
    return OUT_PATH


if __name__ == "__main__":
    path = render()
    print(f"Wrote {path}")
