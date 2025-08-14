.PHONY: help setup start stop test test-unit test-integration test-coverage clean lint format build deploy-dev deploy-staging deploy-prod docs

# Default target
help:
	@echo "Available commands:"
	@echo "  setup          - Set up development environment"
	@echo "  start          - Start all services"
	@echo "  stop           - Stop all services"
	@echo "  test           - Run all tests"
	@echo "  test-unit      - Run unit tests"
	@echo "  test-integration - Run integration tests"
	@echo "  test-coverage  - Run tests with coverage report"
	@echo "  lint           - Run code quality checks"
	@echo "  format         - Format code with black and isort"
	@echo "  build          - Build Docker images"
	@echo "  build-prod     - Build production Docker images"
	@echo "  deploy-dev     - Deploy to development environment"
	@echo "  deploy-staging - Deploy to staging environment"
	@echo "  deploy-prod    - Deploy to production environment"
	@echo "  docs           - Generate documentation"
	@echo "  clean          - Clean up temporary files"
	@echo "  backtest       - Run backtesting analysis"
	@echo "  monitor        - Open monitoring dashboard"

# Environment setup
setup:
	@echo "Setting up development environment..."
	cp .env.example .env
	docker-compose -f docker/docker-compose.yml pull
	pip install -r requirements.txt
	pip install -e ".[dev]"
	pre-commit install

# Service management
start:
	@echo "Starting all services..."
	docker-compose -f docker/docker-compose.yml up -d

stop:
	@echo "Stopping all services..."
	docker-compose -f docker/docker-compose.yml down

restart: stop start

# Testing
test:
	@echo "Running all tests..."
	pytest tests/ -v

test-unit:
	@echo "Running unit tests..."
	pytest tests/unit/ -v

test-integration:
	@echo "Running integration tests..."
	pytest tests/integration/ -v

test-coverage:
	@echo "Running tests with coverage..."
	pytest tests/ --cov=trading_system --cov-report=html --cov-report=term-missing

# Code quality
lint:
	@echo "Running code quality checks..."
	flake8 trading_system/ tests/
	mypy trading_system/
	black --check trading_system/ tests/
	isort --check-only trading_system/ tests/

format:
	@echo "Formatting code..."
	black trading_system/ tests/
	isort trading_system/ tests/

# Build
build:
	@echo "Building Docker images..."
	docker-compose -f docker/docker-compose.yml build

build-prod:
	@echo "Building production Docker images..."
	docker build -f docker/Dockerfile.trading-system -t trading-system:latest .
	docker build -f docker/Dockerfile.kafka -t trading-kafka:latest docker/
	docker build -f docker/Dockerfile.postgres -t trading-postgres:latest docker/

# Trading operations
backtest:
	@echo "Running backtesting analysis..."
	python scripts/run_backtest.py --config config/development.yaml

live-trading:
	@echo "Starting live trading..."
	python scripts/live_trading.py --config config/production.yaml

# Monitoring
monitor:
	@echo "Opening monitoring dashboard..."
	open http://localhost:3000

prometheus:
	@echo "Opening Prometheus..."
	open http://localhost:9090

# Deployment
deploy-dev:
	@echo "Deploying to development environment..."
	docker-compose -f docker/docker-compose.dev.yml up -d

deploy-staging:
	@echo "Deploying to staging environment..."
	kubectl apply -f k8s/staging/

deploy-prod:
	@echo "Deploying to production environment..."
	kubectl apply -f k8s/production/

# Documentation
docs:
	@echo "Generating documentation..."
	cd docs && make html

docs-serve:
	@echo "Serving documentation..."
	cd docs/_build/html && python -m http.server 8000

# Maintenance
clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

reset-db:
	@echo "Resetting database..."
	docker-compose -f docker/docker-compose.yml down -v
	docker-compose -f docker/docker-compose.yml up -d postgres timescaledb

logs:
	@echo "Showing service logs..."
	docker-compose -f docker/docker-compose.yml logs -f

# Development helpers
install-dev:
	pip install -e ".[dev]"

install-docs:
	pip install -e ".[docs]"

install-monitoring:
	pip install -e ".[monitoring]"

# Database operations
db-migrate:
	@echo "Running database migrations..."
	alembic upgrade head

db-revision:
	@echo "Creating new database revision..."
	alembic revision --autogenerate -m "$(MESSAGE)"

db-downgrade:
	@echo "Downgrading database..."
	alembic downgrade -1

# Security
security-scan:
	@echo "Running security scan..."
	safety check
	bandit -r trading_system/
