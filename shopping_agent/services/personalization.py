"""
Personalization Engine for Personal Shopping Agent.
Tracks user behavior and maintains dynamic user profiles.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional, Any
import json
import sys
sys.path.append(str(__file__).rsplit('/', 2)[0])

from utils.config import DATA_DIR


class UserProfile:
    """Represents a dynamic user profile."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.favorite_categories: Dict[str, float] = defaultdict(float)
        self.brand_affinity: Dict[str, float] = defaultdict(float)
        self.price_history: List[float] = []
        self.interaction_history: List[Dict] = []
        self.session_data: Dict = {}
        self.last_updated: datetime = datetime.now()

        # Computed metrics
        self._avg_spending: float = 0.0
        self._preferred_price_range: Dict[str, float] = {"min": 0, "max": 100000}

    @property
    def avg_spending(self) -> float:
        """Get average spending from price history."""
        if self.price_history:
            return np.mean(self.price_history[-50:])  # Last 50 purchases
        return self._avg_spending

    @property
    def preferred_price_range(self) -> Dict[str, float]:
        """Get preferred price range from history."""
        if len(self.price_history) >= 5:
            prices = self.price_history[-50:]
            return {
                "min": float(np.percentile(prices, 10)),
                "max": float(np.percentile(prices, 90))
            }
        return self._preferred_price_range

    def to_dict(self) -> Dict:
        """Convert profile to dictionary."""
        return {
            "user_id": self.user_id,
            "favorite_categories": dict(self.favorite_categories),
            "brand_affinity": dict(self.brand_affinity),
            "avg_spending": self.avg_spending,
            "preferred_price_range": self.preferred_price_range,
            "interaction_count": len(self.interaction_history),
            "last_updated": self.last_updated.isoformat()
        }


class PersonalizationEngine:
    """Engine for real-time personalization and user profile management."""

    # Decay factor for recency weighting (older interactions weighted less)
    RECENCY_DECAY = 0.95

    # Action weights for preference calculation
    ACTION_WEIGHTS = {
        "view": 1.0,
        "click": 2.0,
        "add_to_cart": 4.0,
        "purchase": 8.0
    }

    def __init__(self):
        self.user_profiles: Dict[str, UserProfile] = {}
        self.products_lookup: Dict[str, Dict] = {}
        self.global_popular_categories: Dict[str, float] = defaultdict(float)
        self.global_popular_brands: Dict[str, float] = defaultdict(float)

    def initialize_from_data(
        self,
        users_df: pd.DataFrame,
        products_df: pd.DataFrame,
        interactions_df: pd.DataFrame
    ):
        """Initialize engine with historical data."""
        # Create products lookup
        for _, row in products_df.iterrows():
            self.products_lookup[row["product_id"]] = {
                "category": row["category"],
                "brand": row["brand"],
                "price": row["price"],
                "rating": row.get("rating", 0),
                "name": row["name"]
            }

        # Calculate global popularity
        self._calculate_global_popularity(interactions_df)

        # Initialize user profiles from historical interactions
        print("Initializing user profiles from historical data...")
        for user_id in users_df["user_id"].unique():
            self.get_or_create_profile(user_id)

            # Get user's interactions
            user_interactions = interactions_df[
                interactions_df["user_id"] == user_id
            ].sort_values("timestamp")

            # Process each interaction
            for _, interaction in user_interactions.iterrows():
                self._process_interaction(
                    user_id=user_id,
                    product_id=interaction["product_id"],
                    action=interaction["action"],
                    timestamp=pd.to_datetime(interaction["timestamp"]),
                    rating=interaction.get("rating"),
                    update_history=False  # Don't store individual history for memory efficiency
                )

        print(f"Initialized {len(self.user_profiles)} user profiles")

    def _calculate_global_popularity(self, interactions_df: pd.DataFrame):
        """Calculate global category and brand popularity."""
        for _, interaction in interactions_df.iterrows():
            product_id = interaction["product_id"]
            if product_id not in self.products_lookup:
                continue

            product = self.products_lookup[product_id]
            weight = self.ACTION_WEIGHTS.get(interaction["action"], 1.0)

            self.global_popular_categories[product["category"]] += weight
            self.global_popular_brands[product["brand"]] += weight

        # Normalize
        total_cat = sum(self.global_popular_categories.values()) or 1
        total_brand = sum(self.global_popular_brands.values()) or 1

        for cat in self.global_popular_categories:
            self.global_popular_categories[cat] /= total_cat

        for brand in self.global_popular_brands:
            self.global_popular_brands[brand] /= total_brand

    def get_or_create_profile(self, user_id: str) -> UserProfile:
        """Get existing profile or create new one."""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(user_id)
        return self.user_profiles[user_id]

    def _process_interaction(
        self,
        user_id: str,
        product_id: str,
        action: str,
        timestamp: datetime = None,
        rating: float = None,
        update_history: bool = True
    ):
        """Process a single interaction and update user profile."""
        profile = self.get_or_create_profile(user_id)

        if product_id not in self.products_lookup:
            return

        product = self.products_lookup[product_id]
        weight = self.ACTION_WEIGHTS.get(action, 1.0)

        # Apply recency weighting
        if timestamp:
            days_ago = (datetime.now() - timestamp).days
            recency_weight = self.RECENCY_DECAY ** (days_ago / 7)  # Weekly decay
            weight *= recency_weight

        # Update category preferences
        profile.favorite_categories[product["category"]] += weight

        # Update brand affinity
        profile.brand_affinity[product["brand"]] += weight

        # Update price history for purchases
        if action == "purchase":
            profile.price_history.append(product["price"])

        # Store interaction in history
        if update_history:
            profile.interaction_history.append({
                "product_id": product_id,
                "action": action,
                "timestamp": (timestamp or datetime.now()).isoformat(),
                "rating": rating
            })

            # Keep only recent history (last 100 interactions)
            if len(profile.interaction_history) > 100:
                profile.interaction_history = profile.interaction_history[-100:]

        profile.last_updated = datetime.now()

    def record_interaction(
        self,
        user_id: str,
        product_id: str,
        action: str,
        rating: float = None
    ) -> Dict:
        """Record a new real-time interaction."""
        self._process_interaction(
            user_id=user_id,
            product_id=product_id,
            action=action,
            timestamp=datetime.now(),
            rating=rating,
            update_history=True
        )

        # Update global popularity
        if product_id in self.products_lookup:
            product = self.products_lookup[product_id]
            weight = self.ACTION_WEIGHTS.get(action, 1.0)
            self.global_popular_categories[product["category"]] += weight * 0.001
            self.global_popular_brands[product["brand"]] += weight * 0.001

        profile = self.user_profiles[user_id]
        return profile.to_dict()

    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user preferences."""
        profile = self.get_or_create_profile(user_id)

        # Get top categories
        sorted_categories = sorted(
            profile.favorite_categories.items(),
            key=lambda x: x[1],
            reverse=True
        )
        top_categories = [cat for cat, _ in sorted_categories[:5]]

        # Get top brands
        sorted_brands = sorted(
            profile.brand_affinity.items(),
            key=lambda x: x[1],
            reverse=True
        )
        top_brands = [brand for brand, _ in sorted_brands[:5]]

        # Calculate engagement score
        total_weight = sum(profile.favorite_categories.values())
        engagement_score = min(100, total_weight / 10)  # Normalize to 0-100

        return {
            "user_id": user_id,
            "top_categories": top_categories,
            "top_brands": top_brands,
            "avg_spending": profile.avg_spending,
            "preferred_price_range": profile.preferred_price_range,
            "engagement_score": engagement_score,
            "total_interactions": len(profile.interaction_history),
            "last_active": profile.last_updated.isoformat()
        }

    def get_personalized_filters(self, user_id: str) -> Dict:
        """Get recommended filters based on user preferences."""
        preferences = self.get_user_preferences(user_id)

        return {
            "suggested_categories": preferences["top_categories"],
            "suggested_brands": preferences["top_brands"],
            "price_range": preferences["preferred_price_range"],
            "sort_by": "relevance"
        }

    def get_trending_for_user(
        self,
        user_id: str,
        top_n: int = 5
    ) -> Dict[str, List[str]]:
        """Get trending items aligned with user preferences."""
        profile = self.get_or_create_profile(user_id)

        # Blend user preferences with global trends
        blended_categories = {}
        blended_brands = {}

        # Normalize user preferences
        cat_total = sum(profile.favorite_categories.values()) or 1
        brand_total = sum(profile.brand_affinity.values()) or 1

        for cat, score in profile.favorite_categories.items():
            user_score = score / cat_total
            global_score = self.global_popular_categories.get(cat, 0)
            blended_categories[cat] = 0.7 * user_score + 0.3 * global_score

        for brand, score in profile.brand_affinity.items():
            user_score = score / brand_total
            global_score = self.global_popular_brands.get(brand, 0)
            blended_brands[brand] = 0.7 * user_score + 0.3 * global_score

        # Sort and get top
        top_categories = sorted(
            blended_categories.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        top_brands = sorted(
            blended_brands.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        return {
            "trending_categories": [cat for cat, _ in top_categories],
            "trending_brands": [brand for brand, _ in top_brands]
        }

    def update_session_data(
        self,
        user_id: str,
        session_data: Dict
    ) -> Dict:
        """Update session-specific data for a user."""
        profile = self.get_or_create_profile(user_id)
        profile.session_data.update(session_data)
        profile.last_updated = datetime.now()
        return profile.session_data

    def get_session_data(self, user_id: str) -> Dict:
        """Get session data for a user."""
        profile = self.get_or_create_profile(user_id)
        return profile.session_data

    def reset_user_profile(self, user_id: str) -> bool:
        """Reset a user's profile."""
        if user_id in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(user_id)
            return True
        return False

    def get_all_user_ids(self) -> List[str]:
        """Get all tracked user IDs."""
        return list(self.user_profiles.keys())

    def export_profile(self, user_id: str) -> Optional[Dict]:
        """Export a user's complete profile."""
        if user_id not in self.user_profiles:
            return None
        return self.user_profiles[user_id].to_dict()

    def import_profile(self, user_id: str, profile_data: Dict):
        """Import a user profile from exported data."""
        profile = self.get_or_create_profile(user_id)
        profile.favorite_categories = defaultdict(
            float,
            profile_data.get("favorite_categories", {})
        )
        profile.brand_affinity = defaultdict(
            float,
            profile_data.get("brand_affinity", {})
        )
        profile._avg_spending = profile_data.get("avg_spending", 0)
        profile._preferred_price_range = profile_data.get(
            "preferred_price_range",
            {"min": 0, "max": 100000}
        )


# Singleton instance
_personalization_engine: Optional[PersonalizationEngine] = None


def get_personalization_engine() -> PersonalizationEngine:
    """Get or create singleton personalization engine."""
    global _personalization_engine
    if _personalization_engine is None:
        _personalization_engine = PersonalizationEngine()
    return _personalization_engine


if __name__ == "__main__":
    # Test personalization engine
    users_df = pd.read_csv(DATA_DIR / "users_processed.csv")
    products_df = pd.read_csv(DATA_DIR / "products_processed.csv")
    interactions_df = pd.read_csv(DATA_DIR / "interactions_processed.csv")

    engine = PersonalizationEngine()
    engine.initialize_from_data(users_df, products_df, interactions_df)

    # Test with a user
    test_user_id = users_df["user_id"].iloc[0]
    print(f"\n--- User Profile for {test_user_id} ---")
    preferences = engine.get_user_preferences(test_user_id)
    for key, value in preferences.items():
        print(f"{key}: {value}")

    print(f"\n--- Personalized Filters ---")
    filters = engine.get_personalized_filters(test_user_id)
    for key, value in filters.items():
        print(f"{key}: {value}")

    print(f"\n--- Trending for User ---")
    trending = engine.get_trending_for_user(test_user_id)
    for key, value in trending.items():
        print(f"{key}: {value}")

    # Test recording new interaction
    print(f"\n--- Recording New Interaction ---")
    test_product_id = products_df["product_id"].iloc[0]
    result = engine.record_interaction(
        user_id=test_user_id,
        product_id=test_product_id,
        action="purchase"
    )
    print(f"Updated profile: {result}")
