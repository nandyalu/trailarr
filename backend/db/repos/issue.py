from datetime import datetime, timezone

from sqlmodel import Session, col, select

from db.models.issue import EntityType, Issue, IssueRead, IssueType
from db.engine import read_session, write_session


@write_session
def upsert(
    issue_type: IssueType,
    entity_type: EntityType,
    entity_id: int,
    description: str,
    details: str | None = None,
    *,
    _session: Session = None,  # type: ignore
) -> Issue:
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
def resolve(
    issue_type: IssueType,
    entity_type: EntityType,
    entity_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> bool:
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
def resolve_all_for_entity(
    entity_type: EntityType,
    entity_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> int:
    rows = _session.exec(
        select(Issue).where(
            Issue.entity_type == entity_type,
            col(Issue.entity_id) == entity_id,
        )
    ).all()
    count = len(rows)
    for row in rows:
        _session.delete(row)
    _session.commit()
    return count


@read_session
def get_all(
    entity_type: EntityType | None = None,
    *,
    _session: Session = None,  # type: ignore
) -> list[IssueRead]:
    stmt = select(Issue)
    if entity_type is not None:
        stmt = stmt.where(Issue.entity_type == entity_type)
    return [IssueRead.model_validate(r) for r in _session.exec(stmt).all()]


@read_session
def get_for_entity(
    entity_type: EntityType,
    entity_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> list[IssueRead]:
    rows = _session.exec(
        select(Issue).where(
            Issue.entity_type == entity_type,
            col(Issue.entity_id) == entity_id,
        )
    ).all()
    return [IssueRead.model_validate(r) for r in rows]


@write_session
def delete(issue_id: int, *, _session: Session = None) -> bool:  # type: ignore
    row = _session.get(Issue, issue_id)
    if row is None:
        return False
    _session.delete(row)
    _session.commit()
    return True
