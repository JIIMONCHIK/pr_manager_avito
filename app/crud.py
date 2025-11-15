"""
CRUD операции для работы с базой данных.
Содержит функции для работы с командами, пользователями и PR.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List
from . import models
from . import schemas


def get_team(db: Session, team_name: str):
    return db.query(models.Team).filter(models.Team.team_name == team_name).first()


def create_team(db: Session, team: schemas.TeamCreate):
    # Проверяем, существует ли команда
    db_team = get_team(db, team.team_name)
    if db_team:
        return None
    
    # Создаём команду
    db_team = models.Team(team_name=team.team_name)
    db.add(db_team)
    
    # Создаём/обновляем пользователей
    for member in team.members:
        db_user = get_user(db, member.user_id)
        if db_user:
            # Обновляем существующего пользователя
            db_user.username = member.username
            db_user.is_active = member.is_active
            db_user.team_name = team.team_name
        else:
            # Создаём нового пользователя
            db_user = models.User(
                user_id=member.user_id,
                username=member.username,
                team_name=team.team_name,
                is_active=member.is_active
            )
            db.add(db_user)
    
    db.commit()
    db.refresh(db_team)
    return db_team


def get_user(db: Session, user_id: str):
    return db.query(models.User).filter(models.User.user_id == user_id).first()


def update_user_active(db: Session, user_update: schemas.UserUpdateActive):
    db_user = get_user(db, user_update.user_id)
    if not db_user:
        return None
    
    db_user.is_active = user_update.is_active
    db.commit()
    db.refresh(db_user)
    return db_user


def get_pr(db: Session, pr_id: str):
    return db.query(models.PullRequest).filter(models.PullRequest.pull_request_id == pr_id).first()


def create_pr(db: Session, pr: schemas.PullRequestCreate, reviewers: List[str]):
    db_pr = models.PullRequest(
        pull_request_id=pr.pull_request_id,
        pull_request_name=pr.pull_request_name,
        author_id=pr.author_id,
        assigned_reviewers=reviewers
    )
    db.add(db_pr)
    db.commit()
    db.refresh(db_pr)
    return db_pr


def merge_pr(db: Session, pr_id: str):
    db_pr = get_pr(db, pr_id)
    if not db_pr:
        return None
    
    # Если уже MERGED, не меняем
    if db_pr.status != "MERGED":
        db_pr.status = "MERGED"
        db_pr.merged_at = func.now()
        db.commit()
        db.refresh(db_pr)
    
    return db_pr


def get_active_team_members(db: Session, team_name: str, exclude_user_id: str = None):
    query = db.query(models.User).filter(
        and_(
            models.User.team_name == team_name,
            models.User.is_active == True
        )
    )
    
    if exclude_user_id:
        query = query.filter(models.User.user_id != exclude_user_id)
    
    return query.all()


def get_prs_by_reviewer(db: Session, user_id: str):
    return db.query(models.PullRequest).filter(
        models.PullRequest.assigned_reviewers.contains([user_id])
    ).all()