.PHONY: install install-dev test test-cov lint format run-dev update-postcodes clean help

# Install dependencies (normal packages only)
install:
	uv sync

# Install dependencies (including dev packages)
install-dev:
	uv sync --dev

# Run tests
test:
	uv run pytest tests/

# Run tests with coverage
test-cov:
	uv run coverage run -m pytest tests/
	uv run coverage report
	uv run coverage xml -o coverage.xml

# Lint code
lint:
	uv run ruff check .
	uv run ruff format --check .

# Format code
format:
	uv run ruff check --fix .
	uv run ruff format .

# Run development server
run-dev:
	uv run fastapi dev app/main.py --port 8000

# Update postcode data files
update-postcodes:
	uv run python scripts/update_postcodes.py

# Clean up cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -f coverage.xml

# Help
help:
	@echo "Available commands:"
	@echo "  install          - Install dependencies (normal packages only)"
	@echo "  install-dev      - Install dependencies (including dev packages)"
	@echo "  test             - Run tests"
	@echo "  test-cov         - Run tests with coverage"
	@echo "  lint             - Lint code"
	@echo "  format           - Format code"
	@echo "  run-dev          - Run development server"
	@echo "  update-postcodes - Download and process latest postcode data"
	@echo "  clean            - Clean up cache files"


