# 📝 Guide de Test - Création de Cours

## 🚀 Prérequis

1. **API démarrée** sur le port 8083
2. **Base de données PostgreSQL** connectée
3. **Outils** : `curl`, `jq` (optionnel pour formater JSON)

## 🔧 Démarrage de l'API

```bash
cd /home/laurent/mesprojets/lms/creationcours/backend
source .venv/bin/activate
python test_api_complete.py
```

## 🧪 Tests Manuels

### 1. Vérification de Santé

```bash
curl -s http://localhost:8083/health | jq .
```

**Résultat attendu :**
```json
{
  "status": "healthy",
  "service": "course-platform-api", 
  "database": "connected",
  "api_endpoints": "all_functional"
}
```

### 2. Création de Cours (T041)

```bash
curl -X POST "http://localhost:8083/api/v1/courses" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Formation React Avancé",
    "description": "Maîtriser React avec hooks et Context API",
    "subject_domain": "Développement Frontend",
    "target_audience": "Développeurs Web",
    "difficulty_level": "Avancé",
    "estimated_duration_hours": 30
  }' | jq .
```

**Résultat attendu :**
```json
{
  "message": "Course created successfully",
  "course_id": "uuid-generated",
  "status": "created"
}
```

### 3. Exemples de Cours à Tester

#### Cours Débutant
```json
{
  "title": "Introduction à Python",
  "description": "Premiers pas avec le langage Python",
  "subject_domain": "Programmation", 
  "target_audience": "Débutants",
  "difficulty_level": "Débutant",
  "estimated_duration_hours": 12
}
```

#### Cours Intermédiaire  
```json
{
  "title": "API REST avec FastAPI",
  "description": "Développer des APIs modernes et performantes",
  "subject_domain": "Backend Development",
  "target_audience": "Développeurs Backend",
  "difficulty_level": "Intermédiaire", 
  "estimated_duration_hours": 20
}
```

#### Cours Avancé
```json
{
  "title": "Architecture Microservices",
  "description": "Concevoir et déployer des microservices scalables",
  "subject_domain": "Architecture Logicielle",
  "target_audience": "Architectes Software",
  "difficulty_level": "Avancé",
  "estimated_duration_hours": 45
}
```

### 4. Tests de Validation

#### Données Invalides
```bash
# Titre manquant
curl -X POST "http://localhost:8083/api/v1/courses" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Test sans titre",
    "subject_domain": "Test",
    "target_audience": "Test",
    "difficulty_level": "Test",
    "estimated_duration_hours": 1
  }'
```

#### Durée négative
```bash
curl -X POST "http://localhost:8083/api/v1/courses" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test durée négative",
    "subject_domain": "Test",
    "target_audience": "Test", 
    "difficulty_level": "Test",
    "estimated_duration_hours": -5
  }'
```

### 5. Tests des Endpoints Liés

#### Statut de Génération
```bash
# Utiliser l'ID retourné par la création
curl -s "http://localhost:8083/api/v1/courses/{COURSE_ID}/generation-status" | jq .
```

#### Export de Cours
```bash
curl -X POST "http://localhost:8083/api/v1/courses/{COURSE_ID}/export?export_format=pdf" | jq .
```

#### Métriques de Qualité
```bash
curl -s "http://localhost:8083/api/v1/courses/{COURSE_ID}/quality-metrics" | jq .
```

## 🎯 Script Automatisé

Pour des tests complets automatisés :

```bash
python test_course_creation.py
```

## 📊 Résultats Attendus

### ✅ Succès
- **Status Code**: 201 Created
- **Réponse**: JSON avec `course_id`, `message`, `status`
- **ID généré**: UUID valide
- **Base de données**: Cours enregistré (dans l'implémentation complète)

### ❌ Échecs Possibles
- **400 Bad Request**: Données invalides
- **422 Unprocessable Entity**: Validation échouée
- **500 Internal Server Error**: Erreur serveur/base de données

## 🔍 Débogage

### Vérifier les Logs
```bash
# Voir les logs de l'API
tail -f /tmp/api_complete_running.txt
```

### Test de Connectivité
```bash
# Test simple de ping
curl -s http://localhost:8083/ | jq .
```

### Vérification Base de Données
```bash
# Test endpoint de diagnostic
curl -s http://localhost:8083/test/database | jq .
```

## 📋 Checklist de Test

- [ ] API démarrée et saine
- [ ] Base de données connectée  
- [ ] Création cours valide
- [ ] Validation des champs requis
- [ ] Gestion des erreurs
- [ ] ID UUID généré
- [ ] Endpoints liés fonctionnels
- [ ] Rate limiting (après plusieurs appels)
- [ ] Documentation OpenAPI accessible (`/docs`)

## 🎉 Tests Avancés

### Stress Test
```bash
# Créer 10 cours rapidement
for i in {1..10}; do
  curl -X POST "http://localhost:8083/api/v1/courses" \
    -H "Content-Type: application/json" \
    -d "{\"title\":\"Cours Test $i\",\"subject_domain\":\"Test\",\"target_audience\":\"Test\",\"difficulty_level\":\"Test\",\"estimated_duration_hours\":1}" &
done
wait
```

### Test Rate Limiting
```bash
# Tester les limites de taux (si activées)
for i in {1..15}; do
  curl -X POST "http://localhost:8083/api/v1/courses" \
    -H "Content-Type: application/json" \
    -d '{"title":"Rate Test","subject_domain":"Test","target_audience":"Test","difficulty_level":"Test","estimated_duration_hours":1}'
  echo "Request $i completed"
done
```

---

## 📞 Support

Si vous rencontrez des problèmes :
1. Vérifiez que PostgreSQL est démarré (`docker compose ps`)
2. Vérifiez les variables d'environnement (`.env`)
3. Consultez les logs de l'API
4. Vérifiez la connectivité réseau (`netstat -tlnp | grep 8083`)