"""
FastAPI Backend for Personal Shopping Agent.
Provides REST API endpoints for recommendations, chat, user management, and admin.
"""
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import (
    ChatRequest, ChatResponse,
    RecommendRequest, RecommendResponse,
    InteractionRequest, InteractionResponse,
    UserUpdateRequest, UserProfileResponse,
    ProductListResponse, ProductResponse,
    SimilarProductsResponse, HealthResponse, ErrorResponse
)
from services.recommendation_pipeline import get_pipeline, RecommendationPipeline

# Import auth and admin routes
from api.auth_routes import router as auth_router
from api.admin_routes import router as admin_router

# Import new requirement routers (R6, R7, R8)
from api.feedback_routes import router as feedback_router
from api.catalog_routes import router as catalog_router
from api.storage_routes import router as storage_router


# Global pipeline instance
pipeline: Optional[RecommendationPipeline] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize pipeline and database on startup."""
    global pipeline
    print("Starting up...")
    print("=" * 50)

    # Initialize database and create default admin
    db_connected = False
    try:
        from services.auth import get_auth_service
        auth = get_auth_service()
        auth.create_default_admin()
        db_connected = True
        print("Database connected, default admin ready")
        print("Default admin credentials: admin@shopai.com / admin123456")
    except Exception as e:
        print(f"\nWARNING: Database initialization failed!")
        print(f"Error: {e}")
        print("\nMake sure MongoDB is running on mongodb://localhost:27017")
        print("Authentication features will not work without MongoDB.\n")

    # Initialize recommendation pipeline
    try:
        print("Initializing recommendation pipeline...")
        pipeline = get_pipeline()
        pipeline.initialize()
        print("Pipeline initialized successfully!")
    except Exception as e:
        print(f"Warning: Pipeline initialization failed: {e}")
        print("Recommendation features may not work.")

    print("=" * 50)
    if db_connected:
        print("API ready! Open http://localhost:8000 or frontend")
    else:
        print("API started with LIMITED functionality (no database)")
    print("=" * 50)

    yield
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Personal Shopping Agent API",
    description="An intelligent shopping assistant with NLP and ML-powered recommendations",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(feedback_router)  # R7: Feedback Collection System
app.include_router(catalog_router)   # R6: External Catalog Integration
app.include_router(storage_router)   # R8: Cloud Storage Infrastructure


def get_pipeline_instance() -> RecommendationPipeline:
    """Dependency to get pipeline instance."""
    global pipeline
    if pipeline is None or not pipeline.is_initialized:
        pipeline = get_pipeline()
        pipeline.initialize()
    return pipeline


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "detail": str(exc.detail),
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc),
            "status_code": 500
        }
    )


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(pipe: RecommendationPipeline = Depends(get_pipeline_instance)):
    """Check API health status."""
    # Check database
    db_status = "not_connected"
    try:
        from services.database import get_database
        db = get_database()
        db.db.command('ping')
        db_status = "connected"
    except Exception:
        pass

    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "database": db_status,
            "pipeline": "initialized" if pipe and pipe.is_initialized else "not_initialized",
            "nlp": "ready" if pipe and pipe.nlp_processor else "not_ready",
            "recommender": "ready" if pipe and pipe.recommender else "not_ready",
            "personalization": "ready" if pipe and pipe.personalization_engine else "not_ready"
        }
    }


# Chat endpoint - NLP-powered conversation
@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(
    request: ChatRequest,
    pipe: RecommendationPipeline = Depends(get_pipeline_instance)
):
    """
    Process a natural language query and return recommendations.

    This endpoint:
    - Understands user intent (search, buy, compare, filter)
    - Extracts entities (category, brand, price, features)
    - Returns personalized product recommendations
    """
    try:
        result = pipe.process_query(
            user_id=request.user_id,
            query=request.message,
            top_n=request.top_n
        )

        # Convert recommendations to ProductResponse format
        recommendations = [
            ProductResponse(
                product_id=rec["product_id"],
                name=rec["name"],
                category=rec["category"],
                brand=rec["brand"],
                price=rec["price"],
                rating=rec.get("rating"),
                description=rec["description"],
                score=rec.get("score"),
                feature_matches=rec.get("feature_matches")
            )
            for rec in result["recommendations"]
        ]

        return ChatResponse(
            query=result["query"],
            user_id=result["user_id"],
            intent=result["intent"],
            intent_confidence=result["intent_confidence"],
            entities=result["entities"],
            filters_applied=result["filters_applied"],
            response=result["response"],
            recommendations=recommendations,
            user_preferences=result["user_preferences"],
            cached=result["cached"],
            latency_ms=result["latency_ms"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Recommendations endpoint
@app.get("/recommend", response_model=RecommendResponse, tags=["Recommendations"])
async def get_recommendations(
    user_id: str = Query(..., description="User ID"),
    top_n: int = Query(default=10, ge=1, le=50, description="Number of recommendations"),
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating"),
    pipe: RecommendationPipeline = Depends(get_pipeline_instance)
):
    """
    Get personalized product recommendations for a user.

    Combines collaborative filtering and content-based filtering
    with optional category, brand, and price filters.
    """
    try:
        # Build filters
        filters = {}
        if category:
            filters["category"] = category
        if brand:
            filters["brand"] = brand
        if min_price:
            filters["min_price"] = min_price
        if max_price:
            filters["max_price"] = max_price
        if min_rating:
            filters["min_rating"] = min_rating

        recommendations = pipe.get_recommendations(
            user_id=user_id,
            top_n=top_n,
            filters=filters
        )

        return RecommendResponse(
            user_id=user_id,
            recommendations=[
                ProductResponse(
                    product_id=rec["product_id"],
                    name=rec["name"],
                    category=rec["category"],
                    brand=rec["brand"],
                    price=rec["price"],
                    rating=rec.get("rating"),
                    description=rec["description"],
                    score=rec.get("score")
                )
                for rec in recommendations
            ],
            filters_applied=filters,
            total_results=len(recommendations)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Products endpoint
@app.get("/products", response_model=ProductListResponse, tags=["Products"])
async def get_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of products"),
    pipe: RecommendationPipeline = Depends(get_pipeline_instance)
):
    """
    Get products with optional filtering.

    Returns a list of products matching the specified criteria.
    """
    try:
        products = pipe.get_products(
            category=category,
            brand=brand,
            min_price=min_price,
            max_price=max_price,
            limit=limit
        )

        return ProductListResponse(
            products=[
                ProductResponse(
                    product_id=p["product_id"],
                    name=p["name"],
                    category=p["category"],
                    brand=p["brand"],
                    price=p["price"],
                    rating=p.get("rating"),
                    description=p["description"]
                )
                for p in products
            ],
            total=len(products),
            filters={
                "category": category,
                "brand": brand,
                "min_price": min_price,
                "max_price": max_price
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Similar products endpoint
@app.get("/products/{product_id}/similar", tags=["Products"])
async def get_similar_products(
    product_id: str,
    top_n: int = Query(default=10, ge=1, le=50, description="Number of similar products"),
    same_category: bool = Query(default=True, description="Filter by same category"),
    price_tolerance: float = Query(default=0.5, ge=0.1, le=2.0, description="Price tolerance (0.5 = 50%)"),
    pipe: RecommendationPipeline = Depends(get_pipeline_instance)
):
    """
    Get products similar to a given product with price and category analysis.

    Parameters:
    - product_id: The product to find similar items for
    - top_n: Number of similar products to return
    - same_category: Filter by same category (default: true)
    - price_tolerance: Price range tolerance (default: 0.5 = 50%)

    Returns similar products with:
    - Category filtering (same category)
    - Price analysis (cheaper, similar price, expensive)
    - Recommendations based on price range
    """
    try:
        result = pipe.get_similar_products(
            product_id,
            top_n=top_n,
            same_category=same_category,
            price_tolerance=price_tolerance
        )

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# User profile endpoint
@app.get("/user/{user_id}/profile", response_model=UserProfileResponse, tags=["User"])
async def get_user_profile(
    user_id: str,
    pipe: RecommendationPipeline = Depends(get_pipeline_instance)
):
    """
    Get user profile with preferences and statistics.

    Returns user's favorite categories, brand affinities,
    spending patterns, and engagement metrics.
    """
    try:
        preferences = pipe.get_user_preferences(user_id)

        return UserProfileResponse(
            user_id=preferences["user_id"],
            top_categories=preferences.get("top_categories", []),
            top_brands=preferences.get("top_brands", []),
            avg_spending=preferences.get("avg_spending", 0),
            preferred_price_range=preferences.get("preferred_price_range", {"min": 0, "max": 100000}),
            engagement_score=preferences.get("engagement_score", 0),
            total_interactions=preferences.get("total_interactions", 0),
            last_active=preferences.get("last_active", datetime.now().isoformat())
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Update user preferences endpoint
@app.post("/user/update", response_model=InteractionResponse, tags=["User"])
async def update_user_preferences(
    request: UserUpdateRequest,
    pipe: RecommendationPipeline = Depends(get_pipeline_instance)
):
    """
    Update user preferences.

    Allows manual updates to user preferences for
    favorite categories, brand affinities, etc.
    """
    try:
        pipe.update_user_preferences(
            user_id=request.user_id,
            preferences=request.preferences
        )

        updated_profile = pipe.get_user_preferences(request.user_id)

        return InteractionResponse(
            success=True,
            message="User preferences updated successfully",
            user_profile=updated_profile
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Record interaction endpoint
@app.post("/interaction", response_model=InteractionResponse, tags=["User"])
async def record_interaction(
    request: InteractionRequest,
    pipe: RecommendationPipeline = Depends(get_pipeline_instance)
):
    """
    Record a user interaction with a product.

    Supported actions: view, click, add_to_cart, purchase.
    These interactions update user preferences in real-time.
    """
    valid_actions = ["view", "click", "add_to_cart", "purchase"]
    if request.action not in valid_actions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action. Must be one of: {valid_actions}"
        )

    try:
        result = pipe.record_interaction(
            user_id=request.user_id,
            product_id=request.product_id,
            action=request.action,
            rating=request.rating
        )

        return InteractionResponse(
            success=True,
            message=f"Interaction '{request.action}' recorded successfully",
            user_profile=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Categories endpoint
@app.get("/categories", tags=["Metadata"])
async def get_categories(pipe: RecommendationPipeline = Depends(get_pipeline_instance)):
    """Get list of available product categories."""
    try:
        categories = pipe.products_df["category"].unique().tolist()
        return {"categories": sorted(categories)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Brands endpoint
@app.get("/brands", tags=["Metadata"])
async def get_brands(
    category: Optional[str] = Query(None, description="Filter by category"),
    pipe: RecommendationPipeline = Depends(get_pipeline_instance)
):
    """Get list of available brands, optionally filtered by category."""
    try:
        df = pipe.products_df
        if category:
            df = df[df["category"].str.lower() == category.lower()]
        brands = df["brand"].unique().tolist()
        return {"brands": sorted(brands)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
