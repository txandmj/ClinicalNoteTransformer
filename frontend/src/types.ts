/** Mirrors backend Pydantic enums / fields (snake_case). */

export type Disposition = "Admit" | "Observe" | "Discharge" | "Unknown";

export interface StructuredClinicalOutput {
  chief_complaint: string;
  hpi_summary: string;
  key_findings: string[];
  suspected_conditions: string[];
  disposition_recommendation: Disposition;
  uncertainties: string[];
  revised_hpi: string;
}

export interface SavedCase {
  id: string;
  title: string | null;
  original_note: string;
  structured_output: StructuredClinicalOutput;
  /** 'machine' | 'user' — last author of structured_output */
  source: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface GenerateResponse {
  structured: StructuredClinicalOutput;
  prompt_version: string;
  model: string;
  raw_cot_trace: string | null;
}
