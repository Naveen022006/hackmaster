"""
MongoDB Database Service for Personal Shopping Agent.
Handles all database operations.
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from typing import Dict, List, Optional, Any
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import MONGODB_CONFIG


class DatabaseService:
    """MongoDB database service for all data operations."""

    _instance = None
    _client = None
    _db = None
    _connected = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self.connect()

    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._connected and self._client is not None

    def connect(self):
        """Establish connection to MongoDB."""
        try:
            self._client = MongoClient(
                MONGODB_CONFIG["uri"],
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000
            )
            # Test connection
            self._client.admin.command('ping')
            self._db = self._client[MONGODB_CONFIG["database"]]
            self._connected = True
            print(f"Connected to MongoDB: {MONGODB_CONFIG['database']}")
            self._create_indexes()
        except ConnectionFailure as e:
            self._connected = False
            print(f"ERROR: Failed to connect to MongoDB at {MONGODB_CONFIG['uri']}")
            print(f"ERROR: {e}")
            print("\n=== TROUBLESHOOTING ===")
            print("1. Make sure MongoDB is running:")
            print("   - Windows: Check if MongoDB service is running in Services")
            print("   - Or start it manually: mongod --dbpath <your-data-path>")
            print("2. Check if MongoDB is accessible at: mongodb://localhost:27017")
            print("3. If using MongoDB Compass, ensure the connection is active")
            print("========================\n")
            raise

    def _create_indexes(self):
        """Create necessary indexes for collections."""
        # Users collection indexes
        self._db[MONGODB_CONFIG["collections"]["users"]].create_index(
            "email", unique=True
        )
        self._db[MONGODB_CONFIG["collections"]["users"]].create_index("user_id")

        # Admins collection indexes
        self._db[MONGODB_CONFIG["collections"]["admins"]].create_index(
            "email", unique=True
        )

        # Products collection indexes
        self._db[MONGODB_CONFIG["collections"]["products"]].create_index("product_id", unique=True)
        self._db[MONGODB_CONFIG["collections"]["products"]].create_index("category")
        self._db[MONGODB_CONFIG["collections"]["products"]].create_index("brand")
        self._db[MONGODB_CONFIG["collections"]["products"]].create_index(
            [("name", "text"), ("description", "text")]
        )

        # Interactions collection indexes
        self._db[MONGODB_CONFIG["collections"]["interactions"]].create_index("user_id")
        self._db[MONGODB_CONFIG["collections"]["interactions"]].create_index("product_id")
        self._db[MONGODB_CONFIG["collections"]["interactions"]].create_index(
            [("user_id", ASCENDING), ("timestamp", DESCENDING)]
        )

    @property
    def db(self):
        """Get database instance."""
        return self._db

    @property
    def users(self):
        """Get users collection."""
        return self._db[MONGODB_CONFIG["collections"]["users"]]

    @property
    def admins(self):
        """Get admins collection."""
        return self._db[MONGODB_CONFIG["collections"]["admins"]]

    @property
    def products(self):
        """Get products collection."""
        return self._db[MONGODB_CONFIG["collections"]["products"]]

    @property
    def interactions(self):
        """Get interactions collection."""
        return self._db[MONGODB_CONFIG["collections"]["interactions"]]

    @property
    def user_profiles(self):
        """Get user profiles collection."""
        return self._db[MONGODB_CONFIG["collections"]["user_profiles"]]

    # User Operations
    def create_user(self, user_data: Dict) -> Dict:
        """Create a new user."""
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()
        user_data["is_active"] = True

        try:
            result = self.users.insert_one(user_data)
            user_data["_id"] = str(result.inserted_id)
            return user_data
        except DuplicateKeyError:
            raise ValueError("Email already exists")

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email."""
        return self.users.find_one({"email": email.lower()})

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by user_id."""
        return self.users.find_one({"user_id": user_id})

    def update_user(self, user_id: str, update_data: Dict) -> bool:
        """Update user data."""
        update_data["updated_at"] = datetime.utcnow()
        result = self.users.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get all users with pagination."""
        cursor = self.users.find({}, {"password_hash": 0}).skip(skip).limit(limit)
        return list(cursor)

    def get_user_count(self) -> int:
        """Get total user count."""
        return self.users.count_documents({})

    # Admin Operations
    def create_admin(self, admin_data: Dict) -> Dict:
        """Create a new admin."""
        admin_data["created_at"] = datetime.utcnow()
        admin_data["updated_at"] = datetime.utcnow()
        admin_data["is_active"] = True
        admin_data["role"] = admin_data.get("role", "admin")

        try:
            result = self.admins.insert_one(admin_data)
            admin_data["_id"] = str(result.inserted_id)
            return admin_data
        except DuplicateKeyError:
            raise ValueError("Admin email already exists")

    def get_admin_by_email(self, email: str) -> Optional[Dict]:
        """Get admin by email."""
        return self.admins.find_one({"email": email.lower()})

    def get_all_admins(self) -> List[Dict]:
        """Get all admins."""
        cursor = self.admins.find({}, {"password_hash": 0})
        return list(cursor)

    # Product Operations
    def insert_products(self, products: List[Dict]) -> int:
        """Bulk insert products."""
        if not products:
            return 0

        for product in products:
            product["created_at"] = datetime.utcnow()

        result = self.products.insert_many(products)
        return len(result.inserted_ids)

    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Get product by ID."""
        return self.products.find_one({"product_id": product_id})

    def get_products(
        self,
        category: str = None,
        brand: str = None,
        min_price: float = None,
        max_price: float = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict]:
        """Get products with filters."""
        query = {}

        if category:
            query["category"] = {"$regex": category, "$options": "i"}
        if brand:
            query["brand"] = {"$regex": brand, "$options": "i"}
        if min_price is not None:
            query["price"] = {"$gte": min_price}
        if max_price is not None:
            query.setdefault("price", {})["$lte"] = max_price

        cursor = self.products.find(query).skip(skip).limit(limit)
        return list(cursor)

    def get_product_count(self) -> int:
        """Get total product count."""
        return self.products.count_documents({})

    def get_categories(self) -> List[str]:
        """Get distinct categories."""
        return self.products.distinct("category")

    def get_brands(self, category: str = None) -> List[str]:
        """Get distinct brands, optionally filtered by category."""
        query = {}
        if category:
            query["category"] = {"$regex": category, "$options": "i"}
        return self.products.distinct("brand", query)

    def update_product(self, product_id: str, update_data: Dict) -> bool:
        """Update product data."""
        update_data["updated_at"] = datetime.utcnow()
        result = self.products.update_one(
            {"product_id": product_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    def delete_product(self, product_id: str) -> bool:
        """Delete a product."""
        result = self.products.delete_one({"product_id": product_id})
        return result.deleted_count > 0

    # Interaction Operations
    def insert_interactions(self, interactions: List[Dict]) -> int:
        """Bulk insert interactions."""
        if not interactions:
            return 0

        result = self.interactions.insert_many(interactions)
        return len(result.inserted_ids)

    def add_interaction(self, interaction: Dict) -> str:
        """Add a single interaction."""
        interaction["timestamp"] = datetime.utcnow()
        result = self.interactions.insert_one(interaction)
        return str(result.inserted_id)

    def get_user_interactions(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """Get interactions for a user."""
        cursor = self.interactions.find(
            {"user_id": user_id}
        ).sort("timestamp", DESCENDING).limit(limit)
        return list(cursor)

    def get_all_interactions(self, skip: int = 0, limit: int = 1000) -> List[Dict]:
        """Get all interactions with pagination."""
        cursor = self.interactions.find({}).skip(skip).limit(limit)
        return list(cursor)

    def get_interaction_count(self) -> int:
        """Get total interaction count."""
        return self.interactions.count_documents({})

    # User Profile Operations
    def save_user_profile(self, user_id: str, profile_data: Dict) -> bool:
        """Save or update user profile."""
        profile_data["user_id"] = user_id
        profile_data["updated_at"] = datetime.utcnow()

        result = self.user_profiles.update_one(
            {"user_id": user_id},
            {"$set": profile_data},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None

    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile."""
        return self.user_profiles.find_one({"user_id": user_id})

    # Statistics
    def get_statistics(self) -> Dict:
        """Get database statistics."""
        return {
            "total_users": self.get_user_count(),
            "total_products": self.get_product_count(),
            "total_interactions": self.get_interaction_count(),
            "total_admins": self.admins.count_documents({}),
            "categories": len(self.get_categories()),
            "brands": len(self.get_brands())
        }

    def clear_collection(self, collection_name: str) -> int:
        """Clear a collection (use with caution)."""
        if collection_name not in MONGODB_CONFIG["collections"].values():
            raise ValueError(f"Unknown collection: {collection_name}")

        result = self._db[collection_name].delete_many({})
        return result.deleted_count

    def close(self):
        """Close database connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None


# Singleton instance
_db_service: Optional[DatabaseService] = None


def get_database() -> DatabaseService:
    """Get or create singleton database service."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service


if __name__ == "__main__":
    # Test database connection
    db = get_database()

    print("\n--- Database Statistics ---")
    stats = db.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")

    print("\n--- Categories ---")
    print(db.get_categories())

    print("\n--- Brands (Electronics) ---")
    print(db.get_brands("Electronics"))
