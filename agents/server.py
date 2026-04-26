"""FastAPI server that exposes Defensor's Python agents to the Next.js frontend.

Run locally with:
    uvicorn agents.server:app --reload --port 8000

Next.js API routes POST multipart/form-data here. No auth, same-machine only.
Fly.io deployment will layer auth on top.
"""

from __future__ import annotations

import io

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agents.vision import VisionAgent
from agents.violation import ViolationAgent
from agents.channel import ChannelAgent
from agents.drafter import DrafterAgent

app = FastAPI(
    title="Defensor Agents",
    description="Python agent workers for the Defensor legal advocate.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://defensor-sage.vercel.app", "http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Lazy singletons — constructed on the first request so the server can boot
# for health checks even before ANTHROPIC_API_KEY is wired up.
# ---------------------------------------------------------------------------

_vision: VisionAgent | None = None
_violation: ViolationAgent | None = None
_channel: ChannelAgent | None = None
_drafter: DrafterAgent | None = None


def _get_vision() -> VisionAgent:
    global _vision
    if _vision is None:
        _vision = VisionAgent()
    return _vision


def _get_violation() -> ViolationAgent:
    global _violation
    if _violation is None:
        _violation = ViolationAgent()
    return _violation


def _get_channel() -> ChannelAgent:
    global _channel
    if _channel is None:
        _channel = ChannelAgent()
    return _channel


def _get_drafter() -> DrafterAgent:
    global _drafter
    if _drafter is None:
        _drafter = DrafterAgent()
    return _drafter


ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}
PDF_MIME = "application/pdf"


def _pdf_to_png(pdf_bytes: bytes) -> bytes:
    """Convert first page of a PDF to PNG bytes using pypdfium2."""
    import pypdfium2 as pdfium  # lazy import — only needed for PDF uploads

    pdf = pdfium.PdfDocument(pdf_bytes)
    page = pdf[0]
    bitmap = page.render(scale=2)  # 2× scale for readable quality
    pil_image = bitmap.to_pil()
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class ViolationRequest(BaseModel):
    vision_output: dict[str, object]


class ChannelRequest(BaseModel):
    hospital_network: str
    violations: list[dict[str, object]]
    country: str = "peru"


class DrafterRequest(BaseModel):
    vision_output: dict[str, object]
    violations: list[dict[str, object]]
    recommended_channel: str


class AnalyzeRequest(BaseModel):
    vision_output: dict[str, object]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "defensor-agents"}


@app.post("/vision")
async def vision(document: UploadFile = File(...)) -> JSONResponse:
    mime = document.content_type or ""

    if mime not in ALLOWED_MIME and mime != PDF_MIME:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Tipo de archivo no soportado: {mime}. "
                "Permitidos: JPEG, PNG, WEBP, GIF, PDF."
            ),
        )

    image_bytes = await document.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Archivo vacío.")

    if mime == PDF_MIME:
        try:
            image_bytes = _pdf_to_png(image_bytes)
            mime = "image/png"
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"No se pudo convertir el PDF a imagen: {e}",
            ) from e

    try:
        result = _get_vision().read_document(image_bytes, mime)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    return JSONResponse(result.model_dump())


@app.post("/violation")
async def violation(body: ViolationRequest) -> JSONResponse:
    """Run the Violation Agent on an existing vision output.

    Body: { "vision_output": { ...VisionOutput fields... } }
    Returns: ViolationOutput JSON.
    """
    try:
        result = _get_violation().analyze(body.vision_output)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    return JSONResponse(result.model_dump())


@app.post("/channel")
async def channel(body: ChannelRequest) -> JSONResponse:
    """Run the Channel Agent to determine where to file a complaint.

    Body: { "hospital_network": "EsSalud", "violations": [...], "country": "peru" }
    Returns: ChannelOutput JSON.
    """
    try:
        result = _get_channel().route(
            hospital_network=body.hospital_network,
            violations=body.violations,
            country=body.country,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    return JSONResponse(result.model_dump())


@app.post("/drafter")
async def drafter(body: DrafterRequest) -> JSONResponse:
    """Run the Drafter Agent to produce a formal complaint letter.

    Body: { "vision_output": {...}, "violations": [...], "recommended_channel": "SUSALUD" }
    Returns: DrafterOutput JSON.
    """
    try:
        result = _get_drafter().draft(
            vision_output=body.vision_output,
            violations=body.violations,
            recommended_channel=body.recommended_channel,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    return JSONResponse(result.model_dump())


@app.post("/analyze")
async def analyze(body: AnalyzeRequest) -> JSONResponse:
    """Orchestration endpoint: violation → channel → drafter in sequence.

    Accepts a VisionOutput dict, runs all three downstream agents, and returns
    their combined results in a single response.

    Body: { "vision_output": { ...VisionOutput fields... } }
    Returns: { "violation": {...}, "channel": {...}, "draft": {...} }
    """
    vision_output = body.vision_output

    # Step 1 — violations
    try:
        violation_result = _get_violation().analyze(vision_output)
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Error en el Agente de Violaciones: {e}",
        ) from e

    # Step 2 — channel (deterministic routing + explanation)
    hospital_network = str(vision_output.get("hospital_network", "unknown"))
    violations_list: list[dict[str, object]] = [
        v.model_dump() for v in violation_result.violations
    ]
    try:
        channel_result = _get_channel().route(
            hospital_network=hospital_network,
            violations=violations_list,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Error en el Agente de Canal: {e}",
        ) from e

    # Step 3 — draft the complaint letter
    try:
        draft_result = _get_drafter().draft(
            vision_output=vision_output,
            violations=violations_list,
            recommended_channel=channel_result.primary_channel,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Error en el Agente Redactor: {e}",
        ) from e

    return JSONResponse(
        {
            "violation": violation_result.model_dump(),
            "channel": channel_result.model_dump(),
            "draft": draft_result.model_dump(),
        }
    )
