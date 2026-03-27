from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from app.core.config import Settings, get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(
    x_api_key: str | None = Security(api_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    """Require X-API-Key when CLINICAL_API_KEY is set."""
    if not settings.clinical_api_key:
        return
    if not x_api_key or x_api_key != settings.clinical_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
