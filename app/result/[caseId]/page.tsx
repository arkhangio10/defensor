import Link from "next/link";
import { notFound } from "next/navigation";

import { loadCase } from "@/lib/case-storage";
import type {
  DocumentType,
  HospitalNetwork,
  Severity,
  ViolationItem,
  ViolationType,
} from "@/lib/types";

const DOC_TYPE_LABEL: Record<DocumentType, string> = {
  appointment_denial: "Cita denegada",
  prescription: "Receta médica",
  discharge: "Alta hospitalaria",
  insurance_card: "Carnet de seguro",
  medical_history: "Historia clínica",
  lab_result: "Resultado de laboratorio",
  other: "Otro documento",
};

const NETWORK_LABEL: Record<HospitalNetwork, string> = {
  EsSalud: "EsSalud",
  MINSA: "MINSA",
  EPS: "EPS privada",
  private: "Clínica privada",
  unknown: "Red no identificada",
};

const SEVERITY_COLOR: Record<Severity, string> = {
  alta: "bg-red-100 text-red-800 border-red-200",
  media: "bg-amber-100 text-amber-800 border-amber-200",
  baja: "bg-blue-100 text-blue-800 border-blue-200",
};

const VIOLATION_TYPE_LABEL: Record<ViolationType, string> = {
  confirmada: "Confirmada",
  posible: "Posible",
  no_aplica: "No aplica",
};

function Field({
  label,
  value,
}: {
  label: string;
  value: string | null;
}): React.ReactElement {
  return (
    <div className="border-b border-neutral-100 py-2 last:border-0">
      <div className="text-xs uppercase tracking-wide text-neutral-500">
        {label}
      </div>
      <div className="mt-1 text-sm text-neutral-900">
        {value ?? <span className="text-neutral-400">— no detectado —</span>}
      </div>
    </div>
  );
}

function ViolationCard({
  item,
}: {
  item: ViolationItem;
}): React.ReactElement {
  return (
    <div
      className={`rounded-md border p-4 ${SEVERITY_COLOR[item.severity]}`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-semibold">{item.article}</span>
        <span className="rounded-full border px-2 py-0.5 text-xs font-medium">
          {VIOLATION_TYPE_LABEL[item.violation_type]}
        </span>
      </div>
      <p className="mt-1 text-xs italic opacity-75">{item.article_text_excerpt}</p>
      <p className="mt-2 text-sm">{item.explanation}</p>
    </div>
  );
}

export default async function ResultPage({
  params,
}: {
  params: Promise<{ caseId: string }>;
}): Promise<React.ReactElement> {
  const { caseId } = await params;
  const stored = await loadCase(caseId);
  if (!stored) notFound();

  const v = stored.vision;
  const analysis = stored.analysis;
  const confidencePct = Math.round(v.confidence * 100);

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col px-6 py-10">
      <div className="text-xs uppercase tracking-widest text-neutral-500">
        Caso #{caseId.slice(0, 8)}
      </div>

      <h1 className="mt-2 text-2xl font-semibold text-neutral-900">
        {DOC_TYPE_LABEL[v.document_type]}
      </h1>
      <p className="mt-1 text-sm text-neutral-600">
        {NETWORK_LABEL[v.hospital_network]}
        {v.hospital_name ? ` · ${v.hospital_name}` : ""}
      </p>

      <div className="mt-4 inline-flex w-fit items-center gap-2 rounded-full bg-neutral-100 px-3 py-1 text-xs text-neutral-700">
        <span className="font-medium">Confianza de lectura:</span>
        <span>{confidencePct}%</span>
      </div>

      {v.warnings.length > 0 && (
        <section className="mt-6 rounded-md border border-amber-200 bg-amber-50 p-4">
          <div className="text-sm font-medium text-amber-900">
            Advertencias del lector
          </div>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-900">
            {v.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </section>
      )}

      <section className="mt-8">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-neutral-500">
          Datos extraídos
        </h2>
        <div className="mt-2 rounded-md border border-neutral-200 bg-white p-4">
          <Field label="Paciente" value={v.patient_name} />
          <Field label="DNI" value={v.patient_dni} />
          <Field label="Fecha del documento" value={v.date_of_document} />
          <Field
            label="Fecha de atención intentada"
            value={v.date_of_attempted_care}
          />
          <Field label="Especialidad solicitada" value={v.specialty_requested} />
          <Field label="Motivo (texto original)" value={v.reason_given} />
          <Field
            label="Motivo (en español llano)"
            value={v.reason_given_translated_plain_spanish}
          />
        </div>
      </section>

      {analysis ? (
        <>
          {/* Violations */}
          <section className="mt-8">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-neutral-500">
              Violaciones identificadas
            </h2>
            <p className="mt-1 text-sm text-neutral-600">
              {analysis.violation.summary}
            </p>
            <div className="mt-3 flex flex-col gap-3">
              {analysis.violation.violations.length === 0 ? (
                <p className="text-sm text-neutral-400">
                  No se identificaron violaciones claras.
                </p>
              ) : (
                analysis.violation.violations.map((item, i) => (
                  <ViolationCard key={i} item={item} />
                ))
              )}
            </div>
          </section>

          {/* Channel */}
          <section className="mt-8 rounded-md border border-neutral-200 bg-white p-4">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-neutral-500">
              Dónde presentar tu queja
            </h2>
            <div className="mt-3">
              <div className="text-base font-semibold text-neutral-900">
                {analysis.channel.primary_channel}
              </div>
              {analysis.channel.secondary_channel && (
                <div className="mt-0.5 text-sm text-neutral-500">
                  Alternativa: {analysis.channel.secondary_channel}
                </div>
              )}
              <p className="mt-2 text-sm text-neutral-700">
                {analysis.channel.explanation}
              </p>
              <div className="mt-3 flex flex-wrap gap-3 text-xs text-neutral-500">
                <span>
                  Modalidad:{" "}
                  <strong className="text-neutral-700">
                    {analysis.channel.filing_method}
                  </strong>
                </span>
                <span>
                  Plazo de respuesta:{" "}
                  <strong className="text-neutral-700">
                    {analysis.channel.estimated_response_days} días
                  </strong>
                </span>
              </div>
              {analysis.channel.channel_url && (
                <a
                  href={analysis.channel.channel_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-3 inline-block text-sm text-blue-600 underline underline-offset-4 hover:text-blue-800"
                >
                  Ir al portal oficial →
                </a>
              )}
            </div>
          </section>

          {/* Complaint letter */}
          <section className="mt-8">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-neutral-500">
              Carta de queja formal
            </h2>
            <div className="mt-1 text-xs text-neutral-500">
              {analysis.draft.subject}
            </div>
            {analysis.draft.warnings.length > 0 && (
              <ul className="mt-2 list-disc pl-5 text-xs text-amber-700">
                {analysis.draft.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            )}
            <pre className="mt-3 overflow-auto whitespace-pre-wrap rounded-md border border-neutral-200 bg-neutral-50 p-4 text-sm text-neutral-800 leading-relaxed">
              {analysis.draft.letter_text}
            </pre>
            <p className="mt-3 text-xs text-neutral-500 italic">
              {analysis.draft.disclaimer}
            </p>
          </section>
        </>
      ) : (
        <section className="mt-8 rounded-md border border-neutral-200 bg-neutral-900 p-4 text-sm text-neutral-100">
          <div className="font-medium">Análisis legal en proceso</div>
          <p className="mt-1 text-neutral-300">
            El documento fue leído. El análisis legal (violaciones y carta de
            queja) no pudo completarse. Reintenta o contacta soporte.
          </p>
        </section>
      )}

      <section className="mt-8">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-neutral-500">
          Texto crudo leído del documento
        </h2>
        <pre className="mt-2 overflow-auto whitespace-pre-wrap rounded-md border border-neutral-200 bg-neutral-50 p-4 text-xs text-neutral-700">
          {v.raw_text_extracted || "(vacío)"}
        </pre>
      </section>

      <div className="mt-8">
        <Link
          href="/"
          className="text-sm text-neutral-600 underline underline-offset-4 hover:text-neutral-900"
        >
          ← Analizar otro documento
        </Link>
      </div>

      <footer className="mt-16 border-t border-neutral-200 pt-4 text-xs text-neutral-500">
        Defensor no reemplaza a un abogado. Esta es información legal, no
        asesoría legal.
      </footer>
    </main>
  );
}
