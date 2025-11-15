from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import  schemas
from .. import  crud
from ..services.assignment import assign_reviewers, reassign_reviewer
from ..database import get_db

router = APIRouter(prefix="/pullRequest", tags=["PullRequests"])


@router.post("/create", response_model=schemas.PullRequestResponse, status_code=status.HTTP_201_CREATED)
def create_pull_request(pr: schemas.PullRequestCreate, db: Session = Depends(get_db)):
    # Проверяем, существует ли PR
    existing_pr = crud.get_pr(db, pr.pull_request_id)
    if existing_pr:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "PR_EXISTS",
                    "message": "PR id already exists"
                }
            }
        )
    
    # Проверяем, существует ли автор
    author = crud.get_user(db, pr.author_id)
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "resource not found"
                }
            }
        )
    
    # Назначаем ревьюверов
    reviewers = assign_reviewers(db, pr.author_id)
    
    # Создаём PR
    db_pr = crud.create_pr(db, pr, reviewers)
    return db_pr


@router.post("/merge", response_model=schemas.PullRequestResponse)
def merge_pull_request(pr_merge: schemas.PullRequestMerge, db: Session = Depends(get_db)):
    """
    Помечает PR как MERGED
    """
    db_pr = crud.merge_pr(db, pr_merge.pull_request_id)
    if not db_pr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "resource not found"
                }
            }
        )
    return db_pr


@router.post("/reassign")
def reassign_pull_request(reassign: schemas.PullRequestReassign, db: Session = Depends(get_db)):
    """
    Переназначение конкретного ревьювера на другого из его команды
    """
    pr = crud.get_pr(db, reassign.pull_request_id)
    if not pr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "resource not found"
                }
            }
        )
    
    # Проверяем статус
    if pr.status == "MERGED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "PR_MERGED",
                    "message": "cannot reassign on merged PR"
                }
            }
        )
    
    # Проверяем, что старый ревьювер назначен
    if reassign.old_user_id not in pr.assigned_reviewers:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "NOT_ASSIGNED",
                    "message": "reviewer is not assigned to this PR"
                }
            }
        )
    
    # Переназначаем ревьювера
    new_reviewer_id = reassign_reviewer(db, reassign.pull_request_id, reassign.old_user_id)
    if not new_reviewer_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "NO_CANDIDATE", 
                    "message": "no active replacement candidate in team"
                }
            }
        )
    
    # Обновляем данные PR
    db.refresh(pr)
    
    return {
        "pr": schemas.PullRequestResponse.from_orm(pr),
        "replaced_by": new_reviewer_id
    }