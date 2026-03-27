"""
Versioned prompt templates for clinical CoT generation.

Bump PROMPT_VERSION when changing behavior so outputs stay auditable.
"""

from pathlib import Path

PROMPT_VERSION = "v1"

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def load_cot_template(version: str = PROMPT_VERSION) -> str:
    """Load chain-of-thought system/user template fragment for the given version."""
    path = _TEMPLATES_DIR / version / "cot_clinical.md"
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return _DEFAULT_COT_FALLBACK


_DEFAULT_COT_FALLBACK = """You are a clinical documentation assistant. Follow these rules:
1. Only state facts supported by the provided note. Do not invent findings.
2. Use explicit uncertainty for missing data.
3. The Revised HPI must support the disposition recommendation with clear reasoning.
4. Output valid JSON matching the provided schema exactly.
"""
