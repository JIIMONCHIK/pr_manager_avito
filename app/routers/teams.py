from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import  schemas
from .. import  crud
from ..database import get_db
from ..services.bulk_deactivation import BulkDeactivationService

router = APIRouter(prefix="/team", tags=["Teams"])


@router.post("/add", response_model=schemas.TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(team: schemas.TeamCreate, db: Session = Depends(get_db)):
    db_team = crud.create_team(db, team)
    if not db_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "TEAM_EXISTS",
                    "message": "team_name already exists"
                }
            }
        )
    return db_team


@router.get("/get", response_model=schemas.TeamResponse)
def get_team(team_name: str, db: Session = Depends(get_db)):
    db_team = crud.get_team(db, team_name)
    if not db_team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND", 
                    "message": "resource not found"
                }
            }
        )
    return db_team



@router.post("/deactivateUsers", response_model=schemas.TeamDeactivateResponse, summary="Массовая деактивация пользователей команды")
def deactivate_users_team(deactivate_request: schemas.TeamDeactivateRequest, db: Session = Depends(get_db)):
    """
    Массовая деактивация пользователей команды с безопасным переназначением открытых PR.
    """
    try:
        service = BulkDeactivationService(db)
        result = service.deactivate_users_with_reassignment(
            deactivate_request.team_name,
            deactivate_request.user_ids
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": str(e)
                }
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Ошибка при массовой деактивации пользователей"
                }
            }
        )