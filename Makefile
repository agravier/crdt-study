python_dirs = crdt tests

all: format test

.PHONY: all

format:
	poetry run black $(python_dirs)
	poetry run isort $(python_dirs)

test:
	poetry run black --check $(python_dirs)
	poetry run isort --check-only $(python_dirs)
	poetry run mypy --disallow-untyped-defs $(python_dirs)
	poetry run pylint $(python_dirs)
	poetry run pytest --cov-report term:skip-covered --cov=crdt
