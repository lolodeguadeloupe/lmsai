# Connexions Base de Données

## Paramètres de connexion PostgreSQL

**Host:** localhost  
**Port:** 5432  
**Database:** course_platform  
**Username:** course_user  
**Password:** course_password  

## DBeaver
1. Télécharger: https://dbeaver.io/download/
2. Nouvelle connexion PostgreSQL
3. Utiliser les paramètres ci-dessus
4. Tester la connexion

## pgAdmin Web
- URL: http://localhost:5050
- Email: admin@example.com
- Password: admin123

## CLI psql
```bash
# Se connecter à PostgreSQL
docker exec -it course_postgres psql -U course_user -d course_platform

# Lister les tables
\dt

# Voir la structure d'une table
\d courses

# Voir les données
SELECT * FROM courses LIMIT 5;
```

## Tables créées
- courses (6 colonnes)
- chapters (10 colonnes)  
- subchapters (9 colonnes)
- quizzes (9 colonnes)
- questions (12 colonnes)
- flashcards (10 colonnes)