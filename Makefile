.PHONY: dev test lint format

dev:
	docker compose up --build

test:
	cd apps/api && python -m pytest

lint:
	cd apps/api && ruff check .

format:
	cd apps/api && ruff format .
