import type { FormEvent } from "react";

type Props = {
  value: string;
  onChange: (v: string) => void;
  onGenerate: () => void;
  guidelineText: string;
  onGuidelineChange: (v: string) => void;
  referencePatternText: string;
  onReferencePatternChange: (v: string) => void;
  busy: boolean;
};

export function NoteEditor({
  value,
  onChange,
  onGenerate,
  guidelineText,
  onGuidelineChange,
  referencePatternText,
  onReferencePatternChange,
  busy,
}: Props) {
  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onGenerate();
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <span style={{ fontWeight: 600 }}>Clinical note(s)</span>
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={12}
          placeholder="Paste ER note, H&P, or combined text…"
          style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #ccc" }}
        />
      </label>
      <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <span>Admission guideline (optional)</span>
        <textarea
          value={guidelineText}
          onChange={(e) => onGuidelineChange(e.target.value)}
          rows={4}
          style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #ccc" }}
        />
      </label>
      <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <span>Reference pattern from Case A (optional)</span>
        <textarea
          value={referencePatternText}
          onChange={(e) => onReferencePatternChange(e.target.value)}
          rows={3}
          style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #ccc" }}
        />
      </label>
      <button type="submit" disabled={busy || !value.trim()} style={{ alignSelf: "flex-start", padding: "8px 16px" }}>
        {busy ? "Generating…" : "Generate structured output"}
      </button>
    </form>
  );
}
