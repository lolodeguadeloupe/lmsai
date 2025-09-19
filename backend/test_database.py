#!/usr/bin/env python3
"""
Test de connectivité à la base de données PostgreSQL
"""

import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_database_connection():
    """Test la connexion à la base de données"""
    print("🔍 Test de connexion à la base de données...")
    
    try:
        from sqlalchemy import create_engine, text
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL non définie")
            return False
            
        print(f"🔗 Connexion à: {database_url}")
        
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connexion réussie!")
            print(f"✅ Version PostgreSQL: {version}")
            
            # Test tables exist
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"✅ Tables trouvées: {', '.join(tables)}")
            
            # Test we can query tables
            result = conn.execute(text("SELECT COUNT(*) FROM courses"))
            course_count = result.fetchone()[0]
            print(f"✅ Nombre de cours: {course_count}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def test_sqlalchemy_models():
    """Test que les modèles SQLAlchemy fonctionnent"""
    print("\n🔍 Test des modèles SQLAlchemy...")
    
    try:
        from models.base import Base
        from models.course import CourseTable
        from database.session import get_db_session
        
        # Test session creation
        with get_db_session() as session:
            print("✅ Session SQLAlchemy créée")
            
            # Test query
            courses = session.query(CourseTable).all()
            print(f"✅ Requête courses réussie: {len(courses)} cours trouvés")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur modèles: {e}")
        return False

def test_api_with_database():
    """Test que l'API peut se connecter à la base"""
    print("\n🔍 Test API avec base de données...")
    
    try:
        import asyncio
        import httpx
        import subprocess
        import time
        
        # Start API in background
        print("🚀 Démarrage de l'API...")
        
        # Note: En production, utilisez un gestionnaire de processus approprié
        api_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app", 
            "--host", "0.0.0.0", "--port", "8001"  # Port différent pour les tests
        ], cwd="src", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for API to start
        time.sleep(3)
        
        try:
            # Test API endpoints
            async def test_endpoints():
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Test health
                    response = await client.get("http://localhost:8001/health")
                    if response.status_code == 200:
                        print("✅ Endpoint /health fonctionne")
                    else:
                        print(f"⚠️ /health retourne {response.status_code}")
                    
                    # Test courses list (should work now with DB)
                    response = await client.get("http://localhost:8001/api/v1/courses")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"✅ Endpoint /api/v1/courses fonctionne: {data.get('total', 0)} cours")
                        return True
                    else:
                        print(f"❌ /api/v1/courses retourne {response.status_code}: {response.text}")
                        return False
            
            # Run async test
            result = asyncio.run(test_endpoints())
            
        finally:
            # Stop API
            api_process.terminate()
            api_process.wait()
            
        return result
        
    except Exception as e:
        print(f"❌ Erreur test API: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 TESTS DE BASE DE DONNÉES")
    print("=" * 60)
    
    success_count = 0
    total_tests = 3
    
    # Test 1: Database connection
    if test_database_connection():
        success_count += 1
    
    # Test 2: SQLAlchemy models
    if test_sqlalchemy_models():
        success_count += 1
    
    # Test 3: API with database
    if test_api_with_database():
        success_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 RÉSUMÉ: {success_count}/{total_tests} tests réussis")
    
    if success_count == total_tests:
        print("🎉 TOUS LES TESTS PASSENT!")
        print("\n✅ La base de données est prête pour l'API")
        print("✅ Pour démarrer l'API avec la DB:")
        print("   cd backend && source .venv/bin/activate")
        print("   cd src && uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        
    else:
        print("⚠️ Certains tests ont échoué")
        print("Vérifiez la configuration et les logs d'erreur")

if __name__ == "__main__":
    main()