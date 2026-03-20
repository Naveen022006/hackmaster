"""
Diagnostic script for Personal Shopping Agent.
Run this to check if MongoDB and authentication are working properly.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_mongodb_connection():
    """Test MongoDB connection."""
    print("\n" + "=" * 60)
    print("STEP 1: Testing MongoDB Connection")
    print("=" * 60)

    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure

        uri = "mongodb://localhost:27017"
        print(f"Connecting to: {uri}")

        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')

        print("SUCCESS: MongoDB is running and accessible!")
        print(f"Server info: {client.server_info().get('version', 'unknown')}")

        # Check database
        db = client['shopping_agent']
        collections = db.list_collection_names()
        print(f"Database: shopping_agent")
        print(f"Collections: {collections if collections else 'No collections yet'}")

        client.close()
        return True

    except ConnectionFailure as e:
        print(f"\nFAILED: Cannot connect to MongoDB!")
        print(f"Error: {e}")
        print("\nTROUBLESHOOTING:")
        print("1. Open MongoDB Compass and check if connected to localhost:27017")
        print("2. If MongoDB isn't running, start it:")
        print("   - Windows: Open Services, find MongoDB, click Start")
        print("   - Or run: net start MongoDB")
        print("3. If MongoDB isn't installed, download from: https://www.mongodb.com/try/download/community")
        return False
    except ImportError:
        print("\nFAILED: pymongo not installed!")
        print("Run: pip install pymongo")
        return False


def test_database_service():
    """Test database service."""
    print("\n" + "=" * 60)
    print("STEP 2: Testing Database Service")
    print("=" * 60)

    try:
        from services.database import get_database

        db = get_database()
        print("SUCCESS: Database service initialized!")

        stats = db.get_statistics()
        print(f"\nDatabase Statistics:")
        print(f"  - Users: {stats['total_users']}")
        print(f"  - Products: {stats['total_products']}")
        print(f"  - Interactions: {stats['total_interactions']}")
        print(f"  - Admins: {stats['total_admins']}")

        return True

    except Exception as e:
        print(f"\nFAILED: Database service error!")
        print(f"Error: {e}")
        return False


def test_auth_service():
    """Test authentication service."""
    print("\n" + "=" * 60)
    print("STEP 3: Testing Authentication Service")
    print("=" * 60)

    try:
        from services.auth import get_auth_service, UserLogin

        auth = get_auth_service()
        print("SUCCESS: Auth service initialized!")

        # Create default admin if not exists
        print("\nCreating/checking default admin...")
        auth.create_default_admin()

        # Test admin login
        print("\nTesting admin login (admin@shopai.com / admin123456)...")
        try:
            token = auth.login_admin(UserLogin(
                email="admin@shopai.com",
                password="admin123456"
            ))
            print("SUCCESS: Admin login works!")
            print(f"Token generated: {token.access_token[:50]}...")
            return True
        except ValueError as e:
            print(f"Login failed: {e}")
            return False

    except Exception as e:
        print(f"\nFAILED: Auth service error!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_server():
    """Test if API server is running."""
    print("\n" + "=" * 60)
    print("STEP 4: Testing API Server")
    print("=" * 60)

    try:
        import requests

        response = requests.get("http://localhost:8000/health", timeout=5)
        data = response.json()

        if data.get('status') == 'healthy':
            print("SUCCESS: API server is running!")
            print(f"Components:")
            for key, value in data.get('components', {}).items():
                print(f"  - {key}: {value}")
            return True
        else:
            print("WARNING: API returned unhealthy status")
            return False

    except ImportError:
        print("INFO: requests module not installed, skipping API test")
        print("Run: pip install requests")
        return None
    except Exception as e:
        print(f"\nINFO: API server not running or not accessible")
        print(f"Start it with: python -m uvicorn api.main:app --reload")
        return None


def main():
    """Run all diagnostic tests."""
    print("\n" + "#" * 60)
    print(" Personal Shopping Agent - Diagnostic Tool")
    print("#" * 60)

    results = {}

    # Test 1: MongoDB Connection
    results['mongodb'] = test_mongodb_connection()

    if results['mongodb']:
        # Test 2: Database Service
        results['database'] = test_database_service()

        if results['database']:
            # Test 3: Auth Service
            results['auth'] = test_auth_service()

    # Test 4: API Server (optional)
    results['api'] = test_api_server()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for test, result in results.items():
        if result is None:
            status = "SKIPPED"
        elif result:
            status = "PASSED"
        else:
            status = "FAILED"
            all_passed = False
        print(f"  {test.upper()}: {status}")

    print("\n" + "=" * 60)
    if all_passed:
        print("All tests passed! Your system is ready.")
        print("\nTo use the application:")
        print("1. Start the API: python -m uvicorn api.main:app --reload")
        print("2. Open frontend/index.html in a browser")
        print("3. Login with: admin@shopai.com / admin123456")
    else:
        print("Some tests failed. Please fix the issues above.")
        if not results.get('mongodb'):
            print("\nMost likely issue: MongoDB is not running!")
            print("Start MongoDB and try again.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
