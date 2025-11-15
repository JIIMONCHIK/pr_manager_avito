"""
Роутер для health check эндпоинтов.
Простые эндпоинты для мониторинга работы сервиса.
"""
from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    return {"status": "healthy"}