# backend/core/base/database/manager/issuemanager.py
"""Database manager for Issue records."""

from datetime import datetime, timezone

from sqlmodel import Session, col, select

from app_logger import ModuleLogger
from core.base.database.models.issue import (
    EntityType,
    Issue,
    IssueRead,
    IssueType,
)
from core.base.database.utils.engine import write_session

logger = ModuleLogger("IssueManager")


@write_session
def upsert_issue(
    issue_type: IssueType,
    entity_type: EntityType,
    entity_id: int,
    description: str,
    details: str | None = None,
    *,
    _session: Session = None,  # type: ignore
) -> Issue:
    """Create or update an issue for the given (issue_type, entity_type, entity_id).

    If a row already exists it is updated in-place (idempotent upsert).
    """
    existing = _session.exec(
        select(Issue).where(
            Issue.issue_type == issue_type,
            Issue.entity_type == entity_type,
            col(Issue.entity_id) == entity_id,
        )
    ).first()
    now = datetime.now(timezone.utc)
    if existing:
        existing.description = description
        existing.details = details
        existing.updated_at = now
        _session.add(existing)
        _session.commit()
        _session.refresh(existing)
        return existing
    issue = Issue(
        issue_type=issue_type,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        details=details,
        created_at=now,
        updated_at=now,
    )
    _session.add(issue)
    _session.commit()
    _session.refresh(issue)
    return issue


@write_session
def resolve_issue(
    issue_type: IssueType,
    entity_type: EntityType,
    entity_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> bool:
    """Delete the issue row if it exists, signalling the problem is resolved.

    Returns True if a row was deleted, False if none existed.
    """
    row = _session.exec(
        select(Issue).where(
            Issue.issue_type == issue_type,
            Issue.entity_type == entity_type,
            col(Issue.entity_id) == entity_id,
        )
    ).first()
    if row is None:
        return False
    _session.delete(row)
    _session.commit()
    return True


@write_session
def get_issues(
    entity_type: EntityType | None = None,
    *,
    _session: Session = None,  # type: ignore
) -> list[IssueRead]:
    """Return all issues, optionally filtered by entity_type."""
    stmt = select(Issue)
    if entity_type is not None:
        stmt = stmt.where(Issue.entity_type == entity_type)
    rows = _session.exec(stmt).all()
    return [IssueRead.model_validate(row) for row in rows]


@write_session
def delete_issue(
    issue_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> bool:
    """Delete an issue by id. Returns True if deleted, False if not found."""
    row = _session.get(Issue, issue_id)
    if row is None:
        return False
    _session.delete(row)
    _session.commit()
    return True
