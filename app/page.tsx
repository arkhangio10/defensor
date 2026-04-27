"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";

const ACCEPTED = "image/jpeg,image/png,image/heic,image/heif,application/pdf";
const MAX_MB = 15;
const AGENTS_URL =
  process.env.NEXT_PUBLIC_AGENTS_URL || "http://localhost:8000";

interface BatchEntry {
  caseId: string;
  fileName: string;
}

export default function UploadPage(): React.ReactElement {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progressPct, setProgressPct] = useState(0);
  const [progressLabel, setProgressLabel] = useState<string | null>(null);

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
    setProgressPct(0);

    const totalSteps = files.length * 2; // vision + analyze per file
    let stepsDone = 0;
    const advance = (label: string): void => {
      stepsDone += 1;
      setProgressPct(Math.round((stepsDone / totalSteps) * 100));
      setProgressLabel(label);
    };

    const batch: BatchEntry[] = [];

    try {
      for (const [i, file] of files.entries()) {
        const n = `${i + 1}/${files.length}`;
        setProgressLabel(`Leyendo documento ${n}…`);

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
        advance(`Identificando violaciones legales ${n}…`);

        const analyzeRes = await fetch(`${AGENTS_URL}/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ vision_output: vision }),
        });
        const analysis = analyzeRes.ok ? await analyzeRes.json() : undefined;
        advance(`Documento ${n} listo.`);

        const caseId = crypto.randomUUID();
        sessionStorage.setItem(
          `case:${caseId}`,
          JSON.stringify({
            caseId,
            createdAt: new Date().toISOString(),
            fileName: file.name,
            vision,
            analysis,
          }),
        );
        batch.push({ caseId, fileName: file.name });
      }

      // Persist the batch so the result page can show pagination
      sessionStorage.setItem("batch:lastUpload", JSON.stringify(batch));
      const first = batch[0];
      if (first) router.push(`/result/${first.caseId}`);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Error desconocido";
      setError(`No pudimos analizar el documento: ${msg}`);
      setIsAnalyzing(false);
      setProgressLabel(null);
      setProgressPct(0);
    }
  }

  return (
    <main className="min-h-screen bg-white text-slate-900">
      <nav className="border-b border-slate-100">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-5">
          <div className="flex items-center gap-3">
            <span className="inline-block h-3 w-3 rounded-full bg-rose-400" />
            <span className="text-base font-semibold tracking-tight text-slate-900">
              Defensor
            </span>
          </div>
          <div className="text-xs uppercase tracking-[0.2em] text-slate-500">
            Perú · ES
          </div>
        </div>
      </nav>

      <section className="mx-auto max-w-5xl px-6 pt-16 pb-10 md:pt-24">
        <div className="grid gap-12 md:grid-cols-12">
          <div className="md:col-span-7">
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-rose-500">
              <span className="inline-block h-2 w-2 rounded-full bg-rose-400" />
              Defensoría legal con IA
            </div>
            <h1 className="mt-4 text-4xl font-semibold leading-[1.05] tracking-tight text-slate-900 md:text-6xl">
              Te negaron atención.
              <br />
              <span className="text-rose-500">Nosotros sí la leemos.</span>
            </h1>
            <p className="mt-6 max-w-xl text-base leading-relaxed text-slate-600 md:text-lg">
              Sube la foto de tu cita denegada, receta incumplida o alta
              forzada. Defensor identifica qué artículo de la ley se violó y
              redacta tu reclamo formal — en minutos.
            </p>
          </div>

          <aside className="md:col-span-5">
            <ol className="space-y-4 text-sm text-slate-700">
              {[
                "Lee tu documento con visión de alta resolución",
                "Cita el artículo de la Ley 29414 vulnerado",
                "Redacta tu reclamo en registro legal peruano",
                "Elige el canal correcto: SUSALUD, Defensoría, amparo",
              ].map((line, i) => (
                <li key={i} className="flex gap-3">
                  <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-rose-300 text-[11px] font-semibold text-rose-500">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span>{line}</span>
                </li>
              ))}
            </ol>
          </aside>
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-24">
        <form onSubmit={onSubmit} className="flex flex-col gap-5">
          <label
            htmlFor="document"
            className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50/60 px-6 py-16 text-center transition-colors hover:border-rose-300 hover:bg-rose-50/40"
          >
            <div className="text-base font-medium text-slate-900">
              {files.length === 0
                ? "Toca aquí para elegir una foto o PDF"
                : files.length === 1
                  ? (files[0]?.name ?? "")
                  : `${files.length} archivos seleccionados`}
            </div>
            <div className="text-xs text-slate-500">
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

          {files.length > 1 && !isAnalyzing && (
            <ul className="space-y-1 rounded-md border border-slate-100 bg-white px-4 py-3 text-xs text-slate-600">
              {files.map((f, i) => (
                <li
                  key={i}
                  className="flex items-center justify-between gap-2 py-1"
                >
                  <span className="truncate">
                    <span className="mr-2 text-rose-500">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    {f.name}
                  </span>
                  <span className="shrink-0 text-slate-400">
                    {(f.size / 1024 / 1024).toFixed(1)} MB
                  </span>
                </li>
              ))}
            </ul>
          )}

          {isAnalyzing && (
            <div className="rounded-md border border-slate-200 bg-slate-50 px-4 py-4">
              <div className="flex items-center justify-between text-xs text-slate-700">
                <span>{progressLabel ?? "Analizando…"}</span>
                <span className="font-mono text-slate-500">
                  {progressPct}%
                </span>
              </div>
              <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-200">
                <div
                  className="h-full bg-rose-500 transition-all duration-300"
                  style={{ width: `${progressPct}%` }}
                />
              </div>
            </div>
          )}

          {error && (
            <div
              role="alert"
              className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isAnalyzing || files.length === 0}
            className="group inline-flex h-12 items-center justify-between rounded-full bg-slate-900 px-6 text-sm font-medium text-white transition-colors hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <span>
              {isAnalyzing
                ? "Procesando documentos…"
                : files.length > 1
                  ? `Analizar ${files.length} documentos`
                  : "Analizar documento"}
            </span>
            <span className="ml-3 inline-flex h-8 w-8 items-center justify-center rounded-full bg-rose-500 text-white transition-transform group-hover:translate-x-1">
              →
            </span>
          </button>

          <p className="text-center text-xs text-slate-500">
            Tus datos quedan en tu sesión. No los compartimos con nadie.
          </p>
        </form>
      </section>

      <footer className="border-t border-slate-100">
        <div className="mx-auto max-w-5xl px-6 py-6 text-center text-xs text-slate-500">
          Defensor no reemplaza a un abogado. Esta es información legal, no
          asesoría legal.
        </div>
      </footer>
    </main>
  );
}
