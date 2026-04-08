import { useState } from "react";
import { EditableFields } from "../EditableFields";
import { postExportFhir } from "../../lib/api";
import type { StructuredClinicalOutput, TokenUsage } from "../../types";

type Props = {
  structured: StructuredClinicalOutput | null;
  onStructuredChange: (next: StructuredClinicalOutput) => void;
  editedKeys: Set<string>;
  onFieldEdit: (fieldKey: string) => void;
  meta: { prompt_version?: string; model?: string; usage?: TokenUsage | null } | null;
  revisedHpiBaseline: string;
};

export function StructuredOutput({
  structured,
  onStructuredChange,
  editedKeys,
  onFieldEdit,
  meta,
  revisedHpiBaseline,
}: Props) {
  const [fhirBusy, setFhirBusy] = useState(false);
  const [fhirError, setFhirError] = useState<string | null>(null);

  async function downloadFhir() {
    if (!structured) return;
    setFhirError(null);
    setFhirBusy(true);
    try {
      const bundle = await postExportFhir(structured);
      const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/fhir+json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "clinical-summary-fhir-bundle.json";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setFhirError(e instanceof Error ? e.message : String(e));
    } finally {
      setFhirBusy(false);
    }
  }

  if (!structured) {
    return (
      <div style={{ padding: 16, background: "#fff", borderRadius: 8, border: "1px solid #e5e7eb" }}>
        <p style={{ margin: 0, color: "#6b7280" }}>Run generate to see structured output.</p>
      </div>
    );
  }

  return (
    <div style={{ padding: 16, background: "#fff", borderRadius: 8, border: "1px solid #e5e7eb" }}>
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 12, marginBottom: 12 }}>
        {meta && (
          <p style={{ margin: 0, fontSize: 13, color: "#6b7280", flex: "1 1 240px" }}>
            Model: {meta.model ?? "—"} · Prompt: {meta.prompt_version ?? "—"}
            {meta.usage && (
              <>
                {" "}
                · In: {meta.usage.input_tokens ?? "—"} · Out: {meta.usage.output_tokens ?? "—"}
                {(meta.usage.cache_read_input_tokens ?? 0) > 0 && (
                  <> · Cache read: {meta.usage.cache_read_input_tokens}</>
                )}
                {(meta.usage.cache_creation_input_tokens ?? 0) > 0 && (
                  <> · Cache write: {meta.usage.cache_creation_input_tokens}</>
                )}
              </>
            )}
          </p>
        )}
        <button
          type="button"
          onClick={() => void downloadFhir()}
          disabled={fhirBusy}
          style={{ padding: "6px 12px", fontSize: 13 }}
        >
          {fhirBusy ? "Exporting…" : "Download FHIR Bundle (JSON)"}
        </button>
      </div>
      {fhirError && (
        <p style={{ margin: "0 0 12px", fontSize: 13, color: "#b45309" }}>{fhirError}</p>
      )}
      <EditableFields
        value={structured}
        onChange={onStructuredChange}
        editedKeys={editedKeys}
        onFieldEdit={onFieldEdit}
        revisedHpiBaseline={revisedHpiBaseline}
      />
    </div>
  );
}
