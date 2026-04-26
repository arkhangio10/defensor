"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";

const ACCEPTED = "image/jpeg,image/png,image/heic,image/heif,application/pdf";
const MAX_MB = 15;

export default function UploadPage(): React.ReactElement {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  function onPick(selected: File | null): void {
    setError(null);
    if (!selected) {
      setFile(null);
      return;
    }
    if (selected.size > MAX_MB * 1024 * 1024) {
      setError(`El archivo excede ${MAX_MB} MB. Intenta con una foto más liviana.`);
      return;
    }
    setFile(selected);
  }

  async function onSubmit(e: React.FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault();
    if (!file) {
      setError("Selecciona un documento primero.");
      return;
    }
    setIsAnalyzing(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("document", file);
      const res = await fetch("/api/analyze", { method: "POST", body: fd });
      if (!res.ok) {
        const body = await res.text();
        throw new Error(body || `Error ${res.status}`);
      }
      const data = (await res.json()) as { caseId: string };
      router.push(`/result/${data.caseId}`);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Error desconocido";
      setError(`No pudimos analizar el documento: ${msg}`);
      setIsAnalyzing(false);
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
            {file ? file.name : "Toca aquí para elegir una foto o PDF"}
          </div>
          <div className="text-xs text-neutral-500">
            JPG, PNG, HEIC o PDF · hasta {MAX_MB} MB
          </div>
          <input
            ref={inputRef}
            id="document"
            name="document"
            type="file"
            accept={ACCEPTED}
            className="sr-only"
            onChange={(e) => onPick(e.target.files?.[0] ?? null)}
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

        <Button type="submit" size="lg" disabled={isAnalyzing || !file}>
          {isAnalyzing ? "Analizando documento…" : "Analizar documento"}
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
