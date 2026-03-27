from fastapi import APIRouter, Depends, HTTPException

from app.deps import verify_api_key
from app.schemas import CaseCreate, CaseListResponse, CaseRecord
from app.store import cases_store

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CaseRecord)
def post_cases(body: CaseCreate, _: None = Depends(verify_api_key)) -> CaseRecord:
    return cases_store.put_case(body)


@router.get("", response_model=CaseListResponse)
def get_cases(_: None = Depends(verify_api_key)) -> CaseListResponse:
    return CaseListResponse(cases=cases_store.list_cases())


@router.get("/{case_id}", response_model=CaseRecord)
def get_case(case_id: str, _: None = Depends(verify_api_key)) -> CaseRecord:
    rec = cases_store.get_case(case_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Case not found")
    return rec
