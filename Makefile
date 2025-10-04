.PHONY: help install dev start stop logs clean migrate test

help:
	@echo "MicroAppFinder - Available commands:"
	@echo "  make install   - Install all dependencies"
	@echo "  make dev       - Start development environment"
	@echo "  make start     - Start all services with Docker"
	@echo "  make stop      - Stop all services"
	@echo "  make logs      - Show logs"
	@echo "  make migrate   - Run database migrations"
	@echo "  make clean     - Clean up containers and volumes"
	@echo "  make test      - Run tests"

install:
	@echo "Installing dependencies..."
	cd apps/web && npm install
	cd apps/api && pip install -r requirements.txt
	cd apps/worker && pip install -r requirements.txt

dev:
	@echo "Starting development environment..."
	docker-compose up -d db redis qdrant
	@echo "Services started. Run 'make dev-api' and 'make dev-web' in separate terminals."

dev-api:
	cd apps/api && uvicorn app.main:app --reload

dev-worker:
	cd apps/worker && python -m worker.main

dev-web:
	cd apps/web && npm run dev

start:
	@echo "Starting all services..."
	docker-compose up -d

stop:
	@echo "Stopping all services..."
	docker-compose down

logs:
	docker-compose logs -f

migrate:
	@echo "Running database migrations..."
	cd infra/migrations && alembic upgrade head

clean:
	@echo "Cleaning up..."
	docker-compose down -v
	rm -rf apps/web/.next
	rm -rf apps/web/node_modules
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +

test:
	@echo "Running tests..."
	cd apps/api && pytest
	cd apps/web && npm test
