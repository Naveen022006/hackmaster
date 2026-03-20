"""
Real-Time Recommendation Pipeline for Personal Shopping Agent.
Integrates NLP, Recommendation Engine, and Personalization.
"""
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from functools import lru_cache
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import DATA_DIR, MODELS_DIR, MODEL_CONFIG, CACHE_CONFIG


class LRUCache:
    """Simple LRU cache with TTL support."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, tuple] = {}  # key -> (value, timestamp)

    def get(self, key: str) -> Optional[any]:
        """Get value from cache."""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: any):
        """Set value in cache."""
        # Evict oldest if at capacity
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]

        self.cache[key] = (value, time.time())

    def invalidate(self, key: str):
        """Remove key from cache."""
        if key in self.cache:
            del self.cache[key]

    def clear(self):
        """Clear all cache."""
        self.cache.clear()


class RecommendationPipeline:
    """End-to-end pipeline for real-time recommendations."""

    def __init__(self):
        self.nlp_processor = None
        self.recommender = None
        self.personalization_engine = None
        self.interactions_df = None
        self.products_df = None
        self.users_df = None

        # Cache for recommendations
        self.cache = LRUCache(
            max_size=CACHE_CONFIG["max_size"],
            ttl_seconds=CACHE_CONFIG["ttl_seconds"]
        )

        self.is_initialized = False

    def initialize(self):
        """Initialize all components."""
        print("Initializing recommendation pipeline...")

        # Import here to avoid circular imports
        from services.nlp_processor import get_nlp_processor
        from services.personalization import PersonalizationEngine
        from models.recommender import HybridRecommender
        from services.data_preprocessor import DataPreprocessor

        # Initialize NLP
        print("Loading NLP processor...")
        self.nlp_processor = get_nlp_processor()

        # Load data
        print("Loading data...")
        preprocessor = DataPreprocessor()
        try:
            data = preprocessor.load_preprocessed_data()
        except FileNotFoundError:
            print("Preprocessed data not found. Running preprocessing...")
            data = preprocessor.preprocess_all()

        self.users_df = data["users"]
        self.products_df = data["products"]
        self.interactions_df = pd.read_csv(DATA_DIR / "interactions_processed.csv")
        self.interactions_df["timestamp"] = pd.to_datetime(self.interactions_df["timestamp"])

        # Initialize recommender
        print("Loading recommendation model...")
        try:
            self.recommender = HybridRecommender.load()
        except FileNotFoundError:
            print("Model not found. Training new model...")
            self.recommender = HybridRecommender()
            self.recommender.fit(
                interaction_matrix=data["interaction_matrix"],
                product_embeddings=data["product_embeddings"],
                users_df=self.users_df,
                products_df=self.products_df,
                interactions_df=self.interactions_df
            )
            self.recommender.save()

        # Initialize personalization engine
        print("Loading personalization engine...")
        self.personalization_engine = PersonalizationEngine()
        self.personalization_engine.initialize_from_data(
            self.users_df,
            self.products_df,
            self.interactions_df
        )

        self.is_initialized = True
        print("Pipeline initialized successfully!")

    def process_query(
        self,
        user_id: str,
        query: str,
        top_n: int = None
    ) -> Dict:
        """Process a user query and return recommendations with learning."""
        if not self.is_initialized:
            self.initialize()

        start_time = time.time()
        top_n = top_n or MODEL_CONFIG["top_n_recommendations"]

        # Check cache
        cache_key = f"{user_id}:{query}:{top_n}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            cached_result["cached"] = True
            cached_result["latency_ms"] = (time.time() - start_time) * 1000
            return cached_result

        # Process with NLP (pass user_id for context)
        nlp_result = self.nlp_processor.process(query, user_id=user_id)

        # Get conversation context and user profile (new system)
        context = nlp_result.get("context")
        user_profile = nlp_result.get("user_profile")

        # Get user preferences for context
        user_preferences = self.personalization_engine.get_user_preferences(user_id)

        # Merge NLP filters with user preferences
        filters = self._merge_filters(nlp_result["filters"], user_preferences)

        # Get recommendations if needed
        recommendations = []
        if nlp_result["requires_products"]:
            recommendations = self.recommender.recommend(
                user_id=user_id,
                interactions_df=self.interactions_df,
                top_n=top_n * 2,  # Get more for filtering
                filters=filters
            )

            # Apply feature boosting if features extracted
            if nlp_result["entities"].get("features"):
                recommendations = self._boost_by_features(
                    recommendations,
                    nlp_result["entities"]["features"]
                )

            # Sort by requested order
            sort_order = nlp_result["entities"].get("sort")
            recommendations = self._apply_sorting(recommendations, sort_order)

        # Generate contextual response with actual results count and user profile
        response = self.nlp_processor.generate_response(
            nlp_result["intent"],
            nlp_result["entities"],
            len(recommendations),
            context,
            user_profile
        )

        # Build result
        result = {
            "query": query,
            "user_id": user_id,
            "intent": nlp_result["intent"],
            "intent_confidence": nlp_result["intent_confidence"],
            "entities": nlp_result["entities"],
            "filters_applied": filters,
            "response": response,
            "recommendations": recommendations[:top_n],
            "user_preferences": {
                "top_categories": user_preferences.get("top_categories", [])[:3],
                "avg_spending": user_preferences.get("avg_spending", 0)
            },
            "cached": False,
            "latency_ms": (time.time() - start_time) * 1000
        }

        # Add conversation context info
        if context:
            result["conversation_context"] = {
                "turn_number": context.turn_count + 1,
                "is_refinement": context.is_refinement,
                "is_new_user": context.is_new_user
            }

        # Record turn for learning
        product_ids = [r["product_id"] for r in recommendations[:top_n]]
        self.nlp_processor.record_turn(
            user_id=user_id,
            query=query,
            intent=nlp_result["intent"],
            confidence=nlp_result["intent_confidence"],
            entities=nlp_result["entities"],
            products_shown=product_ids,
            response=response
        )

        # Cache result
        self.cache.set(cache_key, result)

        return result

    def _merge_filters(
        self,
        nlp_filters: Dict,
        user_preferences: Dict
    ) -> Dict:
        """Merge NLP-extracted filters with user preferences."""
        merged = dict(nlp_filters)

        # If no category specified, use user's top category (optional)
        # This is disabled by default to give broader results
        # if not merged.get("category") and user_preferences.get("top_categories"):
        #     merged["category"] = user_preferences["top_categories"][0]

        # Use user's price range if not specified
        if not merged.get("max_price") and not merged.get("min_price"):
            price_range = user_preferences.get("preferred_price_range", {})
            if price_range.get("max") and price_range.get("max") < 100000:
                # Only apply if user has meaningful history
                pass  # Don't auto-apply for broader results

        return merged

    def _boost_by_features(
        self,
        recommendations: List[Dict],
        features: List[str]
    ) -> List[Dict]:
        """Boost products that match requested features."""
        if not features:
            return recommendations

        for rec in recommendations:
            description = rec.get("description", "").lower()
            name = rec.get("name", "").lower()

            # Count matching features
            match_count = sum(
                1 for feature in features
                if feature in description or feature in name
            )

            # Boost score based on feature matches
            rec["feature_matches"] = match_count
            rec["score"] = rec.get("score", 0) + (match_count * 0.1)

        # Re-sort by updated score
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations

    def _apply_sorting(
        self,
        recommendations: List[Dict],
        sort_order: Optional[str]
    ) -> List[Dict]:
        """Apply sorting to recommendations."""
        if not sort_order:
            return recommendations

        if sort_order == "price_asc":
            recommendations.sort(key=lambda x: x.get("price", float("inf")))
        elif sort_order == "price_desc":
            recommendations.sort(key=lambda x: x.get("price", 0), reverse=True)
        elif sort_order == "rating_desc":
            recommendations.sort(
                key=lambda x: x.get("rating") or 0,
                reverse=True
            )

        return recommendations

    def get_recommendations(
        self,
        user_id: str,
        top_n: int = None,
        filters: Dict = None
    ) -> List[Dict]:
        """Get recommendations without NLP processing."""
        if not self.is_initialized:
            self.initialize()

        top_n = top_n or MODEL_CONFIG["top_n_recommendations"]

        return self.recommender.recommend(
            user_id=user_id,
            interactions_df=self.interactions_df,
            top_n=top_n,
            filters=filters or {}
        )

    def get_similar_products(
        self,
        product_id: str,
        top_n: int = 10,
        same_category: bool = True,
        price_tolerance: float = 0.5  # 50% price tolerance
    ) -> Dict:
        """Get similar products with category and price analysis."""
        if not self.is_initialized:
            self.initialize()

        # Get the original product
        original_product = None
        for _, row in self.products_df.iterrows():
            if row["product_id"] == product_id:
                original_product = {
                    "product_id": row["product_id"],
                    "name": row["name"],
                    "category": row["category"],
                    "price": float(row["price"]),
                    "brand": row["brand"]
                }
                break

        if not original_product:
            return {"error": f"Product {product_id} not found"}

        # Get similar products
        similar = self.recommender.get_similar_products(product_id, top_n * 2)

        # Filter by category if requested
        if same_category:
            similar = [p for p in similar if p.get("category") == original_product["category"]]

        # Calculate price analysis
        price_min = original_product["price"] * (1 - price_tolerance)
        price_max = original_product["price"] * (1 + price_tolerance)

        # Categorize by price
        price_categories = {
            "cheaper": [],
            "similar_price": [],
            "expensive": []
        }

        for product in similar:
            price = product.get("price", 0)
            if price < price_min:
                price_categories["cheaper"].append(product)
            elif price > price_max:
                price_categories["expensive"].append(product)
            else:
                price_categories["similar_price"].append(product)

        # Sort within categories
        for category in price_categories:
            price_categories[category].sort(key=lambda x: abs(x.get("price", 0) - original_product["price"]))

        # Build result with analysis
        all_similar = price_categories["similar_price"] + price_categories["cheaper"] + price_categories["expensive"]

        return {
            "original_product": original_product,
            "similar_products": all_similar[:top_n],
            "price_analysis": {
                "original_price": original_product["price"],
                "price_range": {
                    "min": round(price_min, 2),
                    "max": round(price_max, 2)
                },
                "categories": {
                    "cheaper_count": len(price_categories["cheaper"]),
                    "similar_price_count": len(price_categories["similar_price"]),
                    "expensive_count": len(price_categories["expensive"])
                }
            },
            "same_category_filter_applied": same_category,
            "original_category": original_product["category"]
        }

    def record_interaction(
        self,
        user_id: str,
        product_id: str,
        action: str,
        rating: float = None
    ) -> Dict:
        """Record a user interaction."""
        if not self.is_initialized:
            self.initialize()

        # Update personalization engine
        result = self.personalization_engine.record_interaction(
            user_id=user_id,
            product_id=product_id,
            action=action,
            rating=rating
        )

        # Add to interactions dataframe
        new_interaction = pd.DataFrame([{
            "user_id": user_id,
            "product_id": product_id,
            "action": action,
            "rating": rating,
            "timestamp": datetime.now()
        }])

        self.interactions_df = pd.concat(
            [self.interactions_df, new_interaction],
            ignore_index=True
        )

        # Invalidate user's cache
        for key in list(self.cache.cache.keys()):
            if key.startswith(f"{user_id}:"):
                self.cache.invalidate(key)

        return result

    def get_user_preferences(self, user_id: str) -> Dict:
        """Get user preferences."""
        if not self.is_initialized:
            self.initialize()

        return self.personalization_engine.get_user_preferences(user_id)

    def update_user_preferences(
        self,
        user_id: str,
        preferences: Dict
    ) -> Dict:
        """Update user preferences."""
        if not self.is_initialized:
            self.initialize()

        return self.personalization_engine.import_profile(user_id, preferences)

    def get_products(
        self,
        category: str = None,
        brand: str = None,
        min_price: float = None,
        max_price: float = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get products with optional filtering."""
        if not self.is_initialized:
            self.initialize()

        filtered_df = self.products_df.copy()

        if category:
            filtered_df = filtered_df[
                filtered_df["category"].str.lower() == category.lower()
            ]

        if brand:
            filtered_df = filtered_df[
                filtered_df["brand"].str.lower() == brand.lower()
            ]

        if min_price:
            filtered_df = filtered_df[filtered_df["price"] >= min_price]

        if max_price:
            filtered_df = filtered_df[filtered_df["price"] <= max_price]

        # Return as list of dicts
        products = filtered_df.head(limit).to_dict("records")

        return [
            {
                "product_id": p["product_id"],
                "name": p["name"],
                "category": p["category"],
                "brand": p["brand"],
                "price": float(p["price"]),
                "rating": float(p["rating"]) if pd.notna(p.get("rating")) else None,
                "description": p["description"]
            }
            for p in products
        ]


# Singleton instance
_pipeline: Optional[RecommendationPipeline] = None


def get_pipeline() -> RecommendationPipeline:
    """Get or create singleton pipeline."""
    global _pipeline
    if _pipeline is None:
        _pipeline = RecommendationPipeline()
    return _pipeline


if __name__ == "__main__":
    # Test the pipeline
    pipeline = RecommendationPipeline()
    pipeline.initialize()

    # Get a test user
    test_user_id = pipeline.users_df["user_id"].iloc[0]

    # Test queries
    test_queries = [
        "I want a phone under 15000",
        "Show me Samsung laptops",
        "Find affordable shoes",
        "What are the best headphones under 5000 rupees?",
    ]

    print("\n" + "=" * 70)
    print("TESTING RECOMMENDATION PIPELINE")
    print("=" * 70)

    for query in test_queries:
        print(f"\n\nQuery: \"{query}\"")
        print("-" * 70)

        result = pipeline.process_query(
            user_id=test_user_id,
            query=query,
            top_n=5
        )

        print(f"Intent: {result['intent']} (confidence: {result['intent_confidence']:.2f})")
        print(f"Filters: {result['filters_applied']}")
        print(f"Response: {result['response']}")
        print(f"Latency: {result['latency_ms']:.2f}ms")

        print("\nTop Recommendations:")
        for i, rec in enumerate(result["recommendations"], 1):
            print(f"  {i}. {rec['name']}")
            print(f"     Category: {rec['category']} | Brand: {rec['brand']}")
            print(f"     Price: ₹{rec['price']:,.0f} | Rating: {rec.get('rating', 'N/A')}")
            print(f"     Score: {rec['score']:.4f}")

    # Test caching
    print("\n\n" + "=" * 70)
    print("TESTING CACHE")
    print("=" * 70)

    query = "I want a phone under 15000"
    result1 = pipeline.process_query(test_user_id, query)
    print(f"\nFirst query latency: {result1['latency_ms']:.2f}ms (cached: {result1['cached']})")

    result2 = pipeline.process_query(test_user_id, query)
    print(f"Second query latency: {result2['latency_ms']:.2f}ms (cached: {result2['cached']})")
