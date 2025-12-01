.PHONY: help dev dev-backend dev-frontend train ingest build up down logs clean test lint format install-backend install-frontend

help:
	@echo "Real Estate Risk Platform - Available Commands"
	@echo ""
	@echo "Development:"
	@echo "  make dev              - Run backend + frontend in Docker"
	@echo "  make dev-backend      - Run only backend locally"
	@echo "  make dev-frontend     - Run only frontend locally"
	@echo ""
	@echo "Machine Learning:"
	@echo "  make train            - Train anomaly detection models"
	@echo "  make ingest           - Run data ingestion pipeline"
	@echo ""
	@echo "Docker:"
	@echo "  make build            - Build Docker images"
	@echo "  make up               - Start all services"
	@echo "  make down             - Stop all services"
	@echo "  make logs             - View logs"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean            - Clean generated files"
	@echo "  make test             - Run tests"
	@echo "  make lint             - Run linters"
	@echo "  make format           - Format code"
	@echo "  make install-backend  - Install backend dependencies"
	@echo "  make install-frontend - Install frontend dependencies"

dev:
	docker-compose up --build

dev-backend:
	cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

train:
	python ml/model_training.py

ingest:
	python data/ingest.py

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

test:
	cd backend && pytest tests/ -v --cov=. --cov-report=html

lint:
	cd backend && flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	cd backend && pylint **/*.py

format:
	cd backend && black .
	cd backend && isort .

install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install
