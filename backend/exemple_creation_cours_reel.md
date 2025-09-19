# 🏦 Utilisation de l'API Non Simulée (PostgreSQL)

## URL de Base
```
http://localhost:8085
```

## Créer un Nouveau Cours (Sauvegardé Définitivement)

```bash
curl -X POST "http://localhost:8085/api/v1/courses" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Votre Titre de Cours",
    "description": "Description du cours",
    "subject_domain": "Domaine d apprentissage",
    "target_audience": "Public cible",
    "difficulty_level": "Débutant|Intermédiaire|Avancé",
    "estimated_duration_hours": 10,
    "learning_objectives": [
      "Objectif 1",
      "Objectif 2"
    ]
  }'
```

## Lister Tous les Cours

```bash
curl "http://localhost:8085/api/v1/courses"
```

## Récupérer un Cours Spécifique

```bash
curl "http://localhost:8085/api/v1/courses/{COURSE_ID}"
```

## Supprimer un Cours

```bash
curl -X DELETE "http://localhost:8085/api/v1/courses/{COURSE_ID}"
```

## Interface Web

Ouvrez dans votre navigateur :
```
http://localhost:8085/docs
```

## Vérification de Santé

```bash
curl "http://localhost:8085/health"
```

## ✅ Avantages de l'API Non Simulée

- **Persistance** : Les cours survivent aux redémarrages
- **PostgreSQL** : Base de données professionnelle
- **Transactions** : Intégrité des données garantie
- **Scalabilité** : Prête pour la production
- **Relations** : Support des clés étrangères
- **Backup** : Données sauvegardables

## 🎯 Cours Actuellement Sauvegardés

1. Javascript (x2)
2. HTML/CSS pour Débutants  
3. Machine Learning avec Scikit-learn
4. Introduction à FastAPI

**Total : 5 cours en base PostgreSQL**