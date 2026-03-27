import type { SavedCase } from "../../types";

type Props = {
  cases: SavedCase[];
  selectedId: string | null;
  onSelect: (id: string) => void;
};

export function CaseList({ cases, selectedId, onSelect }: Props) {
  if (cases.length === 0) {
    return (
      <div style={{ fontSize: 14, color: "#6b7280" }}>
        No saved cases yet. Save from the editor after generating.
      </div>
    );
  }

  return (
    <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 8 }}>
      {cases.map((c) => (
        <li key={c.id}>
          <button
            type="button"
            onClick={() => onSelect(c.id)}
            style={{
              width: "100%",
              textAlign: "left",
              padding: "10px 12px",
              borderRadius: 8,
              border: selectedId === c.id ? "2px solid #2563eb" : "1px solid #e5e7eb",
              background: selectedId === c.id ? "#eff6ff" : "#fff",
            }}
          >
            <div style={{ fontWeight: 600 }}>{c.title || "Untitled"}</div>
            <div style={{ fontSize: 12, color: "#6b7280" }}>
              {c.updated_at?.slice(0, 19) ?? c.id.slice(0, 8)} · {c.structured_output.disposition_recommendation}
            </div>
          </button>
        </li>
      ))}
    </ul>
  );
}
