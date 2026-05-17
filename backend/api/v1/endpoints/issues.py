from fastapi import APIRouter, HTTPException, status

import db.repos.issue as issue_repo
from db.models.issue import EntityType, IssueRead

issues_router = APIRouter(prefix="/issues", tags=["Issues"])


@issues_router.get("/")
async def get_issues(entity_type: EntityType | None = None) -> list[IssueRead]:
    return issue_repo.get_all(entity_type=entity_type)


@issues_router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_issue(issue_id: int):
    deleted = issue_repo.delete(issue_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue {issue_id} not found",
        )
