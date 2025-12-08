.PHONY: help build up down clean test visual demo report logs status health check-services

# Variables
COMPOSE_FILE := docker-compose.global.yml

# Détection automatique de Docker Compose (plugin moderne ou standalone)
ifeq ($(shell docker compose version >/dev/null 2>&1 && echo plugin),plugin)
    DOCKER_COMPOSE := docker compose -f $(COMPOSE_FILE)
else
    DOCKER_COMPOSE := docker-compose -f $(COMPOSE_FILE)
endif

# Couleurs pour l'affichage
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Affiche cette aide
	@echo "$(GREEN)╔════════════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║         Flask vs Quart - Async/Await Demonstration               ║$(NC)"
	@echo "$(GREEN)╚════════════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

build: ## Build tous les containers
	@echo "$(YELLOW)Building all containers...$(NC)"
	$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✓ Build complete!$(NC)"

up: ## Lance tous les services
	@echo "$(YELLOW)Starting all services...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✓ All services started!$(NC)"
	@echo ""
	@echo "Services are available at:"
	@echo "  • Flask WSGI:         http://localhost:5001"
	@echo "  • Flask Async Trap:   http://localhost:5002"
	@echo "  • Flask ASGI Wrapper: http://localhost:5003"
	@echo "  • Quart Native:       http://localhost:5004"
	@echo ""
	@echo "Run '$(GREEN)make health$(NC)' to check if services are ready"

down: ## Arrête tous les services
	@echo "$(YELLOW)Stopping all services...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✓ All services stopped$(NC)"

restart: down up ## Redémarre tous les services

clean: ## Nettoie tout (containers, volumes, images)
	@echo "$(RED)Cleaning up everything...$(NC)"
	$(DOCKER_COMPOSE) down -v --rmi all
	@rm -rf benchmark_graphs benchmark_results.json BENCHMARK_RESULTS.md
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

logs: ## Affiche les logs de tous les services
	$(DOCKER_COMPOSE) logs -f

logs-%: ## Affiche les logs d'un service spécifique (ex: make logs-flask-wsgi)
	$(DOCKER_COMPOSE) logs -f $*

status: ## Affiche le status de tous les services
	@echo "$(YELLOW)Services status:$(NC)"
	@$(DOCKER_COMPOSE) ps
	@echo ""
	@echo "$(YELLOW)Docker stats:$(NC)"
	@docker stats --no-stream flask-wsgi flask-async-trap flask-asgi-wrapper quart-native 2>/dev/null || true

health: ## Vérifie la santé de tous les services
	@echo "$(YELLOW)Checking services health...$(NC)"
	@echo ""
	@for service in flask-wsgi flask-async-trap flask-asgi-wrapper quart-native; do \
		port=$$(echo $$service | sed 's/flask-wsgi/5001/;s/flask-async-trap/5002/;s/flask-asgi-wrapper/5003/;s/quart-native/5004/'); \
		if curl -s http://localhost:$$port/health > /dev/null 2>&1; then \
			echo "  $(GREEN)✓$(NC) $$service (port $$port) - OK"; \
		else \
			echo "  $(RED)✗$(NC) $$service (port $$port) - DOWN"; \
		fi; \
	done
	@echo ""

check-services: ## Attend que tous les services soient prêts
	@echo "$(YELLOW)Waiting for services to be ready...$(NC)"
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		all_up=true; \
		for port in 5001 5002 5003 5004; do \
			if ! curl -s http://localhost:$$port/health > /dev/null 2>&1; then \
				all_up=false; \
				break; \
			fi; \
		done; \
		if [ "$$all_up" = true ]; then \
			echo "$(GREEN)✓ All services are ready!$(NC)"; \
			exit 0; \
		fi; \
		echo "  Attempt $$i/10 - waiting..."; \
		sleep 3; \
	done; \
	echo "$(RED)✗ Timeout waiting for services$(NC)"; \
	exit 1

test: check-services ## Lance les benchmarks (nécessite services actifs)
	@echo "$(YELLOW)Running benchmarks...$(NC)"
	@cd benchmarks && pipenv run python test_all.py
	@echo "$(GREEN)✓ Benchmarks complete!$(NC)"

visual: ## Génère les graphiques (nécessite test d'abord)
	@echo "$(YELLOW)Generating visualizations...$(NC)"
	@if [ ! -f benchmarks/benchmark_results.json ]; then \
		echo "$(RED)Error: benchmark_results.json not found. Run 'make test' first!$(NC)"; \
		exit 1; \
	fi
	@cd benchmarks && pipenv run python visual_benchmark.py
	@echo "$(GREEN)✓ Visualizations complete!$(NC)"
	@echo "Graphs saved to: benchmarks/benchmark_graphs/"

report: test visual ## Lance les tests ET génère les graphiques
	@echo "$(GREEN)✓ Complete benchmark report generated!$(NC)"
	@echo ""
	@echo "Results available in:"
	@echo "  • JSON:      benchmarks/benchmark_results.json"
	@echo "  • Markdown:  benchmarks/BENCHMARK_RESULTS.md"
	@echo "  • Graphs:    benchmarks/benchmark_graphs/"

demo: up check-services ## Lance une démo interactive complète
	@echo ""
	@echo "$(GREEN)╔════════════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║                    DEMO INTERACTIVE                                ║$(NC)"
	@echo "$(GREEN)╚════════════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)1. Testing Flask WSGI (baseline)...$(NC)"
	@time curl -s http://localhost:5001/slow | jq .
	@echo ""
	@echo "$(YELLOW)2. Testing Flask Async Trap (fake async)...$(NC)"
	@time curl -s http://localhost:5002/slow | jq .
	@echo ""
	@echo "$(YELLOW)3. Testing Flask ASGI Wrapper (overhead)...$(NC)"
	@time curl -s http://localhost:5003/slow | jq .
	@echo ""
	@echo "$(YELLOW)4. Testing Quart Native (true async)...$(NC)"
	@time curl -s http://localhost:5004/slow | jq .
	@echo ""
	@echo "$(GREEN)Now testing concurrent requests (10 parallel)...$(NC)"
	@echo ""
	@echo "$(YELLOW)Flask WSGI with 10 concurrent requests:$(NC)"
	@time for i in 1 2 3 4 5 6 7 8 9 10; do curl -s http://localhost:5001/slow & done; wait
	@echo ""
	@echo "$(YELLOW)Quart Native with 10 concurrent requests:$(NC)"
	@time for i in 1 2 3 4 5 6 7 8 9 10; do curl -s http://localhost:5004/slow & done; wait
	@echo ""
	@echo "$(GREEN)Demo complete! Notice the difference? ✨$(NC)"
	@echo ""
	@echo "Run '$(GREEN)make report$(NC)' for detailed benchmarks"

quick-test: up check-services ## Test rapide avec quelques requêtes
	@echo "$(YELLOW)Quick performance test...$(NC)"
	@echo ""
	@for service in flask-wsgi flask-async-trap flask-asgi-wrapper quart-native; do \
		port=$$(echo $$service | sed 's/flask-wsgi/5001/;s/flask-async-trap/5002/;s/flask-asgi-wrapper/5003/;s/quart-native/5004/'); \
		echo "$(YELLOW)Testing $$service:$(NC)"; \
		time curl -s http://localhost:$$port/slow > /dev/null; \
		echo ""; \
	done

install-deps: ## Installe les dépendances locales pour le développement
	@echo "$(YELLOW)Installing local dependencies...$(NC)"
	@pip install -r benchmarks/requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

dev-setup: install-deps ## Configuration complète pour le développement
	@echo "$(GREEN)✓ Development environment ready!$(NC)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. $(GREEN)make build$(NC)     - Build all containers"
	@echo "  2. $(GREEN)make up$(NC)        - Start all services"
	@echo "  3. $(GREEN)make demo$(NC)      - Run interactive demo"
	@echo "  4. $(GREEN)make report$(NC)    - Generate full benchmark report"

show-results: ## Affiche les derniers résultats de benchmark
	@if [ -f benchmarks/BENCHMARK_RESULTS.md ]; then \
		cat benchmarks/BENCHMARK_RESULTS.md; \
	else \
		echo "$(RED)No results found. Run 'make test' first!$(NC)"; \
	fi

# Commandes par service individuel
up-flask: ## Lance uniquement Flask WSGI
	$(DOCKER_COMPOSE) up -d flask-wsgi

up-async: ## Lance uniquement Flask Async Trap
	$(DOCKER_COMPOSE) up -d flask-async-trap

up-wrapper: ## Lance uniquement Flask ASGI Wrapper
	$(DOCKER_COMPOSE) up -d flask-asgi-wrapper

up-quart: ## Lance uniquement Quart Native
	$(DOCKER_COMPOSE) up -d quart-native

# Commandes de maintenance
prune: ## Nettoie les ressources Docker inutilisées
	@echo "$(YELLOW)Pruning unused Docker resources...$(NC)"
	docker system prune -f
	@echo "$(GREEN)✓ Prune complete$(NC)"

rebuild: clean build up ## Rebuild complet depuis zéro

# Valeur par défaut
.DEFAULT_GOAL := help
