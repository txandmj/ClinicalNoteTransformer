from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routes import cases, generate, guidelines

app = FastAPI(title="Clinical Note Transformer API", version="0.1.0")

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router)
app.include_router(cases.router)
app.include_router(guidelines.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if _STATIC_DIR.is_dir():
    _assets = _STATIC_DIR / "assets"
    if _assets.is_dir():
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    @app.get("/")
    async def _serve_index() -> FileResponse:
        return FileResponse(_STATIC_DIR / "index.html")

    @app.get("/{spa_path:path}")
    async def _serve_spa(_spa_path: str) -> FileResponse:
        return FileResponse(_STATIC_DIR / "index.html")
