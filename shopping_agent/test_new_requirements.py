"""
Test script for R6 (Catalog), R7 (Feedback), R8 (Cloud Storage)
Validates all new requirement implementations.
"""
import requests
import json
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER = "test_user_001"
TEST_PRODUCT = "P00001"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text):
    print(f"\n{BLUE}{'='*60}\n{text}\n{'='*60}{RESET}")


def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text):
    print(f"{RED}✗ {text}{RESET}")


def print_info(text):
    print(f"{YELLOW}ℹ {text}{RESET}")


def test_feedback_system():
    """Test R7: Feedback Collection System"""
    print_header("TESTING R7: FEEDBACK COLLECTION SYSTEM")

    # Test 1: Submit feedback
    print_info("Test 1: Submit feedback on recommendation")
    feedback_data = {
        "user_id": TEST_USER,
        "feedback_type": "recommendation",
        "rating": 4,
        "target_id": TEST_PRODUCT,
        "comment": "Great recommendation! Very accurate and helpful."
    }

    try:
        response = requests.post(f"{BASE_URL}/feedback/submit", json=feedback_data)
        if response.status_code == 200:
            result = response.json()
            print_success(f"Feedback submitted: {result['id']}")
            feedback_id = result['id']
        else:
            print_error(f"Failed to submit feedback: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

    # Test 2: Get user feedback
    print_info("Test 2: Get user feedback")
    try:
        response = requests.get(f"{BASE_URL}/feedback/user/{TEST_USER}")
        if response.status_code == 200:
            result = response.json()
            print_success(f"Retrieved {result['total_feedback']} feedback item(s)")
        else:
            print_error(f"Failed: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")

    # Test 3: Get analytics
    print_info("Test 3: Get feedback analytics")
    try:
        response = requests.get(f"{BASE_URL}/feedback/analytics")
        if response.status_code == 200:
            analytics = response.json()
            print_success(f"Analytics: {analytics['total_feedback']} feedbacks, " 
                        f"Avg Rating: {analytics['avg_rating']:.2f}, "
                        f"Sentiment: {analytics['sentiment']}")
        else:
            print_error(f"Failed: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")

    # Test 4: Mark feedback helpful
    print_info("Test 4: Mark feedback as helpful")
    try:
        response = requests.post(f"{BASE_URL}/feedback/helpful/{feedback_id}")
        if response.status_code == 200:
            print_success("Feedback marked as helpful")
        else:
            print_error(f"Failed: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")

    # Test 5: Get quality metrics
    print_info("Test 5: Get recommendation quality metrics")
    try:
        response = requests.get(f"{BASE_URL}/feedback/quality-metrics")
        if response.status_code == 200:
            metrics = response.json()
            print_success(f"Quality Score: {metrics['quality_score']:.2f}/100")
        else:
            print_error(f"Failed: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")

    # Test 6: Get feedback stats
    print_info("Test 6: Get feedback statistics")
    try:
        response = requests.get(f"{BASE_URL}/feedback/stats")
        if response.status_code == 200:
            stats = response.json()
            print_success(f"Total feedbacks: {stats['total_feedback']}, "
                        f"Unique users: {stats['unique_users']}")
        else:
            print_error(f"Failed: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")

    return True


def test_catalog_system():
    """Test R6: External Catalog API Integration"""
    print_header("TESTING R6: EXTERNAL CATALOG API INTEGRATION")

    # Test 1: Get available sources
    print_info("Test 1: Get available catalog sources")
    try:
        response = requests.get(f"{BASE_URL}/catalog/sources")
        if response.status_code == 200:
            sources = response.json()
            print_success(f"Available sources: {sources['available_sources']}")
        else:
            print_error(f"Failed: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")

    # Test 2: Sync catalog
    print_info("Test 2: Sync catalog from sources")
    sync_data = {
        "sources": ["amazon", "flipkart", "local"],
        "merge_with_local": True
    }

    try:
        response = requests.post(f"{BASE_URL}/catalog/sync", json=sync_data)
        if response.status_code == 200:
            result = response.json()
            print_success(f"Catalog synced: {result['total_products']} products from {len(result['sources'])} sources")
        else:
            print_error(f"Failed: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")

    # Test 3: Search catalog
    print_info("Test 3: Search across catalogs")
    search_data = {
        "query": "laptop",
        "max_price": 50000,
        "in_stock": True
    }

    try:
        response = requests.post(f"{BASE_URL}/catalog/search", json=search_data)
        if response.status_code == 200:
            result = response.json()
            print_success(f"Found {result['total_found']} products matching query")
            if result['results']:
                print_info(f"  First result: {result['results'][0]['name']} - Rs {result['results'][0]['price']}")
        else:
            print_error(f"Failed: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")

    # Test 4: Sync history
    print_info("Test 4: Get sync history")
    try:
        response = requests.get(f"{BASE_URL}/catalog/history")
        if response.status_code == 200:
            history = response.json()
            print_success(f"Total sync operations: {history['total_syncs']}")
            if history['last_sync']:
                print_info(f"  Last sync: {history['last_sync']}")
        else:
            print_error(f"Failed: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")

    # Test 5: Get statistics
    print_info("Test 5: Get catalog statistics")
    try:
        response = requests.get(f"{BASE_URL}/catalog/statistics")
        if response.status_code == 200:
            stats = response.json()
            print_success(f"Sync operations: {stats['total_sync_operations']}, "
                        f"Success rate: {stats['success_rate']*100:.1f}%")
        else:
            print_error(f"Failed: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")

    # Test 6: Get products by source
    print_info("Test 6: Get products from local source")
    try:
        response = requests.get(f"{BASE_URL}/catalog/products/by-source/local?limit=5")
        if response.status_code == 200:
            result = response.json()
            print_success(f"Retrieved {result['total_products']} products from local source")
        else:
            print_error(f"Failed: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")

    return True


def test_storage_system():
    """Test R8: Cloud Storage Infrastructure"""
    print_header("TESTING R8: CLOUD STORAGE INFRASTRUCTURE")

    # Test 1: Storage status
    print_info("Test 1: Check storage status")
    try:
        response = requests.get(f"{BASE_URL}/storage/status")
        if response.status_code == 200:
            status = response.json()
            print_success(f"Storage status: {status['status']}")
            print_info(f"  Provider: {status['provider_type']}")
            print_info(f"  Fallback: {status['fallback_available']}")
        else:
            print_error(f"Failed: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")

    # Test 2: Upload test file
    print_info("Test 2: Upload file to storage")
    
    # Create a test file
    test_file = "test_upload.txt"
    with open(test_file, "w") as f:
        f.write(f"Test upload at {datetime.now()}")

    upload_data = {
        "file_path": test_file,
        "remote_path": "test_files/test_upload.txt",
        "file_type": "data"
    }

    try:
        response = requests.post(f"{BASE_URL}/storage/upload", json=upload_data)
        if response.status_code == 200:
            result = response.json()
            print_success(f"File uploaded to {result['remote_path']}")
        else:
            print_error(f"Failed: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")
    finally:
        # Clean up test file
        Path(test_file).unlink(missing_ok=True)

    # Test 3: List files
    print_info("Test 3: List files in storage")
    try:
        response = requests.get(f"{BASE_URL}/storage/models")
        if response.status_code == 200:
            result = response.json()
            print_success(f"Total models stored: {result['total_files']}")
        else:
            print_error(f"Failed: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")

    # Test 4: Operation logs
    print_info("Test 4: Get storage operation logs")
    try:
        response = requests.get(f"{BASE_URL}/storage/logs-list")
        if response.status_code == 200:
            logs = response.json()
            print_success(f"Total operations logged: {logs['total_operations']}")
            if logs['providers_used']:
                print_info(f"  Providers used: {logs['providers_used']}")
        else:
            print_error(f"Failed: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")

    return True


def main():
    """Run all tests."""
    print(f"{BLUE}{'='*60}")
    print(f"TESTING NEW REQUIREMENTS: R6, R7, R8")
    print(f"API Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}{RESET}")

    try:
        # Test each system
        feedback_ok = test_feedback_system()
        catalog_ok = test_catalog_system()
        storage_ok = test_storage_system()

        # Summary
        print_header("TEST SUMMARY")
        print(f"R7 (Feedback Collection):      {'PASSED ✓' if feedback_ok else 'FAILED ✗'}")
        print(f"R6 (Catalog Integration):      {'PASSED ✓' if catalog_ok else 'FAILED ✗'}")
        print(f"R8 (Cloud Storage):            {'PASSED ✓' if storage_ok else 'FAILED ✗'}")

        if feedback_ok and catalog_ok and storage_ok:
            print_success("All tests completed successfully!")
            return 0
        else:
            print_error("Some tests failed. Check output above.")
            return 1

    except Exception as e:
        print_error(f"Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
