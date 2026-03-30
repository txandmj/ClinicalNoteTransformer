import type { SentenceComparisonItem, StructuredClinicalOutput } from "../types";

export function normalizeStructured(input: StructuredClinicalOutput): StructuredClinicalOutput {
  const rows: SentenceComparisonItem[] = Array.isArray(input.sentence_comparisons)
    ? input.sentence_comparisons.map((row) => ({
        sentence_index: row.sentence_index ?? 0,
        revised: row.revised ?? "",
        source: row.source ?? "",
        reason: row.reason ?? "",
      }))
    : [];

  return {
    chief_complaint: input.chief_complaint ?? "",
    original_hpi: input.original_hpi ?? "",
    hpi_summary: input.hpi_summary ?? "",
    key_findings: Array.isArray(input.key_findings) ? [...input.key_findings] : [],
    suspected_conditions: Array.isArray(input.suspected_conditions) ? [...input.suspected_conditions] : [],
    disposition_recommendation: input.disposition_recommendation ?? "Unknown",
    uncertainties: Array.isArray(input.uncertainties) ? [...input.uncertainties] : [],
    revised_hpi: input.revised_hpi ?? "",
    sentence_comparisons: rows,
  };
}
