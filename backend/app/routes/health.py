from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.deidentify import PHI_PATTERNS, presidio_engine_active

router = APIRouter(tags=["health"])


@router.get("/health")
def get_health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/audit")
def get_health_audit(settings: Settings = Depends(get_settings)) -> dict:
    """
    Non-PHI application audit snapshot for compliance-style monitoring.
    Extend with structured logging / SIEM hooks in production.
    """
    return {
        "report_type": "application_health_audit",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": {
            "name": "clinical-note-transformer-api",
            "version": "0.1.0",
        },
        "security": {
            "phi_persisted_in_logs": False,
            "deidentification": {
                "presidio_engine_active": presidio_engine_active(),
                "regex_rules_count": len(PHI_PATTERNS),
            },
            "api_key_gate_enabled": bool(settings.clinical_api_key),
            "anthropic_key_configured": bool(settings.anthropic_api_key),
        },
        "prompt": {
            "version": settings.prompt_version,
            "anthropic_prompt_cache": settings.anthropic_prompt_cache,
        },
    }
