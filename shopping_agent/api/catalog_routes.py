"""
API Routes for R6: External Catalog API Integration
Handles catalog syncing, searching, and integration with external product sources.
"""
from fastapi import APIRouter, HTTPException

from services.external_catalog_service import get_catalog_client
from api.models import (
    CatalogProductRequest,
    SyncedCatalogResponse,
    CatalogSearchRequest,
    CatalogSearchResponse,
    CatalogHistoryResponse,
    ProductResponse
)

router = APIRouter(prefix="/catalog", tags=["Catalog"])
catalog_client = get_catalog_client()


@router.post("/sync", response_model=SyncedCatalogResponse)
async def sync_catalog(request: CatalogProductRequest):
    """
    Sync products from external catalog sources (Amazon, Flipkart, Bazaar).
    
    - **sources**: List of catalog sources to sync (amazon, flipkart, bazaar, local)
    - **merge_with_local**: Whether to merge with existing local products
    """
    result = catalog_client.sync_catalog(
        sources=request.sources,
        merge_with_local=request.merge_with_local
    )

    return SyncedCatalogResponse(
        timestamp=result["timestamp"],
        sources=result["sources"],
        total_products=result["total_products"],
        merged=result["merged"],
        storage_path=result["storage_path"]
    )


@router.post("/search", response_model=CatalogSearchResponse)
async def search_catalog(request: CatalogSearchRequest):
    """
    Search across all synced catalogs.
    
    - **query**: Search query (product name, brand, category)
    - **source**: Optional filter by catalog source
    - **max_price**: Maximum price filter
    - **min_price**: Minimum price filter
    - **category**: Category filter
    - **in_stock**: Only show in-stock items
    """
    filters = {
        "max_price": request.max_price,
        "min_price": request.min_price,
        "category": request.category,
        "in_stock": request.in_stock
    }
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}

    results = catalog_client.search_catalog(
        query=request.query,
        source=request.source,
        filters=filters if filters else None
    )

    # Convert to ProductResponse
    products = [
        ProductResponse(
            product_id=p.get("external_id", p.get("product_id", "")),
            name=p.get("name", ""),
            category=p.get("category", ""),
            brand=p.get("brand", ""),
            price=p.get("price", 0),
            rating=p.get("rating"),
            description=p.get("description", ""),
            score=p.get("rating")
        )
        for p in results
    ]

    return CatalogSearchResponse(
        query=request.query,
        results=products,
        total_found=len(products),
        filters_applied=filters if filters else {}
    )


@router.get("/sources")
async def get_available_sources():
    """
    Get list of available catalog sources that can be synced.
    """
    return {
        "available_sources": catalog_client.supported_sources,
        "description": {
            "amazon": "Amazon product catalog",
            "flipkart": "Flipkart product catalog",
            "bazaar": "Bazaar product catalog",
            "local": "Local product database"
        }
    }


@router.get("/history", response_model=CatalogHistoryResponse)
async def get_sync_history():
    """
    Get history of all catalog sync operations.
    """
    history = catalog_client.get_sync_history()

    return CatalogHistoryResponse(
        sync_operations=history,
        total_syncs=len(history),
        last_sync=history[-1]["timestamp"] if history else None
    )


@router.get("/statistics")
async def get_catalog_statistics():
    """
    Get statistics about synced catalogs.
    """
    history = catalog_client.get_sync_history()

    # Count by source
    sources_synced = {}
    for entry in history:
        source = entry.get("source")
        if source:
            sources_synced[source] = sources_synced.get(source, 0) + 1

    total_synced = sum(entry.get("product_count", 0) for entry in history)

    return {
        "total_sync_operations": len(history),
        "total_products_synced": total_synced,
        "sources_synced": sources_synced,
        "success_rate": len([e for e in history if e["status"] == "success"]) / len(history) if history else 0
    }


@router.get("/products/by-source/{source}")
async def get_products_by_source(source: str, limit: int = 100):
    """
    Get products from a specific catalog source.
    
    - **source**: Catalog source (amazon, flipkart, bazaar, local)
    - **limit**: Maximum number of products to return
    """
    if source not in catalog_client.supported_sources:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source. Supported: {catalog_client.supported_sources}"
        )

    products = catalog_client.fetch_products_from_source(source, limit=limit)

    return {
        "source": source,
        "total_products": len(products),
        "products": products[:limit]
    }


@router.post("/refresh")
async def refresh_catalog():
    """
    Refresh catalog data from all sources.
    Syncs latest products from all configured external catalogs.
    """
    result = catalog_client.sync_catalog(
        sources=["amazon", "flipkart", "bazaar"],
        merge_with_local=True
    )

    return {
        "success": True,
        "message": "Catalog refresh completed",
        "total_products": result["total_products"],
        "timestamp": result["timestamp"]
    }
