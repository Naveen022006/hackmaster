"""
User Session Manager
Handles real-time tracking of user behavior and dynamic recommendation updates
"""

import threading
from datetime import datetime
from collections import defaultdict
import uuid


class UserSessionManager:
    """Manages user sessions and real-time behavior tracking"""

    def __init__(self, recommender):
        self.recommender = recommender
        self.active_sessions = {}
        self.user_carts = defaultdict(list)
        self.user_wishlists = defaultdict(list)
        self.user_search_history = defaultdict(list)
        self.user_click_history = defaultdict(list)
        self.user_feedback = defaultdict(list)
        self.lock = threading.Lock()

    def create_session(self, user_id=None):
        """Create a new user session"""
        session_id = str(uuid.uuid4())[:8]

        if user_id is None:
            # Guest user
            user_id = f"GUEST_{session_id}"

        session = {
            'session_id': session_id,
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'interactions': [],
            'recommendations_shown': [],
            'current_context': {}
        }

        with self.lock:
            self.active_sessions[session_id] = session

        return session

    def get_session(self, session_id):
        """Get session by ID"""
        return self.active_sessions.get(session_id)

    def track_click(self, user_id, product_id):
        """Track product click"""
        with self.lock:
            self.user_click_history[user_id].append({
                'product_id': product_id,
                'timestamp': datetime.now().isoformat()
            })

            # Update interactions in recommender
            self.recommender.update_interactions(user_id, product_id, 'click')

        return True

    def track_view(self, user_id, product_id):
        """Track product view"""
        self.recommender.update_interactions(user_id, product_id, 'view')
        return True

    def track_search(self, user_id, query, results):
        """Track search query and results"""
        with self.lock:
            self.user_search_history[user_id].append({
                'query': query,
                'results_count': len(results),
                'timestamp': datetime.now().isoformat()
            })

        # Track first result as search interaction
        if results:
            self.recommender.update_interactions(
                user_id, results[0][0], 'search'
            )

        return True

    def add_to_cart(self, user_id, product_id):
        """Add product to user's cart"""
        with self.lock:
            if product_id not in self.user_carts[user_id]:
                self.user_carts[user_id].append(product_id)
                self.recommender.update_interactions(
                    user_id, product_id, 'add_to_cart'
                )

        return self.user_carts[user_id]

    def remove_from_cart(self, user_id, product_id):
        """Remove product from user's cart"""
        with self.lock:
            if product_id in self.user_carts[user_id]:
                self.user_carts[user_id].remove(product_id)

        return self.user_carts[user_id]

    def get_cart(self, user_id):
        """Get user's cart"""
        return self.user_carts.get(user_id, [])

    def clear_cart(self, user_id):
        """Clear user's cart"""
        with self.lock:
            self.user_carts[user_id] = []
        return True

    def add_to_wishlist(self, user_id, product_id):
        """Add product to wishlist"""
        with self.lock:
            if product_id not in self.user_wishlists[user_id]:
                self.user_wishlists[user_id].append(product_id)
                self.recommender.update_interactions(
                    user_id, product_id, 'wishlist'
                )

        return self.user_wishlists[user_id]

    def get_wishlist(self, user_id):
        """Get user's wishlist"""
        return self.user_wishlists.get(user_id, [])

    def record_feedback(self, user_id, product_id, feedback_type, rating=None):
        """Record user feedback (like/dislike)"""
        with self.lock:
            feedback_entry = {
                'product_id': product_id,
                'feedback_type': feedback_type,
                'rating': rating,
                'timestamp': datetime.now().isoformat()
            }
            self.user_feedback[user_id].append(feedback_entry)

            # Update preferences based on feedback
            product = self.recommender.get_product_details(product_id)
            if product:
                category = product['category']
                # Adjust preference weight based on feedback
                if feedback_type == 'like':
                    self.recommender.user_preferences[user_id][category] += 2.0
                elif feedback_type == 'dislike':
                    self.recommender.user_preferences[user_id][category] -= 1.0

        return True

    def get_user_feedback(self, user_id):
        """Get user's feedback history"""
        return self.user_feedback.get(user_id, [])

    def get_dynamic_recommendations(self, user_id, n=10, context=None):
        """Get dynamically updated recommendations based on recent behavior"""

        # Get base recommendations
        category = context.get('category') if context else None
        max_price = context.get('max_price') if context else None

        recommendations = self.recommender.recommend(
            user_id,
            n=n * 2,  # Get more to filter
            category=category,
            max_price=max_price
        )

        # Boost products from recently clicked categories
        recent_clicks = self.user_click_history.get(user_id, [])[-10:]
        boosted_categories = set()

        for click in recent_clicks:
            product = self.recommender.get_product_details(click['product_id'])
            if product:
                boosted_categories.add(product['category'])

        # Re-score recommendations
        reranked = []
        for product_id, score in recommendations:
            product = self.recommender.get_product_details(product_id)
            if product and product['category'] in boosted_categories:
                score *= 1.3  # Boost by 30%

            reranked.append((product_id, score))

        # Sort and return top N
        reranked.sort(key=lambda x: x[1], reverse=True)

        return reranked[:n]

    def get_personalized_deals(self, user_id, n=5):
        """Get deals personalized to user preferences"""
        preferred_categories = self.recommender.get_user_preferred_categories(user_id, n=3)

        deals = []
        products_df = self.recommender.products_df

        # Get discounted products in preferred categories
        for category in preferred_categories:
            category_deals = products_df[
                (products_df['category'] == category) &
                (products_df['discount_percent'] > 0)
            ].sort_values('discount_percent', ascending=False)

            for _, product in category_deals.head(2).iterrows():
                deals.append(product['product_id'])

        # Fill remaining slots with general deals
        if len(deals) < n:
            general_deals = products_df[
                products_df['discount_percent'] > 0
            ].sort_values('discount_percent', ascending=False)

            for _, product in general_deals.iterrows():
                if product['product_id'] not in deals:
                    deals.append(product['product_id'])
                    if len(deals) >= n:
                        break

        return deals[:n]

    def get_session_stats(self, user_id):
        """Get statistics for current session"""
        return {
            'cart_items': len(self.user_carts.get(user_id, [])),
            'wishlist_items': len(self.user_wishlists.get(user_id, [])),
            'searches': len(self.user_search_history.get(user_id, [])),
            'clicks': len(self.user_click_history.get(user_id, [])),
            'feedback_given': len(self.user_feedback.get(user_id, []))
        }
