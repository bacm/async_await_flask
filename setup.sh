#!/bin/bash

# Script d'installation et configuration du projet
# Usage: ./setup.sh

set -e

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║         Flask vs Quart - Setup Script                            ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Vérification de Docker
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed!${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
else
    echo -e "${GREEN}✓ Docker is installed${NC}"
fi

# Détection de Docker Compose (plugin moderne ou standalone)
if docker compose version &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose (plugin) is installed${NC}"
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose (standalone) is installed${NC}"
    DOCKER_COMPOSE="docker-compose"
else
    echo -e "${RED}✗ Docker Compose is not installed!${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Vérification Python (optionnel)
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    echo -e "${GREEN}✓ Python ${PYTHON_VERSION} is installed${NC}"
else
    echo -e "${YELLOW}⚠ Python3 not found (optional for local development)${NC}"
fi

# Vérification Make
if command -v make &> /dev/null; then
    echo -e "${GREEN}✓ Make is installed${NC}"
    USE_MAKE=true
else
    echo -e "${YELLOW}⚠ Make not found (will use docker-compose directly)${NC}"
    USE_MAKE=false
fi

# Création du fichier .env s'il n'existe pas
if [ ! -f .env ]; then
    echo -e "\n${YELLOW}Creating .env file from template...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ .env file created${NC}"
    else
        echo -e "${YELLOW}⚠ .env.example not found, skipping${NC}"
    fi
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Installation des dépendances Python locales (optionnel)
echo -e "\n${YELLOW}Do you want to install Python dependencies locally? (y/N)${NC}"
read -r INSTALL_LOCAL

if [[ $INSTALL_LOCAL =~ ^[Yy]$ ]]; then
    if command -v python3 &> /dev/null; then
        echo -e "${YELLOW}Installing local Python dependencies...${NC}"

        # Créer un environnement virtuel si nécessaire
        if [ ! -d "venv" ]; then
            echo "Creating virtual environment..."
            python3 -m venv venv
        fi

        source venv/bin/activate
        pip install --upgrade pip
        pip install -r benchmarks/requirements.txt

        echo -e "${GREEN}✓ Local dependencies installed${NC}"
        echo -e "${YELLOW}Activate with: source venv/bin/activate${NC}"
    else
        echo -e "${RED}✗ Python3 not found, cannot install dependencies${NC}"
    fi
fi

# Build des containers Docker
echo -e "\n${YELLOW}Building Docker containers...${NC}"
echo "This may take a few minutes on first run..."

if [ "$USE_MAKE" = true ]; then
    make build
else
    $DOCKER_COMPOSE -f docker-compose.global.yml build
fi

echo -e "${GREEN}✓ Containers built successfully${NC}"

# Démarrage des services
echo -e "\n${YELLOW}Do you want to start all services now? (Y/n)${NC}"
read -r START_SERVICES

if [[ ! $START_SERVICES =~ ^[Nn]$ ]]; then
    echo -e "${YELLOW}Starting services...${NC}"

    if [ "$USE_MAKE" = true ]; then
        make up
    else
        $DOCKER_COMPOSE -f docker-compose.global.yml up -d
    fi

    echo -e "\n${YELLOW}Waiting for services to be ready...${NC}"
    sleep 5

    # Health check
    echo "Checking service health..."
    for port in 5001 5002 5003 5004; do
        if curl -s http://localhost:$port/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Service on port $port is ready"
        else
            echo -e "${YELLOW}⚠${NC} Service on port $port is still starting..."
        fi
    done
fi

# Affichage des informations finales
echo -e "\n${GREEN}"
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                    SETUP COMPLETE! 🎉                             ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${YELLOW}Services are available at:${NC}"
echo "  • Flask WSGI:         http://localhost:5001"
echo "  • Flask Async Trap:   http://localhost:5002"
echo "  • Flask ASGI Wrapper: http://localhost:5003"
echo "  • Quart Native:       http://localhost:5004"
echo ""

if [ "$USE_MAKE" = true ]; then
    echo -e "${YELLOW}Quick start commands:${NC}"
    echo "  make health     - Check service health"
    echo "  make demo       - Run interactive demo"
    echo "  make test       - Run benchmarks"
    echo "  make report     - Generate full report"
    echo "  make logs       - View logs"
    echo "  make down       - Stop services"
    echo "  make help       - See all commands"
else
    echo -e "${YELLOW}Quick start commands:${NC}"
    echo "  $DOCKER_COMPOSE -f docker-compose.global.yml ps      - Check status"
    echo "  $DOCKER_COMPOSE -f docker-compose.global.yml logs -f - View logs"
    echo "  $DOCKER_COMPOSE -f docker-compose.global.yml down    - Stop services"
fi

echo ""
echo -e "${GREEN}Read README.md for detailed documentation!${NC}"
echo ""
