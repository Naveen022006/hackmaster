"""
Admin API Routes for Personal Shopping Agent.
Provides admin dashboard functionality.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.auth_routes import require_admin
from services.database import get_database, DatabaseService


# Router
router = APIRouter(prefix="/admin", tags=["Admin"])


# Response Models
class StatsResponse(BaseModel):
    total_users: int
    total_products: int
    total_interactions: int
    total_admins: int
    categories: int
    brands: int


class UserListResponse(BaseModel):
    users: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int


class ProductListResponse(BaseModel):
    products: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int


class ProductCreateRequest(BaseModel):
    product_id: str
    name: str
    category: str
    brand: str
    price: float = Field(..., gt=0)
    rating: Optional[float] = Field(None, ge=0, le=5)
    description: str


class ProductUpdateRequest(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    rating: Optional[float] = Field(None, ge=0, le=5)
    description: Optional[str] = None


class MessageResponse(BaseModel):
    message: str
    success: bool = True


# Dashboard Statistics
@router.get("/stats", response_model=StatsResponse)
async def get_dashboard_stats(
    current_admin: Dict = Depends(require_admin),
    db: DatabaseService = Depends(get_database)
):
    """
    Get dashboard statistics.

    Returns counts for users, products, interactions, etc.
    """
    stats = db.get_statistics()
    return StatsResponse(**stats)


# User Management
@router.get("/users", response_model=UserListResponse)
async def get_all_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_admin: Dict = Depends(require_admin),
    db: DatabaseService = Depends(get_database)
):
    """
    Get all users with pagination.
    """
    skip = (page - 1) * page_size
    users = db.get_all_users(skip=skip, limit=page_size)

    # Convert ObjectId to string
    for user in users:
        if "_id" in user:
            user["_id"] = str(user["_id"])
        if "created_at" in user and user["created_at"]:
            user["created_at"] = user["created_at"].isoformat()
        if "updated_at" in user and user["updated_at"]:
            user["updated_at"] = user["updated_at"].isoformat()
        if "last_login" in user and user["last_login"]:
            user["last_login"] = user["last_login"].isoformat()

    total = db.get_user_count()

    return UserListResponse(
        users=users,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: str,
    current_admin: Dict = Depends(require_admin),
    db: DatabaseService = Depends(get_database)
):
    """
    Get detailed user information.
    """
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Remove sensitive data
    user.pop("password_hash", None)

    # Convert ObjectId
    if "_id" in user:
        user["_id"] = str(user["_id"])

    # Get user interactions
    interactions = db.get_user_interactions(user_id, limit=20)
    for interaction in interactions:
        if "_id" in interaction:
            interaction["_id"] = str(interaction["_id"])
        if "timestamp" in interaction and interaction["timestamp"]:
            interaction["timestamp"] = interaction["timestamp"].isoformat()

    return {
        "user": user,
        "recent_interactions": interactions,
        "interaction_count": len(interactions)
    }


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    is_active: bool,
    current_admin: Dict = Depends(require_admin),
    db: DatabaseService = Depends(get_database)
):
    """
    Activate or deactivate a user.
    """
    success = db.update_user(user_id, {"is_active": is_active})
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    status = "activated" if is_active else "deactivated"
    return MessageResponse(message=f"User {user_id} {status} successfully")


# Product Management
@router.get("/products", response_model=ProductListResponse)
async def get_all_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    brand: Optional[str] = None,
    current_admin: Dict = Depends(require_admin),
    db: DatabaseService = Depends(get_database)
):
    """
    Get all products with pagination and filters.
    """
    skip = (page - 1) * page_size
    products = db.get_products(
        category=category,
        brand=brand,
        skip=skip,
        limit=page_size
    )

    # Convert ObjectId
    for product in products:
        if "_id" in product:
            product["_id"] = str(product["_id"])
        if "created_at" in product and product["created_at"]:
            product["created_at"] = product["created_at"].isoformat()

    total = db.get_product_count()

    return ProductListResponse(
        products=products,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/products", response_model=MessageResponse)
async def create_product(
    product: ProductCreateRequest,
    current_admin: Dict = Depends(require_admin),
    db: DatabaseService = Depends(get_database)
):
    """
    Create a new product.
    """
    # Check if product_id already exists
    existing = db.get_product_by_id(product.product_id)
    if existing:
        raise HTTPException(status_code=400, detail="Product ID already exists")

    product_data = product.dict()
    db.insert_products([product_data])

    return MessageResponse(message=f"Product {product.product_id} created successfully")


@router.put("/products/{product_id}")
async def update_product(
    product_id: str,
    update_data: ProductUpdateRequest,
    current_admin: Dict = Depends(require_admin),
    db: DatabaseService = Depends(get_database)
):
    """
    Update a product.
    """
    # Filter out None values
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}

    if not update_dict:
        raise HTTPException(status_code=400, detail="No update data provided")

    success = db.update_product(product_id, update_dict)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")

    return MessageResponse(message=f"Product {product_id} updated successfully")


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    current_admin: Dict = Depends(require_admin),
    db: DatabaseService = Depends(get_database)
):
    """
    Delete a product.
    """
    success = db.delete_product(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")

    return MessageResponse(message=f"Product {product_id} deleted successfully")


# Interaction Analytics
@router.get("/interactions")
async def get_interactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_admin: Dict = Depends(require_admin),
    db: DatabaseService = Depends(get_database)
):
    """
    Get all interactions with pagination.
    """
    skip = (page - 1) * page_size
    interactions = db.get_all_interactions(skip=skip, limit=page_size)

    # Convert ObjectId and datetime
    for interaction in interactions:
        if "_id" in interaction:
            interaction["_id"] = str(interaction["_id"])
        if "timestamp" in interaction and interaction["timestamp"]:
            if isinstance(interaction["timestamp"], datetime):
                interaction["timestamp"] = interaction["timestamp"].isoformat()

    total = db.get_interaction_count()

    return {
        "interactions": interactions,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/interactions/analytics")
async def get_interaction_analytics(
    current_admin: Dict = Depends(require_admin),
    db: DatabaseService = Depends(get_database)
):
    """
    Get interaction analytics.
    """
    # Aggregate interactions by action type
    pipeline = [
        {"$group": {"_id": "$action", "count": {"$sum": 1}}}
    ]
    action_counts = list(db.interactions.aggregate(pipeline))

    # Aggregate by category (join with products)
    category_pipeline = [
        {"$lookup": {
            "from": "products",
            "localField": "product_id",
            "foreignField": "product_id",
            "as": "product"
        }},
        {"$unwind": "$product"},
        {"$group": {"_id": "$product.category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]

    try:
        category_counts = list(db.interactions.aggregate(category_pipeline))
    except Exception:
        category_counts = []

    return {
        "by_action": {item["_id"]: item["count"] for item in action_counts},
        "by_category": {item["_id"]: item["count"] for item in category_counts if item["_id"]},
        "total_interactions": db.get_interaction_count()
    }


# Admin List
@router.get("/admins")
async def get_all_admins(
    current_admin: Dict = Depends(require_admin),
    db: DatabaseService = Depends(get_database)
):
    """
    Get all admins (superadmin only).
    """
    if current_admin.get("role") != "superadmin":
        raise HTTPException(status_code=403, detail="Superadmin access required")

    admins = db.get_all_admins()

    # Convert ObjectId
    for admin in admins:
        if "_id" in admin:
            admin["_id"] = str(admin["_id"])
        if "created_at" in admin and admin["created_at"]:
            admin["created_at"] = admin["created_at"].isoformat()

    return {"admins": admins}


# Database Operations
@router.post("/database/seed")
async def seed_database(
    current_admin: Dict = Depends(require_admin),
    db: DatabaseService = Depends(get_database)
):
    """
    Seed database with sample data from CSV files.

    Warning: This will clear existing data!
    """
    if current_admin.get("role") != "superadmin":
        raise HTTPException(status_code=403, detail="Superadmin access required")

    try:
        from services.data_migration import migrate_csv_to_mongodb
        result = migrate_csv_to_mongodb()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")
