"""
Feedback Collection and Analysis Service (R7)
Collects, stores, and analyzes user feedback on recommendations and products.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import json
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.config import DATA_DIR


class FeedbackStore:
    """Stores and retrieves user feedback."""

    def __init__(self):
        self.feedback_file = DATA_DIR / "feedback.json"
        self.feedback_data: List[Dict] = []
        self._load_feedback()

    def _load_feedback(self):
        """Load feedback from storage."""
        try:
            if self.feedback_file.exists():
                with open(self.feedback_file) as f:
                    self.feedback_data = json.load(f)
            else:
                self.feedback_data = []
        except Exception as e:
            print(f"Error loading feedback: {e}")
            self.feedback_data = []

    def _save_feedback(self):
        """Save feedback to storage."""
        try:
            with open(self.feedback_file, "w") as f:
                json.dump(self.feedback_data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving feedback: {e}")

    def add_feedback(
        self,
        user_id: str,
        feedback_type: str,  # "recommendation", "product", "chat_quality"
        rating: int,  # 1-5
        target_id: str,  # product_id or recommendation_id
        comment: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Add user feedback."""
        feedback_entry = {
            "id": f"FB{len(self.feedback_data):06d}",
            "user_id": user_id,
            "type": feedback_type,
            "rating": max(1, min(5, rating)),  # Clamp 1-5
            "target_id": target_id,
            "comment": comment,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
            "helpful_count": 0
        }

        self.feedback_data.append(feedback_entry)
        self._save_feedback()

        return feedback_entry

    def get_feedback(
        self,
        user_id: Optional[str] = None,
        feedback_type: Optional[str] = None,
        target_id: Optional[str] = None
    ) -> List[Dict]:
        """Retrieve feedback by filters."""
        results = self.feedback_data

        if user_id:
            results = [f for f in results if f["user_id"] == user_id]

        if feedback_type:
            results = [f for f in results if f["type"] == feedback_type]

        if target_id:
            results = [f for f in results if f["target_id"] == target_id]

        return results

    def mark_helpful(self, feedback_id: str) -> bool:
        """Mark feedback as helpful."""
        for fb in self.feedback_data:
            if fb["id"] == feedback_id:
                fb["helpful_count"] = fb.get("helpful_count", 0) + 1
                self._save_feedback()
                return True
        return False


class FeedbackAnalytics:
    """Analytics for collected feedback."""

    def __init__(self, feedback_store: FeedbackStore):
        self.store = feedback_store

    def get_average_rating(
        self,
        feedback_type: Optional[str] = None,
        target_id: Optional[str] = None
    ) -> float:
        """Get average rating for feedback."""
        feedback = self.store.get_feedback(feedback_type=feedback_type, target_id=target_id)

        if not feedback:
            return 0.0

        ratings = [f["rating"] for f in feedback]
        return float(np.mean(ratings))

    def get_rating_distribution(
        self,
        feedback_type: Optional[str] = None
    ) -> Dict[int, int]:
        """Get distribution of ratings."""
        feedback = self.store.get_feedback(feedback_type=feedback_type)

        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        for f in feedback:
            rating = f["rating"]
            distribution[rating] = distribution.get(rating, 0) + 1

        return distribution

    def get_sentiment_summary(
        self,
        feedback_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get overall sentiment from feedback."""
        feedback = self.store.get_feedback(feedback_type=feedback_type)

        if not feedback:
            return {
                "total_feedback": 0,
                "avg_rating": 0.0,
                "sentiment": "neutral",
                "distribution": {}
            }

        ratings = [f["rating"] for f in feedback]
        avg_rating = np.mean(ratings)

        # Determine sentiment
        if avg_rating >= 4.0:
            sentiment = "very_positive"
        elif avg_rating >= 3.5:
            sentiment = "positive"
        elif avg_rating >= 2.5:
            sentiment = "neutral"
        else:
            sentiment = "negative"

        distribution = self.get_rating_distribution(feedback_type)

        return {
            "total_feedback": len(feedback),
            "avg_rating": float(avg_rating),
            "sentiment": sentiment,
            "distribution": distribution
        }

    def get_product_feedback_summary(self, product_id: str) -> Dict[str, Any]:
        """Get feedback summary for a specific product."""
        feedback = self.store.get_feedback(target_id=product_id)

        if not feedback:
            return {
                "product_id": product_id,
                "total_feedback": 0,
                "avg_rating": 0.0,
                "total_comments": 0
            }

        ratings = [f["rating"] for f in feedback]
        comments = [f["comment"] for f in feedback if f.get("comment")]

        return {
            "product_id": product_id,
            "total_feedback": len(feedback),
            "avg_rating": float(np.mean(ratings)),
            "rating_distribution": self.get_rating_distribution(target_id=product_id),
            "total_comments": len(comments),
            "recent_comments": comments[-5:],  # Last 5 comments
            "helpful_count": sum(f.get("helpful_count", 0) for f in feedback)
        }

    def get_recommendation_quality_metrics(self) -> Dict[str, Any]:
        """Get overall recommendation quality metrics based on feedback."""
        rec_feedback = self.store.get_feedback(feedback_type="recommendation")

        if not rec_feedback:
            return {
                "total_recommendations_rated": 0,
                "avg_recommendation_rating": 0.0,
                "quality_score": 0.0
            }

        ratings = [f["rating"] for f in rec_feedback]
        avg_rating = np.mean(ratings)

        # Calculate quality score (0-100)
        quality_score = (avg_rating / 5.0) * 100

        return {
            "total_recommendations_rated": len(rec_feedback),
            "avg_recommendation_rating": float(avg_rating),
            "quality_score": float(quality_score),
            "distribution": self.get_rating_distribution(feedback_type="recommendation")
        }


# Service class combining store and analytics
class FeedbackService:
    """Main feedback service."""

    def __init__(self):
        self.store = FeedbackStore()
        self.analytics = FeedbackAnalytics(self.store)

    def submit_feedback(
        self,
        user_id: str,
        feedback_type: str,
        rating: int,
        target_id: str,
        comment: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Submit feedback."""
        return self.store.add_feedback(user_id, feedback_type, rating, target_id, comment, metadata)

    def get_feedback(self, **filters) -> List[Dict]:
        """Get feedback with filters."""
        return self.store.get_feedback(**filters)

    def mark_feedback_helpful(self, feedback_id: str) -> bool:
        """Mark feedback as helpful."""
        return self.store.mark_helpful(feedback_id)

    def get_analytics(self, **filters) -> Dict[str, Any]:
        """Get feedback analytics."""
        return self.analytics.get_sentiment_summary(**filters)

    def get_product_analytics(self, product_id: str) -> Dict[str, Any]:
        """Get product-specific analytics."""
        return self.analytics.get_product_feedback_summary(product_id)

    def get_quality_metrics(self) -> Dict[str, Any]:
        """Get recommendation quality metrics."""
        return self.analytics.get_recommendation_quality_metrics()


# Singleton instance
_feedback_service = None


def get_feedback_service() -> FeedbackService:
    """Get singleton feedback service."""
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackService()
    return _feedback_service
