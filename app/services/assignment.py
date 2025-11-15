from sqlalchemy.orm import Session
import random
from typing import List
from .. import crud


def assign_reviewers(db: Session, author_id: str, max_reviewers: str = 2) -> List[str]:
    # Получаем автора
    author = crud.get_user(db, author_id)
    if not author:
        return []
    
    # Получаем активных членов команды (исключая автора)
    team_members = crud.get_active_team_members(db, author.team_name, author_id)
    
    available_reviewers = [user.user_id for user in team_members]
    num_reviewers = min(max_reviewers, len(available_reviewers))
    
    if num_reviewers > 0:
        return random.sample(available_reviewers, num_reviewers)
    
    return []


def reassign_reviewer(db: Session, pr_id: str, old_user_id: str) -> str:
    pr = crud.get_pr(db, pr_id)
    if not pr:
        return None
    
    # Проверяем, что старый ревьювер назначен на PR
    if old_user_id not in pr.assigned_reviewers:
        return None
    
    # Получаем команду старого ревьювера
    old_reviewer = crud.get_user(db, old_user_id)
    if not old_reviewer:
        return None
    
    # Получаем доступных кандидатов из команды
    available_candidates = crud.get_active_team_members(
        db, old_reviewer.team_name, old_user_id
    )
    
    # Исключаем уже назначенных ревьюверов и автора
    available_user_ids = [
        user.user_id for user in available_candidates 
        if user.user_id not in pr.assigned_reviewers and user.user_id != pr.author_id
    ]
    
    if not available_user_ids:
        return None
    
    new_reviewer_id = random.choice(available_user_ids)
    
    new_reviewers = []
    for reviewer in pr.assigned_reviewers:
        if reviewer == old_user_id:
            new_reviewers.append(new_reviewer_id)
        else:
            new_reviewers.append(reviewer)
    
    pr.assigned_reviewers = new_reviewers
    db.commit()
    
    return new_reviewer_id