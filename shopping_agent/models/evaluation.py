"""
Model Evaluation Module for Personal Shopping Agent.
Provides metrics for evaluating recommendation quality.
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import sys
sys.path.append(str(__file__).rsplit('/', 2)[0])

from utils.config import DATA_DIR, MODELS_DIR


class RecommenderEvaluator:
    """Evaluates recommendation model performance."""

    def __init__(self, interactions_df: pd.DataFrame, test_size: float = 0.2):
        self.interactions_df = interactions_df
        self.test_size = test_size
        self.train_df = None
        self.test_df = None
        self.user_actual_items: Dict[str, set] = {}

    def train_test_split(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Split interactions into train and test sets."""
        # Sort by timestamp to simulate temporal split
        self.interactions_df = self.interactions_df.sort_values("timestamp")

        # Use last X% of each user's interactions as test
        train_list = []
        test_list = []

        for user_id, user_df in self.interactions_df.groupby("user_id"):
            n_test = max(1, int(len(user_df) * self.test_size))
            user_train = user_df.iloc[:-n_test]
            user_test = user_df.iloc[-n_test:]

            train_list.append(user_train)
            test_list.append(user_test)

            # Store actual items for evaluation
            self.user_actual_items[user_id] = set(user_test["product_id"].unique())

        self.train_df = pd.concat(train_list, ignore_index=True)
        self.test_df = pd.concat(test_list, ignore_index=True)

        print(f"Train set: {len(self.train_df)} interactions")
        print(f"Test set: {len(self.test_df)} interactions")

        return self.train_df, self.test_df

    def precision_at_k(
        self,
        user_id: str,
        recommended_items: List[str],
        k: int = 10
    ) -> float:
        """Calculate Precision@K for a user."""
        if user_id not in self.user_actual_items:
            return 0.0

        actual = self.user_actual_items[user_id]
        recommended = set(recommended_items[:k])

        if not recommended:
            return 0.0

        hits = len(actual & recommended)
        return hits / k

    def recall_at_k(
        self,
        user_id: str,
        recommended_items: List[str],
        k: int = 10
    ) -> float:
        """Calculate Recall@K for a user."""
        if user_id not in self.user_actual_items:
            return 0.0

        actual = self.user_actual_items[user_id]
        recommended = set(recommended_items[:k])

        if not actual:
            return 0.0

        hits = len(actual & recommended)
        return hits / len(actual)

    def ndcg_at_k(
        self,
        user_id: str,
        recommended_items: List[str],
        k: int = 10
    ) -> float:
        """Calculate NDCG@K (Normalized Discounted Cumulative Gain)."""
        if user_id not in self.user_actual_items:
            return 0.0

        actual = self.user_actual_items[user_id]
        recommended = recommended_items[:k]

        # DCG
        dcg = 0.0
        for i, item in enumerate(recommended):
            if item in actual:
                dcg += 1.0 / np.log2(i + 2)  # +2 because index starts at 0

        # Ideal DCG
        ideal_hits = min(len(actual), k)
        idcg = sum(1.0 / np.log2(i + 2) for i in range(ideal_hits))

        if idcg == 0:
            return 0.0

        return dcg / idcg

    def map_at_k(
        self,
        user_id: str,
        recommended_items: List[str],
        k: int = 10
    ) -> float:
        """Calculate MAP@K (Mean Average Precision)."""
        if user_id not in self.user_actual_items:
            return 0.0

        actual = self.user_actual_items[user_id]
        recommended = recommended_items[:k]

        score = 0.0
        hits = 0

        for i, item in enumerate(recommended):
            if item in actual:
                hits += 1
                score += hits / (i + 1)

        if not actual:
            return 0.0

        return score / min(len(actual), k)

    def hit_rate(
        self,
        user_id: str,
        recommended_items: List[str],
        k: int = 10
    ) -> float:
        """Calculate Hit Rate (1 if any recommended item is relevant)."""
        if user_id not in self.user_actual_items:
            return 0.0

        actual = self.user_actual_items[user_id]
        recommended = set(recommended_items[:k])

        return 1.0 if actual & recommended else 0.0

    def coverage(
        self,
        all_recommendations: Dict[str, List[str]],
        all_products: List[str]
    ) -> float:
        """Calculate catalog coverage (% of products recommended)."""
        recommended_products = set()
        for items in all_recommendations.values():
            recommended_products.update(items)

        return len(recommended_products) / len(all_products) if all_products else 0.0

    def diversity(
        self,
        recommended_items: List[str],
        product_categories: Dict[str, str]
    ) -> float:
        """Calculate recommendation diversity (unique categories)."""
        if not recommended_items:
            return 0.0

        categories = set()
        for item in recommended_items:
            if item in product_categories:
                categories.add(product_categories[item])

        return len(categories) / len(recommended_items)

    def evaluate_model(
        self,
        recommender,
        users: List[str],
        k_values: List[int] = [5, 10, 20]
    ) -> Dict[str, Dict[int, float]]:
        """Evaluate model across all metrics and K values."""
        results = defaultdict(lambda: defaultdict(list))

        for user_id in users:
            if user_id not in self.user_actual_items:
                continue

            # Get recommendations
            try:
                recommendations = recommender.recommend(
                    user_id=user_id,
                    interactions_df=self.train_df,
                    top_n=max(k_values)
                )
                recommended_items = [r["product_id"] for r in recommendations]
            except Exception:
                continue

            for k in k_values:
                results["precision"][k].append(
                    self.precision_at_k(user_id, recommended_items, k)
                )
                results["recall"][k].append(
                    self.recall_at_k(user_id, recommended_items, k)
                )
                results["ndcg"][k].append(
                    self.ndcg_at_k(user_id, recommended_items, k)
                )
                results["map"][k].append(
                    self.map_at_k(user_id, recommended_items, k)
                )
                results["hit_rate"][k].append(
                    self.hit_rate(user_id, recommended_items, k)
                )

        # Average results
        averaged_results = {}
        for metric, k_dict in results.items():
            averaged_results[metric] = {}
            for k, values in k_dict.items():
                averaged_results[metric][k] = np.mean(values) if values else 0.0

        return averaged_results

    def rmse(
        self,
        actual_ratings: np.ndarray,
        predicted_ratings: np.ndarray
    ) -> float:
        """Calculate Root Mean Squared Error."""
        mask = actual_ratings > 0  # Only consider actual ratings
        if not mask.any():
            return 0.0

        diff = actual_ratings[mask] - predicted_ratings[mask]
        return np.sqrt(np.mean(diff ** 2))

    def mae(
        self,
        actual_ratings: np.ndarray,
        predicted_ratings: np.ndarray
    ) -> float:
        """Calculate Mean Absolute Error."""
        mask = actual_ratings > 0
        if not mask.any():
            return 0.0

        diff = np.abs(actual_ratings[mask] - predicted_ratings[mask])
        return np.mean(diff)


class HyperparameterTuner:
    """Tunes hyperparameters for recommendation models."""

    def __init__(self, param_grid: Dict[str, List]):
        self.param_grid = param_grid
        self.results = []

    def grid_search(
        self,
        model_class,
        train_data: Dict,
        evaluator: RecommenderEvaluator,
        test_users: List[str],
        k: int = 10,
        metric: str = "ndcg"
    ) -> Tuple[Dict, float]:
        """Perform grid search for hyperparameter tuning."""
        from itertools import product

        param_names = list(self.param_grid.keys())
        param_values = list(self.param_grid.values())

        best_params = None
        best_score = -1

        for values in product(*param_values):
            params = dict(zip(param_names, values))
            print(f"Testing params: {params}")

            # Train model with current params
            try:
                model = model_class(**params)
                model.fit(
                    interaction_matrix=train_data["interaction_matrix"],
                    product_embeddings=train_data["product_embeddings"],
                    users_df=train_data["users"],
                    products_df=train_data["products"],
                    interactions_df=train_data["interactions"]
                )

                # Evaluate
                results = evaluator.evaluate_model(model, test_users, k_values=[k])
                score = results[metric][k]

                self.results.append({
                    "params": params,
                    "score": score
                })

                print(f"  {metric}@{k}: {score:.4f}")

                if score > best_score:
                    best_score = score
                    best_params = params

            except Exception as e:
                print(f"  Error: {e}")
                continue

        return best_params, best_score

    def get_results_df(self) -> pd.DataFrame:
        """Get tuning results as DataFrame."""
        rows = []
        for result in self.results:
            row = dict(result["params"])
            row["score"] = result["score"]
            rows.append(row)
        return pd.DataFrame(rows)


def run_evaluation():
    """Run complete model evaluation."""
    from services.data_preprocessor import DataPreprocessor
    from models.recommender import HybridRecommender

    print("=" * 70)
    print("MODEL EVALUATION")
    print("=" * 70)

    # Load data
    print("\nLoading data...")
    preprocessor = DataPreprocessor()
    try:
        data = preprocessor.load_preprocessed_data()
    except FileNotFoundError:
        data = preprocessor.preprocess_all()

    interactions_df = pd.read_csv(DATA_DIR / "interactions_processed.csv")
    interactions_df["timestamp"] = pd.to_datetime(interactions_df["timestamp"])

    # Initialize evaluator
    print("\nSplitting data...")
    evaluator = RecommenderEvaluator(interactions_df, test_size=0.2)
    train_df, test_df = evaluator.train_test_split()

    # Train model on training data
    print("\nTraining model on training data...")
    recommender = HybridRecommender()
    recommender.fit(
        interaction_matrix=data["interaction_matrix"],
        product_embeddings=data["product_embeddings"],
        users_df=data["users"],
        products_df=data["products"],
        interactions_df=train_df
    )

    # Evaluate on test users
    test_users = list(evaluator.user_actual_items.keys())[:500]  # Sample for speed
    print(f"\nEvaluating on {len(test_users)} users...")

    results = evaluator.evaluate_model(
        recommender=recommender,
        users=test_users,
        k_values=[5, 10, 20]
    )

    # Print results
    print("\n" + "=" * 70)
    print("EVALUATION RESULTS")
    print("=" * 70)

    for metric, k_scores in results.items():
        print(f"\n{metric.upper()}:")
        for k, score in k_scores.items():
            print(f"  @{k}: {score:.4f}")

    # Calculate catalog coverage
    all_recommendations = {}
    for user_id in test_users[:100]:
        try:
            recs = recommender.recommend(user_id, train_df, top_n=10)
            all_recommendations[user_id] = [r["product_id"] for r in recs]
        except Exception:
            continue

    all_products = data["products"]["product_id"].tolist()
    coverage = evaluator.coverage(all_recommendations, all_products)
    print(f"\nCatalog Coverage: {coverage:.4f}")

    # Calculate diversity
    product_categories = dict(zip(
        data["products"]["product_id"],
        data["products"]["category"]
    ))

    diversities = []
    for items in all_recommendations.values():
        diversities.append(evaluator.diversity(items, product_categories))

    avg_diversity = np.mean(diversities) if diversities else 0
    print(f"Average Diversity: {avg_diversity:.4f}")

    return results


if __name__ == "__main__":
    results = run_evaluation()
