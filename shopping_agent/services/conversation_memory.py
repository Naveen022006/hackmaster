"""
Conversation Memory Service for Personal Shopping Agent.
Manages conversation history, sessions, and user conversation profiles.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import uuid
import json
import os
from pathlib import Path

# Get project root for file storage
PROJECT_ROOT = Path(__file__).parent.parent
CONVERSATION_DATA_DIR = PROJECT_ROOT / "data" / "conversations"


@dataclass
class ConversationTurn:
    """Represents a single conversation turn."""
    timestamp: datetime
    user_query: str
    intent: str
    intent_confidence: float
    entities: Dict[str, Any]
    products_shown: List[str]  # List of product IDs shown
    response_text: str
    user_feedback: Optional[str] = None  # "liked", "clicked", "purchased", None

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "user_query": self.user_query,
            "intent": self.intent,
            "intent_confidence": self.intent_confidence,
            "entities": self.entities,
            "products_shown": self.products_shown,
            "response_text": self.response_text,
            "user_feedback": self.user_feedback
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ConversationTurn":
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            user_query=data["user_query"],
            intent=data["intent"],
            intent_confidence=data.get("intent_confidence", 0.0),
            entities=data.get("entities", {}),
            products_shown=data.get("products_shown", []),
            response_text=data.get("response_text", ""),
            user_feedback=data.get("user_feedback")
        )


@dataclass
class ConversationSession:
    """Represents a user's conversation session."""
    session_id: str
    user_id: str
    started_at: datetime
    last_activity: datetime
    turns: List[ConversationTurn] = field(default_factory=list)

    # Accumulated context within session
    mentioned_categories: List[str] = field(default_factory=list)
    mentioned_brands: List[str] = field(default_factory=list)
    price_preferences: Dict[str, float] = field(default_factory=dict)
    feature_interests: List[str] = field(default_factory=list)

    # Products context for reference resolution
    products_shown_all: List[str] = field(default_factory=list)

    # Session metrics
    refinement_count: int = 0
    successful_queries: int = 0

    def add_turn(self, turn: ConversationTurn) -> None:
        """Add a conversation turn to the session."""
        self.turns.append(turn)
        self.last_activity = datetime.now()

        # Update accumulated context
        if turn.entities.get("category"):
            cat = turn.entities["category"]
            if cat not in self.mentioned_categories:
                self.mentioned_categories.append(cat)

        if turn.entities.get("brand"):
            brand = turn.entities["brand"]
            if brand not in self.mentioned_brands:
                self.mentioned_brands.append(brand)

        if turn.entities.get("price"):
            self.price_preferences.update(turn.entities["price"])

        if turn.entities.get("features"):
            for feature in turn.entities["features"]:
                if feature not in self.feature_interests:
                    self.feature_interests.append(feature)

        # Track products shown
        self.products_shown_all.extend(turn.products_shown)

    def get_last_turn(self) -> Optional[ConversationTurn]:
        """Get the most recent turn."""
        return self.turns[-1] if self.turns else None

    def get_recent_products(self, limit: int = 10) -> List[str]:
        """Get recently shown product IDs."""
        return self.products_shown_all[-limit:] if self.products_shown_all else []

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "started_at": self.started_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "turns": [t.to_dict() for t in self.turns],
            "mentioned_categories": self.mentioned_categories,
            "mentioned_brands": self.mentioned_brands,
            "price_preferences": self.price_preferences,
            "feature_interests": self.feature_interests,
            "products_shown_all": self.products_shown_all,
            "refinement_count": self.refinement_count,
            "successful_queries": self.successful_queries
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ConversationSession":
        """Create from dictionary."""
        session = cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            started_at=datetime.fromisoformat(data["started_at"]),
            last_activity=datetime.fromisoformat(data["last_activity"]),
            mentioned_categories=data.get("mentioned_categories", []),
            mentioned_brands=data.get("mentioned_brands", []),
            price_preferences=data.get("price_preferences", {}),
            feature_interests=data.get("feature_interests", []),
            products_shown_all=data.get("products_shown_all", []),
            refinement_count=data.get("refinement_count", 0),
            successful_queries=data.get("successful_queries", 0)
        )
        session.turns = [ConversationTurn.from_dict(t) for t in data.get("turns", [])]
        return session


@dataclass
class UserConversationProfile:
    """Long-term conversation profile for learning user patterns."""
    user_id: str
    display_name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    # Interaction metrics
    interaction_count: int = 0
    total_sessions: int = 0
    last_session_date: Optional[datetime] = None

    # Learned patterns (weighted by recency and frequency)
    common_intents: Dict[str, float] = field(default_factory=dict)
    common_categories: Dict[str, float] = field(default_factory=dict)
    common_brands: Dict[str, float] = field(default_factory=dict)
    common_features: Dict[str, float] = field(default_factory=dict)

    # Response preferences (learned)
    verbosity_preference: str = "normal"  # "brief", "normal", "detailed"
    prefers_detailed_specs: bool = False
    prefers_alternatives: bool = True
    prefers_price_comparison: bool = True

    # Purchase patterns
    purchase_categories: List[str] = field(default_factory=list)
    avg_purchase_price: float = 0.0

    def get_top_categories(self, limit: int = 3) -> List[str]:
        """Get top preferred categories."""
        if not self.common_categories:
            return []
        sorted_cats = sorted(self.common_categories.items(), key=lambda x: x[1], reverse=True)
        return [cat for cat, _ in sorted_cats[:limit]]

    def get_top_brands(self, limit: int = 3) -> List[str]:
        """Get top preferred brands."""
        if not self.common_brands:
            return []
        sorted_brands = sorted(self.common_brands.items(), key=lambda x: x[1], reverse=True)
        return [brand for brand, _ in sorted_brands[:limit]]

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "user_id": self.user_id,
            "display_name": self.display_name,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "interaction_count": self.interaction_count,
            "total_sessions": self.total_sessions,
            "last_session_date": self.last_session_date.isoformat() if self.last_session_date else None,
            "common_intents": self.common_intents,
            "common_categories": self.common_categories,
            "common_brands": self.common_brands,
            "common_features": self.common_features,
            "verbosity_preference": self.verbosity_preference,
            "prefers_detailed_specs": self.prefers_detailed_specs,
            "prefers_alternatives": self.prefers_alternatives,
            "prefers_price_comparison": self.prefers_price_comparison,
            "purchase_categories": self.purchase_categories,
            "avg_purchase_price": self.avg_purchase_price
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "UserConversationProfile":
        """Create from dictionary."""
        profile = cls(
            user_id=data["user_id"],
            display_name=data.get("display_name"),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            last_updated=datetime.fromisoformat(data.get("last_updated", datetime.now().isoformat())),
            interaction_count=data.get("interaction_count", 0),
            total_sessions=data.get("total_sessions", 0),
            verbosity_preference=data.get("verbosity_preference", "normal"),
            prefers_detailed_specs=data.get("prefers_detailed_specs", False),
            prefers_alternatives=data.get("prefers_alternatives", True),
            prefers_price_comparison=data.get("prefers_price_comparison", True),
            purchase_categories=data.get("purchase_categories", []),
            avg_purchase_price=data.get("avg_purchase_price", 0.0)
        )
        profile.common_intents = data.get("common_intents", {})
        profile.common_categories = data.get("common_categories", {})
        profile.common_brands = data.get("common_brands", {})
        profile.common_features = data.get("common_features", {})

        if data.get("last_session_date"):
            profile.last_session_date = datetime.fromisoformat(data["last_session_date"])

        return profile


@dataclass
class ConversationContext:
    """Context information for natural response generation."""
    # Recent conversation
    last_query: Optional[str] = None
    last_intent: Optional[str] = None
    last_category: Optional[str] = None
    last_brand: Optional[str] = None
    last_price_range: Optional[Dict] = None

    # Reference tracking
    products_shown: List[str] = field(default_factory=list)

    # Conversation state
    is_refinement: bool = False
    references_previous: bool = False
    turn_count: int = 0
    queries_this_session: int = 0

    # Session info
    is_new_user: bool = True
    is_returning_session: bool = False


class ConversationMemoryService:
    """Service for managing conversation memory and persistence."""

    SESSION_TIMEOUT_MINUTES = 30

    def __init__(self, db_service=None):
        """Initialize memory service."""
        self.db = db_service
        self.active_sessions: Dict[str, ConversationSession] = {}
        self.user_profiles: Dict[str, UserConversationProfile] = {}

        # Ensure data directory exists
        CONVERSATION_DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Load existing profiles from file if no DB
        if not self.db:
            self._load_profiles_from_file()

    def get_or_create_session(self, user_id: str) -> ConversationSession:
        """Get active session for user or create a new one."""
        # Check for existing active session
        if user_id in self.active_sessions:
            session = self.active_sessions[user_id]
            # Check if session is still valid (not timed out)
            time_since_activity = datetime.now() - session.last_activity
            if time_since_activity < timedelta(minutes=self.SESSION_TIMEOUT_MINUTES):
                return session
            else:
                # Session timed out, save and create new
                self._end_session(session)

        # Create new session
        session = ConversationSession(
            session_id=f"sess_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            started_at=datetime.now(),
            last_activity=datetime.now()
        )
        self.active_sessions[user_id] = session
        return session

    def add_turn(self, user_id: str, turn: ConversationTurn) -> None:
        """Add a conversation turn to the user's session."""
        session = self.get_or_create_session(user_id)
        session.add_turn(turn)

        # Update user profile interaction count
        profile = self.get_user_profile(user_id)
        profile.interaction_count += 1
        profile.last_updated = datetime.now()

    def get_conversation_context(self, user_id: str) -> ConversationContext:
        """Build conversation context from session history."""
        context = ConversationContext()
        profile = self.get_user_profile(user_id)

        # Set user status
        context.is_new_user = profile.interaction_count == 0

        # Get session if exists
        session = self.active_sessions.get(user_id)
        if not session or not session.turns:
            return context

        context.turn_count = len(session.turns)
        context.queries_this_session = len(session.turns)

        # Get last turn info
        last_turn = session.get_last_turn()
        if last_turn:
            context.last_query = last_turn.user_query
            context.last_intent = last_turn.intent
            context.last_category = last_turn.entities.get("category")
            context.last_brand = last_turn.entities.get("brand")
            context.last_price_range = last_turn.entities.get("price")
            context.products_shown = session.get_recent_products(10)

        return context

    def get_user_profile(self, user_id: str) -> UserConversationProfile:
        """Get or create user conversation profile."""
        if user_id not in self.user_profiles:
            # Try to load from storage
            profile = self._load_profile(user_id)
            if profile:
                self.user_profiles[user_id] = profile
            else:
                # Create new profile
                self.user_profiles[user_id] = UserConversationProfile(user_id=user_id)

        return self.user_profiles[user_id]

    def update_user_profile(self, profile: UserConversationProfile) -> None:
        """Update and persist user profile."""
        profile.last_updated = datetime.now()
        self.user_profiles[profile.user_id] = profile
        self._save_profile(profile)

    def record_feedback(self, user_id: str, turn_index: int, feedback: str) -> None:
        """Record user feedback on a specific turn."""
        session = self.active_sessions.get(user_id)
        if session and 0 <= turn_index < len(session.turns):
            session.turns[turn_index].user_feedback = feedback

    def _end_session(self, session: ConversationSession) -> None:
        """End a session and persist it."""
        # Save session to file/db
        self._save_session(session)

        # Update user profile with session summary
        profile = self.get_user_profile(session.user_id)
        profile.total_sessions += 1
        profile.last_session_date = datetime.now()
        self._save_profile(profile)

    def _save_session(self, session: ConversationSession) -> None:
        """Save session to storage."""
        if self.db:
            self.db.save_conversation_session(session.to_dict())
        else:
            # File-based storage
            session_file = CONVERSATION_DATA_DIR / f"session_{session.session_id}.json"
            with open(session_file, "w") as f:
                json.dump(session.to_dict(), f, indent=2)

    def _save_profile(self, profile: UserConversationProfile) -> None:
        """Save user profile to storage."""
        if self.db:
            self.db.save_conversation_profile(profile.user_id, profile.to_dict())
        else:
            # File-based storage
            profiles_file = CONVERSATION_DATA_DIR / "user_profiles.json"
            all_profiles = {}
            if profiles_file.exists():
                with open(profiles_file, "r") as f:
                    all_profiles = json.load(f)
            all_profiles[profile.user_id] = profile.to_dict()
            with open(profiles_file, "w") as f:
                json.dump(all_profiles, f, indent=2)

    def _load_profile(self, user_id: str) -> Optional[UserConversationProfile]:
        """Load user profile from storage."""
        if self.db:
            data = self.db.get_conversation_profile(user_id)
            if data:
                return UserConversationProfile.from_dict(data)
        else:
            profiles_file = CONVERSATION_DATA_DIR / "user_profiles.json"
            if profiles_file.exists():
                with open(profiles_file, "r") as f:
                    all_profiles = json.load(f)
                if user_id in all_profiles:
                    return UserConversationProfile.from_dict(all_profiles[user_id])
        return None

    def _load_profiles_from_file(self) -> None:
        """Load all profiles from file storage."""
        profiles_file = CONVERSATION_DATA_DIR / "user_profiles.json"
        if profiles_file.exists():
            try:
                with open(profiles_file, "r") as f:
                    all_profiles = json.load(f)
                for user_id, data in all_profiles.items():
                    self.user_profiles[user_id] = UserConversationProfile.from_dict(data)
            except Exception as e:
                print(f"Warning: Could not load profiles: {e}")


# Singleton instance
_memory_service: Optional[ConversationMemoryService] = None


def get_memory_service(db_service=None) -> ConversationMemoryService:
    """Get or create the memory service singleton."""
    global _memory_service
    if _memory_service is None:
        _memory_service = ConversationMemoryService(db_service)
    return _memory_service


if __name__ == "__main__":
    # Test the conversation memory system
    print("Testing Conversation Memory System")
    print("=" * 60)

    memory = get_memory_service()

    # Test session creation
    user_id = "test_user_001"
    session = memory.get_or_create_session(user_id)
    print(f"Created session: {session.session_id}")

    # Add some turns
    turn1 = ConversationTurn(
        timestamp=datetime.now(),
        user_query="Show me Samsung phones",
        intent="search",
        intent_confidence=0.85,
        entities={"category": "Electronics", "brand": "Samsung"},
        products_shown=["P001", "P002", "P003"],
        response_text="Here are some Samsung phones..."
    )
    memory.add_turn(user_id, turn1)

    turn2 = ConversationTurn(
        timestamp=datetime.now(),
        user_query="Under 20000",
        intent="filter",
        intent_confidence=0.78,
        entities={"price": {"max": 20000}},
        products_shown=["P001", "P003"],
        response_text="Filtered to under 20,000..."
    )
    memory.add_turn(user_id, turn2)

    # Get context
    context = memory.get_conversation_context(user_id)
    print(f"\nContext after 2 turns:")
    print(f"  Turn count: {context.turn_count}")
    print(f"  Last intent: {context.last_intent}")
    print(f"  Last brand: {context.last_brand}")
    print(f"  Products shown: {context.products_shown}")

    # Check profile
    profile = memory.get_user_profile(user_id)
    print(f"\nUser profile:")
    print(f"  Interaction count: {profile.interaction_count}")
    print(f"  Verbosity preference: {profile.verbosity_preference}")

    print("\n" + "=" * 60)
    print("Conversation Memory System Test Complete!")
