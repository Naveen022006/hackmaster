"""
Advanced Response Generator for Shopping Assistant Chatbot
Transforms static responses into natural, conversational, human-like interactions

Features:
- Dynamic response variations
- Context awareness (session memory)
- Personalized responses based on user behavior
- Confidence-based response adaptation
- Conversational tone with emojis
- Follow-up question generation
"""

import random
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional, Any, Tuple


class ConversationContext:
    """Maintains conversation context for each user session"""

    def __init__(self):
        self.last_intent: Optional[str] = None
        self.last_category: Optional[str] = None
        self.last_price: Optional[float] = None
        self.last_brand: Optional[str] = None
        self.conversation_history: List[Dict] = []
        self.turn_count: int = 0
        self.session_start: datetime = datetime.now()
        self.pending_context: Dict[str, Any] = {}
        self.awaiting_clarification: bool = False
        self.clarification_type: Optional[str] = None

    def update(self, intent: str, entities: Dict, message: str):
        """Update context with new interaction"""
        self.last_intent = intent
        self.turn_count += 1

        # Update entities if provided
        if entities.get('category'):
            self.last_category = entities['category']
        if entities.get('price'):
            self.last_price = entities['price']
        if entities.get('brand'):
            self.last_brand = entities['brand']

        # Store in history
        self.conversation_history.append({
            'turn': self.turn_count,
            'message': message,
            'intent': intent,
            'entities': entities,
            'timestamp': datetime.now().isoformat()
        })

        # Keep only last 10 turns
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

    def get_combined_entities(self, current_entities: Dict) -> Dict:
        """Combine current entities with context for follow-up queries"""
        combined = {}

        # Use current entities first, fall back to context
        combined['category'] = current_entities.get('category') or self.last_category
        combined['price'] = current_entities.get('price') or self.last_price
        combined['brand'] = current_entities.get('brand') or self.last_brand

        return combined

    def is_follow_up(self, current_intent: str, current_entities: Dict) -> bool:
        """Detect if current message is a follow-up to previous query"""
        if not self.last_intent:
            return False

        # Price-only follow-up to a category search
        if (current_entities.get('price') and not current_entities.get('category')
            and self.last_category):
            return True

        # Category-only follow-up to a price query
        if (current_entities.get('category') and not current_entities.get('price')
            and self.last_price):
            return True

        return False

    def clear_pending(self):
        """Clear pending context after resolution"""
        self.awaiting_clarification = False
        self.clarification_type = None
        self.pending_context = {}


class UserPersonalization:
    """Tracks user behavior for personalized responses"""

    def __init__(self):
        self.category_counts: Dict[str, int] = defaultdict(int)
        self.brand_preferences: Dict[str, int] = defaultdict(int)
        self.price_range_history: List[float] = []
        self.liked_products: List[str] = []
        self.disliked_products: List[str] = []
        self.search_patterns: List[str] = []
        self.total_interactions: int = 0
        self.favorite_categories: List[str] = []

    def track_category(self, category: str):
        """Track category interest"""
        if category:
            self.category_counts[category.lower()] += 1
            self._update_favorites()

    def track_brand(self, brand: str):
        """Track brand preference"""
        if brand:
            self.brand_preferences[brand.lower()] += 1

    def track_price(self, price: float):
        """Track price range preference"""
        if price:
            self.price_range_history.append(price)
            # Keep last 20
            if len(self.price_range_history) > 20:
                self.price_range_history = self.price_range_history[-20:]

    def track_feedback(self, product_id: str, feedback_type: str):
        """Track product feedback"""
        if feedback_type == 'like':
            if product_id not in self.liked_products:
                self.liked_products.append(product_id)
        elif feedback_type == 'dislike':
            if product_id not in self.disliked_products:
                self.disliked_products.append(product_id)

    def _update_favorites(self):
        """Update favorite categories based on interaction count"""
        sorted_cats = sorted(
            self.category_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        self.favorite_categories = [cat for cat, _ in sorted_cats[:3]]

    def get_avg_price_range(self) -> Optional[float]:
        """Get average price preference"""
        if self.price_range_history:
            return sum(self.price_range_history) / len(self.price_range_history)
        return None

    def is_returning_to_category(self, category: str) -> bool:
        """Check if user is returning to a frequently searched category"""
        if not category:
            return False
        return self.category_counts.get(category.lower(), 0) >= 3

    def get_personality_traits(self) -> Dict[str, Any]:
        """Analyze user shopping personality"""
        traits = {
            'is_bargain_hunter': False,
            'is_brand_loyal': False,
            'is_explorer': False,
            'preferred_price_tier': 'mid'
        }

        # Check if bargain hunter (frequently uses price filters)
        if self.price_range_history:
            avg_price = self.get_avg_price_range()
            if avg_price and avg_price < 500:
                traits['is_bargain_hunter'] = True
                traits['preferred_price_tier'] = 'budget'
            elif avg_price and avg_price > 5000:
                traits['preferred_price_tier'] = 'premium'

        # Check if brand loyal
        if self.brand_preferences:
            top_brand_count = max(self.brand_preferences.values())
            if top_brand_count >= 3:
                traits['is_brand_loyal'] = True

        # Check if explorer (searches many categories)
        if len(self.category_counts) >= 5:
            traits['is_explorer'] = True

        return traits


class ResponseGenerator:
    """
    Advanced response generator with natural, conversational responses
    """

    def __init__(self):
        # User contexts and personalization data
        self.user_contexts: Dict[str, ConversationContext] = {}
        self.user_personalization: Dict[str, UserPersonalization] = {}

        # Response templates organized by intent
        self._init_response_templates()

        # Greeting variations based on time of day
        self._init_time_greetings()

        # Emoji mappings
        self._init_emojis()

        # Follow-up questions
        self._init_follow_ups()

        # Confidence thresholds
        self.HIGH_CONFIDENCE = 0.8
        self.MEDIUM_CONFIDENCE = 0.5

    def _init_response_templates(self):
        """Initialize response templates for each intent"""

        self.templates = {
            'greeting': {
                'high': [
                    "Hey there! {time_greeting} Ready to find something awesome? {emoji}",
                    "Hi! {time_greeting} What can I help you discover today? {emoji}",
                    "Hello! {time_greeting} I'm here to help you shop smarter {emoji}",
                    "Hey! Welcome back {emoji} What are we looking for today?",
                    "Hi there! {time_greeting} Let's find you something great {emoji}",
                ],
                'medium': [
                    "Hello! How can I help you today? {emoji}",
                    "Hi there! What would you like to explore? {emoji}",
                    "Hey! Ready to help you find what you need {emoji}",
                ],
                'personalized': [
                    "Welcome back, {name}! {time_greeting} Miss your favorite {fav_category}? {emoji}",
                    "Hey! Good to see you again {emoji} Looking for more {fav_category}?",
                    "Hi there! Back for more shopping? I remember you love {fav_category} {emoji}",
                ]
            },

            'goodbye': {
                'high': [
                    "Take care! Happy shopping {emoji}",
                    "See you soon! Thanks for stopping by {emoji}",
                    "Bye for now! Come back anytime {emoji}",
                    "Catch you later! Hope you found something nice {emoji}",
                    "Goodbye! Don't be a stranger {emoji}",
                ],
                'with_cart': [
                    "Bye! Don't forget - you have {cart_count} items waiting in your cart {emoji}",
                    "See you! Your cart has {cart_count} items saved for later {emoji}",
                ]
            },

            'search_product': {
                'high': [
                    "Got it! Let me find the best {category} for you {emoji}",
                    "Nice choice! Searching for {category} now {emoji}",
                    "On it! Here's what we have in {category} {emoji}",
                    "Perfect! Let me pull up our {category} collection {emoji}",
                    "{category}? Great taste! Here's what I found {emoji}",
                ],
                'with_price': [
                    "Looking for {category} under ₹{price}? Let me find the best deals {emoji}",
                    "Budget-friendly {category}? I love it! Here are options under ₹{price} {emoji}",
                    "{category} within ₹{price}? Smart shopping! Check these out {emoji}",
                ],
                'returning_category': [
                    "Back to {category} again? You really know what you like {emoji}",
                    "More {category}? I see a pattern here {emoji} Here's what's new!",
                    "Ah, {category} again! Let me show you some fresh picks {emoji}",
                ],
                'low': [
                    "Let me search for that... {emoji}",
                    "Checking our catalog now {emoji}",
                ]
            },

            'price_query': {
                'high': [
                    "Budget of ₹{price}? Smart! Let me find the best value {emoji}",
                    "Under ₹{price}? I got you! Here are some great options {emoji}",
                    "Looking for deals under ₹{price}? You're in the right place {emoji}",
                    "₹{price} budget? Let's make every rupee count {emoji}",
                ],
                'with_category': [
                    "Affordable {category} under ₹{price}? Perfect combo! {emoji}",
                    "{category} within budget? Here's what I found under ₹{price} {emoji}",
                    "Smart choice! Best {category} under ₹{price} coming right up {emoji}",
                ],
                'follow_up': [
                    "Got it! Filtering {category} under ₹{price} for you {emoji}",
                    "Adding that price filter... Here's {category} under ₹{price} {emoji}",
                    "Nice! Combining your search - {category} under ₹{price} {emoji}",
                ],
                'bargain_hunter': [
                    "A fellow bargain hunter! {emoji} Let me find the best deals under ₹{price}",
                    "Love the budget consciousness! Here's amazing value under ₹{price} {emoji}",
                ]
            },

            'recommendation': {
                'high': [
                    "Based on what you've been browsing, I think you'll love these {emoji}",
                    "Picked these just for you! {emoji}",
                    "Here's my top picks based on your taste {emoji}",
                    "I've got some recommendations I think you'll really like {emoji}",
                ],
                'new_user': [
                    "Since you're new here, let me show you our best sellers {emoji}",
                    "Welcome! Here are some popular picks to get you started {emoji}",
                    "Let me introduce you to our top-rated products {emoji}",
                ],
                'personalized': [
                    "Based on your love for {fav_category}, you might like these {emoji}",
                    "Since you've been into {fav_category}, check these out {emoji}",
                    "Curated for you based on your {fav_category} interests {emoji}",
                ]
            },

            'category_recommendation': {
                'high': [
                    "Top picks in {category}? You got it {emoji}",
                    "Best {category} coming right up! {emoji}",
                    "Excellent choice! Here are the hottest {category} {emoji}",
                    "Let me show you our finest {category} {emoji}",
                ],
                'with_personality': [
                    "Premium {category} for someone with refined taste {emoji}",
                    "Budget-friendly {category} that don't compromise on quality {emoji}",
                ]
            },

            'cart_add': {
                'high': [
                    "Added! Great choice {emoji}",
                    "Done! It's in your cart {emoji}",
                    "Nice pick! Added to cart {emoji}",
                    "Got it! One more item secured {emoji}",
                    "Added successfully! Your cart is looking good {emoji}",
                ],
                'multiple_items': [
                    "Added! You now have {cart_count} items in your cart {emoji}",
                    "Another great pick! Cart total: {cart_count} items {emoji}",
                ]
            },

            'cart_view': {
                'with_items': [
                    "Here's what's in your cart {emoji}",
                    "Let me show you your cart ({cart_count} items) {emoji}",
                    "Your shopping cart - {cart_count} items waiting for you {emoji}",
                ],
                'empty': [
                    "Your cart is empty! Let's fix that {emoji}",
                    "Nothing in the cart yet. Ready to start shopping? {emoji}",
                    "Cart's empty! Want me to suggest something? {emoji}",
                ]
            },

            'order_status': {
                'high': [
                    "Let me check on that for you {emoji}",
                    "Checking your order status now {emoji}",
                    "One moment while I look that up {emoji}",
                ]
            },

            'help': {
                'high': [
                    "Happy to help! Here's what I can do for you {emoji}",
                    "I'm here for you! Let me explain what I can do {emoji}",
                    "Sure thing! Here's a quick guide {emoji}",
                ],
                'capabilities': """
I can help you with:
{emoji_search} **Search products** - "Show me laptops" or "Find running shoes"
{emoji_price} **Filter by price** - "Under ₹5000" or "Budget phones"
{emoji_rec} **Get recommendations** - "Suggest something for me"
{emoji_deals} **Find deals** - "Show me offers" or "What's on sale?"
{emoji_cart} **Manage cart** - "Add to cart" or "Show my cart"
{emoji_feedback} **Give feedback** - Like or dislike products

Just type naturally - I'll understand! {emoji}
"""
            },

            'feedback': {
                'like': [
                    "Awesome! I'll remember you like this {emoji}",
                    "Noted! I'll show you more like this {emoji}",
                    "Great taste! Added to your preferences {emoji}",
                    "Love it! Your recommendations just got better {emoji}",
                ],
                'dislike': [
                    "Got it! I'll show you less of this type {emoji}",
                    "No problem! Updating your preferences {emoji}",
                    "Understood! I'll find better matches for you {emoji}",
                ]
            },

            'compare': {
                'high': [
                    "Good thinking! Let me compare those for you {emoji}",
                    "Smart move! Here's a side-by-side comparison {emoji}",
                    "Comparison coming up! This will help you decide {emoji}",
                ]
            },

            'deals': {
                'high': [
                    "Deal hunter! Here are today's best offers {emoji}",
                    "Great timing! Check out these hot deals {emoji}",
                    "Savings alert! Here's what's on sale {emoji}",
                    "Looking for bargains? You came to the right place {emoji}",
                ],
                'personalized': [
                    "Deals in your favorite category {fav_category} {emoji}",
                    "Found some {fav_category} deals just for you {emoji}",
                ]
            },

            'clarification': {
                'low_confidence': [
                    "Hmm, let me make sure I understood that right... {emoji}",
                    "Just to clarify - did you mean {suggestion}? {emoji}",
                    "I want to get this right - are you looking for {suggestion}? {emoji}",
                ],
                'ambiguous': [
                    "I found a few possibilities. Could you be more specific? {emoji}",
                    "That could mean a few things - can you tell me more? {emoji}",
                ],
                'missing_info': [
                    "What {missing} are you looking for? {emoji}",
                    "Could you specify the {missing}? {emoji}",
                ]
            },

            'fallback': [
                "I'm not quite sure what you mean. Could you rephrase that? {emoji}",
                "Hmm, I didn't catch that. Try asking in a different way? {emoji}",
                "Let me help you better - what exactly are you looking for? {emoji}",
            ]
        }

    def _init_time_greetings(self):
        """Initialize time-based greetings"""
        self.time_greetings = {
            'morning': [
                "Good morning!",
                "Morning!",
                "Rise and shine!",
            ],
            'afternoon': [
                "Good afternoon!",
                "Afternoon!",
            ],
            'evening': [
                "Good evening!",
                "Evening!",
            ],
            'night': [
                "Late night shopping?",
                "Burning the midnight oil?",
            ]
        }

    def _init_emojis(self):
        """Initialize emoji mappings"""
        self.emojis = {
            'greeting': ['👋', '😊', '🙌', '✨'],
            'goodbye': ['👋', '😊', '🛍️', '✌️'],
            'search': ['🔍', '👀', '📦', '🎯'],
            'price': ['💰', '🏷️', '💵', '🎯'],
            'recommendation': ['⭐', '✨', '🎁', '💫'],
            'cart': ['🛒', '✅', '🛍️', '📦'],
            'help': ['💡', '🤝', '📚', 'ℹ️'],
            'feedback_like': ['👍', '❤️', '🎉', '⭐'],
            'feedback_dislike': ['👎', '📝', '✅'],
            'deals': ['🔥', '💥', '🎉', '🏷️'],
            'compare': ['⚖️', '🔄', '📊'],
            'thinking': ['🤔', '💭', '🧐'],
            'success': ['✅', '👍', '🎉'],
            'neutral': ['😊', '👍', '✨'],
            # For help section
            'emoji_search': '🔍',
            'emoji_price': '💰',
            'emoji_rec': '⭐',
            'emoji_deals': '🔥',
            'emoji_cart': '🛒',
            'emoji_feedback': '👍',
        }

    def _init_follow_ups(self):
        """Initialize follow-up questions"""
        self.follow_ups = {
            'search_product': [
                "Want me to filter by price or brand?",
                "Need a specific price range?",
                "Looking for any particular brand?",
                "Should I sort by rating or price?",
            ],
            'price_query': [
                "Any specific category in mind?",
                "Want me to show only top-rated items?",
                "Should I filter by brand too?",
            ],
            'recommendation': [
                "Want to see a specific category?",
                "Should I filter these by price?",
                "Looking for deals on these?",
            ],
            'category_recommendation': [
                "Any budget in mind?",
                "Want to see only discounted items?",
                "Should I sort by popularity?",
            ],
            'cart_view': [
                "Ready to checkout?",
                "Want to continue shopping?",
                "Should I suggest similar items?",
            ],
            'deals': [
                "Any category you're interested in?",
                "Want me to filter by your favorites?",
            ],
            'compare': [
                "Need more details on any of these?",
                "Want to add any to your cart?",
            ]
        }

    def _get_emoji(self, category: str) -> str:
        """Get a random emoji from category"""
        emojis = self.emojis.get(category, self.emojis['neutral'])
        return random.choice(emojis)

    def _get_time_greeting(self) -> str:
        """Get appropriate greeting based on time of day"""
        hour = datetime.now().hour

        if 5 <= hour < 12:
            return random.choice(self.time_greetings['morning'])
        elif 12 <= hour < 17:
            return random.choice(self.time_greetings['afternoon'])
        elif 17 <= hour < 21:
            return random.choice(self.time_greetings['evening'])
        else:
            return random.choice(self.time_greetings['night'])

    def _get_context(self, user_id: str) -> ConversationContext:
        """Get or create conversation context for user"""
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = ConversationContext()
        return self.user_contexts[user_id]

    def _get_personalization(self, user_id: str) -> UserPersonalization:
        """Get or create personalization data for user"""
        if user_id not in self.user_personalization:
            self.user_personalization[user_id] = UserPersonalization()
        return self.user_personalization[user_id]

    def _format_price(self, price: float) -> str:
        """Format price for display"""
        if price >= 1000:
            return f"{price:,.0f}"
        return f"{price:.0f}"

    def _select_template(self, intent: str, confidence: float,
                        context: ConversationContext,
                        personalization: UserPersonalization,
                        entities: Dict) -> str:
        """Select appropriate template based on context"""

        templates = self.templates.get(intent, self.templates['fallback'])

        if isinstance(templates, list):
            return random.choice(templates)

        # Handle confidence levels
        if confidence >= self.HIGH_CONFIDENCE:
            # Check for personalized templates
            if 'personalized' in templates and personalization.favorite_categories:
                if random.random() < 0.4:  # 40% chance for personalized
                    return random.choice(templates['personalized'])

            # Check for specific conditions
            if intent == 'search_product':
                if entities.get('price'):
                    return random.choice(templates.get('with_price', templates['high']))
                if entities.get('category') and personalization.is_returning_to_category(entities['category']):
                    return random.choice(templates.get('returning_category', templates['high']))

            elif intent == 'price_query':
                if context.is_follow_up(intent, entities):
                    return random.choice(templates.get('follow_up', templates['high']))
                if entities.get('category'):
                    return random.choice(templates.get('with_category', templates['high']))
                traits = personalization.get_personality_traits()
                if traits['is_bargain_hunter'] and 'bargain_hunter' in templates:
                    return random.choice(templates['bargain_hunter'])

            elif intent == 'recommendation':
                if personalization.total_interactions < 3:
                    return random.choice(templates.get('new_user', templates['high']))

            return random.choice(templates.get('high', list(templates.values())[0]))

        elif confidence >= self.MEDIUM_CONFIDENCE:
            return random.choice(templates.get('medium', templates.get('high', [templates])))

        else:
            return random.choice(templates.get('low', templates.get('high', [templates])))

    def generate_response(
        self,
        intent: str,
        entities: Dict,
        confidence: float,
        user_id: str,
        message: str = "",
        cart_count: int = 0,
        products_count: int = 0,
        feedback_type: str = None
    ) -> Dict[str, Any]:
        """
        Generate a natural, contextual response

        Args:
            intent: Detected intent from LSTM
            entities: Extracted entities (category, price, etc.)
            confidence: LSTM confidence score
            user_id: User identifier
            message: Original user message
            cart_count: Number of items in cart
            products_count: Number of products being returned
            feedback_type: 'like' or 'dislike' for feedback intent

        Returns:
            Dict with 'text', 'follow_up', 'action', 'confidence_note'
        """

        # Get user context and personalization
        context = self._get_context(user_id)
        personalization = self._get_personalization(user_id)

        # Handle follow-up detection
        if context.is_follow_up(intent, entities):
            entities = context.get_combined_entities(entities)

        # Update context
        context.update(intent, entities, message)

        # Track personalization
        if entities.get('category'):
            personalization.track_category(entities['category'])
        if entities.get('price'):
            personalization.track_price(entities['price'])
        personalization.total_interactions += 1

        # Select and format template
        template = self._select_template(intent, confidence, context, personalization, entities)

        # Prepare format variables
        format_vars = {
            'emoji': self._get_emoji(self._get_emoji_category(intent, feedback_type)),
            'time_greeting': self._get_time_greeting(),
            'category': entities.get('category', 'products'),
            'price': self._format_price(entities.get('price', 0)) if entities.get('price') else '',
            'brand': entities.get('brand', ''),
            'cart_count': cart_count,
            'fav_category': personalization.favorite_categories[0] if personalization.favorite_categories else 'shopping',
            'name': 'friend',  # Could be personalized
        }

        # Format response text
        try:
            response_text = template.format(**format_vars)
        except KeyError:
            response_text = template.replace('{emoji}', format_vars['emoji'])

        # Handle special intents
        if intent == 'cart_view':
            if cart_count == 0:
                response_text = random.choice(self.templates['cart_view']['empty']).format(**format_vars)
            else:
                response_text = random.choice(self.templates['cart_view']['with_items']).format(**format_vars)

        elif intent == 'feedback':
            if feedback_type == 'like':
                response_text = random.choice(self.templates['feedback']['like']).format(**format_vars)
                personalization.track_feedback("", 'like')
            else:
                response_text = random.choice(self.templates['feedback']['dislike']).format(**format_vars)
                personalization.track_feedback("", 'dislike')

        elif intent == 'help':
            response_text = random.choice(self.templates['help']['high']).format(**format_vars)
            response_text += "\n" + self.templates['help']['capabilities'].format(**self.emojis)

        # Generate follow-up question
        follow_up = self._generate_follow_up(intent, entities, confidence, context)

        # Add confidence note for low confidence
        confidence_note = None
        if confidence < self.MEDIUM_CONFIDENCE:
            confidence_note = self._generate_clarification(intent, entities, confidence)

        # Build response
        response = {
            'text': response_text,
            'follow_up': follow_up,
            'action': self._get_action(intent),
            'confidence_note': confidence_note,
            'is_follow_up_query': context.is_follow_up(intent, entities),
            'combined_entities': entities if context.is_follow_up(intent, entities) else None
        }

        return response

    def _get_emoji_category(self, intent: str, feedback_type: str = None) -> str:
        """Map intent to emoji category"""
        emoji_map = {
            'greeting': 'greeting',
            'goodbye': 'goodbye',
            'search_product': 'search',
            'price_query': 'price',
            'recommendation': 'recommendation',
            'category_recommendation': 'recommendation',
            'cart_add': 'cart',
            'cart_view': 'cart',
            'help': 'help',
            'feedback': f'feedback_{feedback_type}' if feedback_type else 'neutral',
            'compare': 'compare',
            'deals': 'deals',
            'order_status': 'neutral',
        }
        return emoji_map.get(intent, 'neutral')

    def _get_action(self, intent: str) -> str:
        """Get action type for frontend"""
        action_map = {
            'greeting': 'message_only',
            'goodbye': 'message_only',
            'search_product': 'show_products',
            'price_query': 'show_products',
            'recommendation': 'show_products',
            'category_recommendation': 'show_products',
            'cart_add': 'update_cart',
            'cart_view': 'show_cart',
            'help': 'show_help',
            'feedback': 'update_preferences',
            'compare': 'show_comparison',
            'deals': 'show_products',
            'order_status': 'show_orders',
        }
        return action_map.get(intent, 'message_only')

    def _generate_follow_up(
        self,
        intent: str,
        entities: Dict,
        confidence: float,
        context: ConversationContext
    ) -> Optional[str]:
        """Generate contextual follow-up question"""

        # Don't add follow-ups for low confidence
        if confidence < self.MEDIUM_CONFIDENCE:
            return None

        # 60% chance to include follow-up
        if random.random() > 0.6:
            return None

        follow_ups = self.follow_ups.get(intent, [])
        if not follow_ups:
            return None

        # Filter based on what's already known
        filtered = []
        for fup in follow_ups:
            if 'price' in fup.lower() and entities.get('price'):
                continue
            if 'brand' in fup.lower() and entities.get('brand'):
                continue
            if 'category' in fup.lower() and entities.get('category'):
                continue
            filtered.append(fup)

        if filtered:
            return random.choice(filtered)
        return None

    def _generate_clarification(
        self,
        intent: str,
        entities: Dict,
        confidence: float
    ) -> str:
        """Generate clarification request for low confidence"""

        templates = self.templates['clarification']

        # Build suggestion based on intent
        suggestions = {
            'search_product': 'searching for products',
            'price_query': 'filtering by price',
            'recommendation': 'personalized recommendations',
            'category_recommendation': f"recommendations in {entities.get('category', 'a category')}",
        }

        suggestion = suggestions.get(intent, 'something specific')

        template = random.choice(templates['low_confidence'])
        return template.format(
            suggestion=suggestion,
            emoji=self._get_emoji('thinking')
        )

    def handle_context_continuation(
        self,
        user_id: str,
        new_message: str,
        new_intent: str,
        new_entities: Dict
    ) -> Tuple[Dict, bool]:
        """
        Handle context continuation for follow-up messages

        Returns:
            Tuple of (combined_entities, is_continuation)
        """
        context = self._get_context(user_id)

        # Check if this is a continuation
        is_continuation = context.is_follow_up(new_intent, new_entities)

        if is_continuation:
            combined = context.get_combined_entities(new_entities)
            return combined, True

        return new_entities, False

    def get_personalized_greeting(self, user_id: str) -> str:
        """Generate personalized greeting for returning user"""
        personalization = self._get_personalization(user_id)
        context = self._get_context(user_id)

        if personalization.total_interactions > 5:
            # Returning user
            templates = self.templates['greeting']['personalized']
            fav_cat = personalization.favorite_categories[0] if personalization.favorite_categories else 'shopping'

            return random.choice(templates).format(
                name='there',
                fav_category=fav_cat,
                emoji=self._get_emoji('greeting'),
                time_greeting=self._get_time_greeting()
            )

        return self.generate_response(
            'greeting', {}, 0.95, user_id
        )['text']

    def reset_context(self, user_id: str):
        """Reset conversation context for user"""
        if user_id in self.user_contexts:
            self.user_contexts[user_id] = ConversationContext()


# Global instance
response_generator = ResponseGenerator()


def generate_response(
    intent: str,
    entities: Dict,
    confidence: float,
    user_id: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Main function to generate chatbot response

    Args:
        intent: Detected intent from LSTM
        entities: Extracted entities
        confidence: Confidence score
        user_id: User identifier
        **kwargs: Additional context (cart_count, message, etc.)

    Returns:
        Response dictionary with text, follow_up, action
    """
    return response_generator.generate_response(
        intent=intent,
        entities=entities,
        confidence=confidence,
        user_id=user_id,
        **kwargs
    )


def get_follow_up(intent: str) -> Optional[str]:
    """Get a follow-up question for an intent"""
    follow_ups = response_generator.follow_ups.get(intent, [])
    return random.choice(follow_ups) if follow_ups else None


def personalize_response(user_id: str, base_response: str) -> str:
    """Add personalization to a base response"""
    personalization = response_generator._get_personalization(user_id)

    # Add personalization hints
    if personalization.favorite_categories:
        fav = personalization.favorite_categories[0]
        if fav.lower() not in base_response.lower():
            hints = [
                f" Also, check out our new {fav} arrivals!",
                f" Don't forget to browse {fav} - we have new stock!",
            ]
            if random.random() < 0.3:  # 30% chance
                base_response += random.choice(hints)

    return base_response


def handle_context(
    current_input: str,
    session_data: Dict,
    intent: str,
    entities: Dict
) -> Dict:
    """
    Handle context from session for follow-up queries

    Args:
        current_input: Current user message
        session_data: Session data containing user_id etc.
        intent: Current detected intent
        entities: Current extracted entities

    Returns:
        Updated entities with context
    """
    user_id = session_data.get('user_id', 'unknown')
    combined, is_continuation = response_generator.handle_context_continuation(
        user_id, current_input, intent, entities
    )

    return {
        'entities': combined,
        'is_continuation': is_continuation,
        'original_entities': entities
    }


# For testing
if __name__ == '__main__':
    # Test the response generator
    print("=" * 60)
    print("Testing Response Generator")
    print("=" * 60)

    test_cases = [
        ('greeting', {}, 0.95),
        ('search_product', {'category': 'Electronics'}, 0.88),
        ('price_query', {'price': 5000}, 0.82),
        ('price_query', {'category': 'Laptops', 'price': 50000}, 0.91),
        ('recommendation', {}, 0.85),
        ('deals', {}, 0.90),
        ('cart_view', {}, 0.95),
        ('help', {}, 0.92),
        ('goodbye', {}, 0.95),
    ]

    user_id = 'TEST_USER_001'

    for intent, entities, confidence in test_cases:
        response = generate_response(
            intent=intent,
            entities=entities,
            confidence=confidence,
            user_id=user_id,
            cart_count=3
        )

        print(f"\nIntent: {intent} | Confidence: {confidence}")
        print(f"Entities: {entities}")
        print(f"Response: {response['text']}")
        if response['follow_up']:
            print(f"Follow-up: {response['follow_up']}")
        print("-" * 40)
