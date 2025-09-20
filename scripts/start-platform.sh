#!/bin/bash

# Script pour démarrer la plateforme de génération de cours complète
# Frontend Next.js + Backend FastAPI

set -e

echo "🚀 Démarrage de la plateforme CourseGen AI"
echo "========================================="

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier si on est dans le bon répertoire
if [ ! -f "docker-compose.yml" ]; then
    error "docker-compose.yml not found. Assurez-vous d'être dans le répertoire racine du projet."
    exit 1
fi

# Vérifier les prérequis
log "Vérification des prérequis..."

# Docker
if ! command -v docker &> /dev/null; then
    error "Docker n'est pas installé"
    exit 1
fi

# Docker Compose
if ! docker compose version &> /dev/null; then
    error "Docker Compose n'est pas installé"
    exit 1
fi

# Node.js pour le frontend
if ! command -v node &> /dev/null; then
    error "Node.js n'est pas installé"
    exit 1
fi

# Python pour le backend
if ! command -v python3 &> /dev/null; then
    error "Python 3 n'est pas installé"
    exit 1
fi

log "Tous les prérequis sont satisfaits ✅"

# Fonction pour nettoyer à l'arrêt
cleanup() {
    log "Arrêt des services..."
    docker compose down
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM

# Démarrer les services infrastructure (PostgreSQL, Redis, etc.)
log "Démarrage des services infrastructure..."
docker compose up -d postgres redis

# Attendre que PostgreSQL soit prêt
log "Attente de PostgreSQL..."
timeout=30
counter=0
until docker compose exec postgres pg_isready -U postgres &>/dev/null; do
    sleep 1
    counter=$((counter + 1))
    if [ $counter -ge $timeout ]; then
        error "PostgreSQL n'a pas démarré dans les temps"
        exit 1
    fi
done

log "PostgreSQL est prêt ✅"

# Installer les dépendances backend si nécessaire
if [ ! -d "backend/.venv" ]; then
    log "Installation des dépendances backend..."
    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# Initialiser la base de données
log "Initialisation de la base de données..."
cd backend
source .venv/bin/activate

# Vérifier si les tables existent déjà
if ! python -c "
import asyncpg
import asyncio
async def check():
    try:
        conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/coursegenai')
        result = await conn.fetchval('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = \'public\'')
        await conn.close()
        exit(0 if result > 0 else 1)
    except:
        exit(1)
asyncio.run(check())
" 2>/dev/null; then
    log "Création du schéma de base de données..."
    python -m src.cli.db init-schema || warn "Schéma déjà initialisé"
    
    log "Chargement des données de test..."
    python -m src.cli.db seed-test-data || warn "Données déjà chargées"
else
    log "Base de données déjà initialisée ✅"
fi

cd ..

# Démarrer le backend FastAPI
log "Démarrage du backend FastAPI..."
cd backend
source .venv/bin/activate
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Attendre que le backend soit prêt
log "Attente du backend..."
timeout=30
counter=0
until curl -s http://localhost:8000/health &>/dev/null; do
    sleep 1
    counter=$((counter + 1))
    if [ $counter -ge $timeout ]; then
        error "Backend n'a pas démarré dans les temps"
        exit 1
    fi
done

log "Backend FastAPI est prêt ✅"

# Installer les dépendances frontend si nécessaire
if [ ! -d "frontend/node_modules" ]; then
    log "Installation des dépendances frontend..."
    cd frontend
    npm install
    cd ..
fi

# Démarrer le frontend Next.js
log "Démarrage du frontend Next.js..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Attendre que le frontend soit prêt
log "Attente du frontend..."
timeout=30
counter=0
until curl -s http://localhost:3000 &>/dev/null; do
    sleep 1
    counter=$((counter + 1))
    if [ $counter -ge $timeout ]; then
        error "Frontend n'a pas démarré dans les temps"
        exit 1
    fi
done

log "Frontend Next.js est prêt ✅"

echo ""
echo "🎉 Plateforme CourseGen AI démarrée avec succès !"
echo "================================================"
echo ""
echo -e "${BLUE}🌐 Frontend (Next.js):${NC}     http://localhost:3000"
echo -e "${BLUE}🔧 Backend (FastAPI):${NC}      http://localhost:8000"
echo -e "${BLUE}📖 API Documentation:${NC}     http://localhost:8000/docs"
echo -e "${BLUE}🧪 Test API:${NC}              http://localhost:3000/test-api"
echo ""
echo -e "${YELLOW}💡 Pages disponibles:${NC}"
echo "   • Landing page:              http://localhost:3000"
echo "   • Dashboard:                 http://localhost:3000/dashboard"
echo "   • Création de cours:         http://localhost:3000/courses/create"
echo "   • Test API Integration:      http://localhost:3000/test-api"
echo ""
echo -e "${GREEN}✨ Fonctionnalités disponibles:${NC}"
echo "   • Génération de cours par IA"
echo "   • Interface utilisateur moderne"
echo "   • API REST complète"
echo "   • Base de données PostgreSQL"
echo "   • Tests d'intégration"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter tous les services"

# Garder le script en vie
wait