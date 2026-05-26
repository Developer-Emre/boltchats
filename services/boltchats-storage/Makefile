.PHONY: run test lint

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

test:
	pytest tests/ -v

lint:
	ruff check app/ tests/
