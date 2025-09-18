#!/usr/bin/env python3
"""
Script de test simple pour l'API Course Generation Platform.
"""

import asyncio
import httpx
import json
import sys
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
API_V1_URL = f"{BASE_URL}/api/v1"

class APITester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results = []

    async def test_endpoint(self, method: str, endpoint: str, data: Dict[Any, Any] = None, expected_status: int = 200) -> Dict[str, Any]:
        """Test un endpoint spécifique"""
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = await self.client.get(url)
            elif method.upper() == "POST":
                response = await self.client.post(url, json=data)
            elif method.upper() == "PUT":
                response = await self.client.put(url, json=data)
            elif method.upper() == "DELETE":
                response = await self.client.delete(url)
            else:
                raise ValueError(f"Méthode HTTP non supportée: {method}")

            result = {
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "success": response.status_code == expected_status,
                "response_time": response.elapsed.total_seconds(),
                "error": None
            }

            if response.status_code == expected_status:
                try:
                    result["data"] = response.json()
                except:
                    result["data"] = response.text
            else:
                result["error"] = f"Code de statut attendu: {expected_status}, reçu: {response.status_code}"
                try:
                    result["error_detail"] = response.json()
                except:
                    result["error_detail"] = response.text

        except Exception as e:
            result = {
                "endpoint": endpoint,
                "method": method,
                "status_code": None,
                "success": False,
                "response_time": None,
                "error": str(e)
            }

        self.results.append(result)
        return result

    async def run_basic_tests(self):
        """Lance les tests de base"""
        print("🚀 Démarrage des tests API...")
        print("=" * 60)

        # Test 1: Health check
        print("1. Test Health Check...")
        result = await self.test_endpoint("GET", "/health")
        print(f"   ✅ Status: {result['status_code']}" if result['success'] else f"   ❌ Erreur: {result['error']}")

        # Test 2: Root endpoint
        print("2. Test Root Endpoint...")
        result = await self.test_endpoint("GET", "/")
        print(f"   ✅ Status: {result['status_code']}" if result['success'] else f"   ❌ Erreur: {result['error']}")

        # Test 3: API Info
        print("3. Test API Info...")
        result = await self.test_endpoint("GET", "/api/v1/info")
        print(f"   ✅ Status: {result['status_code']}" if result['success'] else f"   ❌ Erreur: {result['error']}")

        # Test 4: API Health
        print("4. Test API v1 Health...")
        result = await self.test_endpoint("GET", "/api/v1/health")
        print(f"   ✅ Status: {result['status_code']}" if result['success'] else f"   ❌ Erreur: {result['error']}")

        # Test 5: Documentation
        print("5. Test Documentation...")
        result = await self.test_endpoint("GET", "/docs", expected_status=200)
        print(f"   ✅ Status: {result['status_code']}" if result['success'] else f"   ❌ Erreur: {result['error']}")

    async def test_courses_endpoints(self):
        """Test les endpoints de cours (sans base de données)"""
        print("\n📚 Test des endpoints de cours...")
        print("=" * 60)

        # Test GET /courses (devrait échouer sans DB, mais tester la route)
        print("1. Test GET /courses...")
        result = await self.test_endpoint("GET", "/api/v1/courses", expected_status=500)  # Attendu: erreur DB
        print(f"   ⚠️  Status: {result['status_code']} (Erreur DB attendue)")

    def print_summary(self):
        """Affiche un résumé des tests"""
        print("\n📊 RÉSUMÉ DES TESTS")
        print("=" * 60)
        
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r['success']])
        
        print(f"Total des tests: {total_tests}")
        print(f"Tests réussis: {successful_tests}")
        print(f"Tests échoués: {total_tests - successful_tests}")
        print(f"Taux de réussite: {(successful_tests/total_tests)*100:.1f}%" if total_tests > 0 else "N/A")

        # Détails des échecs
        failed_tests = [r for r in self.results if not r['success']]
        if failed_tests:
            print("\n❌ TESTS ÉCHOUÉS:")
            for test in failed_tests:
                print(f"   - {test['method']} {test['endpoint']}: {test['error']}")

    async def close(self):
        """Ferme le client HTTP"""
        await self.client.aclose()

async def main():
    """Fonction principale"""
    print("🧪 TESTEUR API - Course Generation Platform")
    print("=" * 60)
    print("Ce script teste les endpoints de base de l'API.")
    print("Assurez-vous que l'API tourne sur http://localhost:8000")
    print()

    tester = APITester()
    
    try:
        # Tests de base
        await tester.run_basic_tests()
        
        # Tests des endpoints métier (optionnel)
        await tester.test_courses_endpoints()
        
        # Résumé
        tester.print_summary()
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrompus par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
    finally:
        await tester.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        sys.exit(1)