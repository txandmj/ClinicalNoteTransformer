import type { GenerateResponse, GuidelinePreset, SavedCase, StructuredClinicalOutput } from "../types";

export type GeneratePayload = {
  er_note: string | null;
  hp_note: string | null;
  note_text: string;
  guideline_key: string | null;
  guideline_text: string | null;
  reference_pattern_text: string | null;
  exemplar_revised_hpi: string | null;
};

async function errorMessage(res: Response): Promise<string> {
  try {
    const j = (await res.json()) as { detail?: unknown };
    const d = j.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) {
      return d
        .map((x) =>
          typeof x === "object" && x !== null && "msg" in x ? String((x as { msg: unknown }).msg) : String(x),
        )
        .join("; ");
    }
  } catch {
    /* ignore */
  }
  return res.statusText || `HTTP ${res.status}`;
}

async function handleJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    throw new Error(await errorMessage(res));
  }
  return res.json() as Promise<T>;
}

function jsonHeaders(): HeadersInit {
  const h: Record<string, string> = {
    Accept: "application/json",
    "Content-Type": "application/json",
  };
  const key = import.meta.env.VITE_CLINICAL_API_KEY;
  if (key) h["X-API-Key"] = key;
  return h;
}

export async function postGenerate(body: GeneratePayload): Promise<GenerateResponse> {
  const res = await fetch("/generate", {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(body),
  });
  return handleJson<GenerateResponse>(res);
}

export async function getGuidelines(): Promise<GuidelinePreset[]> {
  const res = await fetch("/guidelines", { headers: jsonHeaders() });
  const data = await handleJson<{ presets: GuidelinePreset[] }>(res);
  return data.presets;
}

export async function getCases(): Promise<SavedCase[]> {
  const res = await fetch("/cases", { headers: jsonHeaders() });
  const data = await handleJson<{ cases: SavedCase[] }>(res);
  return data.cases;
}

export async function getCase(id: string): Promise<SavedCase> {
  const res = await fetch(`/cases/${encodeURIComponent(id)}`, { headers: jsonHeaders() });
  return handleJson<SavedCase>(res);
}

export async function postCase(body: {
  id: string | null;
  title: string | null;
  original_note: string;
  structured_output: StructuredClinicalOutput;
  source: string;
  revised_hpi_baseline: string | null;
}): Promise<SavedCase> {
  const res = await fetch("/cases", {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(body),
  });
  return handleJson<SavedCase>(res);
}
