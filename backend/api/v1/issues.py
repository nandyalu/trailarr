from fastapi import APIRouter, HTTPException, status

from app_logger import ModuleLogger
import core.base.database.manager.issuemanager as issue_manager
from core.base.database.models.issue import EntityType, IssueRead

logger = ModuleLogger("IssuesAPI")

issues_router = APIRouter(prefix="/issues", tags=["Issues"])


@issues_router.get("/")
async def get_issues(
    entity_type: EntityType | None = None,
) -> list[IssueRead]:
    """Return all active issues, optionally filtered by entity_type."""
    return issue_manager.get_issues(entity_type)


@issues_router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_issue(issue_id: int):
    """Dismiss an issue by id (marks it as acknowledged / resolved)."""
    deleted = issue_manager.delete_issue(issue_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue {issue_id} not found",
        )
