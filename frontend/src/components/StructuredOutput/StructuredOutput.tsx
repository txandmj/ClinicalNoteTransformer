import { EditableFields } from "../EditableFields";
import type { StructuredClinicalOutput, TokenUsage } from "../../types";

type Props = {
  structured: StructuredClinicalOutput | null;
  onStructuredChange: (next: StructuredClinicalOutput) => void;
  editedKeys: Set<string>;
  onFieldEdit: (fieldKey: string) => void;
  meta: { prompt_version?: string; model?: string; usage?: TokenUsage | null } | null;
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
      <EditableFields
        value={structured}
        onChange={onStructuredChange}
        editedKeys={editedKeys}
        onFieldEdit={onFieldEdit}
      />
    </div>
  );
}
