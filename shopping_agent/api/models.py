"""
Pydantic models for API request/response validation.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


# Request Models
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    user_id: str = Field(..., description="User ID")
    message: str = Field(..., description="User message/query")
    top_n: int = Field(default=10, ge=1, le=50, description="Number of recommendations")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "U00001",
                "message": "I want a phone under 15000 with good camera",
                "top_n": 10
            }
        }


class RecommendRequest(BaseModel):
    """Request model for recommendations."""
    user_id: str = Field(..., description="User ID")
    top_n: int = Field(default=10, ge=1, le=50, description="Number of recommendations")
    category: Optional[str] = Field(None, description="Filter by category")
    brand: Optional[str] = Field(None, description="Filter by brand")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="Minimum rating")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "U00001",
                "top_n": 10,
                "category": "Electronics",
                "max_price": 20000
            }
        }


class InteractionRequest(BaseModel):
    """Request model for recording interactions."""
    user_id: str = Field(..., description="User ID")
    product_id: str = Field(..., description="Product ID")
    action: str = Field(..., description="Action type: view, click, add_to_cart, purchase")
    rating: Optional[float] = Field(None, ge=1, le=5, description="Optional rating (1-5)")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "U00001",
                "product_id": "P00001",
                "action": "purchase",
                "rating": 4.5
            }
        }


class UserUpdateRequest(BaseModel):
    """Request model for updating user preferences."""
    user_id: str = Field(..., description="User ID")
    preferences: Dict[str, Any] = Field(..., description="User preferences to update")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "U00001",
                "preferences": {
                    "favorite_categories": {"Electronics": 10, "Clothing": 5},
                    "brand_affinity": {"Samsung": 8, "Nike": 6}
                }
            }
        }


# Response Models
class ProductResponse(BaseModel):
    """Response model for a product."""
    product_id: str
    name: str
    category: str
    brand: str
    price: float
    rating: Optional[float]
    description: str
    score: Optional[float] = None
    feature_matches: Optional[int] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    query: str
    user_id: str
    intent: str
    intent_confidence: float
    entities: Dict[str, Any]
    filters_applied: Dict[str, Any]
    response: str
    recommendations: List[ProductResponse]
    user_preferences: Dict[str, Any]
    cached: bool
    latency_ms: float


class RecommendResponse(BaseModel):
    """Response model for recommendations endpoint."""
    user_id: str
    recommendations: List[ProductResponse]
    filters_applied: Dict[str, Any]
    total_results: int


class UserProfileResponse(BaseModel):
    """Response model for user profile."""
    user_id: str
    top_categories: List[str]
    top_brands: List[str]
    avg_spending: float
    preferred_price_range: Dict[str, float]
    engagement_score: float
    total_interactions: int
    last_active: str


class InteractionResponse(BaseModel):
    """Response model for interaction recording."""
    success: bool
    message: str
    user_profile: Dict[str, Any]


class ProductListResponse(BaseModel):
    """Response model for product list."""
    products: List[ProductResponse]
    total: int
    filters: Dict[str, Any]


class PriceAnalysis(BaseModel):
    """Price analysis for similar products."""
    original_price: float
    price_range: Dict[str, float]
    categories: Dict[str, int]


class EnhancedSimilarProductsResponse(BaseModel):
    """Enhanced response model for similar products with category and price analysis."""
    original_product: Dict
    similar_products: List[ProductResponse]
    price_analysis: PriceAnalysis
    same_category_filter_applied: bool
    original_category: str


class SimilarProductsResponse(BaseModel):
    """Response model for similar products."""
    product_id: str
    similar_products: List[ProductResponse]


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str
    detail: str
    status_code: int


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    version: str
    timestamp: str
    components: Dict[str, str]
