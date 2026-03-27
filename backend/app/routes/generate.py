from fastapi import APIRouter, Depends, HTTPException

from app.core.config import Settings, get_settings
from app.deps import verify_api_key
from app.schemas import GenerateRequest, GenerateResponse
from app.services.llm_engine import generate_structured

router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("", response_model=GenerateResponse)
def post_generate(
    body: GenerateRequest,
    _: None = Depends(verify_api_key),
    settings: Settings = Depends(get_settings),
) -> GenerateResponse:
    try:
        return generate_structured(body, settings)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Generation failed: {e!s}") from e
