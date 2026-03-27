"""
PostgreSQL swap: replace app.store.cases_store with SQLAlchemy models + sessions.

Keep CaseRecord / CaseCreate Pydantic models as API boundaries; map to ORM rows.
"""
