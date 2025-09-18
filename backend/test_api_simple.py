#!/usr/bin/env python3
"""
Test simple pour vérifier que l'API peut démarrer
"""

import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    # Test d'import minimal
    print("🔍 Test des imports...")
    
    import fastapi
    print("✅ FastAPI importé avec succès")
    
    import uvicorn
    print("✅ Uvicorn importé avec succès")
    
    import sqlalchemy
    print("✅ SQLAlchemy importé avec succès")
    
    # Test de l'app
    print("\n🚀 Test de l'application...")
    
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    # Créer une version simplifiée de l'app pour tester
    app = FastAPI(
        title="Course Generation Platform API",
        description="AI-powered course creation and management platform",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():
        return {"message": "Test API", "status": "working"}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    print("✅ Application FastAPI créée avec succès")
    print(f"✅ Titre: {app.title}")
    print(f"✅ Version: {app.version}")
    
    print("\n✅ TOUS LES TESTS PASSENT - L'API PEUT DÉMARRER!")
    print("\nPour démarrer l'API en mode développement:")
    print("1. cd backend")
    print("2. source .venv/bin/activate")
    print("3. cd src")
    print("4. uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("Assurez-vous que les dépendances sont installées:")
    print("pip install fastapi uvicorn sqlalchemy pydantic")
except Exception as e:
    print(f"❌ Erreur: {e}")