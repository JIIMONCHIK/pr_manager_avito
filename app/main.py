from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
from . import models
from .database import engine
from .routers import teams, users, pull_requests, health
from .scripts.init_test_data import init_test_data

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)

    init_test_data() # Тестовые данные для демонстрации

    yield

app = FastAPI(
    title="PR Reviewer Assignment Service",
    description="Сервис для автоматического назначения ревьюеров на Pull Request'ы",
    version="1.0.0",
    lifespan=lifespan
)

# Подключаем роутеры
app.include_router(teams.router)
app.include_router(users.router)
app.include_router(pull_requests.router)
app.include_router(health.router)


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8080"))
    uvicorn.run(app, host=host, port=port)