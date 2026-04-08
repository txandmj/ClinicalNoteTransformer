from fastapi import APIRouter, Depends

from app.deps import verify_api_key
from app.schemas import FhirExportRequest
from app.services.fhir_export import structured_to_fhir_bundle

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/fhir")
def post_fhir_export(
    body: FhirExportRequest,
    _: None = Depends(verify_api_key),
) -> dict:
    """Export structured output as a minimal FHIR R4 Bundle (collection)."""
    return structured_to_fhir_bundle(body.structured)
