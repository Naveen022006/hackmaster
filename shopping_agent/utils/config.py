"""
Configuration settings for the Personal Shopping Agent system.
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# MongoDB Configuration
MONGODB_CONFIG = {
    "uri": os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
    "database": os.getenv("MONGODB_DATABASE", "shopping_agent"),
    "collections": {
        "users": "users",
        "admins": "admins",
        "products": "products",
        "interactions": "interactions",
        "user_profiles": "user_profiles"
    }
}

# JWT Authentication Configuration
JWT_CONFIG = {
    "secret_key": os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production-2024"),
    "algorithm": "HS256",
    "access_token_expire_minutes": 60 * 24,  # 24 hours
    "refresh_token_expire_days": 7
}

# Password Hashing Configuration
PASSWORD_CONFIG = {
    "schemes": ["bcrypt"],
    "deprecated": "auto"
}

# Dataset configuration
DATASET_CONFIG = {
    "num_users": 2000,
    "num_products": 5000,
    "num_interactions": 50000,
    "random_seed": 42
}

# Product categories and brands
CATEGORIES = {
    "Electronics": ["Samsung", "Apple", "Sony", "LG", "OnePlus", "Xiaomi", "Realme", "Oppo"],
    "Clothing": ["Nike", "Adidas", "Puma", "Levis", "H&M", "Zara", "Van Heusen", "Peter England"],
    "Home & Kitchen": ["Prestige", "Pigeon", "Bajaj", "Philips", "Havells", "Bosch", "IFB", "LG"],
    "Books": ["Penguin", "HarperCollins", "Scholastic", "Oxford", "Cambridge", "Pearson"],
    "Beauty": ["Lakme", "Maybelline", "LOreal", "Nivea", "Dove", "Garnier", "The Body Shop"],
    "Sports": ["Nike", "Adidas", "Puma", "Reebok", "Yonex", "Wilson", "Decathlon"],
    "Toys": ["Lego", "Hasbro", "Mattel", "Fisher-Price", "Hot Wheels", "Nerf"],
    "Grocery": ["Tata", "Nestle", "Britannia", "Amul", "MTR", "Haldirams", "Patanjali"]
}

# Location data
LOCATIONS = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
    "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
    "Chandigarh", "Kochi", "Indore", "Nagpur", "Coimbatore"
]

# Action weights for realistic interaction simulation
ACTION_WEIGHTS = {
    "view": 0.50,
    "click": 0.25,
    "add_to_cart": 0.15,
    "purchase": 0.10
}

# Model configuration
MODEL_CONFIG = {
    "embedding_dim": 50,
    "svd_n_factors": 100,
    "content_weight": 0.3,
    "collaborative_weight": 0.7,
    "top_n_recommendations": 10,
    "min_interactions_for_cf": 5
}

# NLP configuration
NLP_CONFIG = {
    "intent_labels": ["search", "buy", "compare", "filter", "general"],
    "max_sequence_length": 128,
    "confidence_threshold": 0.6
}

# API configuration
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": True
}

# Cache configuration
CACHE_CONFIG = {
    "ttl_seconds": 300,  # 5 minutes
    "max_size": 1000
}
