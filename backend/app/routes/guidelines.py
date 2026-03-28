from fastapi import APIRouter, Depends

from app.deps import verify_api_key
from app.schemas import GuidelineListResponse, GuidelinePreset
from app.services.guideline_presets import list_preset_keys

router = APIRouter(prefix="/guidelines", tags=["guidelines"])


@router.get("", response_model=GuidelineListResponse)
def get_guidelines(_: None = Depends(verify_api_key)) -> GuidelineListResponse:
    presets = [GuidelinePreset(id=k, title=t) for k, t in list_preset_keys()]
    return GuidelineListResponse(presets=presets)
