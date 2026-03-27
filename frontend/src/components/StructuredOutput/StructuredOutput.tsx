import { EditableFields } from "../EditableFields";
import type { StructuredClinicalOutput } from "../../types";

type Props = {
  structured: StructuredClinicalOutput | null;
  onStructuredChange: (next: StructuredClinicalOutput) => void;
  editedKeys: Set<string>;
  onFieldEdit: (fieldKey: string) => void;
  meta: { prompt_version?: string; model?: string } | null;
};

export function StructuredOutput({
  structured,
  onStructuredChange,
  editedKeys,
  onFieldEdit,
  meta,
}: Props) {
  if (!structured) {
    return (
      <div style={{ padding: 16, background: "#fff", borderRadius: 8, border: "1px solid #e5e7eb" }}>
        <p style={{ margin: 0, color: "#6b7280" }}>Run generate to see structured output.</p>
      </div>
    );
  }

  return (
    <div style={{ padding: 16, background: "#fff", borderRadius: 8, border: "1px solid #e5e7eb" }}>
      {meta && (
        <p style={{ margin: "0 0 12px", fontSize: 13, color: "#6b7280" }}>
          Model: {meta.model ?? "—"} · Prompt: {meta.prompt_version ?? "—"}
        </p>
      )}
      <EditableFields
        value={structured}
        onChange={onStructuredChange}
        editedKeys={editedKeys}
        onFieldEdit={onFieldEdit}
      />
    </div>
  );
}
