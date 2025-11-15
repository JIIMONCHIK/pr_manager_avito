from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import schemas
from .. import crud
from ..database import get_db

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/setIsActive", response_model=schemas.UserResponse)
def set_user_active(user_update: schemas.UserUpdateActive, db: Session = Depends(get_db)):
    db_user = crud.update_user_active(db, user_update)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "resource not found"
                }
            }
        )
    return db_user


@router.get("/getReview", response_model=schemas.UserPRsResponse)
def get_user_reviews(user_id: str, db: Session = Depends(get_db)):
    """
    Получить PR'ы, где пользователь назначен ревьювером.
    """

    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "resource not found"
                }
            }
        )
    
    prs = crud.get_prs_by_reviewer(db, user_id)
    return schemas.UserPRsResponse(
        user_id=user_id,
        pull_requests=[schemas.PullRequestShort.from_orm(pr) for pr in prs]
    )