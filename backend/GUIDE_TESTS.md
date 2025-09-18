# 🧪 Guide de Test - API Course Generation Platform

Ce guide vous explique comment tester l'API de la plateforme de création de cours IA.

## 📋 Prérequis

### Dépendances Python
```bash
cd backend
source .venv/bin/activate
pip install fastapi uvicorn sqlalchemy pydantic httpx
```

### Services externes (optionnels pour tests de base)
- PostgreSQL (pour tests avec base de données)
- Redis (pour cache et sessions)
- Celery (pour tâches de fond)

## 🚀 Démarrage de l'API

### 1. Démarrage simple (sans base de données)
```bash
cd backend
source .venv/bin/activate
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Vérification du démarrage
L'API sera accessible sur : http://localhost:8000

Points de vérification :
- ✅ **Documentation** : http://localhost:8000/docs
- ✅ **Health Check** : http://localhost:8000/health
- ✅ **API Info** : http://localhost:8000/api/v1/info

## 🧪 Types de Tests

### 1. Tests de Base (Sans DB)

#### A. Test des imports et démarrage
```bash
cd backend
source .venv/bin/activate
python3 test_api_simple.py
```

#### B. Test avec curl
```bash
# Health check
curl -X GET "http://localhost:8000/health"

# Root endpoint
curl -X GET "http://localhost:8000/"

# API v1 info
curl -X GET "http://localhost:8000/api/v1/info"

# Documentation (renvoie HTML)
curl -X GET "http://localhost:8000/docs"
```

#### C. Réponses attendues
```json
// GET /health
{
  "status": "healthy",
  "service": "course-platform-api"
}

// GET /
{
  "message": "Course Generation Platform API",
  "version": "1.0.0",
  "documentation": "/docs",
  "health": "/health",
  "api_v1": "/api/v1"
}

// GET /api/v1/info
{
  "name": "Course Generation Platform API",
  "version": "1.0.0",
  "description": "AI-powered course creation and management platform",
  "endpoints": {
    "courses": "Course management (CRUD operations)",
    "generation": "Course generation status and control",
    "export": "Course export in various formats",
    "quality": "Quality metrics and analysis",
    "chapters": "Chapter content access",
    "quizzes": "Quiz content and attempt handling"
  },
  "documentation": "/docs"
}
```

### 2. Tests des Endpoints (Retournent erreur sans DB)

#### A. Test endpoints courses
```bash
# Liste des cours (erreur DB attendue)
curl -X GET "http://localhost:8000/api/v1/courses"

# Création de cours (erreur DB attendue)
curl -X POST "http://localhost:8000/api/v1/courses" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Course",
    "description": "A test course description",
    "subject_domain": "TECHNOLOGY",
    "target_audience": "PROFESSIONALS",
    "difficulty_level": "INTERMEDIATE",
    "estimated_duration_hours": 10,
    "learning_objectives": ["Learn FastAPI", "Understand APIs"]
  }'
```

#### B. Réponses d'erreur attendues (sans DB)
```json
{
  "detail": "Failed to list courses"  // ou erreur de connexion DB
}
```

### 3. Tests avec Script Python

#### Script de test automatisé
```bash
cd backend
source .venv/bin/activate
python3 ../test_api.py
```

## 🗄️ Tests avec Base de Données

### 1. Configuration PostgreSQL
```bash
# Démarrer PostgreSQL avec Docker
docker compose up -d postgres

# Ou utiliser le docker-compose global du projet
cd ../../  # retour à la racine du projet
docker compose up -d
```

### 2. Variables d'environnement
Créer `.env` dans `backend/` :
```bash
# Database
DATABASE_URL=postgresql://courseplatform:courseplatform@localhost:5432/courseplatform_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# API Keys (optionnel pour tests)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

### 3. Migration de la base
```bash
cd backend
source .venv/bin/activate
# TODO: Implémenter migrations Alembic
# alembic upgrade head
```

### 4. Tests avec données
Une fois la DB configurée, les endpoints retourneront des données réelles :

```bash
# Liste des cours (vide au début)
curl -X GET "http://localhost:8000/api/v1/courses"
# Retourne: {"courses": [], "total": 0, "page": 1, "limit": 10}

# Création de cours (fonctionne)
curl -X POST "http://localhost:8000/api/v1/courses" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Introduction à Python",
    "description": "Cours complet pour apprendre Python",
    "subject_domain": "TECHNOLOGY",
    "target_audience": "BEGINNERS",
    "difficulty_level": "BEGINNER",
    "estimated_duration_hours": 15,
    "learning_objectives": [
      "Maîtriser la syntaxe Python",
      "Comprendre la programmation orientée objet",
      "Créer des applications simples"
    ]
  }'
```

## 🔧 Tests de Performance

### 1. Tests de charge avec Apache Bench
```bash
# Test de charge sur health check
ab -n 100 -c 10 http://localhost:8000/health

# Test sur l'endpoint root
ab -n 100 -c 10 http://localhost:8000/
```

### 2. Tests avec hey (alternative moderne)
```bash
# Installation de hey
go install github.com/rakyll/hey@latest

# Test de performance
hey -n 100 -c 10 http://localhost:8000/health
```

## 🐛 Débuggage

### 1. Logs de l'API
L'API affiche les logs dans la console lors du démarrage avec `--reload`.

### 2. Vérification des erreurs communes

#### Erreur de port occupé
```bash
# Vérifier si le port 8000 est utilisé
lsof -i :8000

# Tuer le processus si nécessaire
kill -9 <PID>
```

#### Erreurs d'import
```bash
# Vérifier l'environnement virtuel
which python3
pip list | grep fastapi

# Réinstaller si nécessaire
pip install --force-reinstall fastapi uvicorn
```

#### Erreurs de base de données
```bash
# Vérifier que PostgreSQL fonctionne
docker compose ps
docker compose logs postgres

# Tester la connexion
psql postgresql://courseplatform:courseplatform@localhost:5432/courseplatform_dev
```

## 📊 Tests Automatisés

### 1. Tests unitaires (à implémenter)
```bash
cd backend
source .venv/bin/activate
pytest tests/
```

### 2. Tests d'intégration (à implémenter)
```bash
# Tests avec base de données de test
pytest tests/integration/
```

### 3. Tests de contrat (existants)
```bash
# Tests TDD existants
python3 run_tests_tdd_verification.py
```

## 🌐 Tests en Production

### 1. Variables d'environnement production
- `DEBUG=False`
- `DATABASE_URL` avec vraie DB
- Clés API valides
- Domaines CORS restreints

### 2. Tests de santé
```bash
# Health check
curl -X GET "https://api.courseplatform.com/health"

# Monitoring continu
while true; do
  curl -s https://api.courseplatform.com/health | jq '.status'
  sleep 30
done
```

## 📝 Checklist de Tests

### ✅ Tests de Base
- [ ] API démarre sans erreur
- [ ] Health check répond 200
- [ ] Documentation accessible
- [ ] Endpoints retournent les bonnes structures JSON
- [ ] Gestion d'erreurs appropriée

### ✅ Tests Fonctionnels
- [ ] CRUD courses complet
- [ ] Génération de contenu
- [ ] Export de cours
- [ ] Métriques qualité
- [ ] Accès chapitres et quiz

### ✅ Tests Non-Fonctionnels
- [ ] Performance sous charge
- [ ] Sécurité (CORS, validation)
- [ ] Logging approprié
- [ ] Gestion des timeouts

---

## 🚨 Problèmes Connus

1. **Base de données requise** : La plupart des endpoints nécessitent une connexion DB
2. **Services externes** : AI et vector DB optionnels pour tests de base
3. **Migrations** : Système de migrations à finaliser
4. **Authentication** : Non implémentée (Phase 3.6)

## 📞 Support

Pour des problèmes de test, vérifiez :
1. Logs de l'API
2. Status des services Docker
3. Variables d'environnement
4. Permissions et ports réseau