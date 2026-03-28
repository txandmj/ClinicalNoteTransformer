from anthropic import AuthenticationError
from fastapi import APIRouter, Depends, HTTPException

from app.core.config import Settings, get_settings
from app.deps import verify_api_key
from app.schemas import GenerateRequest, GenerateResponse
from app.services.guideline_presets import GuidelinePresetError, merge_guideline_for_request
from app.services.llm_engine import generate_structured

router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("", response_model=GenerateResponse)
def post_generate(
    body: GenerateRequest,
    _: None = Depends(verify_api_key),
    settings: Settings = Depends(get_settings),
) -> GenerateResponse:
    try:
        merged = merge_guideline_for_request(body.guideline_key, body.guideline_text)
        return generate_structured(body, settings, merged)
    except GuidelinePresetError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except AuthenticationError as e:
        raise HTTPException(
            status_code=502,
            detail=(
                "Anthropic rejected the API key (invalid or missing). "
                "Put ANTHROPIC_API_KEY=sk-ant-api03-... in backend/.env (one line, no quotes). "
                "Create or rotate a key at https://console.anthropic.com/ then restart uvicorn."
            ),
        ) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Generation failed: {e!s}") from e
