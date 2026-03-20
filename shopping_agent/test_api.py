"""
Sample API Test Script for Personal Shopping Agent.
Demonstrates all API endpoints with example requests and responses.
"""
import requests
import json
from typing import Dict


BASE_URL = "http://localhost:8000"


def print_response(title: str, response: requests.Response):
    """Pretty print API response."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(json.dumps(data, indent=2, default=str)[:2000])  # Truncate for readability
        if len(json.dumps(data)) > 2000:
            print("... (truncated)")
    except Exception:
        print(response.text)
    print()


def test_health():
    """Test health check endpoint."""
    response = requests.get(f"{BASE_URL}/health")
    print_response("1. Health Check", response)
    return response.ok


def test_chat():
    """Test chat endpoint with NLP."""
    queries = [
        "I want a phone under 15000 with good camera",
        "Show me Samsung laptops",
        "Find affordable Nike shoes",
        "Compare premium headphones"
    ]

    for query in queries:
        response = requests.post(f"{BASE_URL}/chat", json={
            "user_id": "U00001",
            "message": query,
            "top_n": 3
        })
        print_response(f"2. Chat: '{query}'", response)


def test_recommendations():
    """Test recommendations endpoint."""
    # Basic recommendations
    response = requests.get(f"{BASE_URL}/recommend", params={
        "user_id": "U00001",
        "top_n": 5
    })
    print_response("3. Basic Recommendations", response)

    # With filters
    response = requests.get(f"{BASE_URL}/recommend", params={
        "user_id": "U00001",
        "top_n": 5,
        "category": "Electronics",
        "max_price": 20000
    })
    print_response("4. Filtered Recommendations (Electronics under ₹20,000)", response)


def test_products():
    """Test products endpoint."""
    response = requests.get(f"{BASE_URL}/products", params={
        "category": "Electronics",
        "limit": 5
    })
    print_response("5. Browse Products (Electronics)", response)


def test_similar_products():
    """Test similar products endpoint."""
    response = requests.get(f"{BASE_URL}/products/P00001/similar", params={
        "top_n": 5
    })
    print_response("6. Similar Products to P00001", response)


def test_user_profile():
    """Test user profile endpoint."""
    response = requests.get(f"{BASE_URL}/user/U00001/profile")
    print_response("7. User Profile", response)


def test_record_interaction():
    """Test interaction recording."""
    response = requests.post(f"{BASE_URL}/interaction", json={
        "user_id": "U00001",
        "product_id": "P00001",
        "action": "view"
    })
    print_response("8. Record Interaction (view)", response)


def test_categories_and_brands():
    """Test metadata endpoints."""
    response = requests.get(f"{BASE_URL}/categories")
    print_response("9. Available Categories", response)

    response = requests.get(f"{BASE_URL}/brands", params={"category": "Electronics"})
    print_response("10. Brands in Electronics", response)


def run_all_tests():
    """Run all API tests."""
    print("\n" + "#"*60)
    print("# PERSONAL SHOPPING AGENT - API TEST SUITE")
    print("#"*60)

    # Check if server is running
    try:
        if not test_health():
            print("Server health check failed!")
            return
    except requests.exceptions.ConnectionError:
        print(f"\nERROR: Cannot connect to server at {BASE_URL}")
        print("Please start the server first: python main.py serve")
        return

    # Run all tests
    test_chat()
    test_recommendations()
    test_products()
    test_similar_products()
    test_user_profile()
    test_record_interaction()
    test_categories_and_brands()

    print("\n" + "#"*60)
    print("# ALL TESTS COMPLETED")
    print("#"*60)


if __name__ == "__main__":
    run_all_tests()
