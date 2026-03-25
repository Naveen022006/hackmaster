"""
API Integration with Product Catalog
Connects to external product APIs and syncs with local catalog
Supports multiple e-commerce platforms
"""

import requests
import json
import pandas as pd
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
import hashlib
import os
import time
from abc import ABC, abstractmethod


class ProductAPIConnector(ABC):
    """Abstract base class for product API connectors"""

    @abstractmethod
    def search_products(self, query: str, **kwargs) -> List[Dict]:
        pass

    @abstractmethod
    def get_product(self, product_id: str) -> Optional[Dict]:
        pass

    @abstractmethod
    def get_categories(self) -> List[str]:
        pass


class LocalCatalogAPI(ProductAPIConnector):
    """Local product catalog API (uses CSV data)"""

    def __init__(self, products_df: pd.DataFrame):
        self.products_df = products_df
        self.last_sync = datetime.now()
        print(f"  LocalCatalogAPI initialized with {len(products_df)} products")

    def search_products(self, query: str, category: str = None,
                       min_price: float = None, max_price: float = None,
                       limit: int = 20) -> List[Dict]:
        """Search products in local catalog"""
        results = self.products_df.copy()

        # Filter by query
        if query:
            query_lower = query.lower()
            results = results[
                results['name'].str.lower().str.contains(query_lower, na=False) |
                results['category'].str.lower().str.contains(query_lower, na=False)
            ]

        # Filter by category
        if category:
            results = results[results['category'].str.lower() == category.lower()]

        # Filter by price
        if min_price:
            results = results[results['price'] >= min_price]
        if max_price:
            results = results[results['price'] <= max_price]

        # Sort by relevance (discount first)
        if 'discount_percent' in results.columns:
            results = results.sort_values('discount_percent', ascending=False)

        return results.head(limit).to_dict('records')

    def get_product(self, product_id: str) -> Optional[Dict]:
        """Get single product by ID"""
        product = self.products_df[self.products_df['product_id'] == product_id]
        if not product.empty:
            return product.iloc[0].to_dict()
        return None

    def get_categories(self) -> List[str]:
        """Get all categories"""
        return sorted(self.products_df['category'].unique().tolist())

    def get_products_by_category(self, category: str, limit: int = 50) -> List[Dict]:
        """Get products by category"""
        products = self.products_df[
            self.products_df['category'].str.lower() == category.lower()
        ].head(limit)
        return products.to_dict('records')

    def get_deals(self, min_discount: float = 10, limit: int = 20) -> List[Dict]:
        """Get products with discounts"""
        if 'discount_percent' in self.products_df.columns:
            deals = self.products_df[
                self.products_df['discount_percent'] >= min_discount
            ].sort_values('discount_percent', ascending=False)
            return deals.head(limit).to_dict('records')
        return []


class ExternalAPIConnector(ProductAPIConnector):
    """Connector for external e-commerce APIs"""

    def __init__(self, api_name: str, base_url: str, api_key: str = None):
        self.api_name = api_name
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {'Content-Type': 'application/json'}
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request with caching"""
        cache_key = hashlib.md5(f"{endpoint}{str(params)}".encode()).hexdigest()

        # Check cache
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=self.cache_ttl):
                return cached_data

        try:
            response = requests.get(
                f"{self.base_url}/{endpoint}",
                params=params,
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.cache[cache_key] = (datetime.now(), data)
                return data
        except Exception as e:
            print(f"API Error ({self.api_name}): {e}")

        return None

    def search_products(self, query: str, **kwargs) -> List[Dict]:
        """Search products via external API"""
        params = {'q': query, **kwargs}
        result = self._make_request('products/search', params)
        return result.get('products', []) if result else []

    def get_product(self, product_id: str) -> Optional[Dict]:
        """Get product by ID"""
        result = self._make_request(f'products/{product_id}')
        return result

    def get_categories(self) -> List[str]:
        """Get all categories"""
        result = self._make_request('categories')
        return result.get('categories', []) if result else []


class MockExternalAPI(ProductAPIConnector):
    """Mock external API for testing (simulates Amazon/Flipkart-like API)"""

    def __init__(self, products_df: pd.DataFrame):
        self.products_df = products_df
        self.request_count = 0
        self.latency_ms = 100  # Simulated latency

    def _simulate_latency(self):
        """Simulate network latency"""
        time.sleep(self.latency_ms / 1000)
        self.request_count += 1

    def search_products(self, query: str, page: int = 1,
                       per_page: int = 10, **kwargs) -> List[Dict]:
        """Search products with pagination"""
        self._simulate_latency()

        results = self.products_df.copy()
        if query:
            results = results[
                results['name'].str.lower().str.contains(query.lower(), na=False)
            ]

        # Pagination
        start = (page - 1) * per_page
        end = start + per_page

        products = results.iloc[start:end].to_dict('records')

        # Add API-style metadata
        return {
            'products': products,
            'total': len(results),
            'page': page,
            'per_page': per_page,
            'has_more': end < len(results)
        }

    def get_product(self, product_id: str) -> Optional[Dict]:
        """Get product details with extended info"""
        self._simulate_latency()

        product = self.products_df[self.products_df['product_id'] == product_id]
        if not product.empty:
            p = product.iloc[0].to_dict()
            # Add extended API fields
            p['availability'] = 'in_stock'
            p['shipping_days'] = 3
            p['seller'] = 'Official Store'
            p['reviews_count'] = 100
            p['avg_rating'] = 4.2
            return p
        return None

    def get_categories(self) -> List[str]:
        """Get categories"""
        self._simulate_latency()
        return sorted(self.products_df['category'].unique().tolist())


class ProductCatalogManager:
    """
    Unified Product Catalog Manager
    Aggregates multiple API sources and provides unified interface
    """

    def __init__(self, products_df: pd.DataFrame = None):
        self.connectors: Dict[str, ProductAPIConnector] = {}
        self.primary_source = None
        self.sync_callbacks: List[Callable] = []
        self.last_sync = None

        # Initialize local catalog if provided
        if products_df is not None:
            self.add_connector('local', LocalCatalogAPI(products_df))
            self.primary_source = 'local'

    def add_connector(self, name: str, connector: ProductAPIConnector):
        """Add API connector"""
        self.connectors[name] = connector
        if self.primary_source is None:
            self.primary_source = name
        print(f"  Added connector: {name}")

    def set_primary_source(self, name: str):
        """Set primary data source"""
        if name in self.connectors:
            self.primary_source = name

    def search_products(self, query: str, source: str = None, **kwargs) -> List[Dict]:
        """Search products across sources"""
        source = source or self.primary_source
        if source and source in self.connectors:
            return self.connectors[source].search_products(query, **kwargs)
        return []

    def get_product(self, product_id: str, source: str = None) -> Optional[Dict]:
        """Get product from specified source"""
        source = source or self.primary_source
        if source and source in self.connectors:
            return self.connectors[source].get_product(product_id)
        return None

    def get_categories(self, source: str = None) -> List[str]:
        """Get categories from source"""
        source = source or self.primary_source
        if source and source in self.connectors:
            return self.connectors[source].get_categories()
        return []

    def search_all_sources(self, query: str, **kwargs) -> Dict[str, List[Dict]]:
        """Search across all connected sources"""
        results = {}
        for name, connector in self.connectors.items():
            try:
                results[name] = connector.search_products(query, **kwargs)
            except Exception as e:
                print(f"Error searching {name}: {e}")
                results[name] = []
        return results

    def sync_catalog(self, source: str = None):
        """Sync catalog from source"""
        self.last_sync = datetime.now()
        for callback in self.sync_callbacks:
            callback(source, self.last_sync)

    def on_sync(self, callback: Callable):
        """Register sync callback"""
        self.sync_callbacks.append(callback)

    def get_stats(self) -> Dict:
        """Get catalog statistics"""
        stats = {
            'connectors': list(self.connectors.keys()),
            'primary_source': self.primary_source,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None
        }

        # Get counts from local if available
        if 'local' in self.connectors:
            local = self.connectors['local']
            if hasattr(local, 'products_df'):
                stats['total_products'] = len(local.products_df)
                stats['categories'] = local.get_categories()

        return stats


# Factory function
def create_catalog_manager(products_df: pd.DataFrame = None,
                          add_mock_api: bool = False) -> ProductCatalogManager:
    """Create and configure catalog manager"""
    manager = ProductCatalogManager(products_df)

    if add_mock_api and products_df is not None:
        # Add mock external API for testing
        manager.add_connector('external_mock', MockExternalAPI(products_df))

    return manager


# For testing
if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    print("=" * 60)
    print("Testing Product Catalog API Integration")
    print("=" * 60)

    # Load products
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    products_df = pd.read_csv(os.path.join(data_dir, 'products.csv'))

    # Create manager
    manager = create_catalog_manager(products_df, add_mock_api=True)

    print("\nCatalog Stats:")
    print(json.dumps(manager.get_stats(), indent=2, default=str))

    print("\nSearching 'laptop' in local catalog:")
    results = manager.search_products('laptop', limit=5)
    for r in results[:3]:
        print(f"  - {r['name'][:40]}: Rs.{r['price']}")

    print("\nSearching via mock external API:")
    results = manager.search_products('phone', source='external_mock', per_page=3)
    if isinstance(results, dict):
        for p in results.get('products', [])[:3]:
            print(f"  - {p['name'][:40]}: Rs.{p['price']}")

    print("\nTest complete!")
