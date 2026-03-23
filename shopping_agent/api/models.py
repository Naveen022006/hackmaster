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


# R6: External Catalog Integration Models
class CatalogProductRequest(BaseModel):
    """Request model for syncing catalog products."""
    sources: List[str] = Field(..., description="Catalog sources to sync (amazon, flipkart, bazaar)")
    merge_with_local: bool = Field(default=True, description="Merge with local products")

    class Config:
        json_schema_extra = {
            "example": {
                "sources": ["amazon", "flipkart"],
                "merge_with_local": True
            }
        }


class SyncedCatalogResponse(BaseModel):
    """Response model for catalog sync."""
    timestamp: str
    sources: Dict[str, Dict[str, Any]]
    total_products: int
    merged: bool
    storage_path: str


class CatalogSearchRequest(BaseModel):
    """Request model for searching catalog."""
    query: str = Field(..., description="Search query")
    source: Optional[str] = Field(None, description="Filter by catalog source")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price")
    category: Optional[str] = Field(None, description="Filter by category")
    in_stock: Optional[bool] = Field(None, description="Only in-stock items")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "laptop",
                "source": "amazon",
                "max_price": 50000,
                "in_stock": True
            }
        }


class CatalogSearchResponse(BaseModel):
    """Response model for catalog search."""
    query: str
    results: List[ProductResponse]
    total_found: int
    filters_applied: Dict[str, Any]


class CatalogHistoryResponse(BaseModel):
    """Response model for sync history."""
    sync_operations: List[Dict[str, Any]]
    total_syncs: int
    last_sync: Optional[str]


# R7: Feedback Collection Models
class FeedbackSubmitRequest(BaseModel):
    """Request model for submitting feedback."""
    user_id: str = Field(..., description="User ID")
    feedback_type: str = Field(..., description="Type: recommendation, product, chat_quality")
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5")
    target_id: str = Field(..., description="Product ID or recommendation ID")
    comment: Optional[str] = Field(None, description="Optional comment/review")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "U00001",
                "feedback_type": "recommendation",
                "rating": 4,
                "target_id": "P00001",
                "comment": "Great recommendation! Very accurate"
            }
        }


class FeedbackResponse(BaseModel):
    """Response model for feedback submission."""
    id: str
    user_id: str
    type: str
    rating: int
    target_id: str
    timestamp: str
    message: str


class FeedbackAnalyticsResponse(BaseModel):
    """Response model for feedback analytics."""
    total_feedback: int
    avg_rating: float
    sentiment: str  # very_positive, positive, neutral, negative
    distribution: Dict[int, int]
    recommendation_quality_score: Optional[float] = None


class ProductFeedbackResponse(BaseModel):
    """Response model for product-specific feedback."""
    product_id: str
    total_feedback: int
    avg_rating: float
    rating_distribution: Dict[int, int]
    total_comments: int
    recent_comments: List[str]
    helpful_count: int


class QualityMetricsResponse(BaseModel):
    """Response model for recommendation quality metrics."""
    total_recommendations_rated: int
    avg_recommendation_rating: float
    quality_score: float
    distribution: Dict[int, int]


# R8: Cloud Storage Models
class CloudUploadRequest(BaseModel):
    """Request model for uploading to cloud storage."""
    file_path: str = Field(..., description="Local file path")
    remote_path: str = Field(..., description="Remote storage path")
    file_type: str = Field(..., description="Type: model, log, data")

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "models/svd_model.pkl",
                "remote_path": "models/svd_model_v1.pkl",
                "file_type": "model"
            }
        }


class CloudDownloadRequest(BaseModel):
    """Request model for downloading from cloud storage."""
    remote_path: str = Field(..., description="Remote storage path")
    local_path: str = Field(..., description="Local destination path")

    class Config:
        json_schema_extra = {
            "example": {
                "remote_path": "models/svd_model_v1.pkl",
                "local_path": "models/downloaded_model.pkl"
            }
        }


class StorageOperationResponse(BaseModel):
    """Response model for storage operations."""
    success: bool
    operation: str
    status: str
    local_path: Optional[str] = None
    remote_path: str
    timestamp: str
    provider: str


class StorageListResponse(BaseModel):
    """Response model for listing files."""
    prefix: str
    files: List[str]
    total_files: int
    provider: str


class StorageOperationLogResponse(BaseModel):
    """Response model for operation logs."""
    operations: List[Dict[str, Any]]
    total_operations: int
    providers_used: List[str]
