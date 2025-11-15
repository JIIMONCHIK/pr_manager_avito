"""
Сервис для массовой деактивации пользователей и безопасного переназначения PR
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, update
from typing import List, Dict
import time
import logging
from .. import models, crud

logger = logging.getLogger(__name__)


class BulkDeactivationService:
    def __init__(self, db: Session):
        self.db = db
        self.start_time = time.time()
    
    def deactivate_users_with_reassignment(self, team_name: str, user_ids: List[str]) -> Dict:
        """
        Массовая деактивация пользователей с безопасным переназначением открытых PR
        """

        logger.info(f"Начало массовой деактивации пользователей: {user_ids} из команды {team_name}")
        
        # Проверяем существование команды
        team = crud.get_team(self.db, team_name)
        if not team:
            raise ValueError(f"Команда {team_name} не найдена")
        
        # Проверяем существование пользователей
        valid_users = []
        failed_deactivations = []
        
        for user_id in user_ids:
            user = crud.get_user(self.db, user_id)
            if user and user.team_name == team_name:
                valid_users.append(user_id)
            else:
                failed_deactivations.append(user_id)
                logger.warning(f"Пользователь {user_id} не найден или не принадлежит команде {team_name}")
        
        if not valid_users:
            return {
                "deactivated_users": [],
                "failed_deactivations": failed_deactivations,
                "reassigned_prs": [],
                "total_operations": 0,
                "processing_time_ms": 0
            }
        
        # Находим все открытые PR, где деактивируемые пользователи являются ревьюверами
        open_prs_with_deactivated_reviewers = self._find_open_prs_with_reviewers(valid_users)
        
        # Переназначаем ревьюверов в найденных PR
        reassignment_results = self._reassign_reviewers_bulk(open_prs_with_deactivated_reviewers, valid_users, team_name)
        
        # Деактивируем пользователей
        deactivated_users = self._deactivate_users_bulk(valid_users)
        
        return {
            "deactivated_users": deactivated_users,
            "failed_deactivations": failed_deactivations,
            "reassigned_prs": reassignment_results,
            "total_operations": len(deactivated_users) + len(reassignment_results)
        }
    
    def _find_open_prs_with_reviewers(self, user_ids: List[str]) -> List[models.PullRequest]:
        """Находит все открытые PR, где указанные пользователи являются ревьюверами"""        
        prs = self.db.query(models.PullRequest).filter(
            and_(
                models.PullRequest.status == 'OPEN',
                or_(*[models.PullRequest.assigned_reviewers.contains([user_id]) for user_id in user_ids])
            )
        ).all()
        
        return prs
    
    def _reassign_reviewers_bulk(self, prs: List[models.PullRequest], 
                               deactivated_user_ids: List[str], team_name: str) -> List[Dict]:
        """Массовое переназначение ревьюверов в PR"""
        results = []
        
        for pr in prs:
            for deactivated_user_id in deactivated_user_ids:
                if deactivated_user_id in pr.assigned_reviewers:
                    result = self._safe_reassign_reviewer(pr, deactivated_user_id, team_name)
                    results.append(result)
        
        if results:
            self.db.commit()
        
        return results
    
    def _safe_reassign_reviewer(self, pr: models.PullRequest, old_user_id: str, team_name: str) -> Dict:
        """Безопасное переназначение одного ревьювера"""
        if pr.status != 'OPEN':
            return {
                "pull_request_id": pr.pull_request_id,
                "pull_request_name": pr.pull_request_name,
                "old_reviewer": old_user_id,
                "new_reviewer": None,
                "status": "SKIPPED_MERGED"
            }
        
        # Ищем замену из активных пользователей команды
        new_reviewer_id = self._find_replacement_candidate(pr, old_user_id, team_name)
        
        if new_reviewer_id:
            new_reviewers = []
            for reviewer in pr.assigned_reviewers:
                if reviewer == old_user_id:
                    new_reviewers.append(new_reviewer_id)
                else:
                    new_reviewers.append(reviewer)
            
            pr.assigned_reviewers = new_reviewers
            
            return {
                "pull_request_id": pr.pull_request_id,
                "pull_request_name": pr.pull_request_name,
                "old_reviewer": old_user_id,
                "new_reviewer": new_reviewer_id,
                "status": "SUCCESS"
            }
        else:
            # Удаляем деактивируемого пользователя из ревьюверов (без замены)
            new_reviewers = [r for r in pr.assigned_reviewers if r != old_user_id]
            pr.assigned_reviewers = new_reviewers
            
            return {
                "pull_request_id": pr.pull_request_id,
                "pull_request_name": pr.pull_request_name,
                "old_reviewer": old_user_id,
                "new_reviewer": None,
                "status": "NO_CANDIDATE"
            }
    
    def _find_replacement_candidate(self, pr: models.PullRequest, old_user_id: str, team_name: str) -> str:
        """Находит подходящего кандидата для замены ревьювера"""
        available_users = self.db.query(models.User).filter(
            and_(
                models.User.team_name == team_name,
                models.User.is_active == True,
                models.User.user_id != old_user_id,
                models.User.user_id != pr.author_id,
                ~models.User.user_id.in_(pr.assigned_reviewers)
            )
        ).all()
        
        if not available_users:
            return None
        
        user_assignments = self._get_user_assignment_counts(team_name, [u.user_id for u in available_users])
        
        # Сортируем по количеству назначений
        available_users.sort(key=lambda u: user_assignments.get(u.user_id, 0))
        
        return available_users[0].user_id
    
    def _get_user_assignment_counts(self, team_name: str, user_ids: List[str]) -> Dict[str, int]:
        """Возвращает количество текущих назначений для пользователей"""
        from sqlalchemy import func
        
        if not user_ids:
            return {}
        
        assignment_counts = self.db.query(
            models.User.user_id,
            func.count(models.PullRequest.pull_request_id).label('assignment_count')
        ).join(
            models.PullRequest,
            func.array_to_string(models.PullRequest.assigned_reviewers, ',').contains(models.User.user_id)
        ).filter(
            and_(
                models.User.team_name == team_name,
                models.User.user_id.in_(user_ids),
                models.PullRequest.status == 'OPEN'
            )
        ).group_by(models.User.user_id).all()
        
        return {user_id: count for user_id, count in assignment_counts}
    
    def _deactivate_users_bulk(self, user_ids: List[str]) -> List[str]:
        """Массовая деактивация пользователей одним запросом"""
        if not user_ids:
            return []
        
        stmt = update(models.User).where(
            models.User.user_id.in_(user_ids)
        ).values(is_active=False)
        
        result = self.db.execute(stmt)
        self.db.commit()
                
        return user_ids