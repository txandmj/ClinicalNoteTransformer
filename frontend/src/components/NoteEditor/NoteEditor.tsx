import type { FormEvent } from "react";
import type { GuidelinePreset } from "../../types";
import { hasAnyClinicalInput } from "../../lib/originalNoteFormat";

type Props = {
  erNote: string;
  onErNoteChange: (v: string) => void;
  hpNote: string;
  onHpNoteChange: (v: string) => void;
  otherNote: string;
  onOtherNoteChange: (v: string) => void;
  onGenerate: () => void;
  guidelinePresets: GuidelinePreset[];
  guidelineKey: string;
  onGuidelineKeyChange: (v: string) => void;
  guidelineText: string;
  onGuidelineChange: (v: string) => void;
  referencePatternText: string;
  onReferencePatternChange: (v: string) => void;
  exemplarRevisedHpi: string;
  onExemplarRevisedHpiChange: (v: string) => void;
  busy: boolean;
};

export function NoteEditor({
  erNote,
  onErNoteChange,
  hpNote,
  onHpNoteChange,
  otherNote,
  onOtherNoteChange,
  onGenerate,
  guidelinePresets,
  guidelineKey,
  onGuidelineKeyChange,
  guidelineText,
  onGuidelineChange,
  referencePatternText,
  onReferencePatternChange,
  exemplarRevisedHpi,
  onExemplarRevisedHpiChange,
  busy,
}: Props) {
  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onGenerate();
  }

  const canSubmit = hasAnyClinicalInput(erNote, hpNote, otherNote);

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <fieldset style={{ margin: 0, padding: 12, borderRadius: 8, border: "1px solid #e5e7eb" }}>
        <legend style={{ fontWeight: 600 }}>Current case — source notes</legend>
        <p style={{ margin: "0 0 8px", fontSize: 13, color: "#6b7280" }}>
          Paste ER and H&P separately (recommended). Use “Additional notes” if you prefer one combined block
          or extra text.
        </p>
        <label style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 10 }}>
          <span style={{ fontWeight: 600 }}>Original ER note</span>
          <textarea
            value={erNote}
            onChange={(e) => onErNoteChange(e.target.value)}
            rows={8}
            placeholder="Emergency department note…"
            style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #ccc" }}
          />
        </label>
        <label style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 10 }}>
          <span style={{ fontWeight: 600 }}>Original H&amp;P note</span>
          <textarea
            value={hpNote}
            onChange={(e) => onHpNoteChange(e.target.value)}
            rows={8}
            placeholder="History & physical…"
            style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #ccc" }}
          />
        </label>
        <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <span>Additional or combined clinical note(s)</span>
          <textarea
            value={otherNote}
            onChange={(e) => onOtherNoteChange(e.target.value)}
            rows={4}
            placeholder="Optional overflow or single pasted chart…"
            style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #ccc" }}
          />
        </label>
      </fieldset>

      <fieldset style={{ margin: 0, padding: 12, borderRadius: 8, border: "1px solid #e5e7eb" }}>
        <legend style={{ fontWeight: 600 }}>Guidance materials</legend>
        <label style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 10 }}>
          <span>Guideline preset (bundled MCG-style text, cache-friendly)</span>
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
        <label style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 10 }}>
          <span>Extra admission guideline text (optional; merged after preset)</span>
          <textarea
            value={guidelineText}
            onChange={(e) => onGuidelineChange(e.target.value)}
            rows={4}
            style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #ccc" }}
          />
        </label>
        <label style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 10 }}>
          <span>Reference pattern from Case A (optional — bullets / rubric)</span>
          <textarea
            value={referencePatternText}
            onChange={(e) => onReferencePatternChange(e.target.value)}
            rows={3}
            style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #ccc" }}
          />
        </label>
        <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <span>
            <strong>Human revised HPI (Case A exemplar)</strong> — optional; teaches structure &amp; reasoning.
            Not used as facts for the current patient.
          </span>
          <textarea
            value={exemplarRevisedHpi}
            onChange={(e) => onExemplarRevisedHpiChange(e.target.value)}
            rows={6}
            placeholder="Paste the human-optimized revised HPI from your reference case…"
            style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #ccc" }}
          />
        </label>
      </fieldset>

      <button type="submit" disabled={busy || !canSubmit} style={{ alignSelf: "flex-start", padding: "8px 16px" }}>
        {busy ? "Generating…" : "Generate structured output"}
      </button>
    </form>
  );
}
