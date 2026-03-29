import { diffWords } from "diff";
import type { CSSProperties } from "react";
import { useMemo, useState } from "react";

const addedStyle: CSSProperties = {
  backgroundColor: "#bbf7d0",
  color: "#14532d",
  borderRadius: 3,
  padding: "0 3px",
};

const removedStyle: CSSProperties = {
  textDecoration: "line-through",
  textDecorationThickness: "from-font",
  backgroundColor: "#fecaca",
  color: "#7f1d1d",
  borderRadius: 3,
  padding: "0 3px",
};

type Props = {
  /** Last machine-generated or loaded/saved clean revised HPI (before human edits). */
  baselineRevisedHpi: string;
  /** Current clean revised HPI text (may include human edits). */
  currentRevisedHpi: string;
};

/**
 * Word-level diff: baseline clean revised HPI vs current (after human edits).
 * Green = added by editor; red strikethrough = removed from baseline.
 */
export function HpiWordDiff({ baselineRevisedHpi, currentRevisedHpi }: Props) {
  const [open, setOpen] = useState(true);
  const parts = useMemo(
    () => diffWords(baselineRevisedHpi.trim(), currentRevisedHpi.trim()),
    [baselineRevisedHpi, currentRevisedHpi]
  );

  const hasDiff = parts.some((p) => p.added || p.removed);
  if (!baselineRevisedHpi.trim() && !currentRevisedHpi.trim()) return null;
  if (!hasDiff) return null;

  return (
    <details
      open={open}
      onToggle={(e) => setOpen(e.currentTarget.open)}
      style={{
        marginTop: 8,
        padding: 10,
        background: "#fafafa",
        borderRadius: 8,
        border: "1px solid #e5e7eb",
      }}
    >
      <summary style={{ cursor: "pointer", fontWeight: 600, fontSize: 13, color: "#374151" }}>
        Human edits to clean revised HPI (word-level)
      </summary>
      <p style={{ margin: "8px 0 6px", fontSize: 12, color: "#6b7280" }}>
        Compared to the last <strong>generated</strong> or <strong>saved</strong> version.{" "}
        <span style={{ ...addedStyle, display: "inline", marginRight: 6 }}>added</span>
        <span style={{ ...removedStyle, display: "inline" }}>removed</span>
        <span style={{ marginLeft: 8 }}>unchanged text has no highlight.</span>
      </p>
      <div
        role="region"
        aria-label="Human edits vs baseline clean revised HPI"
        style={{
          lineHeight: 1.65,
          fontSize: 14,
          color: "#1f2937",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
        }}
      >
        {parts.map((part, i) => {
          if (part.added) {
            return (
              <span key={i} style={addedStyle}>
                {part.value}
              </span>
            );
          }
          if (part.removed) {
            return (
              <span key={i} style={removedStyle}>
                {part.value}
              </span>
            );
          }
          return <span key={i}>{part.value}</span>;
        })}
      </div>
    </details>
  );
}
