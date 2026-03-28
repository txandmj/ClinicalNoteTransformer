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
2. Output one JSON object with: chief_complaint, original_hpi, hpi_summary, key_findings,
   suspected_conditions, disposition_recommendation (Admit|Observe|Discharge|Unknown),
   uncertainties, revised_hpi (clean revised HPI), sentence_comparisons (array of
   {sentence_index, revised, source, reason}).
3. revised_hpi disposition must be consistent with disposition_recommendation.
4. If an exemplar revised HPI is provided, use it for style/reasoning only; never copy its patient facts.
"""
