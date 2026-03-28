# ClinicalNoteTransformer
## Architecture
ClinicalNoteTransformer/
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   └── app/
│       ├── main.py                 # FastAPI + CORS + routers
│       ├── deps.py                 # Optional X-API-Key → CLINICAL_API_KEY
│       ├── schemas.py              # Pydantic: Generate*, Case*, StructuredClinicalOutput
│       ├── core/config.py          # Settings (Anthropic key, model, prompt_version)
│       ├── db/__init__.py          # Placeholder for PostgreSQL swap
│       ├── prompts/
│       │   ├── config.py           # PROMPT_VERSION + load_cot_template()
│       │   └── templates/v1/cot_clinical.md
│       ├── services/
│       │   ├── llm_engine.py       # Anthropic Claude → JSON → StructuredClinicalOutput
│       │   └── cot_prompt_builder.py
│       ├── store/cases_store.py    # In-memory cases (swap for DB)
│       └── routes/
│           ├── generate.py       # POST /generate
│           └── cases.py            # POST /cases, GET /cases, GET /cases/{case_id}
└── frontend/
    ├── .env.example                # VITE_CLINICAL_API_KEY (optional)
    ├── package.json
    ├── vite.config.ts              # Proxy /generate, /cases → :8000
    ├── index.html
    └── src/
        ├── App.tsx                 # Wires editor, output, save, list + localStorage mirror
        ├── types.ts
        ├── lib/
        │   ├── api.ts              # fetch → FastAPI
        │   └── persistence.ts      # localStorage saved cases
        └── components/
            ├── NoteEditor/
            ├── StructuredOutput/   # wraps EditableFields + model/prompt meta
            ├── EditableFields/     # (machine) / (edited) tags
            └── CaseList/