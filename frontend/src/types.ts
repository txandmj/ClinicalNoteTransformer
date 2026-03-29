/** Mirrors backend Pydantic enums / fields (snake_case). */

export type Disposition = "Admit" | "Observe" | "Discharge" | "Unknown";

export interface SentenceComparisonItem {
  sentence_index: number;
  revised: string;
  source: string;
  reason: string;
}

export interface StructuredClinicalOutput {
  chief_complaint: string;
  /** §2 Original HPI — from source notes only */
  original_hpi: string;
  /** Short structured summary (rubric) */
  hpi_summary: string;
  key_findings: string[];
  suspected_conditions: string[];
  disposition_recommendation: Disposition;
  uncertainties: string[];
  /** §3 Clean revised HPI */
  revised_hpi: string;
  /** §4 Sentence-by-sentence comparison rows */
  sentence_comparisons: SentenceComparisonItem[];
}

export interface SavedCase {
  id: string;
  title: string | null;
  original_note: string;
  structured_output: StructuredClinicalOutput;
  /** 'machine' | 'user' — last author of structured_output */
  source: string;
  /** Saved snapshot for human-edit diff vs structured_output.revised_hpi */
  revised_hpi_baseline?: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface TokenUsage {
  input_tokens?: number | null;
  output_tokens?: number | null;
  cache_read_input_tokens?: number | null;
  cache_creation_input_tokens?: number | null;
}

export interface GenerateResponse {
  structured: StructuredClinicalOutput;
  prompt_version: string;
  model: string;
  raw_cot_trace: string | null;
  usage: TokenUsage | null;
}

export interface GuidelinePreset {
  id: string;
  title: string;
}
