from ..database import SessionLocal
from ..crud import create_team, create_pr
from ..schemas import TeamCreate, TeamMemberBase, PullRequestCreate
from ..services.assignment import assign_reviewers
from .. import models


def is_database_empty(db):
    try:
        # Проверяем наличие таблиц и данных
        team_count = db.query(models.Team).count()
        user_count = db.query(models.User).count()
        pr_count = db.query(models.PullRequest).count()
                
        # Считаем базу пустой, если нет команд (так как команды создаются первыми)
        return team_count == 0
    except Exception as e:
        # Если произошла ошибка, считаем что база пустая
        return True


def init_test_data():    
    db = SessionLocal()
    try:
        if not is_database_empty(db):
            return

        teams_data = [
            {
                "team_name": "backend",
                "members": [
                    {"user_id": "1", "username": "Alice", "is_active": True},
                    {"user_id": "2", "username": "Bob", "is_active": True},
                    {"user_id": "3", "username": "Charlie", "is_active": True},
                    {"user_id": "4", "username": "David", "is_active": False},  # неактивный
                ]
            },
            {
                "team_name": "frontend", 
                "members": [
                    {"user_id": "5", "username": "Eve", "is_active": True},
                    {"user_id": "6", "username": "Frank", "is_active": True},
                    {"user_id": "7", "username": "Grace", "is_active": True},
                ]
            },
            {
                "team_name": "mobile",
                "members": [
                    {"user_id": "8", "username": "Henry", "is_active": True},
                    {"user_id": "9", "username": "Ivy", "is_active": True},
                ]
            }
        ]
        
        # Создаем команды и пользователей
        for team_data in teams_data:
            team_create = TeamCreate(
                team_name=team_data["team_name"],
                members=[TeamMemberBase(**member) for member in team_data["members"]]
            )
            create_team(db, team_create)
        
        # Создаем тестовые PR
        prs_data = [
            {
                "pull_request_id": "1",
                "pull_request_name": "Add user authentication",
                "author_id": "1"
            },
            {
                "pull_request_id": "2",
                "pull_request_name": "Fix login page styling",
                "author_id": "5"
            },
            {
                "pull_request_id": "3",
                "pull_request_name": "Implement push notifications",
                "author_id": "8"
            }
        ]
        
        for pr_data in prs_data:
            # Назначаем ревьюверов
            reviewers = assign_reviewers(db, pr_data["author_id"])
            
            pr_create = PullRequestCreate(**pr_data)
            create_pr(db, pr_create, reviewers)
        
        # Создадим мердженый PR для демонстрации
        merged_pr_data = {
            "pull_request_id": "4",
            "pull_request_name": "Initial project setup", 
            "author_id": "1"
        }
        reviewers = assign_reviewers(db, merged_pr_data["author_id"])
        merged_pr = create_pr(db, PullRequestCreate(**merged_pr_data), reviewers)
        
        # Мерджим его
        from sqlalchemy import func
        merged_pr.status = "MERGED"
        merged_pr.merged_at = func.now()
        db.commit()
        
    except Exception as e:
        print(f"Ошибка при инициализации тестовых данных: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_test_data()