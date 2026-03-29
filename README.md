# Clinical Note Transformer

Internal-style demo that turns unstructured **ER** and **H&P** text (plus optional MCG-style guidance) into a **structured summary** and a **clean, admission-oriented revised HPI**, with editing, save/reopen, and reviewer-oriented UI affordances.

---

## 1. Architecture overview

```text
┌─────────────────────────────────────────────────────────────────┐
│  Browser (React + Vite)                                         │
│  NoteEditor → POST /generate  │  StructuredOutput + save/list │
│  localStorage mirror of cases │  proxy to API in dev            │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP (JSON)
┌────────────────────────────▼────────────────────────────────────┐
│  FastAPI (`app.main`)                                             │
│  • POST /generate   → merge inputs → Anthropic → validate JSON    │
│  • GET/POST /cases  → in-memory store (swap for DB in prod)       │
│  • GET /guidelines  → bundled MCG-style preset registry           │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  Services                                                         │
│  cot_prompt_builder   – static vs dynamic message blocks + cache  │
│  llm_engine           – Claude call, JSON parse, abbrev expansion  │
│  guideline_presets    – load `app/guidelines/*.md` by key         │
│  clinical_abbreviations – post-process §3 / §4 “revised” strings  │
└───────────────────────────────────────────────────────────────────┘
```

**Data flow (generate):** the client sends labeled source notes and optional guidance; the server builds a **system** prompt from versioned markdown (`prompts/templates/v1/cot_clinical.md`), then **user** blocks in a fixed order (guideline → reference pattern → exemplar revised HPI → current case notes) so **Anthropic prompt caching** can apply to stable prefixes. The model returns **one JSON object**; the server parses it into `StructuredClinicalOutput`, expands common abbreviations in the revised HPI fields, and returns it with optional **usage** metadata.

---

## 2. Tech stack choices and why

| Layer | Choice | Why |
|--------|--------|-----|
| **API** | **FastAPI** | Typed request/response with **Pydantic**, OpenAPI for free, async-friendly, quick to run locally. |
| **Validation** | **Pydantic v2** | Same shapes for API and internal models; clear errors for bad generate payloads. |
| **LLM** | **Anthropic Claude** (Messages API) | Strong instruction-following for JSON-only output and long clinical context. |
| **Caching** | **Ephemeral `cache_control`** on static blocks | Lowers repeated cost when the same guideline / reference / exemplar is reused across cases. |
| **UI** | **React + TypeScript + Vite** | Fast dev loop, type-safe UI, simple proxy to the API without CORS pain in development. |
| **Persistence (MVP)** | **In-memory cases + `localStorage` mirror** | Meets take-home scope; `app/db/__init__.py` documents swapping to **PostgreSQL**. |
| **Optional API gate** | **`X-API-Key`** vs `CLINICAL_API_KEY` | Lightweight protection for a shared dev server without full auth. |

---

## 3. How the clinical note is structured

**Inputs (left panel)**

- **Current case — source notes**  
  - **Original ER note** and **Original H&P** (recommended split).  
  - **Additional or combined clinical note(s)** if you prefer one blob or overflow text.  
  - At least one of ER / H&P / additional must be non-empty.

- **Guidance materials**  
  - **Guideline preset** — loads bundled markdown from `backend/app/guidelines/` (see `registry.json`).  
  - **Extra admission guideline text** — merged after the preset.  
  - **Reference pattern (Case A)** — rubric or pasted reference-case narrative; teaching context only.  
  - **Human revised HPI (Case A exemplar)** — gold narrative for style/reasoning; prompt forbids copying its patient-specific facts into the output.

**Saved `original_note`**

- Serialized with markers (`---ER---`, `---H&P---`, `---OTHER---`) so reopening a case restores the three fields. Legacy saves without markers load entirely into “additional” notes.

**Outputs (right panel)**

- **§1–§4 style structured fields** plus rubric lists: chief complaint, original HPI, clean revised HPI, HPI summary, sentence-by-sentence comparison rows, disposition, key findings, suspected conditions, uncertainties.  
- **Revised HPI preview:** hover sentences to see **Source** / **Reason** from §4; click ↗ to scroll to the matching row.

---

## 4. How the Revised HPI is generated

1. **Prompting** — `cot_clinical.md` defines the JSON schema, Case-A-style sections (including `revised_hpi` as the **clean revised HPI** and `sentence_comparisons` aligned to those sentences), and rules: ground everything in the **current** ER/H&P, keep disposition consistent with narrative, treat exemplar text as non-factual for the current patient.

2. **Model call** — `llm_engine.py` sends system + user content blocks; the model must answer with **valid JSON** (fenced code stripped if present).

3. **Post-processing** — `clinical_abbreviations.py` expands a **curated** set of clinical abbreviations in `revised_hpi` and each §4 **`revised`** string (e.g. EMS → Emergency medical services) for readability.

4. **Human loop** — the user edits any field; the UI marks **(edited)** vs **(machine)**. Saving posts `structured_output` to `POST /cases` (and mirrors to `localStorage`).

---

## 5. How uncertainty or missing information is handled

- **Schema** — `uncertainties` is a **list of strings** in the structured output; the prompt requires calling out gaps instead of inventing data.  
- **Disposition** — enum includes **`Unknown`** when evidence is insufficient.  
- **Prompt rules** — explicit instructions not to fabricate findings and to align `revised_hpi` with the chosen disposition.  
- **API validation** — generate requests must include at least one non-empty clinical source (ER, H&P, or additional note).

---

## 6. How to run the project locally

**Prerequisites:** Python 3.11+ (recommended), Node 18+, an **Anthropic API key**.

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix:    source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set ANTHROPIC_API_KEY=sk-ant-... in .env (and optionally CLINICAL_API_KEY + matching VITE_CLINICAL_API_KEY on the client)
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm install
# Optional: create frontend/.env with VITE_CLINICAL_API_KEY if the backend enforces CLINICAL_API_KEY
npm run dev
```

Open **http://localhost:5173** — Vite proxies `/generate`, `/cases`, `/guidelines`, and `/health` to port **8000**.

**Guideline content:** replace or extend files under `backend/app/guidelines/` and `registry.json` for your real MCG-style text.

---

## 7. Link to deployed application

**Not deployed** in this repository. Add your production URL here after deployment, for example:

- **App:** `https://your-app.example.com`  
- **API:** `https://your-api.example.com`  

Update CORS in `app/main.py` and any API base URLs for non-proxy production builds.

---

## 8. Which AI tools were used and how

| Tool | Use |
|------|-----|
| **Anthropic Claude** (server-side, **Messages API**) | End-to-end **structured extraction** and **revised HPI** generation from the composed prompt; JSON parsed and validated in Python. |
| **Cursor (or similar IDE assistant)** | Scaffolding, refactors, prompt drafting, and UI wiring during development — **not** a runtime dependency. |

**Important:** do not paste real **PHI** into third-party tools or shared prompts; use synthetic or de-identified notes for demos and development.

---

## 9. If there were more time, what would improve

- **Database** — PostgreSQL (or similar) for durable cases, audit trails, and multi-user isolation instead of in-memory + `localStorage`.  
- **Auth / tenancy** — proper login and row-level security for any real clinical-adjacent deployment.  
- **Evaluation harness** — scripted runs against fixed Case A/B fixtures with rubric scoring (factuality, disposition alignment, uncertainty handling).  
- **Stronger grounding** — retrieval over source chunks, citation spans, or a second-pass “self-check” pass that flags claims not supported by quoted spans.  
- **Diff / versioning** — optional persisted **baseline revised HPI** per case for a stable “human edit” diff after save (if not already merged on your branch).  
- **Tests** — pytest for API + prompt assembly; Vitest/RTL for critical UI paths.  
- **Ops** — Docker Compose, CI, secret management, rate limiting, and structured logging.

---

## Repository layout (short)

```text
backend/app/
  main.py, deps.py, schemas.py
  routes/          # generate, cases, guidelines
  services/        # llm_engine, cot_prompt_builder, guideline_presets, clinical_abbreviations
  prompts/         # versioned cot_clinical.md
  guidelines/      # registry.json + preset markdown
  store/           # in-memory cases
frontend/src/
  App.tsx, lib/api.ts, lib/persistence.ts, lib/structuredDefaults.ts, lib/originalNoteFormat.ts
  components/      # NoteEditor, StructuredOutput, EditableFields, CaseList, RevisedHpiPreview, …
```

---

*This project is a **demonstration** and is **not** intended for production clinical decision-making without full compliance, safety, and governance review.*
