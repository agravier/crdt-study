python_dirs = crdt tests

all: format static-tests pytest test

.PHONY: all

format:
	poetry run black $(python_dirs)
	poetry run isort $(python_dirs)

static-tests:
	poetry run black --check $(python_dirs)
	poetry run isort --check-only $(python_dirs)
	poetry run mypy --disallow-untyped-defs $(python_dirs)
	poetry run pylint $(python_dirs)

pytest:
	poetry run pytest --cov-report term:skip-covered --cov=crdt

test: static-tests pytest
