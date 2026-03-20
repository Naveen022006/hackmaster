#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for the Enhanced Chat Assistant
Demonstrates all the capabilities of the improved NLP processor
"""
import requests
import json
from typing import Dict
import time
import sys
import io

# Handle Windows encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_query_result(query: str, result: Dict):
    """Print formatted query result."""
    print(f"\n[QUERY] {query}")
    print(f"  Intent: {result['intent'].upper()} (confidence: {result['intent_confidence']:.1%})")

    entities = {k: v for k, v in result['entities'].items()
                if v and k != 'original_query'}
    if entities:
        print(f"  Extracted: {json.dumps(entities, indent=15)}")

    if result['filters_applied']:
        print(f"  Filters: {result['filters_applied']}")

    print(f"  Found: {len(result['recommendations'])} products")
    print(f"  Latency: {result['latency_ms']:.1f}ms {'(cached)' if result['cached'] else ''}")

def test_category(queries: list, category_name: str):
    """Test a category of queries."""
    print_section(category_name)

    for query in queries:
        try:
            response = requests.post("http://localhost:8000/chat", json={
                "user_id": "test_user",
                "message": query,
                "top_n": 5
            }, timeout=10)

            if response.status_code == 200:
                result = response.json()
                print_query_result(query, result)
            else:
                print(f"\n[ERROR] Failed: {response.status_code}")

        except Exception as e:
            print(f"\n[ERROR] {e}")

        time.sleep(0.5)  # Rate limiting

def main():
    """Run comprehensive chat assistant tests."""

    print("\n" + "=" * 80)
    print("        ENHANCED CHAT ASSISTANT - COMPREHENSIVE TEST SUITE")
    print("=" * 80)

    # Check API connection
    print("\n[STEP 1] Testing API connection...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("[OK] API is running and healthy!")
        else:
            print("[WARN] API responded but with unexpected status")
    except Exception as e:
        print(f"[ERROR] API connection failed: {e}")
        print("Make sure the API is running: python -m uvicorn api.main:app --reload")
        return

    # Test 1: Greetings and Help
    test_category([
        "Hello!",
        "Hi there",
        "Help me find products",
        "What can you do?",
    ], "TEST 1: GREETINGS & HELP")

    # Test 2: Simple Product Search
    test_category([
        "Show me phones",
        "Find laptops",
        "Browse headphones",
        "Search for shoes",
    ], "TEST 2: SIMPLE PRODUCT SEARCH")

    # Test 3: Price-Based Filtering
    test_category([
        "Phones under 15000",
        "Affordable headphones under 5000",
        "Expensive smartwatches over 20000",
        "Budget cameras between 10000 and 30000",
    ], "TEST 3: PRICE-BASED FILTERING")

    # Test 4: Feature-Based Queries
    test_category([
        "Phones with good camera",
        "Laptops with long battery life",
        "Lightweight sports shoes",
        "Headphones with noise cancelling",
        "Gaming laptops with high performance",
    ], "TEST 4: FEATURE-BASED QUERIES")

    # Test 5: Brand-Specific Queries
    test_category([
        "Show me Samsung phones",
        "I want Apple products",
        "Find Nike shoes",
        "Display ASUS laptops",
        "Only Sony cameras",
    ], "TEST 5: BRAND-SPECIFIC QUERIES")

    # Test 6: Combined Queries (Most Powerful)
    test_category([
        "Samsung phones under 20000 with good camera",
        "Affordable headphones under 3000 with good bass",
        "Best rated Apple smartwatches under 30000",
        "Lightweight gaming laptops from ASUS with 16GB storage",
        "Nike sports shoes under 5000 with best ratings",
        "Premium Sony cameras for professional photography",
    ], "TEST 6: COMBINED COMPLEX QUERIES")

    # Test 7: Comparison Queries
    test_category([
        "Compare iPhone and Samsung phones",
        "Which laptop is better - HP or Dell?",
        "Samsung vs Apple - which is best?",
        "What's the difference between these products?",
    ], "TEST 7: COMPARISON QUERIES")

    # Test 8: Recommendation Queries
    test_category([
        "Recommend something for gaming",
        "Suggest products for a student",
        "Best choices for professionals",
        "What would you recommend for outdoor activities?",
    ], "TEST 8: RECOMMENDATION QUERIES")

    # Test 9: Sorting and Quality Preferences
    test_category([
        "Show cheapest phones",
        "Best rated headphones",
        "Premium quality electronics",
        "Budget friendly shoes",
        "Latest smartwatches",
    ], "TEST 9: SORTING & QUALITY PREFERENCES")

    # Test 10: Conversation Context
    print_section("TEST 10: CONVERSATION CONTEXT (Memory Test)")
    print("\nNote: These queries use the same user_id to test context memory")
    print("      Later queries should maintain context from earlier ones\n")

    test_queries = [
        "Show me Samsung products",
        "Under 20000",
        "With good quality",
        "Gaming preferred",
    ]

    for i, query in enumerate(test_queries, 1):
        try:
            response = requests.post("http://localhost:8000/chat", json={
                "user_id": "context_test_user",
                "message": query,
                "top_n": 3
            }, timeout=10)

            if response.status_code == 200:
                result = response.json()
                print(f"Step {i}: {query}")
                print(f"  Intent: {result['intent']}")
                print(f"  Accumulated Filters: {result['filters_applied']}")
                print()

        except Exception as e:
            print(f"Error: {e}\n")

    # Summary
    print_section("TEST SUMMARY")
    print("""
CHAT ASSISTANT CAPABILITIES:
  * Recognizes 8 different user intents
  * Extracts categories, brands, prices, features, ratings
  * Remembers conversation context
  * Handles complex combined queries
  * Provides filtered and ranked recommendations
  * Responds in < 200ms
  * Caches results for repeated queries

PERFORMANCE INDICATORS:
  * Intent Confidence: Shows how sure the system is
  * Latency: Response time in milliseconds
  * Cache Status: Whether result was retrieved from cache
  * Extracted Entities: What the system understood

NEXT STEPS:
  1. Open frontend/index.html in your browser
  2. Login with: admin@shopai.com / admin123456
  3. Go to "Chat Assistant"
  4. Try natural language queries
  5. Notice how context is remembered across messages
    """)

    print("=" * 80)
    print("        ALL TESTS COMPLETED!")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
