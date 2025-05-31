.PHONY: help install install-dev clean lint format test test-coverage run-api run-dashboard run-scraper run-scheduler db-init db-migrate db-upgrade db-downgrade db-seed db-reset docker-build docker-up docker-down logs build dist upload-test upload-prod

# Default target
help:
	@echo "Available commands:"
	@echo "  Development:"
	@echo "    install          Install production dependencies"
	@echo "    install-dev      Install development dependencies"
	@echo "    clean            Clean build artifacts and cache"
	@echo ""
	@echo "  Code Quality:"
	@echo "    lint             Run linting with ruff"
	@echo "    format           Format code with ruff"
	@echo "    test             Run tests"
	@echo "    test-coverage    Run tests with coverage report"
	@echo ""
	@echo "  Application:"
	@echo "    run-api          Start the Flask API server"
	@echo "    run-dashboard    Start the Streamlit dashboard"
	@echo "    run-scraper      Run the data scraper"
	@echo "    run-scheduler    Start the scheduler"
	@echo ""
	@echo "  Database:"
	@echo "    db-init          Initialize database with Alembic"
	@echo "    db-migrate       Create new migration"
	@echo "    db-upgrade       Apply migrations"
	@echo "    db-downgrade     Rollback last migration"
	@echo "    db-seed          Seed database with sample data"
	@echo "    db-reset         Reset database (drop and recreate)"
	@echo ""
	@echo "  Docker:"
	@echo "    docker-build     Build Docker images"
	@echo "    docker-up        Start services with docker-compose"
	@echo "    docker-down      Stop services"
	@echo "    logs             Show docker logs"
	@echo ""
	@echo "  Distribution:"
	@echo "    build            Build distribution packages"
	@echo "    dist             Create source and wheel distributions"
	@echo "    upload-test      Upload to TestPyPI"
	@echo "    upload-prod      Upload to PyPI"

# Development setup
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pip install ruff pytest pytest-cov black isort mypy

# Cleanup
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Code quality
lint:
	ruff check .

format:
	ruff format .
	ruff check --fix .

# Application runners
run-extractor:
	python public_transport_watcher/extractor/extractor.py

run-api:
	python public_transport_watcher/api/app.py

run-monitoring:
	streamlit run public_transport_watcher/monitoring/app.py

run-app:
	streamlit run public_transport_watcher/application/app.py

# Database operations
db-init:
	alembic init alembic
	@echo "Database initialized. Edit alembic.ini and env.py as needed."

db-migrate:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1

db-seed:
	python public_transport_watcher/seeds/generate_logs.py
	@echo "Seed data generated. Apply with: psql -d your_db -f api_logs_seeds.sql"

db-reset:
	@echo "WARNING: This will drop and recreate the database!"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		alembic downgrade base; \
		alembic upgrade head; \
		echo "Database reset complete."; \
	else \
		echo "Operation cancelled."; \
	fi

# Docker operations
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

logs:
	docker-compose logs -f

# Development workflow shortcuts
dev-setup: install-dev
	@echo "Development environment setup complete!"
	@echo "Run 'make help' to see available commands."

check: lint test
	@echo "All checks passed!"

deploy-prep: clean lint test build
	@echo "Ready for deployment!" 