from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_
import logging

from ..database import get_db
from .. import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stats", tags=["Statistics"])


@router.get("/assignments", summary="Статистика назначений ревьюеров")
def get_assignment_stats(db: Session = Depends(get_db)):
    """
    Возвращает статистику назначений ревьюеров:
    - Количество назначений по пользователям
    - Общее количество назначений
    - Самые активные ревьюверы
    """
    try:
        # Статистика по пользователям: количество назначений на PR
        user_assignment_stats = db.query(
            models.User.user_id,
            models.User.username,
            models.Team.team_name,
            models.User.is_active,
            func.count(models.PullRequest.pull_request_id).label('assignment_count')
        ).join(
            models.Team, models.User.team_name == models.Team.team_name
        ).join(
            models.PullRequest, 
            func.array_to_string(models.PullRequest.assigned_reviewers, ',').contains(models.User.user_id)
        ).group_by(
            models.User.user_id,
            models.User.username,
            models.Team.team_name,
            models.User.is_active
        ).order_by(
            func.count(models.PullRequest.pull_request_id).desc()
        ).all()

        # Общая статистика
        total_assignments = db.query(func.count(models.PullRequest.pull_request_id)).scalar() or 0
        total_users = db.query(func.count(models.User.user_id)).scalar() or 0
        active_users = db.query(func.count(models.User.user_id)).filter(models.User.is_active == True).scalar() or 0
        
        # PR по статусам
        pr_status_stats = db.query(
            models.PullRequest.status,
            func.count(models.PullRequest.pull_request_id).label('count')
        ).group_by(models.PullRequest.status).all()

        # Назначения по командам
        team_assignment_stats = db.query(
            models.Team.team_name,
            func.count(models.PullRequest.pull_request_id).label('assignment_count')
        ).join(
            models.User, models.Team.team_name == models.User.team_name
        ).join(
            models.PullRequest,
            func.array_to_string(models.PullRequest.assigned_reviewers, ',').contains(models.User.user_id)
        ).group_by(models.Team.team_name).all()

        return {
            "user_assignments": [
                {
                    "user_id": user_id,
                    "username": username,
                    "team_name": team_name,
                    "is_active": is_active,
                    "assignment_count": assignment_count
                }
                for user_id, username, team_name, is_active, assignment_count in user_assignment_stats
            ],
            "summary": {
                "total_assignments": total_assignments,
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": total_users - active_users,
                "pr_by_status": {
                    status: count for status, count in pr_status_stats
                }
            },
            "team_assignments": [
                {
                    "team_name": team_name,
                    "assignment_count": assignment_count
                }
                for team_name, assignment_count in team_assignment_stats
            ]
        }
    
    except Exception as e:
        logger.error(f"Ошибка при получении статистики назначений: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pr", summary="Статистика по Pull Request'ам")
def get_pr_stats(db: Session = Depends(get_db)):
    """
    Возвращает статистику по PR:
    - Количество PR по командам
    - Количество PR по авторам
    - Среднее количество ревьюверов на PR
    """
    try:
        # PR по командам (через авторов)
        pr_by_team = db.query(
            models.Team.team_name,
            func.count(models.PullRequest.pull_request_id).label('pr_count')
        ).join(
            models.User, models.Team.team_name == models.User.team_name
        ).join(
            models.PullRequest, models.User.user_id == models.PullRequest.author_id
        ).group_by(models.Team.team_name).all()

        # PR по авторам
        pr_by_author = db.query(
            models.User.user_id,
            models.User.username,
            models.Team.team_name,
            func.count(models.PullRequest.pull_request_id).label('pr_count')
        ).join(
            models.Team, models.User.team_name == models.Team.team_name
        ).join(
            models.PullRequest, models.User.user_id == models.PullRequest.author_id
        ).group_by(
            models.User.user_id,
            models.User.username,
            models.Team.team_name
        ).order_by(func.count(models.PullRequest.pull_request_id).desc()).all()

        # Статистика по ревьюверам в PR
        pr_reviewer_stats = db.query(
            func.avg(func.cardinality(models.PullRequest.assigned_reviewers)).label('avg_reviewers'),
            func.min(func.cardinality(models.PullRequest.assigned_reviewers)).label('min_reviewers'),
            func.max(func.cardinality(models.PullRequest.assigned_reviewers)).label('max_reviewers')
        ).filter(models.PullRequest.status == 'OPEN').first()

        # PR без ревьюверов
        pr_without_reviewers = db.query(
            func.count(models.PullRequest.pull_request_id)
        ).filter(
            and_(
                models.PullRequest.status == 'OPEN',
                func.cardinality(models.PullRequest.assigned_reviewers) == 0
            )
        ).scalar() or 0

        return {
            "pr_by_team": [
                {
                    "team_name": team_name,
                    "pr_count": pr_count
                }
                for team_name, pr_count in pr_by_team
            ],
            "pr_by_author": [
                {
                    "user_id": user_id,
                    "username": username,
                    "team_name": team_name,
                    "pr_count": pr_count
                }
                for user_id, username, team_name, pr_count in pr_by_author
            ],
            "reviewer_stats": {
                "average_reviewers_per_pr": float(pr_reviewer_stats.avg_reviewers or 0),
                "min_reviewers_per_pr": pr_reviewer_stats.min_reviewers or 0,
                "max_reviewers_per_pr": pr_reviewer_stats.max_reviewers or 0,
                "pr_without_reviewers": pr_without_reviewers
            }
        }
    
    except Exception as e:
        logger.error(f"Ошибка при получении статистики PR: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/overview", summary="Общая статистика")
def get_overview_stats(db: Session = Depends(get_db)):
    """
    Возвращает общую сводку статистики системы
    """
    try:
        # Основные метрики
        total_teams = db.query(func.count(models.Team.team_name)).scalar() or 0
        total_users = db.query(func.count(models.User.user_id)).scalar() or 0
        active_users = db.query(func.count(models.User.user_id)).filter(models.User.is_active == True).scalar() or 0
        total_pr = db.query(func.count(models.PullRequest.pull_request_id)).scalar() or 0
        open_pr = db.query(func.count(models.PullRequest.pull_request_id)).filter(models.PullRequest.status == 'OPEN').scalar() or 0
        merged_pr = db.query(func.count(models.PullRequest.pull_request_id)).filter(models.PullRequest.status == 'MERGED').scalar() or 0

        # Среднее количество ревьюверов на PR
        avg_reviewers = db.query(
            func.avg(func.cardinality(models.PullRequest.assigned_reviewers))
        ).scalar() or 0

        # PR с максимальным количеством ревьюверов
        max_reviewers_pr = db.query(
            models.PullRequest.pull_request_id,
            models.PullRequest.pull_request_name,
            func.cardinality(models.PullRequest.assigned_reviewers).label('reviewer_count')
        ).order_by(
            func.cardinality(models.PullRequest.assigned_reviewers).desc()
        ).first()

        return {
            "overview": {
                "total_teams": total_teams,
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": total_users - active_users,
                "total_pr": total_pr,
                "open_pr": open_pr,
                "merged_pr": merged_pr,
                "completion_rate": (merged_pr / total_pr * 100) if total_pr > 0 else 0
            },
            "reviewer_metrics": {
                "average_reviewers_per_pr": float(avg_reviewers),
                "pr_with_most_reviewers": {
                    "pr_id": max_reviewers_pr[0] if max_reviewers_pr else None,
                    "pr_name": max_reviewers_pr[1] if max_reviewers_pr else None,
                    "reviewer_count": max_reviewers_pr[2] if max_reviewers_pr else 0
                } if max_reviewers_pr else None
            },
            "last_updated": db.query(func.max(models.PullRequest.created_at)).scalar()
        }
    
    except Exception as e:
        logger.error(f"Ошибка при получении общей статистики: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")