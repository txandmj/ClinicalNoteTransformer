"""
In-memory case store for development.

Swap with PostgreSQL (SQLAlchemy/async) using the same CaseRecord shape.
"""

import uuid
from datetime import datetime, timezone

from app.schemas import CaseCreate, CaseRecord


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_cases: dict[str, CaseRecord] = {}


def _baseline_persist(body: CaseCreate, existing: CaseRecord | None) -> str | None:
    """Keep baseline from body when sent; on update allow omit to retain prior."""
    if body.revised_hpi_baseline is not None:
        return body.revised_hpi_baseline
    if existing is not None:
        return existing.revised_hpi_baseline
    return None


def create_case(body: CaseCreate) -> CaseRecord:
    cid = str(uuid.uuid4())
    now = _now_iso()
    rec = CaseRecord(
        id=cid,
        title=body.title,
        original_note=body.original_note,
        structured_output=body.structured_output,
        source=body.source,
        revised_hpi_baseline=body.revised_hpi_baseline,
        created_at=now,
        updated_at=now,
    )
    _cases[cid] = rec
    return rec


def update_case(case_id: str, body: CaseCreate) -> CaseRecord | None:
    existing = _cases.get(case_id)
    if not existing:
        return None
    now = _now_iso()
    rec = CaseRecord(
        id=case_id,
        title=body.title if body.title is not None else existing.title,
        original_note=body.original_note,
        structured_output=body.structured_output,
        source=body.source,
        revised_hpi_baseline=_baseline_persist(body, existing),
        created_at=existing.created_at,
        updated_at=now,
    )
    _cases[case_id] = rec
    return rec


def get_case(case_id: str) -> CaseRecord | None:
    return _cases.get(case_id)


def list_cases() -> list[CaseRecord]:
    return sorted(_cases.values(), key=lambda c: (c.updated_at or ""), reverse=True)


def put_case(body: CaseCreate) -> CaseRecord:
    """Create or update when body.id matches an existing case."""
    case_id = body.id
    if case_id and case_id in _cases:
        updated = update_case(case_id, body)
        assert updated is not None
        return updated
    if case_id:
        now = _now_iso()
        rec = CaseRecord(
            id=case_id,
            title=body.title,
            original_note=body.original_note,
            structured_output=body.structured_output,
            source=body.source,
            revised_hpi_baseline=body.revised_hpi_baseline,
            created_at=now,
            updated_at=now,
        )
        _cases[case_id] = rec
        return rec
    return create_case(body)
