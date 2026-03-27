import type { Disposition, StructuredClinicalOutput } from "../../types";

type FieldMeta = {
  key: keyof StructuredClinicalOutput;
  label: string;
  multiline?: boolean;
};

const FIELDS: FieldMeta[] = [
  { key: "chief_complaint", label: "Chief complaint" },
  { key: "hpi_summary", label: "HPI summary", multiline: true },
  { key: "revised_hpi", label: "Revised HPI", multiline: true },
];

type Props = {
  value: StructuredClinicalOutput;
  onChange: (next: StructuredClinicalOutput) => void;
  /** Keys the user has edited (for machine vs user distinction). */
  editedKeys: Set<string>;
  onFieldEdit: (fieldKey: string) => void;
};

export function EditableFields({ value, onChange, editedKeys, onFieldEdit }: Props) {
  function set<K extends keyof StructuredClinicalOutput>(key: K, v: StructuredClinicalOutput[K]) {
    onFieldEdit(key);
    onChange({ ...value, [key]: v });
  }

  function setList(key: "key_findings" | "suspected_conditions" | "uncertainties", text: string) {
    onFieldEdit(key);
    const lines = text
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean);
    onChange({ ...value, [key]: lines });
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {FIELDS.map(({ key, label, multiline }) => (
        <label key={key} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <span>
            {label}{" "}
            {editedKeys.has(key) ? (
              <span style={{ color: "#b45309", fontSize: 12 }}>(edited)</span>
            ) : (
              <span style={{ color: "#6b7280", fontSize: 12 }}>(machine)</span>
            )}
          </span>
          {multiline ? (
            <textarea
              value={String(value[key] ?? "")}
              onChange={(e) => set(key, e.target.value as StructuredClinicalOutput[typeof key])}
              rows={key === "revised_hpi" ? 10 : 4}
              style={{ width: "100%", padding: 8, borderRadius: 8, border: "1px solid #ccc" }}
            />
          ) : (
            <input
              value={String(value[key] ?? "")}
              onChange={(e) => set(key, e.target.value as StructuredClinicalOutput[typeof key])}
              style={{ padding: 8, borderRadius: 8, border: "1px solid #ccc" }}
            />
          )}
        </label>
      ))}

      <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <span>
          Disposition{" "}
          {editedKeys.has("disposition_recommendation") ? (
            <span style={{ color: "#b45309", fontSize: 12 }}>(edited)</span>
          ) : (
            <span style={{ color: "#6b7280", fontSize: 12 }}>(machine)</span>
          )}
        </span>
        <select
          value={value.disposition_recommendation}
          onChange={(e) => set("disposition_recommendation", e.target.value as Disposition)}
          style={{ padding: 8, maxWidth: 240 }}
        >
          {(["Admit", "Observe", "Discharge", "Unknown"] as const).map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
      </label>

      {(
        [
          ["key_findings", "Key findings (one per line)"],
          ["suspected_conditions", "Suspected condition(s) (one per line)"],
          ["uncertainties", "Uncertainties / missing information (one per line)"],
        ] as const
      ).map(([key, label]) => (
        <label key={key} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <span>
            {label}{" "}
            {editedKeys.has(key) ? (
              <span style={{ color: "#b45309", fontSize: 12 }}>(edited)</span>
            ) : (
              <span style={{ color: "#6b7280", fontSize: 12 }}>(machine)</span>
            )}
          </span>
          <textarea
            value={(value[key] as string[]).join("\n")}
            onChange={(e) => setList(key, e.target.value)}
            rows={4}
            style={{ width: "100%", padding: 8, borderRadius: 8, border: "1px solid #ccc" }}
          />
        </label>
      ))}
    </div>
  );
}
