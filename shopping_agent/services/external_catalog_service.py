"""
External Product Catalog API Integration Service (R6)
Integrates with external product catalogs and syncs with local database.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
from pathlib import Path
import json
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.config import DATA_DIR, MODELS_DIR


class ExternalCatalogClient:
    """Client for integrating with external product catalogs."""

    def __init__(self):
        self.supported_sources = ["amazon", "flipkart", "bazaar", "local"]
        self.api_endpoints = {
            "amazon": "https://api.amazon-like.example/products",
            "flipkart": "https://api.flipkart-like.example/products",
            "bazaar": "https://api.bazaar-like.example/products"
        }
        self.products_cache: Dict[str, Any] = {}
        self.last_sync: datetime = None
        self.sync_log = []

    def fetch_products_from_source(
        self,
        source: str,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Fetch products from external source."""
        if source not in self.supported_sources:
            raise ValueError(f"Unsupported source: {source}. Supported: {self.supported_sources}")

        if source == "local":
            return self._fetch_local_products(category, limit)

        try:
            # In production, this would call real APIs
            print(f"Fetching from {source}...")
            products = self._mock_fetch_from_api(source, category, limit)
            self._log_sync("success", source, len(products))
            return products
        except Exception as e:
            self._log_sync("error", source, 0, str(e))
            return []

    def _fetch_local_products(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Fetch products from local CSV (fallback)."""
        try:
            products_df = pd.read_csv(DATA_DIR / "products.csv")
            if category:
                products_df = products_df[products_df["category"].str.lower() == category.lower()]
            return products_df.head(limit).to_dict("records")
        except Exception as e:
            print(f"Error fetching local products: {e}")
            return []

    def _mock_fetch_from_api(
        self,
        source: str,
        category: Optional[str],
        limit: int
    ) -> List[Dict]:
        """Mock API call - in production would use actual APIs."""
        # Simulate API response
        mock_products = []
        brands = ["Sony", "Samsung", "LG", "Apple", "Dell", "HP", "Lenovo"]
        categories = ["Electronics", "Home & Kitchen", "Clothing"]

        for i in range(limit):
            mock_products.append({
                "external_id": f"{source}_P{i:05d}",
                "source": source,
                "name": f"Product {i} from {source.title()}",
                "category": category or np.random.choice(categories),
                "brand": np.random.choice(brands),
                "price": float(np.random.randint(500, 150000)),
                "rating": float(np.random.uniform(2.5, 5.0)),
                "description": f"Product sourced from {source}",
                "availability": np.random.choice([True, False], p=[0.8, 0.2]),
                "stock": np.random.randint(0, 500),
                "sync_date": datetime.now().isoformat()
            })

        return mock_products

    def sync_catalog(
        self,
        sources: List[str],
        merge_with_local: bool = True
    ) -> Dict[str, Any]:
        """Sync products from multiple catalog sources."""
        sync_result = {
            "timestamp": datetime.now().isoformat(),
            "sources": {},
            "total_products": 0,
            "merged": False,
            "storage_path": None
        }

        all_products = []

        # Fetch from each source
        for source in sources:
            print(f"Syncing from {source}...")
            products = self.fetch_products_from_source(source)
            sync_result["sources"][source] = {
                "count": len(products),
                "status": "success" if products else "failed"
            }
            all_products.extend(products)

        # Merge with local products if requested
        if merge_with_local and "local" not in sources:
            local_products = self.fetch_products_from_source("local")
            all_products.extend(local_products)
            sync_result["merged"] = True

        # Remove duplicates by external_id
        seen_ids = set()
        unique_products = []
        for product in all_products:
            external_id = product.get("external_id", product.get("product_id"))
            if external_id not in seen_ids:
                seen_ids.add(external_id)
                unique_products.append(product)

        sync_result["total_products"] = len(unique_products)

        # Store synced catalog
        storage_path = self._store_synced_catalog(unique_products)
        sync_result["storage_path"] = str(storage_path)

        self.last_sync = datetime.now()
        return sync_result

    def _store_synced_catalog(self, products: List[Dict]) -> Path:
        """Store synced catalog to file."""
        try:
            sync_dir = DATA_DIR / "catalogs"
            sync_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = sync_dir / f"synced_catalog_{timestamp}.json"

            with open(filepath, "w") as f:
                json.dump(products, f, indent=2, default=str)

            return filepath
        except Exception as e:
            print(f"Error storing synced catalog: {e}")
            return None

    def _log_sync(
        self,
        status: str,
        source: str,
        count: int,
        error: Optional[str] = None
    ):
        """Log sync operations."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "source": source,
            "product_count": count,
            "error": error
        }
        self.sync_log.append(log_entry)

    def get_sync_history(self) -> List[Dict]:
        """Get sync operation history."""
        return self.sync_log

    def search_catalog(
        self,
        query: str,
        source: Optional[str] = None,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Search across synced catalogs."""
        search_results = []
        query_lower = query.lower()

        # Load latest synced catalog
        try:
            sync_dir = DATA_DIR / "catalogs"
            if sync_dir.exists():
                latest_file = max(sync_dir.glob("synced_catalog_*.json"), default=None)
                if latest_file:
                    with open(latest_file) as f:
                        all_products = json.load(f)

                    # Search
                    for product in all_products:
                        # Filter by source if specified
                        if source and product.get("source") != source:
                            continue

                        # Match query
                        if query_lower in product.get("name", "").lower() or \
                           query_lower in product.get("brand", "").lower() or \
                           query_lower in product.get("category", "").lower():

                            # Apply filters
                            if filters:
                                if "max_price" in filters and product.get("price", float("inf")) > filters["max_price"]:
                                    continue
                                if "min_price" in filters and product.get("price", 0) < filters["min_price"]:
                                    continue
                                if "category" in filters and product.get("category") != filters["category"]:
                                    continue
                                if "in_stock" in filters and filters["in_stock"] and not product.get("availability"):
                                    continue

                            search_results.append(product)

            return search_results
        except Exception as e:
            print(f"Error searching catalog: {e}")
            return []


# Singleton instance
_catalog_client = None


def get_catalog_client() -> ExternalCatalogClient:
    """Get singleton catalog client."""
    global _catalog_client
    if _catalog_client is None:
        _catalog_client = ExternalCatalogClient()
    return _catalog_client
