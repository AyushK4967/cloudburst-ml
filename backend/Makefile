# ML Platform Backend Makefile
# Convenient commands for development and deployment

.PHONY: help install start stop restart logs clean test verify health prod-up prod-down

# Default target
help:
	@echo "ML Platform Backend Commands:"
	@echo "  make install    - Install Python dependencies"
	@echo "  make start      - Start development environment"
	@echo "  make stop       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - Show service logs"
	@echo "  make clean      - Clean up containers and volumes"
	@echo "  make test       - Run tests"
	@echo "  make verify     - Verify backend setup"
	@echo "  make health     - Check service health"
	@echo "  make prod-up    - Start production environment"
	@echo "  make prod-down  - Stop production environment"

# Development commands
install:
	pip install -r requirements.txt

start:
	chmod +x start.sh
	./start.sh

stop:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# Testing and verification
test:
	python -m pytest tests/ -v

verify:
	python scripts/verify-setup.py

health:
	chmod +x scripts/health-check.sh
	./scripts/health-check.sh

# Production commands
prod-up:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-down:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# Database commands
db-migrate:
	docker-compose exec backend alembic upgrade head

db-revision:
	docker-compose exec backend alembic revision --autogenerate -m "$(MSG)"

db-reset:
	docker-compose down -v
	docker-compose up -d db
	sleep 10
	docker-compose exec backend alembic upgrade head

# Monitoring
monitor:
	open http://localhost:3000  # Grafana
	open http://localhost:9090  # Prometheus

# Development helpers
shell:
	docker-compose exec backend bash

db-shell:
	docker-compose exec db psql -U postgres -d mlplatform

redis-shell:
	docker-compose exec redis redis-cli

# Backup and restore
backup:
	docker-compose exec db pg_dump -U postgres mlplatform > backup_$(date +%Y%m%d_%H%M%S).sql

restore:
	docker-compose exec -T db psql -U postgres -d mlplatform < $(FILE)