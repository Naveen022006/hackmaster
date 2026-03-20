"""
Conversation Learner for Personal Shopping Agent.
Learns user patterns and preferences from conversations to provide adaptive responses.
"""
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict
import math

from services.conversation_memory import (
    ConversationTurn,
    ConversationSession,
    UserConversationProfile,
    ConversationContext
)


class ConversationLearner:
    """Learns user patterns and preferences from conversations."""

    # Decay factors for recency weighting
    DAILY_DECAY = 0.95  # 5% decay per day
    SESSION_DECAY = 0.9  # 10% decay per session

    # Learning weights for different signals
    WEIGHTS = {
        "explicit_mention": 2.0,      # User explicitly asks for something
        "refinement": 1.5,            # User refines to specific values
        "repeated_query": 2.5,        # User repeats similar queries
        "implicit_preference": 1.0,   # Inferred from context
        "click_signal": 3.0,          # User clicked on product
        "add_to_cart": 4.0,           # User added to cart
        "purchase_signal": 5.0,       # User purchased product
    }

    # Refinement keywords
    REFINEMENT_KEYWORDS = [
        "cheaper", "expensive", "more", "less", "different",
        "another", "other", "else", "instead", "also", "similar"
    ]

    def __init__(self):
        """Initialize the learner."""
        pass

    def learn_from_turn(
        self,
        turn: ConversationTurn,
        session: ConversationSession,
        profile: UserConversationProfile
    ) -> UserConversationProfile:
        """Learn from a single conversation turn in real-time."""

        # Check if this is a refinement
        is_refinement = self._is_refinement(turn, session)
        if is_refinement:
            session.refinement_count += 1
            # Users who refine often appreciate more options
            profile.prefers_alternatives = True

        # Learn category preferences
        if turn.entities.get("category"):
            category = turn.entities["category"]
            weight = self.WEIGHTS["explicit_mention"]
            profile.common_categories[category] = (
                profile.common_categories.get(category, 0) + weight
            )

        # Learn brand preferences
        if turn.entities.get("brand"):
            brand = turn.entities["brand"]
            weight = self.WEIGHTS["explicit_mention"]
            profile.common_brands[brand] = (
                profile.common_brands.get(brand, 0) + weight
            )

        # Learn feature preferences
        if turn.entities.get("features"):
            for feature in turn.entities["features"]:
                weight = self.WEIGHTS["implicit_preference"]
                profile.common_features[feature] = (
                    profile.common_features.get(feature, 0) + weight
                )

        # Learn intent patterns
        profile.common_intents[turn.intent] = (
            profile.common_intents.get(turn.intent, 0) + 1
        )

        # Track successful queries (those that returned products)
        if turn.products_shown:
            session.successful_queries += 1

        # Update interaction timestamp
        profile.last_updated = datetime.now()

        return profile

    def learn_from_session(
        self,
        session: ConversationSession,
        profile: UserConversationProfile
    ) -> UserConversationProfile:
        """Learn from a completed session - called when session ends."""

        if not session.turns:
            return profile

        # Calculate session-level metrics
        total_turns = len(session.turns)

        # Learn verbosity preference from query patterns
        profile = self._learn_verbosity_preference(session, profile)

        # Learn response preferences
        profile = self._learn_response_preferences(session, profile)

        # Apply recency decay to old preferences
        profile = self._apply_recency_decay(profile)

        # Update session metrics
        profile.total_sessions += 1
        profile.last_session_date = datetime.now()

        return profile

    def learn_from_feedback(
        self,
        turn: ConversationTurn,
        feedback: str,
        profile: UserConversationProfile
    ) -> UserConversationProfile:
        """Learn from explicit user feedback on a turn."""

        weight_multiplier = {
            "liked": 1.5,
            "clicked": 2.0,
            "added_to_cart": 3.0,
            "purchased": 4.0,
            "disliked": -1.0
        }.get(feedback, 1.0)

        # Boost/reduce preferences based on feedback
        if turn.entities.get("category"):
            category = turn.entities["category"]
            adjustment = self.WEIGHTS["click_signal"] * weight_multiplier
            profile.common_categories[category] = max(
                0, profile.common_categories.get(category, 0) + adjustment
            )

        if turn.entities.get("brand"):
            brand = turn.entities["brand"]
            adjustment = self.WEIGHTS["click_signal"] * weight_multiplier
            profile.common_brands[brand] = max(
                0, profile.common_brands.get(brand, 0) + adjustment
            )

        return profile

    def _is_refinement(
        self,
        turn: ConversationTurn,
        session: ConversationSession
    ) -> bool:
        """Detect if this turn is refining a previous query."""
        if not session.turns:
            return False

        query_lower = turn.user_query.lower()

        # Check for refinement keywords
        if any(keyword in query_lower for keyword in self.REFINEMENT_KEYWORDS):
            return True

        # Check for progressive filtering (adding constraints)
        last_turn = session.turns[-1] if session.turns else None
        if last_turn:
            # New price constraint added
            if turn.entities.get("price") and not last_turn.entities.get("price"):
                return True
            # New brand constraint added
            if turn.entities.get("brand") and not last_turn.entities.get("brand"):
                return True
            # New feature constraint added
            if turn.entities.get("features") and not last_turn.entities.get("features"):
                return True
            # Same category, continuing search
            if (turn.entities.get("category") == last_turn.entities.get("category") and
                turn.intent in ["search", "filter"]):
                return True

        return False

    def _learn_verbosity_preference(
        self,
        session: ConversationSession,
        profile: UserConversationProfile
    ) -> UserConversationProfile:
        """Learn user's preferred response length from their query patterns."""

        if not session.turns:
            return profile

        # Calculate average query length
        query_lengths = [len(t.user_query.split()) for t in session.turns]
        avg_query_length = sum(query_lengths) / len(query_lengths)

        # Short queries suggest preference for brief responses
        if avg_query_length < 4:
            # Lean towards brief
            if profile.verbosity_preference == "detailed":
                profile.verbosity_preference = "normal"
            else:
                profile.verbosity_preference = "brief"

        # Long, detailed queries suggest they appreciate detailed responses
        elif avg_query_length > 10:
            # Lean towards detailed
            if profile.verbosity_preference == "brief":
                profile.verbosity_preference = "normal"
            else:
                profile.verbosity_preference = "detailed"

        return profile

    def _learn_response_preferences(
        self,
        session: ConversationSession,
        profile: UserConversationProfile
    ) -> UserConversationProfile:
        """Learn what response elements user appreciates."""

        # Check if user frequently asks for specs/details
        spec_keywords = ["specs", "specifications", "details", "features", "technical"]
        spec_queries = sum(
            1 for t in session.turns
            if any(kw in t.user_query.lower() for kw in spec_keywords)
        )
        if spec_queries >= 2:
            profile.prefers_detailed_specs = True

        # Check if user frequently compares products
        compare_queries = sum(1 for t in session.turns if t.intent == "compare")
        if compare_queries >= 2:
            profile.prefers_price_comparison = True

        # Check refinement frequency
        if session.refinement_count >= 3:
            profile.prefers_alternatives = True

        return profile

    def _apply_recency_decay(
        self,
        profile: UserConversationProfile
    ) -> UserConversationProfile:
        """Apply decay to old preferences to keep learning fresh."""

        # Apply decay to category preferences
        for category in profile.common_categories:
            profile.common_categories[category] *= self.SESSION_DECAY

        # Apply decay to brand preferences
        for brand in profile.common_brands:
            profile.common_brands[brand] *= self.SESSION_DECAY

        # Apply decay to feature preferences
        for feature in profile.common_features:
            profile.common_features[feature] *= self.SESSION_DECAY

        # Clean up very low values
        profile.common_categories = {
            k: v for k, v in profile.common_categories.items() if v >= 0.1
        }
        profile.common_brands = {
            k: v for k, v in profile.common_brands.items() if v >= 0.1
        }
        profile.common_features = {
            k: v for k, v in profile.common_features.items() if v >= 0.1
        }

        return profile

    def get_adaptive_response_config(
        self,
        profile: UserConversationProfile,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Get configuration for adaptive response generation."""

        config = {
            "verbosity": profile.verbosity_preference,
            "include_specs": profile.prefers_detailed_specs,
            "include_alternatives": profile.prefers_alternatives,
            "include_price_comparison": profile.prefers_price_comparison,
            "greeting_style": "brief" if profile.interaction_count > 20 else "warm",
            "suggest_refinements": context.turn_count > 0,
            "is_new_user": profile.interaction_count < 3,
            "is_returning_user": profile.total_sessions > 1,
            "is_frequent_user": profile.interaction_count > 50,
        }

        # New users get more guidance
        if profile.interaction_count < 3:
            config["include_help_hints"] = True
            config["verbosity"] = "detailed"

        # Frequent users get efficiency
        if profile.interaction_count > 50:
            config["skip_pleasantries"] = True
            config["direct_results"] = True

        return config

    def get_proactive_suggestions(
        self,
        profile: UserConversationProfile,
        context: ConversationContext
    ) -> List[str]:
        """Generate proactive suggestions based on learned patterns."""

        suggestions = []

        # Suggest top categories if user hasn't specified one
        if not context.last_category and profile.common_categories:
            top_cats = profile.get_top_categories(2)
            if top_cats:
                suggestions.append(f"Looking for {top_cats[0]} today?")

        # Suggest favorite brands if they're browsing a category
        if context.last_category and profile.common_brands:
            top_brands = profile.get_top_brands(2)
            if top_brands:
                suggestions.append(f"Would you like to see {top_brands[0]} options?")

        # Suggest based on purchase history
        if profile.purchase_categories:
            recent_purchase_cat = profile.purchase_categories[-1]
            if recent_purchase_cat != context.last_category:
                suggestions.append(f"Need accessories for your recent {recent_purchase_cat}?")

        return suggestions[:2]  # Return max 2 suggestions

    def detect_user_state(
        self,
        session: ConversationSession,
        profile: UserConversationProfile
    ) -> Dict[str, Any]:
        """Detect user's current state for adaptive responses."""

        state = {
            "is_frustrated": False,
            "is_confused": False,
            "is_browsing": False,
            "is_ready_to_buy": False,
            "needs_help": False
        }

        if not session.turns:
            return state

        # Detect frustration (repeated similar queries with no clicks)
        if len(session.turns) >= 3:
            recent_intents = [t.intent for t in session.turns[-3:]]
            if recent_intents.count("search") >= 3 and session.successful_queries < 2:
                state["is_frustrated"] = True

        # Detect confusion (help intent or question marks)
        help_queries = sum(
            1 for t in session.turns
            if t.intent == "help" or "?" in t.user_query
        )
        if help_queries >= 2:
            state["is_confused"] = True
            state["needs_help"] = True

        # Detect browsing (multiple searches, different categories)
        unique_categories = set(session.mentioned_categories)
        if len(unique_categories) >= 3:
            state["is_browsing"] = True

        # Detect ready to buy (specific queries, single focus)
        if len(session.turns) >= 2:
            recent_turn = session.turns[-1]
            if (recent_turn.intent == "buy" or
                (recent_turn.entities.get("brand") and
                 recent_turn.entities.get("price") and
                 recent_turn.entities.get("category"))):
                state["is_ready_to_buy"] = True

        return state


# Singleton instance
_learner: Optional[ConversationLearner] = None


def get_conversation_learner() -> ConversationLearner:
    """Get or create the learner singleton."""
    global _learner
    if _learner is None:
        _learner = ConversationLearner()
    return _learner


if __name__ == "__main__":
    # Test the conversation learner
    from services.conversation_memory import ConversationTurn, ConversationSession, UserConversationProfile

    print("Testing Conversation Learner")
    print("=" * 60)

    learner = get_conversation_learner()

    # Create test session and profile
    session = ConversationSession(
        session_id="test_sess_001",
        user_id="test_user",
        started_at=datetime.now(),
        last_activity=datetime.now()
    )

    profile = UserConversationProfile(user_id="test_user")

    # Simulate conversation turns
    turns = [
        ConversationTurn(
            timestamp=datetime.now(),
            user_query="Show me Samsung phones under 20000",
            intent="search",
            intent_confidence=0.85,
            entities={"category": "Electronics", "brand": "Samsung", "price": {"max": 20000}},
            products_shown=["P001", "P002"],
            response_text="Here are Samsung phones..."
        ),
        ConversationTurn(
            timestamp=datetime.now(),
            user_query="Something cheaper please",
            intent="filter",
            intent_confidence=0.78,
            entities={"price": {"max": 15000}},
            products_shown=["P003"],
            response_text="Here are cheaper options..."
        ),
        ConversationTurn(
            timestamp=datetime.now(),
            user_query="Show me OnePlus phones too",
            intent="search",
            intent_confidence=0.82,
            entities={"category": "Electronics", "brand": "OnePlus"},
            products_shown=["P004", "P005"],
            response_text="Here are OnePlus phones..."
        ),
    ]

    # Learn from each turn
    for turn in turns:
        session.add_turn(turn)
        profile = learner.learn_from_turn(turn, session, profile)

    # Learn from completed session
    profile = learner.learn_from_session(session, profile)

    print(f"\nLearned Profile:")
    print(f"  Common categories: {profile.common_categories}")
    print(f"  Common brands: {profile.common_brands}")
    print(f"  Verbosity preference: {profile.verbosity_preference}")
    print(f"  Prefers alternatives: {profile.prefers_alternatives}")
    print(f"  Session refinements: {session.refinement_count}")

    # Get adaptive config
    from services.conversation_memory import ConversationContext
    context = ConversationContext(
        last_category="Electronics",
        last_brand="Samsung",
        turn_count=3
    )

    config = learner.get_adaptive_response_config(profile, context)
    print(f"\nAdaptive Config:")
    for key, value in config.items():
        print(f"  {key}: {value}")

    # Get suggestions
    suggestions = learner.get_proactive_suggestions(profile, context)
    print(f"\nProactive Suggestions:")
    for suggestion in suggestions:
        print(f"  - {suggestion}")

    # Detect user state
    state = learner.detect_user_state(session, profile)
    print(f"\nDetected User State:")
    for key, value in state.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 60)
    print("Conversation Learner Test Complete!")
