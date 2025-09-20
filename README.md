# CourseGen AI - Plateforme de Génération de Cours par IA

> 🚀 Une plateforme moderne de création de cours alimentée par l'intelligence artificielle, inspirée de Coursebox.ai

## ✨ Fonctionnalités

### 🤖 Génération IA Avancée
- Création de cours complets à partir de simples descriptions
- Génération de contenu pédagogique optimisé
- Adaptation automatique au niveau d'audience
- Support de multiples langues

### 🎨 Interface Moderne
- Design inspiré de Coursebox.ai
- Interface utilisateur intuitive avec Next.js et Tailwind CSS
- Animations fluides avec Framer Motion
- Responsive design pour tous les appareils

### 🔧 API Robuste
- API REST complète avec FastAPI
- Documentation automatique avec Swagger/OpenAPI
- Validation de données avec Pydantic
- Architecture microservices ready

### 📊 Fonctionnalités Avancées
- Dashboard analytics en temps réel
- Système de quality metrics
- Export multi-formats (SCORM, xAPI, PDF, HTML)
- Gestion des utilisateurs et permissions

## 🏗️ Architecture

### Stack Technique
- **Backend** : Python 3.11+, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend** : React 18, TypeScript, Vite, TailwindCSS
- **IA** : OpenAI GPT-4, Anthropic Claude
- **Cache** : Redis
- **Vector DB** : ChromaDB/Pinecone
- **Queue** : Celery

### Structure du Projet
```
├── backend/                 # API Python FastAPI
│   ├── src/
│   │   ├── models/         # Modèles de données
│   │   ├── services/       # Logique métier
│   │   ├── api/           # Endpoints API
│   │   └── cli/           # Commandes CLI
│   └── tests/             # Tests automatisés
├── frontend/               # Interface React
│   ├── src/
│   │   ├── components/    # Composants UI
│   │   ├── pages/         # Pages de l'application
│   │   └── services/      # Services API
└── docs/                  # Documentation
```

## 🛠️ Installation

### Prérequis
- Python 3.11+
- Node.js 18+
- Docker et docker compose
- Git

### Configuration Rapide

1. **Cloner le projet**
```bash
git clone <repository>
cd lms/creationcours
```

2. **Configurer l'environnement**
```bash
# Backend
cd backend
cp .env.example .env
# Éditer .env avec vos clés API

# Frontend  
cd ../frontend
cp .env.example .env
```

3. **Lancer les services avec Docker**
```bash
# Depuis la racine du projet
docker compose up -d postgres redis chromadb
```

4. **Installer les dépendances**
```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

5. **Démarrer l'application**
```bash
# Backend (terminal 1)
cd backend
python -m src.main

# Frontend (terminal 2)  
cd frontend
npm run dev
```

L'application sera accessible sur :
- Frontend : http://localhost:3000
- Backend API : http://localhost:8000
- Documentation API : http://localhost:8000/docs

## 📋 Phase de Développement Actuelle

### ✅ Phase 3.1 : Setup (Terminée)
- [x] Structure du projet créée
- [x] Configuration backend Python/FastAPI
- [x] Configuration frontend React/TypeScript  
- [x] Docker Compose configuré
- [x] Variables d'environnement

### 📋 Prochaines Étapes
- **Phase 3.2** : Tests (TDD) - Création des tests de contrat et d'intégration
- **Phase 3.3** : Implémentation - Modèles, services IA, endpoints API
- **Phase 3.4** : Intégration - Base de données, cache, middleware
- **Phase 3.5** : Polish - Tests unitaires, performance, documentation

## 🧪 Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## 📚 Documentation

- [Spécification complète](./specs/001-plateforme-de-cr/spec.md)
- [Plan d'implémentation](./specs/001-plateforme-de-cr/plan.md)
- [Tâches détaillées](./specs/001-plateforme-de-cr/tasks.md)
- [Guide de démarrage](./specs/001-plateforme-de-cr/quickstart.md)

## 🤝 Contribution

Voir le fichier [tasks.md](./specs/001-plateforme-de-cr/tasks.md) pour les tâches en cours et à venir.

## 📄 Licence

[À définir]