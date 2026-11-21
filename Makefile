.PHONY: install dev test lint run docker

install:
	pip install -r requirements.txt

dev:
	cp -n .env.example .env || true
	uvicorn app.main:app --reload

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

test:
	pytest -q

lint:
	ruff check app tests

docker:
	docker compose up --build
