.PHONY: help install sync lint format type-check test coverage clean build publish-test publish dist

SHELL := /bin/bash
PYTHON := python
UV := uv
PROJECT_NAME := mt5forge
TESTS_DIR := tests
SRC_DIR := $(PROJECT_NAME)

help:
	@echo "MT5Forge Development Commands"
	@echo "=============================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install          Install dependencies using uv"
	@echo "  make sync             Sync dependencies (uv sync)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run ruff linter"
	@echo "  make format           Format code with ruff"
	@echo "  make type-check       Type check with mypy"
	@echo "  make check            Run all checks (lint + type-check)"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run pytest"
	@echo "  make test-v           Run pytest verbose"
	@echo "  make coverage         Run tests with coverage report"
	@echo ""
	@echo "Build & Publishing:"
	@echo "  make build            Build distribution package"
	@echo "  make dist             Alias for build"
	@echo "  make publish-test     Publish to TestPyPI"
	@echo "  make publish          Publish to PyPI"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean            Remove build artifacts and cache"
	@echo "  make clean-pyc        Remove Python cache files"
	@echo "  make clean-test       Remove test and coverage files"
	@echo "  make clean-build      Remove build directories"

install:
	$(UV) sync --all-extras --dev

sync:
	$(UV) sync --all-extras --dev

lint:
	$(UV) run ruff check $(SRC_DIR) $(TESTS_DIR)

format:
	$(UV) run ruff format $(SRC_DIR) $(TESTS_DIR)
	$(UV) run ruff check --fix $(SRC_DIR) $(TESTS_DIR)

type-check:
	$(UV) run mypy $(SRC_DIR) --ignore-missing-imports

check: lint type-check
	@echo "All checks passed!"

test:
	$(UV) run pytest $(TESTS_DIR) -v

test-v:
	$(UV) run pytest $(TESTS_DIR) -vv

coverage:
	$(UV) run pytest $(TESTS_DIR) -v --cov=$(PROJECT_NAME) --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

build:
	$(UV) build

dist: build

verify-dist: dist
	$(UV) pip install twine
	twine check dist/*

publish-test: verify-dist
	@echo "Publishing to TestPyPI..."
	twine upload --repository testpypi dist/*

publish: verify-dist
	@echo "Publishing to PyPI..."
	twine upload dist/*

clean: clean-build clean-pyc clean-test

clean-build:
	rm -rf build/
	rm -rf dist/
	rm -rf .eggs/
	find . -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.egg' -delete

clean-pyc:
	find . -type f -name '*.py[cod]' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	find . -name '*~' -delete
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/

clean-test:
	rm -rf .tox/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf coverage.xml

dev-install: sync
	@echo "Development environment ready!"
	@echo "Run 'make help' to see available commands"

.DEFAULT_GOAL := help
