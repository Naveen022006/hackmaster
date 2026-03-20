"""
Hybrid Recommendation Engine for Personal Shopping Agent.
Combines Collaborative Filtering (SVD) and Content-Based Filtering.
"""
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds
from typing import List, Dict, Optional, Tuple
import pickle
import sys
sys.path.append(str(__file__).rsplit('/', 2)[0])

from utils.config import MODEL_CONFIG, MODELS_DIR, DATA_DIR


class CollaborativeFilteringModel:
    """Matrix Factorization using SVD for collaborative filtering."""

    def __init__(self, n_factors: int = None):
        self.n_factors = n_factors or MODEL_CONFIG["svd_n_factors"]
        self.user_factors = None
        self.item_factors = None
        self.sigma = None
        self.user_means = None
        self.global_mean = None
        self.is_fitted = False

    def fit(self, interaction_matrix: csr_matrix):
        """Fit SVD model to interaction matrix."""
        # Convert to dense for SVD (for smaller datasets)
        # For production, use implicit ALS or incremental SVD
        matrix = interaction_matrix.toarray().astype(float)

        # Calculate means for bias correction
        self.global_mean = np.mean(matrix[matrix > 0])
        self.user_means = np.zeros(matrix.shape[0])

        for i in range(matrix.shape[0]):
            user_interactions = matrix[i, matrix[i, :] > 0]
            if len(user_interactions) > 0:
                self.user_means[i] = np.mean(user_interactions)
            else:
                self.user_means[i] = self.global_mean

        # Center the matrix
        matrix_centered = matrix.copy()
        for i in range(matrix.shape[0]):
            mask = matrix[i, :] > 0
            matrix_centered[i, mask] -= self.user_means[i]

        # Perform SVD
        n_factors = min(self.n_factors, min(matrix.shape) - 1)
        U, sigma, Vt = svds(csr_matrix(matrix_centered), k=n_factors)

        # Store factors
        self.user_factors = U
        self.sigma = sigma
        self.item_factors = Vt.T

        self.is_fitted = True
        return self

    def predict(self, user_idx: int, item_indices: np.ndarray = None) -> np.ndarray:
        """Predict ratings for a user."""
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        if user_idx >= len(self.user_factors):
            # Cold start user - return zeros
            if item_indices is not None:
                return np.zeros(len(item_indices))
            return np.zeros(self.item_factors.shape[0])

        # Calculate predicted ratings
        user_vector = self.user_factors[user_idx]
        predictions = user_vector @ np.diag(self.sigma) @ self.item_factors.T

        # Add user bias back
        predictions += self.user_means[user_idx]

        if item_indices is not None:
            return predictions[item_indices]
        return predictions

    def get_similar_users(self, user_idx: int, top_n: int = 10) -> List[int]:
        """Find similar users based on latent factors."""
        if not self.is_fitted or user_idx >= len(self.user_factors):
            return []

        user_vector = self.user_factors[user_idx].reshape(1, -1)
        similarities = cosine_similarity(user_vector, self.user_factors)[0]

        # Exclude self and get top N
        similar_indices = np.argsort(similarities)[::-1][1:top_n+1]
        return similar_indices.tolist()


class ContentBasedModel:
    """Content-based filtering using TF-IDF embeddings."""

    def __init__(self):
        self.product_embeddings = None
        self.similarity_matrix = None
        self.is_fitted = False

    def fit(self, product_embeddings: np.ndarray):
        """Fit content-based model with product embeddings."""
        self.product_embeddings = product_embeddings

        # Precompute similarity matrix
        self.similarity_matrix = cosine_similarity(product_embeddings)

        self.is_fitted = True
        return self

    def get_similar_products(
        self,
        product_idx: int,
        top_n: int = 10,
        exclude_indices: List[int] = None
    ) -> List[Tuple[int, float]]:
        """Get similar products based on content similarity."""
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        if product_idx >= len(self.similarity_matrix):
            return []

        similarities = self.similarity_matrix[product_idx]

        # Create mask for exclusions
        mask = np.ones(len(similarities), dtype=bool)
        mask[product_idx] = False  # Exclude self
        if exclude_indices:
            mask[exclude_indices] = False

        # Get top N indices
        valid_indices = np.where(mask)[0]
        valid_similarities = similarities[valid_indices]
        top_indices = np.argsort(valid_similarities)[::-1][:top_n]

        return [
            (valid_indices[i], valid_similarities[i])
            for i in top_indices
        ]

    def recommend_from_history(
        self,
        product_indices: List[int],
        top_n: int = 10,
        weights: List[float] = None
    ) -> List[Tuple[int, float]]:
        """Recommend products based on user's interaction history."""
        if not self.is_fitted or not product_indices:
            return []

        # Calculate weighted average of embeddings
        if weights is None:
            weights = [1.0] * len(product_indices)

        weights = np.array(weights) / sum(weights)

        user_profile = np.zeros(self.product_embeddings.shape[1])
        for idx, weight in zip(product_indices, weights):
            if idx < len(self.product_embeddings):
                user_profile += weight * self.product_embeddings[idx]

        # Calculate similarity to all products
        similarities = cosine_similarity(
            user_profile.reshape(1, -1),
            self.product_embeddings
        )[0]

        # Exclude already interacted products
        mask = np.ones(len(similarities), dtype=bool)
        mask[product_indices] = False

        valid_indices = np.where(mask)[0]
        valid_similarities = similarities[valid_indices]
        top_indices = np.argsort(valid_similarities)[::-1][:top_n]

        return [
            (valid_indices[i], valid_similarities[i])
            for i in top_indices
        ]


class HybridRecommender:
    """Hybrid recommendation system combining CF and content-based approaches."""

    def __init__(
        self,
        cf_weight: float = None,
        content_weight: float = None
    ):
        self.cf_weight = cf_weight or MODEL_CONFIG["collaborative_weight"]
        self.content_weight = content_weight or MODEL_CONFIG["content_weight"]

        self.cf_model = CollaborativeFilteringModel()
        self.content_model = ContentBasedModel()

        self.popular_products: List[int] = []
        self.products_df: Optional[pd.DataFrame] = None
        self.users_df: Optional[pd.DataFrame] = None
        self.user_id_to_idx: Dict[str, int] = {}
        self.product_id_to_idx: Dict[str, int] = {}
        self.idx_to_product_id: Dict[int, str] = {}
        self.is_fitted = False

    def fit(
        self,
        interaction_matrix: csr_matrix,
        product_embeddings: np.ndarray,
        users_df: pd.DataFrame,
        products_df: pd.DataFrame,
        interactions_df: pd.DataFrame
    ):
        """Fit both models."""
        print("Fitting collaborative filtering model...")
        self.cf_model.fit(interaction_matrix)

        print("Fitting content-based model...")
        self.content_model.fit(product_embeddings)

        # Store reference data
        self.products_df = products_df
        self.users_df = users_df

        # Create ID mappings
        self.user_id_to_idx = dict(zip(users_df["user_id"], users_df["user_idx"]))
        self.product_id_to_idx = dict(zip(products_df["product_id"], products_df["product_idx"]))
        self.idx_to_product_id = {v: k for k, v in self.product_id_to_idx.items()}

        # Calculate popular products (fallback for cold start)
        self._calculate_popular_products(interactions_df, products_df)

        self.is_fitted = True
        print("Hybrid recommender fitted successfully!")
        return self

    def _calculate_popular_products(
        self,
        interactions_df: pd.DataFrame,
        products_df: pd.DataFrame,
        top_n: int = 100
    ):
        """Calculate popular products for cold-start fallback."""
        # Popularity score = purchase_count * avg_rating
        product_scores = interactions_df[
            interactions_df["action"] == "purchase"
        ].groupby("product_id").size().reset_index(name="purchase_count")

        product_scores = product_scores.merge(
            products_df[["product_id", "rating", "product_idx"]],
            on="product_id"
        )

        product_scores["popularity_score"] = (
            product_scores["purchase_count"] *
            product_scores["rating"].fillna(3.5)
        )

        product_scores = product_scores.sort_values(
            "popularity_score", ascending=False
        )

        self.popular_products = product_scores["product_idx"].head(top_n).tolist()

    def get_user_history(
        self,
        user_id: str,
        interactions_df: pd.DataFrame
    ) -> List[int]:
        """Get user's interaction history as product indices."""
        user_interactions = interactions_df[
            interactions_df["user_id"] == user_id
        ]

        product_ids = user_interactions["product_id"].unique()
        product_indices = [
            self.product_id_to_idx[pid]
            for pid in product_ids
            if pid in self.product_id_to_idx
        ]

        return product_indices

    def recommend(
        self,
        user_id: str,
        interactions_df: pd.DataFrame,
        top_n: int = None,
        filters: Dict = None
    ) -> List[Dict]:
        """Generate hybrid recommendations for a user."""
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        top_n = top_n or MODEL_CONFIG["top_n_recommendations"]

        # Get user index
        user_idx = self.user_id_to_idx.get(user_id)
        user_history = self.get_user_history(user_id, interactions_df)

        # Check for cold-start user
        is_cold_start = (
            user_idx is None or
            len(user_history) < MODEL_CONFIG["min_interactions_for_cf"]
        )

        if is_cold_start:
            return self._cold_start_recommendations(
                user_history, top_n, filters
            )

        # Get CF predictions
        cf_scores = self.cf_model.predict(user_idx)

        # Get content-based scores
        if user_history:
            content_recs = self.content_model.recommend_from_history(
                user_history, top_n=len(cf_scores)
            )
            content_scores = np.zeros(len(cf_scores))
            for idx, score in content_recs:
                content_scores[idx] = score
        else:
            content_scores = np.zeros(len(cf_scores))

        # Normalize scores
        cf_scores_norm = self._normalize_scores(cf_scores)
        content_scores_norm = self._normalize_scores(content_scores)

        # Combine scores
        hybrid_scores = (
            self.cf_weight * cf_scores_norm +
            self.content_weight * content_scores_norm
        )

        # Exclude already interacted products
        hybrid_scores[user_history] = -np.inf

        # Apply filters if provided
        if filters:
            hybrid_scores = self._apply_filters(hybrid_scores, filters)

        # Get top N recommendations
        top_indices = np.argsort(hybrid_scores)[::-1][:top_n]

        return self._format_recommendations(top_indices, hybrid_scores)

    def _cold_start_recommendations(
        self,
        user_history: List[int],
        top_n: int,
        filters: Dict = None
    ) -> List[Dict]:
        """Handle cold-start users with popular items or content-based."""
        if user_history:
            # Use content-based from limited history
            content_recs = self.content_model.recommend_from_history(
                user_history, top_n=top_n * 2
            )
            scores = np.zeros(len(self.products_df))
            for idx, score in content_recs:
                scores[idx] = score

            if filters:
                scores = self._apply_filters(scores, filters)

            scores[user_history] = -np.inf
            top_indices = np.argsort(scores)[::-1][:top_n]
        else:
            # Pure cold start - use popular items
            scores = np.zeros(len(self.products_df))
            for i, idx in enumerate(self.popular_products):
                scores[idx] = len(self.popular_products) - i

            if filters:
                scores = self._apply_filters(scores, filters)

            top_indices = np.argsort(scores)[::-1][:top_n]

        return self._format_recommendations(top_indices, scores)

    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """Normalize scores to [0, 1] range."""
        min_score = np.min(scores[scores > -np.inf])
        max_score = np.max(scores[scores < np.inf])

        if max_score == min_score:
            return np.zeros_like(scores)

        normalized = (scores - min_score) / (max_score - min_score + 1e-10)
        normalized[scores == -np.inf] = -np.inf
        return normalized

    def _apply_filters(
        self,
        scores: np.ndarray,
        filters: Dict
    ) -> np.ndarray:
        """Apply filters (category, price, brand) to scores."""
        for idx, row in self.products_df.iterrows():
            product_idx = row.get("product_idx", idx)

            # Category filter
            if "category" in filters and filters["category"]:
                if row["category"].lower() != filters["category"].lower():
                    scores[product_idx] = -np.inf

            # Price filter
            if "max_price" in filters and filters["max_price"]:
                if row["price"] > filters["max_price"]:
                    scores[product_idx] = -np.inf

            if "min_price" in filters and filters["min_price"]:
                if row["price"] < filters["min_price"]:
                    scores[product_idx] = -np.inf

            # Brand filter
            if "brand" in filters and filters["brand"]:
                if row["brand"].lower() != filters["brand"].lower():
                    scores[product_idx] = -np.inf

            # Minimum rating filter
            if "min_rating" in filters and filters["min_rating"]:
                if pd.notna(row["rating"]) and row["rating"] < filters["min_rating"]:
                    scores[product_idx] = -np.inf

        return scores

    def _format_recommendations(
        self,
        product_indices: np.ndarray,
        scores: np.ndarray
    ) -> List[Dict]:
        """Format recommendations as list of product dictionaries."""
        recommendations = []

        for idx in product_indices:
            if scores[idx] == -np.inf:
                continue

            product_id = self.idx_to_product_id.get(idx)
            if product_id is None:
                continue

            product_row = self.products_df[
                self.products_df["product_id"] == product_id
            ].iloc[0]

            recommendations.append({
                "product_id": product_id,
                "name": product_row["name"],
                "category": product_row["category"],
                "brand": product_row["brand"],
                "price": float(product_row["price"]),
                "rating": float(product_row["rating"]) if pd.notna(product_row["rating"]) else None,
                "description": product_row["description"],
                "score": float(scores[idx]) if scores[idx] != -np.inf else 0.0
            })

        return recommendations

    def get_similar_products(
        self,
        product_id: str,
        top_n: int = 10
    ) -> List[Dict]:
        """Get products similar to a given product."""
        product_idx = self.product_id_to_idx.get(product_id)
        if product_idx is None:
            return []

        similar = self.content_model.get_similar_products(product_idx, top_n)

        scores = np.zeros(len(self.products_df))
        for idx, score in similar:
            scores[idx] = score

        indices = [idx for idx, _ in similar]
        return self._format_recommendations(np.array(indices), scores)

    def save(self, path: str = None):
        """Save model to disk."""
        path = path or str(MODELS_DIR / "hybrid_recommender.pkl")
        with open(path, "wb") as f:
            pickle.dump(self, f)
        print(f"Model saved to {path}")

    @staticmethod
    def load(path: str = None) -> "HybridRecommender":
        """Load model from disk."""
        path = path or str(MODELS_DIR / "hybrid_recommender.pkl")
        with open(path, "rb") as f:
            return pickle.load(f)


if __name__ == "__main__":
    from services.data_preprocessor import DataPreprocessor

    # Load preprocessed data
    preprocessor = DataPreprocessor()

    try:
        data = preprocessor.load_preprocessed_data()
        print("Loaded preprocessed data from disk.")
    except FileNotFoundError:
        print("Preprocessed data not found. Running preprocessing...")
        data = preprocessor.preprocess_all()

    # Load interactions
    interactions_df = pd.read_csv(DATA_DIR / "interactions_processed.csv")
    interactions_df["timestamp"] = pd.to_datetime(interactions_df["timestamp"])

    # Initialize and fit hybrid recommender
    recommender = HybridRecommender()
    recommender.fit(
        interaction_matrix=data["interaction_matrix"],
        product_embeddings=data["product_embeddings"],
        users_df=data["users"],
        products_df=data["products"],
        interactions_df=interactions_df
    )

    # Test recommendations
    test_user_id = data["users"]["user_id"].iloc[0]
    print(f"\nRecommendations for user {test_user_id}:")
    recommendations = recommender.recommend(
        user_id=test_user_id,
        interactions_df=interactions_df,
        top_n=5
    )

    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['name']} ({rec['category']}) - Rs.{rec['price']:.0f} - Score: {rec['score']:.4f}")

    # Test with filters
    print("\nRecommendations with filters (Electronics, max Rs.20000):")
    filtered_recs = recommender.recommend(
        user_id=test_user_id,
        interactions_df=interactions_df,
        top_n=5,
        filters={"category": "Electronics", "max_price": 20000}
    )

    for i, rec in enumerate(filtered_recs, 1):
        print(f"{i}. {rec['name']} - Rs.{rec['price']:.0f}")

    # Save model
    recommender.save()
    print("\nModel saved successfully!")
