import type { FormEvent } from "react";
import type { GuidelinePreset } from "../../types";

type Props = {
  value: string;
  onChange: (v: string) => void;
  onGenerate: () => void;
  guidelinePresets: GuidelinePreset[];
  guidelineKey: string;
  onGuidelineKeyChange: (v: string) => void;
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
  guidelinePresets,
  guidelineKey,
  onGuidelineKeyChange,
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
        <span>Guideline preset (bundled MCG-style text, token-cache friendly)</span>
        <select
          value={guidelineKey}
          onChange={(e) => onGuidelineKeyChange(e.target.value)}
          style={{ padding: 8, borderRadius: 8, border: "1px solid #ccc", maxWidth: "100%" }}
        >
          <option value="">None — paste only below</option>
          {guidelinePresets.map((p) => (
            <option key={p.id} value={p.id}>
              {p.title} ({p.id})
            </option>
          ))}
        </select>
      </label>
      <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <span>
          Extra admission guideline text (optional; appended after preset — still combined for caching)
        </span>
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
