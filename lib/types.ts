export type DocumentType =
  | "appointment_denial"
  | "prescription"
  | "discharge"
  | "insurance_card"
  | "medical_history"
  | "lab_result"
  | "other";

export type HospitalNetwork =
  | "EsSalud"
  | "MINSA"
  | "EPS"
  | "private"
  | "unknown";

export type ViolationType = "confirmada" | "posible" | "no_aplica";
export type Severity = "alta" | "media" | "baja";
export type FilingMethod = "presencial" | "virtual" | "ambos";

export interface VisionOutput {
  document_type: DocumentType;
  hospital_name: string | null;
  hospital_network: HospitalNetwork;
  patient_name: string | null;
  patient_dni: string | null;
  date_of_document: string | null;
  date_of_attempted_care: string | null;
  specialty_requested: string | null;
  reason_given: string | null;
  reason_given_translated_plain_spanish: string;
  raw_text_extracted: string;
  confidence: number;
  warnings: string[];
}

export interface ViolationItem {
  article: string;
  article_text_excerpt: string;
  violation_type: ViolationType;
  explanation: string;
  severity: Severity;
}

export interface ViolationOutput {
  violations: ViolationItem[];
  summary: string;
  recommended_channel: string;
  complaint_viable: boolean;
  confidence: number;
}

export interface ChannelOutput {
  primary_channel: string;
  secondary_channel: string | null;
  channel_url: string | null;
  explanation: string;
  filing_method: FilingMethod;
  estimated_response_days: number;
}

export interface DrafterOutput {
  letter_text: string;
  addressee: string;
  subject: string;
  legal_articles_cited: string[];
  patient_request: string;
  estimated_response_days: number;
  disclaimer: string;
  warnings: string[];
}

export interface AnalysisResult {
  violation: ViolationOutput;
  channel: ChannelOutput;
  draft: DrafterOutput;
}
