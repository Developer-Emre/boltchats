PYTHON  ?= python3.11
PYTEST  := $(PYTHON) -m pytest
PORT    ?= 8001

.PHONY: run dev test test-unit test-integration lint format help

run:
	uvicorn app.main:app --host 0.0.0.0 --port $(PORT)

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port $(PORT)

test:
	$(PYTEST) tests/ -v

test-unit:
	$(PYTEST) tests/unit/ -v

test-integration:
	$(PYTEST) tests/integration/ -v -m integration

lint:
	ruff check app/ tests/

format:
	black app/ tests/
	isort app/ tests/

help:
	@echo "run             start production server (PORT=$(PORT))"
	@echo "dev             start dev server with auto-reload"
	@echo "test            run all tests"
	@echo "test-unit       run unit tests only"
	@echo "test-integration run integration tests only"
	@echo "lint            ruff check"
	@echo "format          black + isort"
