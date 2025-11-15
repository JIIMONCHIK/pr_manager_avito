# PR Reviewer Assignment Service

Сервис для автоматического назначения ревьюеров на Pull Request'ы.

## Запуск

```bash
docker-compose up -d --build
```

Сервисы будут доступны по адресам:

API: http://localhost:8080

Документация (Swagger): http://localhost:8080/docs

База данных: http://localhost:5050 (pgAdmin)

## Основные эндпоинты

### Команды
- POST /team/add - Создать команду с участниками

- GET /team/get - Получить команду по имени

- POST /team/deactivateUsers - Массовая деактивация пользователей

### Пользователи
- POST /users/setIsActive - Изменить активность пользователя

- GET /users/getReview - Получить PR пользователя как ревьювера

### Pull Request'ы
- POST /pullRequest/create - Создать PR (автоназначение ревьюверов)

- POST /pullRequest/merge - Отметить PR как мердженый

- POST /pullRequest/reassign - Переназначить ревьювера

### Статистика
- GET /stats/overview - Общая статистика системы

- GET /stats/assignments - Статистика назначений

- GET /stats/pr - Статистика по PR

- GET /stats/users - Статистика по пользователям

## Архитектура
- FastAPI - веб-фреймворк

- PostgreSQL - база данных

- SQLAlchemy - ORM

- Docker - контейнеризация


## Структура проекта
```bash
pr-manager-avitp/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   ├── routers/
│   │   ├── teams.py
│   │   ├── users.py
│   │   ├── pull_requests.py
│   │   ├── health.py
│   │   └── stats.py
│   ├── services/
│   │   ├── assignment.py
│   │   └── bulk_deactivation.py
│   └── scripts/
│       └── init_test_data.py
├── .env
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Комментарии

- Структура проекта соответствует приложенной спецификации OpenAPI

- В проекте 3 сервиса: web (основной), db (база данных), pgadmin (использовался для удобного отслеживания изменений в бд)

- Если база данных пустая, то при запуске генерируются тестовые данные (scripts/init_test_data.py)

- Выполнены следующие дополнительные задания: Добавить простой эндпоинт статистики; Добавить метод массовой деактивации пользователей команды и безопасную переназначаемость открытых PR.

