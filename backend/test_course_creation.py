#!/usr/bin/env python3
"""
Script de test pour la création de cours
Course Platform API - Test de création et validation
"""

import requests
import json
import time
from datetime import datetime

API_BASE_URL = "http://localhost:8083"

def test_api_health():
    """Test de santé de l'API"""
    print("🔍 Test de santé de l'API...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API Status: {data.get('status')}")
            print(f"   ✅ Database: {data.get('database')}")
            return True
        else:
            print(f"   ❌ API Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")
        return False

def create_course(course_data):
    """Créer un nouveau cours"""
    print(f"\n📝 Création du cours: {course_data['title']}")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/courses",
            headers={"Content-Type": "application/json"},
            json=course_data
        )
        
        if response.status_code == 201:
            data = response.json()
            course_id = data.get('course_id')
            print(f"   ✅ Cours créé avec succès")
            print(f"   📋 ID: {course_id}")
            print(f"   📋 Message: {data.get('message')}")
            return course_id
        else:
            print(f"   ❌ Échec de création: {response.status_code}")
            print(f"   📋 Réponse: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return None

def get_course_list():
    """Récupérer la liste des cours"""
    print(f"\n📋 Récupération de la liste des cours...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/courses")
        if response.status_code == 200:
            data = response.json()
            courses = data.get('courses', [])
            pagination = data.get('pagination', {})
            
            print(f"   ✅ {len(courses)} cours trouvés")
            print(f"   📊 Total: {pagination.get('total', 0)}")
            
            for i, course in enumerate(courses, 1):
                print(f"   {i}. {course.get('title')} (ID: {course.get('id')})")
            
            return courses
        else:
            print(f"   ❌ Échec de récupération: {response.status_code}")
            return []
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return []

def get_course_details(course_id):
    """Récupérer les détails d'un cours"""
    print(f"\n🔍 Récupération des détails du cours {course_id}")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/courses/{course_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Cours trouvé: {data.get('title')}")
            print(f"   📋 Description: {data.get('description')}")
            print(f"   📋 Status: {data.get('status')}")
            return data
        elif response.status_code == 404:
            print(f"   ⚠️ Cours non trouvé (404) - Normal pour un cours simulé")
            return None
        else:
            print(f"   ❌ Échec: {response.status_code}")
            return None
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return None

def test_generation_status(course_id):
    """Tester le statut de génération"""
    print(f"\n⚡ Test du statut de génération pour {course_id}")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/courses/{course_id}/generation-status")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {data.get('status')}")
            print(f"   📊 Progrès: {data.get('progress')}%")
            print(f"   📋 Chapitres: {data.get('chapters_generated')}/{data.get('total_chapters')}")
            return data
        else:
            print(f"   ❌ Échec: {response.status_code}")
            return None
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return None

def main():
    """Fonction principale de test"""
    print("🎯 TEST COMPLET DE CRÉATION DE COURS")
    print("=" * 50)
    
    # Test de santé
    if not test_api_health():
        print("❌ L'API n'est pas disponible. Arrêt des tests.")
        return
    
    # Exemples de cours à créer
    courses_to_test = [
        {
            "title": "Python pour Débutants",
            "description": "Introduction complète au langage Python",
            "subject_domain": "Programmation",
            "target_audience": "Débutants",
            "difficulty_level": "Débutant",
            "estimated_duration_hours": 15
        },
        {
            "title": "Machine Learning avec Python",
            "description": "Cours avancé sur l'apprentissage automatique",
            "subject_domain": "Intelligence Artificielle",
            "target_audience": "Data Scientists",
            "difficulty_level": "Avancé",
            "estimated_duration_hours": 40
        },
        {
            "title": "Développement Web avec FastAPI",
            "description": "Créer des APIs modernes avec FastAPI",
            "subject_domain": "Développement Web",
            "target_audience": "Développeurs",
            "difficulty_level": "Intermédiaire",
            "estimated_duration_hours": 25
        }
    ]
    
    created_courses = []
    
    # Créer les cours
    for course_data in courses_to_test:
        course_id = create_course(course_data)
        if course_id:
            created_courses.append({
                "id": course_id,
                "title": course_data["title"]
            })
        time.sleep(1)  # Délai entre les créations
    
    # Lister tous les cours
    get_course_list()
    
    # Tester les détails et statut de génération pour chaque cours créé
    for course in created_courses:
        get_course_details(course["id"])
        test_generation_status(course["id"])
        time.sleep(0.5)
    
    # Résumé
    print(f"\n🎉 RÉSUMÉ DES TESTS")
    print("=" * 30)
    print(f"✅ Cours créés avec succès: {len(created_courses)}")
    print(f"📋 Total de cours testés: {len(courses_to_test)}")
    
    if created_courses:
        print(f"\n📝 IDs des cours créés:")
        for course in created_courses:
            print(f"   - {course['title']}: {course['id']}")

if __name__ == "__main__":
    main()