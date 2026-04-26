"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";

const ACCEPTED = "image/jpeg,image/png,image/heic,image/heif,application/pdf";
const MAX_MB = 15;
const AGENTS_URL =
  process.env.NEXT_PUBLIC_AGENTS_URL || "http://localhost:8000";

export default function UploadPage(): React.ReactElement {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState<string | null>(null);

  function onPick(selected: File[]): void {
    setError(null);
    const oversized = selected.find((f) => f.size > MAX_MB * 1024 * 1024);
    if (oversized) {
      setError(
        `"${oversized.name}" excede ${MAX_MB} MB. Intenta con una foto más liviana.`,
      );
      return;
    }
    setFiles(selected);
  }

  async function onSubmit(
    e: React.FormEvent<HTMLFormElement>,
  ): Promise<void> {
    e.preventDefault();
    if (files.length === 0) {
      setError("Selecciona al menos un documento.");
      return;
    }
    setIsAnalyzing(true);
    setError(null);

    try {
      for (const [i, file] of files.entries()) {
        setProgress(`Analizando documento ${i + 1} de ${files.length}…`);

        // Step 1 — Vision: send file directly to Railway
        const visionFd = new FormData();
        visionFd.append("document", file);
        const visionRes = await fetch(`${AGENTS_URL}/vision`, {
          method: "POST",
          body: visionFd,
        });
        if (!visionRes.ok) {
          const detail = await visionRes.text();
          throw new Error(`Agente Visión: ${detail}`);
        }
        const vision = await visionRes.json();

        // Step 2 — Analysis: violation + channel + drafter
        setProgress(
          `Identificando violaciones legales (${i + 1}/${files.length})…`,
        );
        const analyzeRes = await fetch(`${AGENTS_URL}/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ vision_output: vision }),
        });
        const analysis = analyzeRes.ok ? await analyzeRes.json() : undefined;

        // Store in sessionStorage so the result page can read it
        const caseId = crypto.randomUUID();
        sessionStorage.setItem(
          `case:${caseId}`,
          JSON.stringify({
            caseId,
            createdAt: new Date().toISOString(),
            vision,
            analysis,
          }),
        );

        // Navigate to first result
        if (i === 0) {
          router.push(`/result/${caseId}`);
          return;
        }
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Error desconocido";
      setError(`No pudimos analizar el documento: ${msg}`);
      setIsAnalyzing(false);
      setProgress(null);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-between px-6 py-10">
      <header>
        <div className="text-xs uppercase tracking-widest text-neutral-500">
          Defensor · Perú
        </div>
        <h1 className="mt-2 text-3xl font-semibold text-neutral-900 md:text-4xl">
          Te negaron atención. <br />
          Nosotros sí la leemos.
        </h1>
        <p className="mt-4 max-w-xl text-neutral-600">
          Sube la foto de tu cita denegada, receta incumplida o alta forzada.
          Defensor identifica qué artículo de la ley se violó y redacta tu
          reclamo formal — en minutos.
        </p>
      </header>

      <form onSubmit={onSubmit} className="mt-10 flex flex-col gap-4">
        <label
          htmlFor="document"
          className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-neutral-300 bg-neutral-50 px-6 py-12 text-center transition-colors hover:border-neutral-400 hover:bg-neutral-100"
        >
          <div className="text-sm font-medium text-neutral-900">
            {files.length === 0
              ? "Toca aquí para elegir una foto o PDF"
              : files.length === 1
                ? (files[0]?.name ?? "")
                : `${files.length} archivos seleccionados`}
          </div>
          <div className="text-xs text-neutral-500">
            JPG, PNG, HEIC o PDF · hasta {MAX_MB} MB · puedes elegir varios
          </div>
          <input
            ref={inputRef}
            id="document"
            name="document"
            type="file"
            accept={ACCEPTED}
            multiple
            className="sr-only"
            onChange={(e) => onPick(Array.from(e.target.files ?? []))}
          />
        </label>

        {error && (
          <div
            role="alert"
            className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
          >
            {error}
          </div>
        )}

        <Button
          type="submit"
          size="lg"
          disabled={isAnalyzing || files.length === 0}
        >
          {isAnalyzing
            ? (progress ?? "Analizando documento…")
            : "Analizar documento"}
        </Button>

        <p className="text-center text-xs text-neutral-500">
          Tus datos quedan en tu sesión. No los compartimos con nadie.
        </p>
      </form>

      <footer className="mt-16 border-t border-neutral-200 pt-4 text-xs text-neutral-500">
        Defensor no reemplaza a un abogado. Esta es información legal, no
        asesoría legal.
      </footer>
    </main>
  );
}
