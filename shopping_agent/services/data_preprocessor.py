"""
Data Preprocessing Pipeline for Personal Shopping Agent.
Handles data cleaning, feature engineering, and embedding generation.
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler, MinMaxScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import csr_matrix
import json
from datetime import datetime
from typing import Dict, Tuple, Optional
import pickle
import sys
sys.path.append(str(__file__).rsplit('/', 2)[0])

from utils.config import DATA_DIR, MODELS_DIR, MODEL_CONFIG


class DataPreprocessor:
    """Handles all data preprocessing and feature engineering."""

    def __init__(self):
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None
        self.user_encoder: Optional[LabelEncoder] = None
        self.product_encoder: Optional[LabelEncoder] = None

    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Load all datasets."""
        users_df = pd.read_csv(DATA_DIR / "users.csv")
        products_df = pd.read_csv(DATA_DIR / "products.csv")
        interactions_df = pd.read_csv(DATA_DIR / "interactions.csv")
        return users_df, products_df, interactions_df

    def clean_users(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean users dataset."""
        df = df.copy()

        # Handle missing ages - impute with median
        median_age = df["age"].median()
        df["age"] = df["age"].fillna(median_age).astype(int)

        # Ensure age is within valid range
        df["age"] = df["age"].clip(18, 80)

        # Parse preferences JSON
        df["preferences_parsed"] = df["preferences"].apply(
            lambda x: json.loads(x) if isinstance(x, str) else {}
        )

        return df

    def clean_products(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean products dataset."""
        df = df.copy()

        # Handle missing ratings - impute with category mean
        category_mean_rating = df.groupby("category")["rating"].transform("mean")
        df["rating"] = df["rating"].fillna(category_mean_rating)

        # Fill any remaining NaN ratings with global mean
        df["rating"] = df["rating"].fillna(df["rating"].mean())

        # Ensure price is valid
        df["price"] = df["price"].clip(1, 500000)

        # Clean text fields
        df["name"] = df["name"].str.strip()
        df["description"] = df["description"].str.strip()

        return df

    def clean_interactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean interactions dataset."""
        df = df.copy()

        # Convert timestamp to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Handle missing ratings
        df["rating"] = df["rating"].fillna(0)  # 0 means no rating

        # Remove duplicate interactions (same user, product, action within 1 minute)
        df = df.sort_values("timestamp")
        df["time_diff"] = df.groupby(["user_id", "product_id", "action"])["timestamp"].diff()
        df = df[
            (df["time_diff"].isna()) |
            (df["time_diff"] > pd.Timedelta(minutes=1))
        ]
        df = df.drop(columns=["time_diff"])

        return df.reset_index(drop=True)

    def encode_categorical_features(
        self,
        users_df: pd.DataFrame,
        products_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Encode categorical features."""
        users_df = users_df.copy()
        products_df = products_df.copy()

        # Encode user features
        for col in ["gender", "location"]:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                users_df[f"{col}_encoded"] = self.label_encoders[col].fit_transform(users_df[col])
            else:
                users_df[f"{col}_encoded"] = self.label_encoders[col].transform(users_df[col])

        # Encode product features
        for col in ["category", "brand"]:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                products_df[f"{col}_encoded"] = self.label_encoders[col].fit_transform(products_df[col])
            else:
                products_df[f"{col}_encoded"] = self.label_encoders[col].transform(products_df[col])

        # Encode user and product IDs
        self.user_encoder = LabelEncoder()
        users_df["user_idx"] = self.user_encoder.fit_transform(users_df["user_id"])

        self.product_encoder = LabelEncoder()
        products_df["product_idx"] = self.product_encoder.fit_transform(products_df["product_id"])

        return users_df, products_df

    def normalize_features(
        self,
        users_df: pd.DataFrame,
        products_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Normalize numerical features."""
        users_df = users_df.copy()
        products_df = products_df.copy()

        # Normalize user age
        self.scalers["age"] = MinMaxScaler()
        users_df["age_normalized"] = self.scalers["age"].fit_transform(
            users_df[["age"]]
        )

        # Normalize product price (log transform first for better distribution)
        products_df["log_price"] = np.log1p(products_df["price"])
        self.scalers["price"] = MinMaxScaler()
        products_df["price_normalized"] = self.scalers["price"].fit_transform(
            products_df[["log_price"]]
        )

        # Normalize product rating
        self.scalers["rating"] = MinMaxScaler()
        products_df["rating_normalized"] = self.scalers["rating"].fit_transform(
            products_df[["rating"]]
        )

        return users_df, products_df

    def create_user_features(
        self,
        users_df: pd.DataFrame,
        interactions_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Create user-level features from interactions."""
        users_df = users_df.copy()

        # Calculate interaction statistics per user
        user_stats = interactions_df.groupby("user_id").agg({
            "product_id": "count",
            "rating": lambda x: x[x > 0].mean() if (x > 0).any() else 0,
            "timestamp": ["min", "max"]
        }).reset_index()

        user_stats.columns = [
            "user_id", "total_interactions", "avg_rating_given",
            "first_interaction", "last_interaction"
        ]

        # Calculate action-specific counts
        action_counts = interactions_df.pivot_table(
            index="user_id",
            columns="action",
            aggfunc="size",
            fill_value=0
        ).reset_index()

        # Calculate conversion rate
        action_counts["conversion_rate"] = (
            action_counts.get("purchase", 0) /
            (action_counts.get("view", 1) + 0.001)
        ).clip(0, 1)

        # Merge features
        users_df = users_df.merge(user_stats, on="user_id", how="left")
        users_df = users_df.merge(action_counts, on="user_id", how="left")

        # Fill NaN for users with no interactions
        fill_cols = ["total_interactions", "avg_rating_given", "conversion_rate"]
        for col in fill_cols:
            if col in users_df.columns:
                users_df[col] = users_df[col].fillna(0)

        return users_df

    def create_product_features(
        self,
        products_df: pd.DataFrame,
        interactions_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Create product-level features from interactions."""
        products_df = products_df.copy()

        # Calculate product popularity
        product_stats = interactions_df.groupby("product_id").agg({
            "user_id": "nunique",
            "action": "count",
            "rating": lambda x: x[x > 0].mean() if (x > 0).any() else 0
        }).reset_index()

        product_stats.columns = [
            "product_id", "unique_users", "total_interactions", "avg_user_rating"
        ]

        # Calculate purchase rate
        purchase_counts = interactions_df[
            interactions_df["action"] == "purchase"
        ].groupby("product_id").size().reset_index(name="purchase_count")

        product_stats = product_stats.merge(purchase_counts, on="product_id", how="left")
        product_stats["purchase_count"] = product_stats["purchase_count"].fillna(0)
        product_stats["purchase_rate"] = (
            product_stats["purchase_count"] /
            (product_stats["total_interactions"] + 0.001)
        ).clip(0, 1)

        # Merge features
        products_df = products_df.merge(product_stats, on="product_id", how="left")

        # Fill NaN for products with no interactions
        fill_cols = ["unique_users", "total_interactions", "avg_user_rating", "purchase_rate"]
        for col in fill_cols:
            if col in products_df.columns:
                products_df[col] = products_df[col].fillna(0)

        return products_df

    def create_product_embeddings(self, products_df: pd.DataFrame) -> np.ndarray:
        """Create TF-IDF embeddings from product descriptions."""
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=MODEL_CONFIG["embedding_dim"],
            stop_words="english",
            ngram_range=(1, 2)
        )

        # Combine name and description for richer text
        text_data = (
            products_df["name"].fillna("") + " " +
            products_df["description"].fillna("") + " " +
            products_df["category"].fillna("") + " " +
            products_df["brand"].fillna("")
        )

        tfidf_matrix = self.tfidf_vectorizer.fit_transform(text_data)
        return tfidf_matrix.toarray()

    def create_interaction_matrix(
        self,
        interactions_df: pd.DataFrame,
        users_df: pd.DataFrame,
        products_df: pd.DataFrame
    ) -> csr_matrix:
        """Create user-item interaction matrix with action weights."""
        # Action weights for implicit feedback
        action_weights = {
            "view": 1.0,
            "click": 2.0,
            "add_to_cart": 3.0,
            "purchase": 5.0
        }

        # Map IDs to indices
        user_id_to_idx = dict(zip(users_df["user_id"], users_df["user_idx"]))
        product_id_to_idx = dict(zip(products_df["product_id"], products_df["product_idx"]))

        # Calculate recency weight
        interactions_df = interactions_df.copy()
        max_timestamp = interactions_df["timestamp"].max()
        interactions_df["days_ago"] = (max_timestamp - interactions_df["timestamp"]).dt.days
        interactions_df["recency_weight"] = np.exp(-interactions_df["days_ago"] / 30)

        # Create weighted interactions
        interactions_df["weight"] = (
            interactions_df["action"].map(action_weights) *
            interactions_df["recency_weight"]
        )

        # Aggregate weights per user-product pair
        aggregated = interactions_df.groupby(["user_id", "product_id"])["weight"].sum().reset_index()

        # Map to indices
        aggregated["user_idx"] = aggregated["user_id"].map(user_id_to_idx)
        aggregated["product_idx"] = aggregated["product_id"].map(product_id_to_idx)

        # Remove any rows with missing indices
        aggregated = aggregated.dropna(subset=["user_idx", "product_idx"])

        # Create sparse matrix
        n_users = len(users_df)
        n_products = len(products_df)

        interaction_matrix = csr_matrix(
            (
                aggregated["weight"].values,
                (
                    aggregated["user_idx"].astype(int).values,
                    aggregated["product_idx"].astype(int).values
                )
            ),
            shape=(n_users, n_products)
        )

        return interaction_matrix

    def calculate_interaction_frequency(
        self,
        interactions_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Calculate interaction frequency features."""
        # User interaction frequency
        user_freq = interactions_df.groupby("user_id").agg({
            "timestamp": lambda x: (x.max() - x.min()).days + 1,
            "product_id": "count"
        }).reset_index()
        user_freq.columns = ["user_id", "active_days", "interaction_count"]
        user_freq["interactions_per_day"] = (
            user_freq["interaction_count"] / (user_freq["active_days"] + 1)
        )

        return user_freq

    def preprocess_all(self) -> Dict:
        """Run complete preprocessing pipeline."""
        print("Loading data...")
        users_df, products_df, interactions_df = self.load_data()

        print("Cleaning data...")
        users_df = self.clean_users(users_df)
        products_df = self.clean_products(products_df)
        interactions_df = self.clean_interactions(interactions_df)

        print("Encoding categorical features...")
        users_df, products_df = self.encode_categorical_features(users_df, products_df)

        print("Normalizing features...")
        users_df, products_df = self.normalize_features(users_df, products_df)

        print("Creating user features...")
        users_df = self.create_user_features(users_df, interactions_df)

        print("Creating product features...")
        products_df = self.create_product_features(products_df, interactions_df)

        print("Creating product embeddings...")
        product_embeddings = self.create_product_embeddings(products_df)

        print("Creating interaction matrix...")
        interaction_matrix = self.create_interaction_matrix(
            interactions_df, users_df, products_df
        )

        print("Calculating interaction frequency...")
        user_frequency = self.calculate_interaction_frequency(interactions_df)

        # Prepare output
        preprocessed_data = {
            "users": users_df,
            "products": products_df,
            "interactions": interactions_df,
            "product_embeddings": product_embeddings,
            "interaction_matrix": interaction_matrix,
            "user_frequency": user_frequency,
            "encoders": {
                "label_encoders": self.label_encoders,
                "user_encoder": self.user_encoder,
                "product_encoder": self.product_encoder,
                "tfidf_vectorizer": self.tfidf_vectorizer,
                "scalers": self.scalers
            }
        }

        # Save preprocessed data
        self.save_preprocessed_data(preprocessed_data)

        print("Preprocessing complete!")
        return preprocessed_data

    def save_preprocessed_data(self, data: Dict):
        """Save preprocessed data to disk."""
        # Save DataFrames
        data["users"].to_csv(DATA_DIR / "users_processed.csv", index=False)
        data["products"].to_csv(DATA_DIR / "products_processed.csv", index=False)
        data["interactions"].to_csv(DATA_DIR / "interactions_processed.csv", index=False)

        # Save numpy arrays and sparse matrices
        np.save(DATA_DIR / "product_embeddings.npy", data["product_embeddings"])

        from scipy.sparse import save_npz
        save_npz(DATA_DIR / "interaction_matrix.npz", data["interaction_matrix"])

        # Save encoders
        with open(MODELS_DIR / "encoders.pkl", "wb") as f:
            pickle.dump(data["encoders"], f)

        print(f"Preprocessed data saved to {DATA_DIR}")

    def load_preprocessed_data(self) -> Dict:
        """Load preprocessed data from disk."""
        from scipy.sparse import load_npz

        users_df = pd.read_csv(DATA_DIR / "users_processed.csv")
        products_df = pd.read_csv(DATA_DIR / "products_processed.csv")
        interactions_df = pd.read_csv(DATA_DIR / "interactions_processed.csv")

        product_embeddings = np.load(DATA_DIR / "product_embeddings.npy")
        interaction_matrix = load_npz(DATA_DIR / "interaction_matrix.npz")

        with open(MODELS_DIR / "encoders.pkl", "rb") as f:
            encoders = pickle.load(f)

        return {
            "users": users_df,
            "products": products_df,
            "interactions": interactions_df,
            "product_embeddings": product_embeddings,
            "interaction_matrix": interaction_matrix,
            "encoders": encoders
        }


if __name__ == "__main__":
    preprocessor = DataPreprocessor()
    data = preprocessor.preprocess_all()

    print("\n--- Preprocessed Users ---")
    print(data["users"].head())
    print(f"\nUser features: {data['users'].columns.tolist()}")

    print("\n--- Preprocessed Products ---")
    print(data["products"].head())
    print(f"\nProduct features: {data['products'].columns.tolist()}")

    print("\n--- Interaction Matrix Shape ---")
    print(data["interaction_matrix"].shape)

    print("\n--- Product Embeddings Shape ---")
    print(data["product_embeddings"].shape)
