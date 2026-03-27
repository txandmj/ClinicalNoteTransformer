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
    guideline_text: str | None = Field(None, description="MCG-style admission guideline")
    reference_pattern_text: str | None = Field(
        None, description="Optional distilled pattern from a reference case"
    )


class StructuredClinicalOutput(BaseModel):
    """Machine- or user-edited structured result."""

    chief_complaint: str = ""
    hpi_summary: str = ""
    key_findings: list[str] = Field(default_factory=list)
    suspected_conditions: list[str] = Field(default_factory=list)
    disposition_recommendation: Disposition = Disposition.UNKNOWN
    uncertainties: list[str] = Field(default_factory=list)
    revised_hpi: str = ""


class GenerateResponse(BaseModel):
    structured: StructuredClinicalOutput
    prompt_version: str
    model: str
    raw_cot_trace: str | None = Field(None, description="Optional chain-of-thought for debugging")


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
