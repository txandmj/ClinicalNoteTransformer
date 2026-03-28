import type { Disposition, SentenceComparisonItem, StructuredClinicalOutput } from "../../types";

type ScalarKey = Exclude<
  keyof StructuredClinicalOutput,
  "key_findings" | "suspected_conditions" | "uncertainties" | "sentence_comparisons"
>;

const SECTION_FIELDS: { key: ScalarKey; label: string; multiline: boolean; rows?: number }[] = [
  { key: "chief_complaint", label: "1. Chief complaint", multiline: false },
  { key: "original_hpi", label: "2. Original HPI", multiline: true, rows: 8 },
  { key: "revised_hpi", label: "3. Clean revised HPI", multiline: true, rows: 8 },
];

type Props = {
  value: StructuredClinicalOutput;
  onChange: (next: StructuredClinicalOutput) => void;
  editedKeys: Set<string>;
  onFieldEdit: (fieldKey: string) => void;
};

export function EditableFields({ value, onChange, editedKeys, onFieldEdit }: Props) {
  function setScalar<K extends ScalarKey>(key: K, v: StructuredClinicalOutput[K]) {
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

  function setComparisons(next: SentenceComparisonItem[]) {
    onFieldEdit("sentence_comparisons");
    onChange({ ...value, sentence_comparisons: next });
  }

  function updateRow(index: number, patch: Partial<SentenceComparisonItem>) {
    const rows = value.sentence_comparisons.map((row, i) =>
      i === index ? { ...row, ...patch } : row
    );
    setComparisons(rows);
  }

  function addRow() {
    const n = value.sentence_comparisons.length + 1;
    setComparisons([
      ...value.sentence_comparisons,
      { sentence_index: n, revised: "", source: "", reason: "" },
    ]);
  }

  function removeRow(index: number) {
    const next = value.sentence_comparisons.filter((_, i) => i !== index).map((row, i) => ({
      ...row,
      sentence_index: i + 1,
    }));
    setComparisons(next);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {SECTION_FIELDS.map(({ key, label, multiline, rows }) => (
        <label key={key} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <span style={{ fontWeight: 600 }}>
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
              onChange={(e) => setScalar(key, e.target.value as StructuredClinicalOutput[typeof key])}
              rows={rows ?? 5}
              style={{ width: "100%", padding: 8, borderRadius: 8, border: "1px solid #ccc" }}
            />
          ) : (
            <input
              value={String(value[key] ?? "")}
              onChange={(e) => setScalar(key, e.target.value as StructuredClinicalOutput[typeof key])}
              style={{ padding: 8, borderRadius: 8, border: "1px solid #ccc" }}
            />
          )}
        </label>
      ))}

      <fieldset
        style={{
          margin: 0,
          padding: 12,
          borderRadius: 8,
          border: "1px solid #e5e7eb",
        }}
      >
        <legend style={{ fontWeight: 600 }}>
          4. Sentence-by-sentence comparison{" "}
          {editedKeys.has("sentence_comparisons") ? (
            <span style={{ color: "#b45309", fontSize: 12 }}>(edited)</span>
          ) : (
            <span style={{ color: "#6b7280", fontSize: 12 }}>(machine)</span>
          )}
        </legend>
        <p style={{ margin: "0 0 8px", fontSize: 13, color: "#6b7280" }}>
          Per sentence in §3: Revised → Source (note quotes) → Reason (clinical + guideline linkage).
        </p>
        {value.sentence_comparisons.map((row, index) => (
          <div
            key={index}
            style={{
              marginBottom: 12,
              padding: 10,
              background: "#fafafa",
              borderRadius: 8,
              border: "1px solid #eee",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
              <strong style={{ fontSize: 14 }}>Sentence {row.sentence_index}</strong>
              <button type="button" onClick={() => removeRow(index)} style={{ fontSize: 12 }}>
                Remove
              </button>
            </div>
            <label style={{ display: "block", marginBottom: 6, fontSize: 13 }}>
              Revised
              <textarea
                value={row.revised}
                onChange={(e) => updateRow(index, { revised: e.target.value })}
                rows={2}
                style={{ display: "block", width: "100%", marginTop: 4, padding: 6 }}
              />
            </label>
            <label style={{ display: "block", marginBottom: 6, fontSize: 13 }}>
              Source
              <textarea
                value={row.source}
                onChange={(e) => updateRow(index, { source: e.target.value })}
                rows={2}
                style={{ display: "block", width: "100%", marginTop: 4, padding: 6 }}
              />
            </label>
            <label style={{ display: "block", fontSize: 13 }}>
              Reason
              <textarea
                value={row.reason}
                onChange={(e) => updateRow(index, { reason: e.target.value })}
                rows={3}
                style={{ display: "block", width: "100%", marginTop: 4, padding: 6 }}
              />
            </label>
          </div>
        ))}
        <button type="button" onClick={addRow} style={{ padding: "6px 12px" }}>
          Add sentence row
        </button>
      </fieldset>

      <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <span style={{ fontWeight: 600 }}>
          HPI summary (brief rubric){" "}
          {editedKeys.has("hpi_summary") ? (
            <span style={{ color: "#b45309", fontSize: 12 }}>(edited)</span>
          ) : (
            <span style={{ color: "#6b7280", fontSize: 12 }}>(machine)</span>
          )}
        </span>
        <textarea
          value={value.hpi_summary}
          onChange={(e) => setScalar("hpi_summary", e.target.value)}
          rows={4}
          style={{ width: "100%", padding: 8, borderRadius: 8, border: "1px solid #ccc" }}
        />
      </label>

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
          onChange={(e) => setScalar("disposition_recommendation", e.target.value as Disposition)}
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
