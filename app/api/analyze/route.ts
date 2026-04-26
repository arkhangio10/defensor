import { randomUUID } from "node:crypto";

import { NextResponse } from "next/server";

import { saveCase } from "@/lib/case-storage";
import type { AnalysisResult, VisionOutput } from "@/lib/types";

const AGENTS_URL = process.env.AGENTS_URL || "http://localhost:8000";

export async function POST(req: Request): Promise<NextResponse> {
  const form = await req.formData();
  const file = form.get("document");

  if (!(file instanceof File)) {
    return NextResponse.json(
      { error: "Falta el archivo 'document' en el formulario." },
      { status: 400 },
    );
  }

  // Step 1 — Vision Agent: read the document image
  const upstream = new FormData();
  upstream.append("document", file, file.name);

  let visionRes: Response;
  try {
    visionRes = await fetch(`${AGENTS_URL}/vision`, {
      method: "POST",
      body: upstream,
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : "conexión rechazada";
    return NextResponse.json(
      {
        error:
          "No se pudo conectar al servicio de agentes. " +
          "¿Está corriendo 'npm run agents' en el puerto 8000?",
        detail: msg,
      },
      { status: 502 },
    );
  }

  if (!visionRes.ok) {
    const detail = await visionRes.text();
    return NextResponse.json(
      { error: "El Agente Visión rechazó el documento.", detail },
      { status: visionRes.status },
    );
  }

  const vision = (await visionRes.json()) as VisionOutput;
  const caseId = randomUUID();

  // Step 2 — Analysis pipeline: violation → channel → drafter
  let analysis: AnalysisResult | undefined;
  try {
    const analyzeRes = await fetch(`${AGENTS_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ vision_output: vision }),
    });

    if (analyzeRes.ok) {
      analysis = (await analyzeRes.json()) as AnalysisResult;
    }
    // If analysis fails, we still save the vision result and show partial results.
  } catch {
    // Non-fatal: save vision alone, show partial results page.
  }

  await saveCase(caseId, vision, analysis);
  return NextResponse.json({ caseId });
}
