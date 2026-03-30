import type { SavedCase } from "../types";

const STORAGE_KEY = "clinical_note_transformer_cases_v1";

type CaseMap = Record<string, SavedCase>;

function readMap(): CaseMap {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return {};
    return parsed as CaseMap;
  } catch {
    return {};
  }
}

function writeMap(m: CaseMap) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(m));
}

function sortKey(c: SavedCase): string {
  return c.updated_at || c.created_at || "";
}

export function listLocalCases(): SavedCase[] {
  const m = readMap();
  return Object.values(m).sort((a, b) => sortKey(b).localeCompare(sortKey(a)));
}

export function upsertLocalCase(c: SavedCase) {
  const m = readMap();
  m[c.id] = c;
  writeMap(m);
}

export function getLocalCase(id: string): SavedCase | undefined {
  return readMap()[id];
}
