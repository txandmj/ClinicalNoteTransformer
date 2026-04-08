from fastapi import APIRouter, Depends

from app.deps import verify_api_key
from app.deidentify import deidentify_note, presidio_engine_active
from app.schemas import DeidentifyPreviewRequest, DeidentifyPreviewResponse

router = APIRouter(prefix="/privacy", tags=["privacy"])


@router.post("/deidentify-preview", response_model=DeidentifyPreviewResponse)
def post_deidentify_preview(
    body: DeidentifyPreviewRequest,
    _: None = Depends(verify_api_key),
) -> DeidentifyPreviewResponse:
    """Return de-identified ER/H&P/other text as it will be used in the model prompt (human review)."""
    presidio = presidio_engine_active()
    note = (
        "De-identification: Microsoft Presidio (NER) + regex rules."
        if presidio
        else "De-identification: regex rules only (Presidio unavailable or spaCy model missing)."
    )
    return DeidentifyPreviewResponse(
        er_note=deidentify_note(body.er_note),
        hp_note=deidentify_note(body.hp_note),
        note_text=deidentify_note(body.note_text) or "",
        presidio_active=presidio,
        note=note,
    )
