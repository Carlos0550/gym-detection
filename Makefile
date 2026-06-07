.PHONY: help up down build rebuild restart logs ps \
        shell shell-fe db-shell seed migrate makemigration \
        test lint typecheck fe-lint fe-typecheck \
        clean fclean

# ===== Config =====
COMPOSE        = docker compose
COMPOSE_FILE   = docker-compose.yml
BACKEND        = backend
FRONTEND       = frontend
POSTGRES       = postgres

# Cargar .env del backend si existe (target compose ya lo hace, pero lo necesitamos para algunos comandos)
ifneq (,$(wildcard ./backend/.env))
include ./backend/.env
export
endif

# ===== Default =====
help: ## Mostrar esta ayuda
	@awk 'BEGIN {FS = ":.*##"; printf "\nUso: make \033[36m<target>\033[0m\n\nTargets:\n"} \
	/^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# ===== Docker compose =====
up: ## Levantar todos los servicios en background
	$(COMPOSE) -f $(COMPOSE_FILE) up -d --build

down: ## Detener y eliminar contenedores (NO elimina volúmenes)
	$(COMPOSE) -f $(COMPOSE_FILE) down

build: ## Construir imágenes
	$(COMPOSE) -f $(COMPOSE_FILE) build

rebuild: ## Reconstruir imágenes sin cache
	$(COMPOSE) -f $(COMPOSE_FILE) build --no-cache

restart: ## Reiniciar servicios
	$(COMPOSE) -f $(COMPOSE_FILE) restart

logs: ## Ver logs en vivo (todos los servicios)
	$(COMPOSE) -f $(COMPOSE_FILE) logs -f

logs-be: ## Ver logs del backend
	$(COMPOSE) -f $(COMPOSE_FILE) logs -f $(BACKEND)

logs-fe: ## Ver logs del frontend
	$(COMPOSE) -f $(COMPOSE_FILE) logs -f $(FRONTEND)

logs-db: ## Ver logs de postgres
	$(COMPOSE) -f $(COMPOSE_FILE) logs -f $(POSTGRES)

ps: ## Listar servicios corriendo
	$(COMPOSE) -f $(COMPOSE_FILE) ps

# ===== Shells =====
shell: ## Entrar al bash del backend
	$(COMPOSE) -f $(COMPOSE_FILE) exec $(BACKEND) bash

shell-fe: ## Entrar al bash del frontend
	$(COMPOSE) -f $(COMPOSE_FILE) exec $(FRONTEND) sh

db-shell: ## Abrir psql en postgres
	$(COMPOSE) -f $(COMPOSE_FILE) exec $(POSTGRES) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

# ===== Backend: DB y migraciones =====
migrate: ## Aplicar migraciones pendientes (alembic upgrade head)
	$(COMPOSE) -f $(COMPOSE_FILE) exec $(BACKEND) alembic upgrade head

makemigration: ## Generar migración autogenerada (uso: make makemigration m="descripcion")
	$(COMPOSE) -f $(COMPOSE_FILE) exec $(BACKEND) alembic revision --autogenerate -m "$(m)"

seed: ## Ejecutar seed inicial
	$(COMPOSE) -f $(COMPOSE_FILE) exec $(BACKEND) python -m app.seed

# ===== Backend: tests y calidad =====
test-setup: ## Preparar DB de tests (drop+create+migrate). Una vez antes de la primera corrida.
	$(COMPOSE) -f $(COMPOSE_FILE) exec $(BACKEND) python -m tests.setup_test_db

test: test-setup ## Correr tests del backend (corre test-setup antes)
	$(COMPOSE) -f $(COMPOSE_FILE) exec $(BACKEND) pytest

lint: ## Correr ruff en el backend
	$(COMPOSE) -f $(COMPOSE_FILE) exec $(BACKEND) ruff check .

typecheck: ## Correr tsc --noEmit en el backend (placeholder: no hay tipos aún)
	@echo "Etapa 1+: agregar mypy/pyright al backend"

# ===== Frontend: calidad =====
fe-lint: ## Correr next lint en el frontend
	$(COMPOSE) -f $(COMPOSE_FILE) exec $(FRONTEND) npm run lint

fe-typecheck: ## Correr tsc --noEmit en el frontend
	$(COMPOSE) -f $(COMPOSE_FILE) exec $(FRONTEND) npm run typecheck

# ===== Limpieza =====
clean: ## Detener y eliminar contenedores + volúmenes
	$(COMPOSE) -f $(COMPOSE_FILE) down -v

fclean: ## clean + borrar imágenes construidas
	$(COMPOSE) -f $(COMPOSE_FILE) down -v --rmi all
