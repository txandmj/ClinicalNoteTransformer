import type { SentenceComparisonItem } from "../../types";

function norm(s: string): string {
  return s.replace(/\s+/g, " ").trim().toLowerCase();
}

/** Split paragraph into rough sentences for hover/link alignment. */
export function splitIntoSentences(text: string): string[] {
  const t = text.trim();
  if (!t) return [];
  const chunks = t.split(/(?<=[.!?])\s+(?=[A-Z(0-9"'])/);
  const out = chunks.map((c) => c.trim()).filter(Boolean);
  return out.length ? out : [t];
}

function findComparisonRowIndex(
  segment: string,
  segmentIndex: number,
  rows: SentenceComparisonItem[]
): number {
  const seg = norm(segment);
  if (!rows.length) return -1;

  const byText = rows.findIndex((r) => norm(r.revised) === seg);
  if (byText >= 0) return byText;

  const bySentenceNum = rows.findIndex((r) => r.sentence_index === segmentIndex + 1);
  if (bySentenceNum >= 0) {
    const r = rows[bySentenceNum];
    if (!r.revised.trim() || norm(r.revised) === seg) return bySentenceNum;
  }

  if (segmentIndex < rows.length) {
    const r = rows[segmentIndex];
    if (norm(r.revised) === seg || !r.revised.trim()) return segmentIndex;
  }

  return -1;
}

function tooltipFor(row: SentenceComparisonItem): string {
  return `Source\n${row.source}\n\nReason\n${row.reason}`;
}

type Props = {
  revisedHpi: string;
  comparisons: SentenceComparisonItem[];
};

export function RevisedHpiPreview({ revisedHpi, comparisons }: Props) {
  if (!revisedHpi.trim()) return null;

  const segments = splitIntoSentences(revisedHpi);

  return (
    <div
      style={{
        marginTop: 8,
        padding: 10,
        background: "#f8fafc",
        borderRadius: 8,
        border: "1px solid #e2e8f0",
      }}
      role="region"
      aria-label="Clean revised HPI preview with sources"
    >
      <div style={{ fontSize: 12, color: "#64748b", marginBottom: 8 }}>
        Hover a sentence for <strong>Source</strong> and <strong>Reason</strong>. Click ↗ to jump to the matching row in §4.
      </div>
      <p style={{ lineHeight: 1.65, margin: 0, fontSize: 14, color: "#1e293b" }}>
        {segments.map((seg, i) => {
          const ri = findComparisonRowIndex(seg, i, comparisons);
          const row = ri >= 0 ? comparisons[ri] : null;
          const gap = i < segments.length - 1 ? " " : "";
          return (
            <span key={i} style={{ whiteSpace: "pre-wrap" }}>
              <span
                title={
                  row
                    ? tooltipFor(row)
                    : "No matching §4 row — align Revised fields in the sentence list with this text."
                }
                style={{
                  cursor: row ? "help" : "default",
                  borderBottom: row ? "1px dotted #60a5fa" : undefined,
                }}
              >
                {seg}
              </span>
              {row ? (
                <a
                  href={`#sentence-compare-${ri}`}
                  onClick={(e) => {
                    e.preventDefault();
                    const el = document.getElementById(`sentence-compare-${ri}`);
                    el?.scrollIntoView({ behavior: "smooth", block: "nearest" });
                    el?.animate(
                      [
                        { outline: "2px solid #2563eb", outlineOffset: "2px" },
                        { outline: "2px solid transparent", outlineOffset: "2px" },
                      ],
                      { duration: 900 }
                    );
                  }}
                  style={{
                    marginLeft: 3,
                    fontSize: 11,
                    verticalAlign: "super",
                    textDecoration: "none",
                    color: "#2563eb",
                    fontWeight: 600,
                  }}
                  aria-label={`Jump to sentence comparison row ${ri + 1}`}
                >
                  ↗
                </a>
              ) : null}
              {gap}
            </span>
          );
        })}
      </p>
    </div>
  );
}
