# 🗄️ Guide de Configuration Base de Données

Configuration complète de PostgreSQL + Alembic pour l'API Course Generation Platform.

## ✅ Configuration Réussie

**Status :** Tous les composants fonctionnels  
**Base de données :** PostgreSQL 15 avec 7 tables  
**Migrations :** Alembic configuré et appliqué  
**Modèles :** 6 modèles SQLAlchemy chargés  

## 🏗️ Architecture

```
backend/
├── .env                    # Variables d'environnement
├── alembic.ini            # Configuration Alembic
├── alembic/               # Migrations
│   ├── env.py            # Configuration des modèles
│   └── versions/         # Fichiers de migration
├── src/
│   ├── models/           # Modèles SQLAlchemy
│   ├── database/         # Session et connexion
│   └── api/              # Endpoints API
└── test_*.py             # Scripts de test
```

## 📊 Tables Créées

1. **courses** - Cours principaux
2. **chapters** - Chapitres de cours
3. **subchapters** - Sous-chapitres
4. **quizzes** - Quiz et évaluations
5. **questions** - Questions des quiz
6. **flashcards** - Cartes mémo
7. **alembic_version** - Versioning des migrations

## 🚀 Utilisation

### Démarrage rapide
```bash
# 1. Activer l'environnement
cd backend
source .venv/bin/activate

# 2. Démarrer l'API
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 3. Tester
curl http://localhost:8000/health
```

### Tests de la base de données
```bash
# Test complet
python3 test_final.py

# Test base de données uniquement
python3 test_database.py

# Test API simple
python3 test_api_simple.py
```

## 🔧 Configuration des Services

### PostgreSQL (Docker)
```yaml
# docker-compose.yml
postgres:
  image: postgres:15-alpine
  environment:
    POSTGRES_DB: course_platform
    POSTGRES_USER: course_user
    POSTGRES_PASSWORD: course_password
  ports:
    - "5432:5432"
```

**Commandes utiles :**
```bash
# Démarrer PostgreSQL
docker compose up -d postgres

# Se connecter à la DB
docker exec -it creationcours-postgres-1 psql -U course_user -d course_platform

# Voir les tables
\dt

# Voir le contenu d'une table
SELECT * FROM courses;
```

### Configuration Alembic

**alembic.ini :**
- `prepend_sys_path = src` - Accès aux modèles
- Base de données via variable d'environnement

**env.py :**
- Import automatique de tous les modèles
- Configuration des métadonnées
- Support des variables d'environnement

### Variables d'environnement (.env)
```bash
DATABASE_URL=postgresql://course_user:course_password@localhost:5432/course_platform
ENVIRONMENT=development
DEBUG=true
```

## 🛠️ Commandes Alembic

```bash
# Vérifier la configuration
alembic check

# Créer une nouvelle migration
alembic revision --autogenerate -m "Description des changements"

# Appliquer les migrations
alembic upgrade head

# Voir l'historique
alembic history

# Revenir en arrière
alembic downgrade -1
```

## 📝 Workflow de Développement

### 1. Modifier un modèle
```python
# src/models/course.py
class CourseTable(Base):
    # Ajouter une nouvelle colonne
    new_field = Column(String(100), nullable=True)
```

### 2. Créer la migration
```bash
alembic revision --autogenerate -m "Add new_field to courses"
```

### 3. Vérifier la migration
```python
# alembic/versions/xxx_add_new_field.py
def upgrade():
    op.add_column('courses', sa.Column('new_field', sa.String(100), nullable=True))
```

### 4. Appliquer la migration
```bash
alembic upgrade head
```

## 🧪 Tests et Validation

### Script de test automatisé
```bash
python3 test_final.py
```
**Vérifie :**
- ✅ PostgreSQL actif
- ✅ Connexion DB
- ✅ Migrations Alembic
- ✅ Modèles chargés
- ✅ API fonctionnelle

### Tests manuels
```bash
# Test connexion directe
psql postgresql://course_user:course_password@localhost:5432/course_platform

# Test modèles Python
python3 -c "
from src.models.base import Base
print(f'Tables: {list(Base.metadata.tables.keys())}')"

# Test API
curl http://localhost:8000/health
```

## 🐛 Dépannage

### Problèmes courants

**1. "No module named 'psycopg2'"**
```bash
pip install psycopg2-binary
```

**2. "Connection refused"**
```bash
# Vérifier que PostgreSQL tourne
docker compose ps
docker compose up -d postgres
```

**3. "Import errors in env.py"**
```bash
# Vérifier le PYTHONPATH
cd backend
export PYTHONPATH="$PWD/src:$PYTHONPATH"
alembic check
```

**4. "Permission denied"**
```bash
# Vérifier les permissions Docker
sudo chown -R $USER:$USER postgres_data/
```

### Logs et diagnostic
```bash
# Logs PostgreSQL
docker compose logs postgres

# Test connexion
python3 -c "
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    result = conn.execute('SELECT version()')
    print(result.fetchone()[0])
"
```

## 🔐 Sécurité et Production

### Variables d'environnement de production
```bash
DATABASE_URL=postgresql://user:password@prod-host:5432/prod_db
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-strong-secret-key
```

### Backup et restauration
```bash
# Backup
docker exec creationcours-postgres-1 pg_dump -U course_user course_platform > backup.sql

# Restauration
docker exec -i creationcours-postgres-1 psql -U course_user course_platform < backup.sql
```

## 📈 Monitoring

### Métriques à surveiller
- Connexions actives
- Taille de la base
- Performance des requêtes
- Status des migrations

### Requêtes utiles
```sql
-- Connexions actives
SELECT count(*) FROM pg_stat_activity;

-- Taille des tables
SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables WHERE schemaname = 'public';

-- Version migration actuelle
SELECT version_num FROM alembic_version;
```

---

## 🎯 État Actuel : PRÊT POUR L'API

✅ **PostgreSQL configuré et actif**  
✅ **Alembic migrations appliquées**  
✅ **6 modèles de données créés**  
✅ **7 tables en base de données**  
✅ **Tests de connectivité réussis**  

**Prochaine étape :** Corriger les imports relatifs dans l'API pour activer tous les endpoints.