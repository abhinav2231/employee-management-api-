.PHONY: migrate seed seed-reset seed-reset-force export test run

migrate:
	alembic upgrade head

seed: migrate
	python -m scripts.seed

seed-reset: migrate
	python -m scripts.seed --reset

seed-reset-force: migrate
	python -m scripts.seed --reset --force

export:
	python -m scripts.export_csv

test:
	pytest -v

run: migrate
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
