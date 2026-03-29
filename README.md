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

## 8. AI assistance, prompts, attribution, and verification

### Which AI-assisted tools were used

| Tool | Role |
|------|------|
| **Anthropic Claude** (Messages API) | **Runtime** model: produces the structured JSON (including revised HPI) for each generate request. |
| **Cursor** (IDE agent / chat) | **Development-time** help: scaffolding, refactors, debugging, prompt drafting for `cot_clinical.md`, and documentation (including this README). |

Other local tooling (Python, Node, git) is standard and not AI-hosted.

**PHI:** do not paste real **protected health information** into third-party assistants or cloud LLM UIs; use synthetic or de-identified vignettes only.

### Prompts used for frontend scaffolding and/or text parsing

Exact chat transcripts were not archived. The **kinds** of Cursor-style prompts that drove development included:

- **Backend scaffold** — e.g. FastAPI app layout, `POST /generate` and case CRUD routes, Pydantic models aligned to a fixed JSON shape, and wiring to the Anthropic client.
- **Frontend scaffold** — e.g. Vite + React + TypeScript app with a note editor, structured output panel, `fetch` helpers, and Vite proxy to the API.
- **Feature iterations** — e.g. split ER/H&P fields, guideline presets + `GET /guidelines`, prompt caching breakpoints, hover/scroll from revised HPI to §4, human-edit diff vs a saved baseline, `.env` loading from `backend/` regardless of cwd.

**Text parsing in the product** is **not** done by the IDE assistant at runtime. It is implemented in code:

- **LLM output:** JSON extracted in `llm_engine.py` (strip markdown fences if present), then validated with **Pydantic** (`StructuredClinicalOutput`).
- **Saved notes:** `original_note` serialization uses explicit markers (`---ER---`, etc.) in `frontend/src/lib/originalNoteFormat.ts` — designed and implemented in the repo, not by ad-hoc AI parsing of free text.

**Clinical prompting** (what we send to Claude) lives in `prompts/templates/v1/cot_clinical.md` and the composed user blocks in `services/cot_prompt_builder.py`; those were refined through a mix of manual editing and assistant-assisted drafting.

### Which parts were AI-generated

- **End-user clinical output** for each run: **model-generated** by Claude from the current notes + guidance, then **post-processed** in Python (abbreviation expansion) and **validated** against schemas.
- **Substantial portions of application source and docs** began as **AI-drafted** suggestions in Cursor (typical for new files, boilerplate, and iterative patches), then were reviewed and adjusted in the editor.

### Which parts were manually implemented or modified

- **Domain and safety choices** — schema fields, disposition enum, uncertainty handling rules, and what goes into bundled guidelines (`app/guidelines/`) and `registry.json`.
- **`cot_clinical.md`** — rubric alignment, “do not copy exemplar facts,” JSON shape instructions, and grounding rules (human-owned, with assistant help for wording).
- **`clinical_abbreviations.py`** — which abbreviations expand and how (curated list, not model-invented at runtime).
- **Config and hardening** — `core/config.py`, optional `X-API-Key`, CORS allowlist, friendly error handling for auth failures.
- **UX polish** — layout, labels, controlled components (e.g. disclosure panels), diff behavior, and local/backend sync for saved cases.
- **Git history, merges, and deployment-related README sections** — human-driven.

### How correctness was verified

| Area | Method |
|------|--------|
| **API contracts** | Pydantic validation on requests and on parsed LLM JSON; FastAPI returns 4xx/5xx with clear messages when validation fails. |
| **Types on the client** | TypeScript types mirror backend shapes; `npm run build` runs `tsc -b` before Vite build. |
| **Generate path** | Manual runs with **synthetic** ER/H&P snippets: check JSON fields populate, disposition matches narrative, §4 row count aligns with revised HPI sentences where expected, and UI hover/diff behave. |
| **Persistence** | Save → reload case; confirm `original_note` round-trips ER/H&P/other and structured fields match. |
| **Automated tests** | Limited in this repo; correctness today relies on the checks above rather than a large CI test suite (see §9). |

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
