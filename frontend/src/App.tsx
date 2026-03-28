import { useCallback, useEffect, useMemo, useState } from "react";
import { CaseList } from "./components/CaseList";
import { NoteEditor } from "./components/NoteEditor";
import { StructuredOutput } from "./components/StructuredOutput";
import { getCase, getCases, getGuidelines, postCase, postGenerate } from "./lib/api";
import * as local from "./lib/persistence";
import { normalizeStructured } from "./lib/structuredDefaults";
import { deserializeOriginalNote, serializeOriginalNote } from "./lib/originalNoteFormat";
import type { GuidelinePreset, StructuredClinicalOutput, TokenUsage } from "./types";

export default function App() {
  const [erNote, setErNote] = useState("");
  const [hpNote, setHpNote] = useState("");
  const [otherNote, setOtherNote] = useState("");
  const [guidelineKey, setGuidelineKey] = useState("");
  const [guideline, setGuideline] = useState("");
  const [referencePattern, setReferencePattern] = useState("");
  const [exemplarRevisedHpi, setExemplarRevisedHpi] = useState("");
  const [guidelinePresets, setGuidelinePresets] = useState<GuidelinePreset[]>([]);
  const [structured, setStructured] = useState<StructuredClinicalOutput | null>(null);
  const [meta, setMeta] = useState<{
    prompt_version?: string;
    model?: string;
    usage?: TokenUsage | null;
  } | null>(null);
  const [editedKeys, setEditedKeys] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [caseId, setCaseId] = useState<string | null>(null);
  const [localCases, setLocalCases] = useState(() => local.listLocalCases());
  const [useBackendList, setUseBackendList] = useState(true);

  const refreshList = useCallback(async () => {
    setLocalCases(local.listLocalCases());
    if (useBackendList) {
      try {
        const remote = await getCases();
        remote.forEach((c) => local.upsertLocalCase(c));
        setLocalCases(local.listLocalCases());
      } catch {
        /* offline — keep local only */
      }
    }
  }, [useBackendList]);

  useEffect(() => {
    void refreshList();
  }, [refreshList]);

  useEffect(() => {
    void (async () => {
      try {
        setGuidelinePresets(await getGuidelines());
      } catch {
        /* offline */
      }
    })();
  }, []);

  const onFieldEdit = useCallback((key: string) => {
    setEditedKeys((prev) => new Set(prev).add(key));
  }, []);

  const handleGenerate = async () => {
    setError(null);
    setBusy(true);
    setEditedKeys(new Set());
    try {
      const res = await postGenerate({
        er_note: erNote.trim() || null,
        hp_note: hpNote.trim() || null,
        note_text: otherNote.trim() || "",
        guideline_key: guidelineKey || null,
        guideline_text: guideline || null,
        reference_pattern_text: referencePattern || null,
        exemplar_revised_hpi: exemplarRevisedHpi.trim() || null,
      });
      setStructured(normalizeStructured(res.structured));
      setMeta({ prompt_version: res.prompt_version, model: res.model, usage: res.usage });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const handleSave = async () => {
    if (!structured) return;
    setError(null);
    try {
      const original_note = serializeOriginalNote(erNote, hpNote, otherNote);
      const titleSeed = erNote.trim() || hpNote.trim() || otherNote.trim() || "Case";
      const saved = await postCase({
        id: caseId,
        title: titleSeed.slice(0, 80),
        original_note,
        structured_output: structured,
        source: editedKeys.size ? "user" : "machine",
      });
      setCaseId(saved.id);
      local.upsertLocalCase(saved);
      setLocalCases(local.listLocalCases());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const loadCase = async (id: string) => {
    setError(null);
    try {
      const c = await getCase(id);
      setCaseId(c.id);
      const parsed = deserializeOriginalNote(c.original_note);
      setErNote(parsed.er);
      setHpNote(parsed.hp);
      setOtherNote(parsed.other);
      setStructured(normalizeStructured(c.structured_output));
      setEditedKeys(new Set());
      setMeta(null);
    } catch {
      const loc = local.getLocalCase(id);
      if (loc) {
        setCaseId(loc.id);
        const p = deserializeOriginalNote(loc.original_note);
        setErNote(p.er);
        setHpNote(p.hp);
        setOtherNote(p.other);
        setStructured(normalizeStructured(loc.structured_output));
        setEditedKeys(new Set());
        setMeta(null);
      } else setError("Case not found");
    }
  };

  const newCase = () => {
    setCaseId(null);
    setErNote("");
    setHpNote("");
    setOtherNote("");
    setStructured(null);
    setMeta(null);
    setEditedKeys(new Set());
    setError(null);
  };

  const listItems = useMemo(() => localCases, [localCases]);

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: 24 }}>
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ margin: "0 0 8px", fontSize: 22 }}>Clinical Note Transformer</h1>
        <p style={{ margin: 0, color: "#6b7280", fontSize: 14 }}>
          Paste notes, generate structured output + Revised HPI, edit, save. Cases sync to backend when available;
          localStorage mirrors for offline reopen.
        </p>
      </header>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, alignItems: "start" }}>
        <section>
          <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
            <button type="button" onClick={newCase} style={{ padding: "6px 12px" }}>
              New case
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={!structured}
              style={{ padding: "6px 12px" }}
            >
              Save case
            </button>
            <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 14 }}>
              <input
                type="checkbox"
                checked={useBackendList}
                onChange={(e) => setUseBackendList(e.target.checked)}
              />
              Sync list from API
            </label>
          </div>
          <NoteEditor
            erNote={erNote}
            onErNoteChange={setErNote}
            hpNote={hpNote}
            onHpNoteChange={setHpNote}
            otherNote={otherNote}
            onOtherNoteChange={setOtherNote}
            onGenerate={handleGenerate}
            guidelinePresets={guidelinePresets}
            guidelineKey={guidelineKey}
            onGuidelineKeyChange={setGuidelineKey}
            guidelineText={guideline}
            onGuidelineChange={setGuideline}
            referencePatternText={referencePattern}
            onReferencePatternChange={setReferencePattern}
            exemplarRevisedHpi={exemplarRevisedHpi}
            onExemplarRevisedHpiChange={setExemplarRevisedHpi}
            busy={busy}
          />
        </section>

        <section>
          {error && (
            <div
              style={{
                marginBottom: 12,
                padding: 12,
                background: "#fef2f2",
                border: "1px solid #fecaca",
                borderRadius: 8,
                fontSize: 14,
              }}
            >
              {error}
            </div>
          )}
          <StructuredOutput
            structured={structured}
            onStructuredChange={setStructured}
            editedKeys={editedKeys}
            onFieldEdit={onFieldEdit}
            meta={meta}
          />
        </section>
      </div>

      <section style={{ marginTop: 32 }}>
        <h2 style={{ fontSize: 16, marginBottom: 12 }}>Saved cases</h2>
        <CaseList cases={listItems} selectedId={caseId} onSelect={(id) => void loadCase(id)} />
      </section>
    </div>
  );
}
