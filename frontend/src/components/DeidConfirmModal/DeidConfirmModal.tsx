import type { ReactNode } from "react";
import type { DeidentifyPreviewResponse } from "../../types";

/** Regex-layer tags like [MRN], [PHONE]; Presidio-style <PERSON>, <PHONE_NUMBER>, etc. */
const DEID_PLACEHOLDER_RE = /(\[[A-Z][A-Z0-9_]*\]|<[A-Za-z][A-Za-z0-9_]*>)/g;

function countDeidPlaceholders(text: string): number {
  const m = text.match(DEID_PLACEHOLDER_RE);
  return m ? m.length : 0;
}

function highlightDeidPlaceholders(text: string): ReactNode {
  const nodes: ReactNode[] = [];
  let last = 0;
  const re = new RegExp(DEID_PLACEHOLDER_RE.source, "g");
  let m: RegExpExecArray | null;
  let key = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) {
      nodes.push(text.slice(last, m.index));
    }
    nodes.push(
      <mark
        key={key++}
        style={{
          backgroundColor: "#fef08a",
          color: "#713f12",
          fontWeight: 600,
          padding: "0 3px",
          borderRadius: 4,
          boxDecorationBreak: "clone",
          WebkitBoxDecorationBreak: "clone",
        }}
        title="De-identified placeholder"
      >
        {m[0]}
      </mark>,
    );
    last = m.index + m[0].length;
  }
  if (last < text.length) {
    nodes.push(text.slice(last));
  }
  return nodes.length > 0 ? nodes : text;
}

type Props = {
  open: boolean;
  loading: boolean;
  error: string | null;
  preview: DeidentifyPreviewResponse | null;
  acknowledged: boolean;
  onAcknowledgedChange: (v: boolean) => void;
  onCancel: () => void;
  onConfirm: () => void;
  generateBusy: boolean;
};

export function DeidConfirmModal({
  open,
  loading,
  error,
  preview,
  acknowledged,
  onAcknowledgedChange,
  onCancel,
  onConfirm,
  generateBusy,
}: Props) {
  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="deid-modal-title"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 50,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 16,
        background: "rgba(0,0,0,0.45)",
      }}
    >
      <div
        style={{
          width: "min(920px, 100%)",
          maxHeight: "90vh",
          overflow: "auto",
          background: "#fff",
          borderRadius: 12,
          padding: 20,
          boxShadow: "0 20px 50px rgba(0,0,0,0.2)",
        }}
      >
        <h2 id="deid-modal-title" style={{ margin: "0 0 8px", fontSize: 18 }}>
          Review de-identified source notes
        </h2>
        <p style={{ margin: "0 0 16px", fontSize: 14, color: "#374151" }}>
          This is a <strong>human-in-the-loop</strong> step. The text below matches what the backend will send to
          the model after automated de-identification (Presidio when available, plus regex rules). Confirm that
          nothing sensitive remains before generation.
        </p>

        {error && (
          <div
            style={{
              marginBottom: 12,
              padding: 10,
              background: "#fef2f2",
              border: "1px solid #fecaca",
              borderRadius: 8,
              fontSize: 14,
            }}
          >
            {error}
          </div>
        )}

        {loading && <p style={{ margin: 0, color: "#6b7280" }}>Loading preview…</p>}

        {!loading && preview && (
          <>
            <p style={{ margin: "0 0 12px", fontSize: 13, color: "#6b7280" }}>
              <strong>Engine:</strong> {preview.presidio_active ? "Presidio + regex" : "Regex only"} ·{" "}
              {preview.note}
            </p>
            <p style={{ margin: "0 0 12px", fontSize: 12, color: "#6b7280" }}>
              <mark
                style={{
                  backgroundColor: "#fef08a",
                  color: "#713f12",
                  fontWeight: 600,
                  padding: "1px 6px",
                  borderRadius: 4,
                }}
              >
                Yellow highlights
              </mark>{" "}
              show de-ID tokens ({`[MRN]`}, {`<PERSON>`}, etc.) for a quick scan.
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <PreviewBlock title="ER (after de-id)" text={preview.er_note} />
              <PreviewBlock title="H&P (after de-id)" text={preview.hp_note} />
              <PreviewBlock title="Additional notes (after de-id)" text={preview.note_text} />
            </div>
            <label
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: 10,
                marginTop: 16,
                fontSize: 14,
                cursor: "pointer",
              }}
            >
              <input
                type="checkbox"
                checked={acknowledged}
                onChange={(e) => onAcknowledgedChange(e.target.checked)}
                style={{ marginTop: 3 }}
              />
              <span>
                I have reviewed the de-identified text above and confirm it is appropriate to send for model
                processing.
              </span>
            </label>
          </>
        )}

        <div style={{ display: "flex", gap: 10, marginTop: 20, flexWrap: "wrap" }}>
          <button type="button" onClick={onCancel} disabled={generateBusy} style={{ padding: "8px 16px" }}>
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={generateBusy || loading || !preview || !acknowledged}
            style={{ padding: "8px 16px" }}
          >
            {generateBusy ? "Generating…" : "Confirm and generate"}
          </button>
        </div>
      </div>
    </div>
  );
}

function PreviewBlock({ title, text }: { title: string; text: string | null | undefined }) {
  const raw = text?.trim() ? text : "";
  const empty = !raw;
  const v = empty ? "— (empty)" : raw;
  const n = empty ? 0 : countDeidPlaceholders(raw);

  return (
    <div>
      <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>
        {title}
        {!empty && (
          <span style={{ fontWeight: 400, color: "#6b7280", marginLeft: 8 }}>
            ({n} placeholder{n === 1 ? "" : "s"})
          </span>
        )}
      </div>
      <div
        style={{
          margin: 0,
          padding: 10,
          fontSize: 12,
          fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
          lineHeight: 1.45,
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
          background: "#f9fafb",
          border: "1px solid #e5e7eb",
          borderRadius: 8,
          maxHeight: 180,
          overflow: "auto",
        }}
      >
        {empty ? v : highlightDeidPlaceholders(v)}
      </div>
    </div>
  );
}
