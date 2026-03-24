"""
Hybrid Recommendation System
Combines Collaborative Filtering and Content-Based Filtering
"""

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
from collections import defaultdict
import os


class CollaborativeFiltering:
    """User-Item Collaborative Filtering using Matrix Factorization"""

    def __init__(self, n_factors=50, learning_rate=0.01, regularization=0.02, n_epochs=20):
        self.n_factors = n_factors
        self.learning_rate = learning_rate
        self.regularization = regularization
        self.n_epochs = n_epochs
        self.user_factors = None
        self.item_factors = None
        self.user_to_idx = {}
        self.idx_to_user = {}
        self.item_to_idx = {}
        self.idx_to_item = {}
        self.global_mean = 0

    def fit(self, interactions_df, users_df, products_df):
        """Train the collaborative filtering model"""

        print("Training Collaborative Filtering model...")

        # Create user and item mappings
        users = interactions_df['user_id'].unique()
        items = interactions_df['product_id'].unique()

        self.user_to_idx = {user: idx for idx, user in enumerate(users)}
        self.idx_to_user = {idx: user for user, idx in self.user_to_idx.items()}
        self.item_to_idx = {item: idx for idx, item in enumerate(items)}
        self.idx_to_item = {idx: item for item, idx in self.item_to_idx.items()}

        n_users = len(users)
        n_items = len(items)

        # Create interaction matrix with implicit feedback
        # Weight different interaction types
        interaction_weights = {
            'purchase': 5.0,
            'add_to_cart': 4.0,
            'wishlist': 3.0,
            'click': 2.0,
            'view': 1.0,
            'search': 1.5
        }

        # Aggregate interactions
        user_item_scores = defaultdict(float)
        for _, row in interactions_df.iterrows():
            user_idx = self.user_to_idx.get(row['user_id'])
            item_idx = self.item_to_idx.get(row['product_id'])
            if user_idx is not None and item_idx is not None:
                weight = interaction_weights.get(row['interaction_type'], 1.0)
                user_item_scores[(user_idx, item_idx)] += weight

        # Convert to matrix format
        rows, cols, values = [], [], []
        for (user_idx, item_idx), score in user_item_scores.items():
            rows.append(user_idx)
            cols.append(item_idx)
            values.append(min(score, 10.0))  # Cap at 10

        interaction_matrix = csr_matrix(
            (values, (rows, cols)),
            shape=(n_users, n_items)
        ).toarray()

        self.global_mean = np.mean(values)

        # Initialize factor matrices
        self.user_factors = np.random.normal(0, 0.1, (n_users, self.n_factors))
        self.item_factors = np.random.normal(0, 0.1, (n_items, self.n_factors))

        # Train using SGD
        for epoch in range(self.n_epochs):
            total_error = 0
            n_samples = 0

            for user_idx in range(n_users):
                for item_idx in range(n_items):
                    if interaction_matrix[user_idx, item_idx] > 0:
                        prediction = np.dot(
                            self.user_factors[user_idx],
                            self.item_factors[item_idx]
                        )
                        error = interaction_matrix[user_idx, item_idx] - prediction

                        # Update factors
                        user_update = self.learning_rate * (
                            error * self.item_factors[item_idx] -
                            self.regularization * self.user_factors[user_idx]
                        )
                        item_update = self.learning_rate * (
                            error * self.user_factors[user_idx] -
                            self.regularization * self.item_factors[item_idx]
                        )

                        self.user_factors[user_idx] += user_update
                        self.item_factors[item_idx] += item_update

                        total_error += error ** 2
                        n_samples += 1

            rmse = np.sqrt(total_error / max(n_samples, 1))
            if (epoch + 1) % 5 == 0:
                print(f"  Epoch {epoch + 1}/{self.n_epochs}, RMSE: {rmse:.4f}")

        print("  Collaborative Filtering training complete!")

    def predict(self, user_id, product_id):
        """Predict score for a user-item pair"""
        if user_id not in self.user_to_idx or product_id not in self.item_to_idx:
            return self.global_mean

        user_idx = self.user_to_idx[user_id]
        item_idx = self.item_to_idx[product_id]

        score = np.dot(self.user_factors[user_idx], self.item_factors[item_idx])
        return max(0, min(10, score))  # Clip to valid range

    def get_similar_users(self, user_id, n=10):
        """Find similar users based on factor similarity"""
        if user_id not in self.user_to_idx:
            return []

        user_idx = self.user_to_idx[user_id]
        user_vector = self.user_factors[user_idx].reshape(1, -1)

        similarities = cosine_similarity(user_vector, self.user_factors)[0]
        similar_indices = np.argsort(similarities)[::-1][1:n+1]

        return [(self.idx_to_user[idx], similarities[idx]) for idx in similar_indices]

    def recommend_for_user(self, user_id, n=10, exclude_interacted=True, interacted_items=None):
        """Get top N recommendations for a user"""
        if user_id not in self.user_to_idx:
            return []

        user_idx = self.user_to_idx[user_id]
        scores = np.dot(self.user_factors[user_idx], self.item_factors.T)

        # Get all items with scores
        item_scores = [(self.idx_to_item[idx], scores[idx]) for idx in range(len(scores))]

        # Exclude already interacted items
        if exclude_interacted and interacted_items:
            item_scores = [(item, score) for item, score in item_scores
                          if item not in interacted_items]

        # Sort by score
        item_scores.sort(key=lambda x: x[1], reverse=True)

        return item_scores[:n]


class ContentBasedFiltering:
    """Content-Based Filtering using TF-IDF on product descriptions"""

    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = None
        self.products_df = None
        self.product_to_idx = {}
        self.idx_to_product = {}

    def fit(self, products_df):
        """Build TF-IDF matrix from product data"""
        print("Training Content-Based Filtering model...")

        self.products_df = products_df.copy()

        # Create combined text features
        self.products_df['combined_features'] = (
            self.products_df['name'].fillna('') + ' ' +
            self.products_df['category'].fillna('') + ' ' +
            self.products_df['subcategory'].fillna('') + ' ' +
            self.products_df['brand'].fillna('') + ' ' +
            self.products_df['description'].fillna('') + ' ' +
            self.products_df['tags'].fillna('').str.replace('|', ' ')
        )

        # Create mappings
        self.product_to_idx = {
            pid: idx for idx, pid in enumerate(self.products_df['product_id'])
        }
        self.idx_to_product = {idx: pid for pid, idx in self.product_to_idx.items()}

        # Build TF-IDF matrix
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(
            self.products_df['combined_features']
        )

        print(f"  TF-IDF matrix shape: {self.tfidf_matrix.shape}")
        print("  Content-Based Filtering training complete!")

    def get_similar_products(self, product_id, n=10):
        """Find similar products based on content similarity"""
        if product_id not in self.product_to_idx:
            return []

        idx = self.product_to_idx[product_id]
        product_vector = self.tfidf_matrix[idx]

        similarities = cosine_similarity(product_vector, self.tfidf_matrix)[0]
        similar_indices = np.argsort(similarities)[::-1][1:n+1]

        return [
            (self.idx_to_product[i], similarities[i])
            for i in similar_indices
        ]

    def recommend_by_category(self, category, n=10, max_price=None):
        """Recommend products in a specific category"""
        filtered = self.products_df[
            self.products_df['category'].str.lower() == category.lower()
        ]

        if max_price:
            filtered = filtered[filtered['price'] <= max_price]

        if len(filtered) == 0:
            # Try subcategory match
            filtered = self.products_df[
                self.products_df['subcategory'].str.lower() == category.lower()
            ]
            if max_price:
                filtered = filtered[filtered['price'] <= max_price]

        # Sort by rating and reviews
        filtered = filtered.sort_values(
            by=['rating', 'num_reviews'],
            ascending=[False, False]
        )

        return filtered.head(n)['product_id'].tolist()

    def recommend_by_query(self, query, n=10, max_price=None):
        """Recommend products based on a text query"""
        query_vector = self.tfidf_vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.tfidf_matrix)[0]

        # Get top matches
        top_indices = np.argsort(similarities)[::-1]

        results = []
        for idx in top_indices:
            if len(results) >= n:
                break

            product_id = self.idx_to_product[idx]
            product = self.products_df[
                self.products_df['product_id'] == product_id
            ].iloc[0]

            if max_price and product['price'] > max_price:
                continue

            results.append((product_id, similarities[idx]))

        return results


class HybridRecommender:
    """Hybrid Recommendation System combining CF and CB"""

    def __init__(self, cf_weight=0.6, cb_weight=0.4):
        self.cf_weight = cf_weight
        self.cb_weight = cb_weight
        self.cf_model = CollaborativeFiltering()
        self.cb_model = ContentBasedFiltering()
        self.users_df = None
        self.products_df = None
        self.interactions_df = None
        self.user_preferences = defaultdict(lambda: defaultdict(float))

    def fit(self, users_df, products_df, interactions_df):
        """Train both recommendation models"""
        print("\n" + "="*50)
        print("Training Hybrid Recommendation System")
        print("="*50 + "\n")

        self.users_df = users_df
        self.products_df = products_df
        self.interactions_df = interactions_df

        # Train models
        self.cf_model.fit(interactions_df, users_df, products_df)
        print()
        self.cb_model.fit(products_df)

        # Build user preference profiles
        self._build_user_preferences()

        print("\n" + "="*50)
        print("Hybrid Recommendation System ready!")
        print("="*50 + "\n")

    def _build_user_preferences(self):
        """Build user preference profiles from interactions"""
        print("\nBuilding user preference profiles...")

        for _, row in self.interactions_df.iterrows():
            user_id = row['user_id']
            product_id = row['product_id']

            # Get product info
            product_info = self.products_df[
                self.products_df['product_id'] == product_id
            ]
            if len(product_info) == 0:
                continue

            product = product_info.iloc[0]
            category = product['category']

            # Weight by interaction type
            weights = {
                'purchase': 5.0,
                'add_to_cart': 3.0,
                'wishlist': 2.5,
                'click': 1.5,
                'view': 1.0,
                'search': 2.0
            }
            weight = weights.get(row['interaction_type'], 1.0)

            self.user_preferences[user_id][category] += weight

        print(f"  Built profiles for {len(self.user_preferences)} users")

    def get_user_preferred_categories(self, user_id, n=3):
        """Get user's top preferred categories"""
        if user_id not in self.user_preferences:
            return []

        prefs = self.user_preferences[user_id]
        sorted_cats = sorted(prefs.items(), key=lambda x: x[1], reverse=True)
        return [cat for cat, _ in sorted_cats[:n]]

    def recommend(self, user_id, n=10, category=None, max_price=None):
        """Generate hybrid recommendations for a user"""

        # Get interacted items
        user_interactions = self.interactions_df[
            self.interactions_df['user_id'] == user_id
        ]['product_id'].tolist()

        recommendations = {}

        # Get CF recommendations
        cf_recs = self.cf_model.recommend_for_user(
            user_id, n=n*2, interacted_items=set(user_interactions)
        )
        for product_id, score in cf_recs:
            recommendations[product_id] = self.cf_weight * score

        # Get CB recommendations based on user's interacted items
        if user_interactions:
            # Use most recent interactions
            recent_items = user_interactions[-5:]
            for item in recent_items:
                similar = self.cb_model.get_similar_products(item, n=5)
                for product_id, score in similar:
                    if product_id not in user_interactions:
                        if product_id in recommendations:
                            recommendations[product_id] += self.cb_weight * score * 2
                        else:
                            recommendations[product_id] = self.cb_weight * score * 2

        # Filter by category if specified
        if category:
            category_products = set(
                self.products_df[
                    self.products_df['category'].str.lower() == category.lower()
                ]['product_id'].tolist()
            )
            recommendations = {
                k: v for k, v in recommendations.items()
                if k in category_products
            }

        # Filter by price if specified
        if max_price:
            price_filtered = set(
                self.products_df[
                    self.products_df['price'] <= max_price
                ]['product_id'].tolist()
            )
            recommendations = {
                k: v for k, v in recommendations.items()
                if k in price_filtered
            }

        # Sort and return top N
        sorted_recs = sorted(
            recommendations.items(),
            key=lambda x: x[1],
            reverse=True
        )[:n]

        # If not enough recommendations, add popular items
        if len(sorted_recs) < n:
            popular = self._get_popular_products(
                n=n - len(sorted_recs),
                exclude=set([r[0] for r in sorted_recs] + user_interactions),
                category=category,
                max_price=max_price
            )
            for pid in popular:
                sorted_recs.append((pid, 0.5))

        return sorted_recs

    def _get_popular_products(self, n=10, exclude=None, category=None, max_price=None):
        """Get popular products as fallback"""
        products = self.products_df.copy()

        if category:
            products = products[products['category'].str.lower() == category.lower()]

        if max_price:
            products = products[products['price'] <= max_price]

        if exclude:
            products = products[~products['product_id'].isin(exclude)]

        # Sort by rating and reviews
        products = products.sort_values(
            by=['rating', 'num_reviews'],
            ascending=[False, False]
        )

        return products.head(n)['product_id'].tolist()

    def search_products(self, query, n=10, max_price=None):
        """Search products using content-based filtering"""
        return self.cb_model.recommend_by_query(query, n=n, max_price=max_price)

    def update_interactions(self, user_id, product_id, interaction_type):
        """Update interactions data in real-time"""
        from datetime import datetime

        new_interaction = {
            'interaction_id': len(self.interactions_df) + 1,
            'user_id': user_id,
            'product_id': product_id,
            'interaction_type': interaction_type,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'rating': None,
            'session_id': f"S{np.random.randint(1, 10000):04d}",
            'device': 'web',
            'search_query': None
        }

        self.interactions_df = pd.concat([
            self.interactions_df,
            pd.DataFrame([new_interaction])
        ], ignore_index=True)

        # Update user preferences
        product_info = self.products_df[
            self.products_df['product_id'] == product_id
        ]
        if len(product_info) > 0:
            category = product_info.iloc[0]['category']
            weights = {
                'purchase': 5.0,
                'add_to_cart': 3.0,
                'click': 1.5,
                'view': 1.0
            }
            self.user_preferences[user_id][category] += weights.get(interaction_type, 1.0)

        return new_interaction

    def get_product_details(self, product_id):
        """Get product details by ID"""
        product = self.products_df[self.products_df['product_id'] == product_id]
        if len(product) == 0:
            return None
        return product.iloc[0].to_dict()

    def get_products_by_ids(self, product_ids):
        """Get multiple products by their IDs"""
        products = self.products_df[self.products_df['product_id'].isin(product_ids)]
        return products.to_dict('records')

    def save_interactions(self, filepath):
        """Save updated interactions to CSV"""
        self.interactions_df.to_csv(filepath, index=False)


if __name__ == '__main__':
    # Test the recommendation system
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    users_df = pd.read_csv(os.path.join(base_dir, 'data', 'users.csv'))
    products_df = pd.read_csv(os.path.join(base_dir, 'data', 'products.csv'))
    interactions_df = pd.read_csv(os.path.join(base_dir, 'data', 'interactions.csv'))

    # Initialize and train
    recommender = HybridRecommender()
    recommender.fit(users_df, products_df, interactions_df)

    # Test recommendations
    test_user = users_df.iloc[0]['user_id']
    print(f"\nRecommendations for {test_user}:")
    recs = recommender.recommend(test_user, n=5)
    for pid, score in recs:
        product = recommender.get_product_details(pid)
        print(f"  {product['name']} - ${product['price']:.2f} (score: {score:.2f})")
