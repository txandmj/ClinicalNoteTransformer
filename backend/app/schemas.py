from enum import Enum
from typing import Any, Self

from pydantic import BaseModel, Field, model_validator


class Disposition(str, Enum):
    ADMIT = "Admit"
    OBSERVE = "Observe"
    DISCHARGE = "Discharge"
    UNKNOWN = "Unknown"


class GenerateRequest(BaseModel):
    """Input for POST /generate."""

    er_note: str | None = Field(None, description="Original emergency department note")
    hp_note: str | None = Field(None, description="Original history & physical note")
    note_text: str = Field(
        default="",
        description="Optional combined or overflow note text (use if ER/H&P not split)",
    )
    guideline_key: str | None = Field(
        None,
        description="Bundled preset id (see GET /guidelines), e.g. MCG_ISC_DIABETES",
    )
    guideline_text: str | None = Field(
        None,
        description="Extra MCG-style text; merged after preset body when guideline_key is set",
    )
    reference_pattern_text: str | None = Field(
        None, description="Optional distilled bullets / rubric from a reference case"
    )
    exemplar_revised_hpi: str | None = Field(
        None,
        description=(
            "Human revised HPI from a reference (Case A) — pattern, tone, and reasoning only; "
            "must not be treated as facts for the current patient"
        ),
    )

    @model_validator(mode="after")
    def require_some_clinical_source(self) -> Self:
        chunks = [self.er_note or "", self.hp_note or "", self.note_text or ""]
        if not any(c.strip() for c in chunks):
            raise ValueError("Provide at least one of: er_note, hp_note, or note_text with content")
        return self


class GuidelinePreset(BaseModel):
    id: str
    title: str


class GuidelineListResponse(BaseModel):
    presets: list[GuidelinePreset]


class SentenceComparisonItem(BaseModel):
    """One row under §4 Sentence-by-sentence comparison (Case A style)."""

    sentence_index: int = 1
    revised: str = ""
    source: str = ""  # citations / quotes from ER+H&P supporting the revision
    reason: str = ""  # e.g. clinical + guideline-linked rationale (Part 1 / Part 2 ok in prose)


class StructuredClinicalOutput(BaseModel):
    """Machine- or user-edited structured result aligned with MCG-style Case A layout."""

    chief_complaint: str = ""
    original_hpi: str = Field(
        "",
        description="§2 Original HPI — narrative condensed from source notes (no invention).",
    )
    hpi_summary: str = Field("", description="Short structured summary (rubric auxiliary).")
    key_findings: list[str] = Field(default_factory=list)
    suspected_conditions: list[str] = Field(default_factory=list)
    disposition_recommendation: Disposition = Disposition.UNKNOWN
    uncertainties: list[str] = Field(default_factory=list)
    revised_hpi: str = Field(
        "",
        description="§3 Clean revised HPI — admission-supporting narrative paragraph(s).",
    )
    sentence_comparisons: list[SentenceComparisonItem] = Field(
        default_factory=list,
        description="§4 Sentence-by-sentence: revised vs source vs reason.",
    )


class TokenUsage(BaseModel):
    """Subset of Anthropic usage (prompt caching fields when enabled)."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_read_input_tokens: int | None = None
    cache_creation_input_tokens: int | None = None


class GenerateResponse(BaseModel):
    structured: StructuredClinicalOutput
    prompt_version: str
    model: str
    raw_cot_trace: str | None = Field(None, description="Optional chain-of-thought for debugging")
    usage: TokenUsage | None = None


class CaseCreate(BaseModel):
    """Body for POST /cases — save a case with optional original note + edited output."""

    id: str | None = Field(None, description="Set when updating an existing saved case")
    title: str | None = None
    original_note: str = ""
    structured_output: StructuredClinicalOutput
    source: str = Field("user", description="'machine' | 'user' — who last authored structured_output")
    revised_hpi_baseline: str | None = Field(
        None,
        description=(
            "Clean revised HPI text before human edits (e.g. last model output). "
            "Stored so UI can show add/remove highlights vs structured_output.revised_hpi."
        ),
    )


class CaseRecord(BaseModel):
    id: str
    title: str | None = None
    original_note: str = ""
    structured_output: StructuredClinicalOutput
    source: str = "user"
    revised_hpi_baseline: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CaseListResponse(BaseModel):
    cases: list[CaseRecord]


class DeidentifyPreviewRequest(BaseModel):
    """Preview what will be sent to the model after de-identification."""

    er_note: str | None = None
    hp_note: str | None = None
    note_text: str = ""

    @model_validator(mode="after")
    def require_some_clinical_source(self) -> Self:
        chunks = [self.er_note or "", self.hp_note or "", self.note_text or ""]
        if not any(c.strip() for c in chunks):
            raise ValueError("Provide at least one of: er_note, hp_note, or note_text with content")
        return self


class DeidentifyPreviewResponse(BaseModel):
    er_note: str | None = None
    hp_note: str | None = None
    note_text: str = ""
    presidio_active: bool = False
    note: str = Field(
        default="",
        description="Non-PHI hint about which de-id layers ran (for audit UI).",
    )


class FhirExportRequest(BaseModel):
    structured: StructuredClinicalOutput


# --- PostgreSQL swap: replace in-memory store with DB rows using these fields ---


class CaseRow(BaseModel):
    """Future ORM-friendly shape (local dev uses JSON file or memory)."""

    id: str
    payload: dict[str, Any]
