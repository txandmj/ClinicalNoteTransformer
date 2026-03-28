from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Disposition(str, Enum):
    ADMIT = "Admit"
    OBSERVE = "Observe"
    DISCHARGE = "Discharge"
    UNKNOWN = "Unknown"


class GenerateRequest(BaseModel):
    """Input for POST /generate."""

    note_text: str = Field(..., min_length=1, description="Unstructured clinical note(s)")
    guideline_key: str | None = Field(
        None,
        description="Bundled preset id (see GET /guidelines), e.g. MCG_ISC_DIABETES",
    )
    guideline_text: str | None = Field(
        None,
        description="Extra MCG-style text; merged after preset body when guideline_key is set",
    )
    reference_pattern_text: str | None = Field(
        None, description="Optional distilled pattern from a reference case"
    )


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


class CaseRecord(BaseModel):
    id: str
    title: str | None = None
    original_note: str = ""
    structured_output: StructuredClinicalOutput
    source: str = "user"
    created_at: str | None = None
    updated_at: str | None = None


class CaseListResponse(BaseModel):
    cases: list[CaseRecord]


# --- PostgreSQL swap: replace in-memory store with DB rows using these fields ---


class CaseRow(BaseModel):
    """Future ORM-friendly shape (local dev uses JSON file or memory)."""

    id: str
    payload: dict[str, Any]
