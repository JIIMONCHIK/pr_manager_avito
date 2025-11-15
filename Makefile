.PHONY: run build up down logs test

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

# test:
# 	pytest

# migrate:
# 	alembic upgrade head