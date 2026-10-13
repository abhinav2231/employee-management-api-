.PHONY: seed export test run

seed:
	python -m scripts.seed

seed-reset:
	python -m scripts.seed --reset

export:
	python -m scripts.export_csv

test:
	pytest -v

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
