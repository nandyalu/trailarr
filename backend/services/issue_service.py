"""Issue service — thin facade over db.repos.issue.

Exists so that callers (services, tasks) import from services.issue_service
rather than directly from the repo, keeping the layer boundary clean.
"""
from db.models.issue import EntityType, IssueRead, IssueType
import db.repos.issue as issue_repo


def upsert(
    issue_type: IssueType,
    entity_type: EntityType,
    entity_id: int,
    description: str,
    details: str | None = None,
) -> None:
    issue_repo.upsert(issue_type, entity_type, entity_id, description, details)


def resolve(issue_type: IssueType, entity_type: EntityType, entity_id: int) -> bool:
    return issue_repo.resolve(issue_type, entity_type, entity_id)


def resolve_all_for_entity(entity_type: EntityType, entity_id: int) -> int:
    return issue_repo.resolve_all_for_entity(entity_type, entity_id)


def get_all(entity_type: EntityType | None = None) -> list[IssueRead]:
    return issue_repo.get_all(entity_type)


def get_for_entity(entity_type: EntityType, entity_id: int) -> list[IssueRead]:
    return issue_repo.get_for_entity(entity_type, entity_id)


def delete(issue_id: int) -> bool:
    return issue_repo.delete(issue_id)
