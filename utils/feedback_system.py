"""
Enhanced Feedback Collection System
Comprehensive feedback collection with ratings, reviews, surveys, and analytics
"""

import json
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import hashlib
import threading


class FeedbackType:
    """Feedback type constants"""
    LIKE = 'like'
    DISLIKE = 'dislike'
    RATING = 'rating'
    REVIEW = 'review'
    SURVEY = 'survey'
    NPS = 'nps'  # Net Promoter Score
    SUGGESTION = 'suggestion'
    BUG_REPORT = 'bug_report'


class FeedbackEntry:
    """Single feedback entry"""

    def __init__(self, user_id: str, feedback_type: str,
                 product_id: str = None, **kwargs):
        self.id = self._generate_id()
        self.user_id = user_id
        self.feedback_type = feedback_type
        self.product_id = product_id
        self.timestamp = datetime.now()

        # Type-specific fields
        self.rating = kwargs.get('rating')  # 1-5 stars
        self.review_text = kwargs.get('review_text')
        self.sentiment = kwargs.get('sentiment')  # positive/negative/neutral
        self.nps_score = kwargs.get('nps_score')  # 0-10
        self.survey_responses = kwargs.get('survey_responses', {})
        self.tags = kwargs.get('tags', [])
        self.metadata = kwargs.get('metadata', {})

    def _generate_id(self) -> str:
        """Generate unique feedback ID"""
        data = f"{datetime.now().isoformat()}{os.urandom(8).hex()}"
        return hashlib.md5(data.encode()).hexdigest()[:12]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'feedback_type': self.feedback_type,
            'product_id': self.product_id,
            'timestamp': self.timestamp.isoformat(),
            'rating': self.rating,
            'review_text': self.review_text,
            'sentiment': self.sentiment,
            'nps_score': self.nps_score,
            'survey_responses': self.survey_responses,
            'tags': self.tags,
            'metadata': self.metadata
        }


class SurveyTemplate:
    """Survey template definition"""

    def __init__(self, survey_id: str, name: str, questions: List[Dict]):
        self.survey_id = survey_id
        self.name = name
        self.questions = questions  # List of {id, text, type, options}
        self.created_at = datetime.now()

    def to_dict(self) -> Dict:
        return {
            'survey_id': self.survey_id,
            'name': self.name,
            'questions': self.questions,
            'created_at': self.created_at.isoformat()
        }


class FeedbackCollector:
    """
    Enhanced Feedback Collection System
    Handles all types of user feedback with analytics
    """

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(__file__), '..', 'data', 'feedback'
        )
        os.makedirs(self.storage_path, exist_ok=True)

        self.feedback_entries: List[FeedbackEntry] = []
        self.surveys: Dict[str, SurveyTemplate] = {}
        self.lock = threading.Lock()

        # Analytics cache
        self._analytics_cache = {}
        self._cache_ttl = 300  # 5 minutes

        # Initialize default surveys
        self._init_default_surveys()

        # Load existing feedback
        self._load_feedback()

        print(f"  FeedbackCollector initialized with {len(self.feedback_entries)} entries")

    def _init_default_surveys(self):
        """Initialize default survey templates"""
        # Post-purchase survey
        self.surveys['post_purchase'] = SurveyTemplate(
            'post_purchase',
            'Post-Purchase Experience',
            [
                {'id': 'q1', 'text': 'How satisfied are you with your purchase?',
                 'type': 'rating', 'options': [1, 2, 3, 4, 5]},
                {'id': 'q2', 'text': 'Was the product as described?',
                 'type': 'boolean', 'options': ['Yes', 'No']},
                {'id': 'q3', 'text': 'How was the delivery experience?',
                 'type': 'rating', 'options': [1, 2, 3, 4, 5]},
                {'id': 'q4', 'text': 'Would you recommend this product?',
                 'type': 'boolean', 'options': ['Yes', 'No']},
                {'id': 'q5', 'text': 'Any additional comments?',
                 'type': 'text', 'options': None}
            ]
        )

        # Chatbot satisfaction survey
        self.surveys['chatbot_satisfaction'] = SurveyTemplate(
            'chatbot_satisfaction',
            'Chatbot Experience',
            [
                {'id': 'q1', 'text': 'Did the chatbot understand your query?',
                 'type': 'rating', 'options': [1, 2, 3, 4, 5]},
                {'id': 'q2', 'text': 'Were the recommendations helpful?',
                 'type': 'boolean', 'options': ['Yes', 'No']},
                {'id': 'q3', 'text': 'How natural was the conversation?',
                 'type': 'rating', 'options': [1, 2, 3, 4, 5]},
                {'id': 'q4', 'text': 'What could we improve?',
                 'type': 'text', 'options': None}
            ]
        )

        # NPS Survey
        self.surveys['nps'] = SurveyTemplate(
            'nps',
            'Net Promoter Score',
            [
                {'id': 'nps', 'text': 'How likely are you to recommend us (0-10)?',
                 'type': 'nps', 'options': list(range(11))},
                {'id': 'reason', 'text': 'What is the primary reason for your score?',
                 'type': 'text', 'options': None}
            ]
        )

    def _load_feedback(self):
        """Load feedback from storage"""
        feedback_file = os.path.join(self.storage_path, 'feedback.json')
        if os.path.exists(feedback_file):
            try:
                with open(feedback_file, 'r') as f:
                    data = json.load(f)
                    for entry_data in data:
                        entry = FeedbackEntry(
                            user_id=entry_data['user_id'],
                            feedback_type=entry_data['feedback_type'],
                            product_id=entry_data.get('product_id'),
                            rating=entry_data.get('rating'),
                            review_text=entry_data.get('review_text'),
                            sentiment=entry_data.get('sentiment'),
                            nps_score=entry_data.get('nps_score'),
                            survey_responses=entry_data.get('survey_responses', {}),
                            tags=entry_data.get('tags', []),
                            metadata=entry_data.get('metadata', {})
                        )
                        entry.id = entry_data['id']
                        entry.timestamp = datetime.fromisoformat(entry_data['timestamp'])
                        self.feedback_entries.append(entry)
            except Exception as e:
                print(f"  Warning: Could not load feedback: {e}")

    def _save_feedback(self):
        """Save feedback to storage"""
        feedback_file = os.path.join(self.storage_path, 'feedback.json')
        with open(feedback_file, 'w') as f:
            json.dump([e.to_dict() for e in self.feedback_entries], f, indent=2)

    # ==========================================
    # FEEDBACK COLLECTION METHODS
    # ==========================================

    def collect_like_dislike(self, user_id: str, product_id: str,
                            is_like: bool) -> FeedbackEntry:
        """Collect simple like/dislike feedback"""
        entry = FeedbackEntry(
            user_id=user_id,
            feedback_type=FeedbackType.LIKE if is_like else FeedbackType.DISLIKE,
            product_id=product_id,
            sentiment='positive' if is_like else 'negative'
        )
        with self.lock:
            self.feedback_entries.append(entry)
            self._save_feedback()
        return entry

    def collect_rating(self, user_id: str, product_id: str,
                      rating: int, review_text: str = None) -> FeedbackEntry:
        """Collect star rating with optional review"""
        rating = max(1, min(5, rating))  # Clamp to 1-5

        # Determine sentiment from rating
        if rating >= 4:
            sentiment = 'positive'
        elif rating <= 2:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'

        entry = FeedbackEntry(
            user_id=user_id,
            feedback_type=FeedbackType.RATING,
            product_id=product_id,
            rating=rating,
            review_text=review_text,
            sentiment=sentiment
        )
        with self.lock:
            self.feedback_entries.append(entry)
            self._save_feedback()
        return entry

    def collect_review(self, user_id: str, product_id: str,
                      review_text: str, rating: int = None,
                      tags: List[str] = None) -> FeedbackEntry:
        """Collect detailed product review"""
        # Simple sentiment analysis
        positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'best', 'perfect']
        negative_words = ['bad', 'poor', 'terrible', 'worst', 'hate', 'awful', 'disappointed']

        text_lower = review_text.lower()
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)

        if pos_count > neg_count:
            sentiment = 'positive'
        elif neg_count > pos_count:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'

        entry = FeedbackEntry(
            user_id=user_id,
            feedback_type=FeedbackType.REVIEW,
            product_id=product_id,
            rating=rating,
            review_text=review_text,
            sentiment=sentiment,
            tags=tags or []
        )
        with self.lock:
            self.feedback_entries.append(entry)
            self._save_feedback()
        return entry

    def collect_nps(self, user_id: str, score: int,
                   reason: str = None) -> FeedbackEntry:
        """Collect Net Promoter Score"""
        score = max(0, min(10, score))  # Clamp to 0-10

        # Categorize NPS
        if score >= 9:
            sentiment = 'promoter'
        elif score >= 7:
            sentiment = 'passive'
        else:
            sentiment = 'detractor'

        entry = FeedbackEntry(
            user_id=user_id,
            feedback_type=FeedbackType.NPS,
            nps_score=score,
            review_text=reason,
            sentiment=sentiment
        )
        with self.lock:
            self.feedback_entries.append(entry)
            self._save_feedback()
        return entry

    def collect_survey_response(self, user_id: str, survey_id: str,
                               responses: Dict) -> FeedbackEntry:
        """Collect survey responses"""
        if survey_id not in self.surveys:
            raise ValueError(f"Survey {survey_id} not found")

        entry = FeedbackEntry(
            user_id=user_id,
            feedback_type=FeedbackType.SURVEY,
            survey_responses=responses,
            metadata={'survey_id': survey_id}
        )
        with self.lock:
            self.feedback_entries.append(entry)
            self._save_feedback()
        return entry

    def collect_suggestion(self, user_id: str, suggestion: str,
                          category: str = 'general') -> FeedbackEntry:
        """Collect user suggestion"""
        entry = FeedbackEntry(
            user_id=user_id,
            feedback_type=FeedbackType.SUGGESTION,
            review_text=suggestion,
            tags=[category]
        )
        with self.lock:
            self.feedback_entries.append(entry)
            self._save_feedback()
        return entry

    # ==========================================
    # ANALYTICS METHODS
    # ==========================================

    def get_product_rating_stats(self, product_id: str) -> Dict:
        """Get rating statistics for a product"""
        ratings = [e.rating for e in self.feedback_entries
                  if e.product_id == product_id and e.rating is not None]

        if not ratings:
            return {'avg_rating': 0, 'total_ratings': 0, 'distribution': {}}

        distribution = {i: ratings.count(i) for i in range(1, 6)}

        return {
            'avg_rating': round(sum(ratings) / len(ratings), 2),
            'total_ratings': len(ratings),
            'distribution': distribution
        }

    def get_product_sentiment(self, product_id: str) -> Dict:
        """Get sentiment analysis for a product"""
        entries = [e for e in self.feedback_entries if e.product_id == product_id]

        sentiments = {'positive': 0, 'negative': 0, 'neutral': 0}
        for e in entries:
            if e.sentiment in sentiments:
                sentiments[e.sentiment] += 1

        total = sum(sentiments.values())
        if total == 0:
            return {'sentiments': sentiments, 'sentiment_score': 0}

        # Calculate sentiment score (-100 to +100)
        score = ((sentiments['positive'] - sentiments['negative']) / total) * 100

        return {
            'sentiments': sentiments,
            'sentiment_score': round(score, 2),
            'total_feedback': total
        }

    def calculate_nps(self, days: int = 30) -> Dict:
        """Calculate Net Promoter Score"""
        cutoff = datetime.now() - timedelta(days=days)

        nps_entries = [e for e in self.feedback_entries
                      if e.feedback_type == FeedbackType.NPS
                      and e.timestamp >= cutoff]

        if not nps_entries:
            return {'nps': 0, 'promoters': 0, 'passives': 0, 'detractors': 0}

        promoters = sum(1 for e in nps_entries if e.nps_score >= 9)
        passives = sum(1 for e in nps_entries if 7 <= e.nps_score <= 8)
        detractors = sum(1 for e in nps_entries if e.nps_score <= 6)

        total = len(nps_entries)
        nps = ((promoters - detractors) / total) * 100

        return {
            'nps': round(nps, 2),
            'promoters': promoters,
            'passives': passives,
            'detractors': detractors,
            'total_responses': total
        }

    def get_feedback_trends(self, days: int = 30) -> Dict:
        """Get feedback trends over time"""
        cutoff = datetime.now() - timedelta(days=days)

        daily_counts = defaultdict(lambda: {'total': 0, 'positive': 0, 'negative': 0})

        for entry in self.feedback_entries:
            if entry.timestamp >= cutoff:
                day = entry.timestamp.strftime('%Y-%m-%d')
                daily_counts[day]['total'] += 1
                if entry.sentiment == 'positive':
                    daily_counts[day]['positive'] += 1
                elif entry.sentiment == 'negative':
                    daily_counts[day]['negative'] += 1

        return dict(daily_counts)

    def get_user_feedback_history(self, user_id: str) -> List[Dict]:
        """Get feedback history for a user"""
        entries = [e for e in self.feedback_entries if e.user_id == user_id]
        return [e.to_dict() for e in sorted(entries, key=lambda x: x.timestamp, reverse=True)]

    def get_survey(self, survey_id: str) -> Optional[Dict]:
        """Get survey template"""
        if survey_id in self.surveys:
            return self.surveys[survey_id].to_dict()
        return None

    def get_overall_stats(self) -> Dict:
        """Get overall feedback statistics"""
        total = len(self.feedback_entries)

        type_counts = defaultdict(int)
        sentiment_counts = defaultdict(int)

        for entry in self.feedback_entries:
            type_counts[entry.feedback_type] += 1
            if entry.sentiment:
                sentiment_counts[entry.sentiment] += 1

        # Average rating
        ratings = [e.rating for e in self.feedback_entries if e.rating]
        avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0

        return {
            'total_feedback': total,
            'by_type': dict(type_counts),
            'by_sentiment': dict(sentiment_counts),
            'average_rating': avg_rating,
            'nps': self.calculate_nps(),
            'unique_users': len(set(e.user_id for e in self.feedback_entries))
        }


# Global instance
_feedback_collector = None


def get_feedback_collector(storage_path: str = None) -> FeedbackCollector:
    """Get or create feedback collector instance"""
    global _feedback_collector
    if _feedback_collector is None:
        _feedback_collector = FeedbackCollector(storage_path)
    return _feedback_collector


# For testing
if __name__ == "__main__":
    print("=" * 60)
    print("Testing Feedback Collection System")
    print("=" * 60)

    collector = FeedbackCollector()

    # Test different feedback types
    print("\n1. Collecting like feedback...")
    collector.collect_like_dislike('U001', 'P001', is_like=True)

    print("2. Collecting rating...")
    collector.collect_rating('U001', 'P001', rating=4, review_text="Great product!")

    print("3. Collecting review...")
    collector.collect_review('U002', 'P001',
                            "This laptop is amazing! Best purchase ever.",
                            rating=5, tags=['laptop', 'electronics'])

    print("4. Collecting NPS...")
    collector.collect_nps('U001', score=9, reason="Great service!")

    print("\n5. Analytics:")
    stats = collector.get_overall_stats()
    print(f"   Total feedback: {stats['total_feedback']}")
    print(f"   By type: {stats['by_type']}")
    print(f"   Average rating: {stats['average_rating']}")
    print(f"   NPS: {stats['nps']['nps']}")

    print("\nTest complete!")
