"""
Enhanced NLP Module for Personal Shopping Agent.
Handles intent classification, entity extraction, and smart response generation.
"""
import re
import random
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import pickle
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import NLP_CONFIG, MODELS_DIR, CATEGORIES


class IntentClassifier:
    """Advanced intent classifier with expanded training data."""

    INTENT_LABELS = ["search", "buy", "compare", "filter", "greeting", "help", "recommendation", "inquiry", "refine", "general"]

    # Product keywords for fallback detection
    PRODUCT_KEYWORDS = [
        "phone", "laptop", "watch", "shoe", "shirt", "book", "headphone", "camera", "tv",
        "speaker", "tablet", "earbuds", "earphones", "computer", "monitor", "keyboard",
        "mouse", "charger", "powerbank", "bag", "wallet", "belt", "jeans", "dress",
        "jacket", "sneakers", "sandals", "perfume", "cream", "shampoo", "toys", "games"
    ]

    # Action verbs for intent detection
    ACTION_VERBS = ["show", "find", "get", "buy", "search", "compare", "display", "list", "browse", "look"]

    # Expanded training data for better classification (400+ examples)
    TRAINING_DATA = [
        # ============== SEARCH INTENT (60+ examples) ==============
        ("show me phones", "search"),
        ("find laptops", "search"),
        ("search for headphones", "search"),
        ("looking for shoes", "search"),
        ("browse electronics", "search"),
        ("what phones do you have", "search"),
        ("display shirts", "search"),
        ("show me options for books", "search"),
        ("i want to see watches", "search"),
        ("list all cameras", "search"),
        ("show products", "search"),
        ("find me a good tv", "search"),
        ("search mobiles", "search"),
        ("looking for a tablet", "search"),
        ("show me some options", "search"),
        ("what do you have in electronics", "search"),
        ("i need a laptop", "search"),
        ("can you show me phones", "search"),
        ("display all available headphones", "search"),
        ("find wireless earbuds", "search"),
        ("show me smart watches", "search"),
        ("search gaming laptops", "search"),
        ("find me bluetooth speakers", "search"),
        ("looking for fitness bands", "search"),
        ("i'm looking for a new phone", "search"),
        ("what laptops are available", "search"),
        ("do you have wireless earbuds", "search"),
        ("show me all headphones", "search"),
        ("any good tablets available", "search"),
        ("where can i find shoes", "search"),
        ("get me some shirt options", "search"),
        ("i want to explore cameras", "search"),
        ("show available products", "search"),
        ("find iphone", "search"),
        ("search samsung phones", "search"),
        ("looking for nike shoes", "search"),
        ("show me adidas products", "search"),
        ("find apple watch", "search"),
        ("search for sony headphones", "search"),
        ("i want to browse laptops", "search"),
        ("display television options", "search"),
        ("show me refrigerators", "search"),
        ("find washing machines", "search"),
        ("looking for air conditioner", "search"),
        ("search for mixer grinder", "search"),
        ("show kitchen appliances", "search"),
        ("find home decor items", "search"),
        ("looking for furniture", "search"),
        ("search beauty products", "search"),
        ("show skincare items", "search"),
        ("find makeup products", "search"),
        ("looking for perfumes", "search"),
        ("search for groceries", "search"),
        ("show me toys for kids", "search"),
        ("find gaming consoles", "search"),
        ("looking for playstation", "search"),
        ("search xbox games", "search"),
        ("show me books on python", "search"),
        ("find fiction novels", "search"),
        ("looking for textbooks", "search"),

        # ============== BUY INTENT (50+ examples) ==============
        ("i want to buy a laptop", "buy"),
        ("purchase this phone", "buy"),
        ("add to cart", "buy"),
        ("buy now", "buy"),
        ("order this product", "buy"),
        ("i need to buy headphones", "buy"),
        ("want to purchase shoes", "buy"),
        ("checkout", "buy"),
        ("place order", "buy"),
        ("get me this item", "buy"),
        ("i will take this one", "buy"),
        ("proceed to buy", "buy"),
        ("confirm purchase", "buy"),
        ("add this to my cart", "buy"),
        ("i want to order", "buy"),
        ("i'll buy this one", "buy"),
        ("yes purchase it", "buy"),
        ("i want to place an order", "buy"),
        ("complete my purchase", "buy"),
        ("add this product to cart", "buy"),
        ("buy this for me", "buy"),
        ("i'm buying this", "buy"),
        ("order now", "buy"),
        ("confirm order", "buy"),
        ("proceed to checkout", "buy"),
        ("finalize purchase", "buy"),
        ("i'll take two of these", "buy"),
        ("purchase immediately", "buy"),
        ("book this product", "buy"),
        ("reserve this item", "buy"),
        ("i want to get this", "buy"),
        ("let me buy this", "buy"),
        ("yes order it", "buy"),
        ("place my order", "buy"),
        ("complete order", "buy"),
        ("add to my bag", "buy"),
        ("put in cart", "buy"),
        ("i'm ordering this", "buy"),
        ("buy all of these", "buy"),
        ("purchase selected items", "buy"),
        ("go to cart", "buy"),
        ("proceed with order", "buy"),
        ("submit order", "buy"),
        ("make purchase", "buy"),
        ("i need to order this", "buy"),
        ("buy it right now", "buy"),
        ("i want to purchase this", "buy"),
        ("order these products", "buy"),
        ("buying this phone", "buy"),
        ("i'll order the laptop", "buy"),

        # ============== COMPARE INTENT (45+ examples) ==============
        ("compare phones", "compare"),
        ("which is better samsung or apple", "compare"),
        ("difference between laptop models", "compare"),
        ("compare prices", "compare"),
        ("what's the best option", "compare"),
        ("comparison between products", "compare"),
        ("which one should i buy", "compare"),
        ("best among these", "compare"),
        ("pros and cons", "compare"),
        ("better value for money", "compare"),
        ("iphone vs samsung", "compare"),
        ("which laptop is better", "compare"),
        ("compare these two products", "compare"),
        ("what is the difference between", "compare"),
        ("help me decide between", "compare"),
        ("which phone has better camera samsung or iphone", "compare"),
        ("what's the difference between these two", "compare"),
        ("is samsung better than apple", "compare"),
        ("oneplus vs xiaomi which is better", "compare"),
        ("compare dell and hp laptops", "compare"),
        ("macbook vs windows laptop", "compare"),
        ("which headphone is best", "compare"),
        ("sony vs bose headphones", "compare"),
        ("compare jbl and boat speakers", "compare"),
        ("nike vs adidas which should i buy", "compare"),
        ("which brand is better", "compare"),
        ("compare these options", "compare"),
        ("differentiate between", "compare"),
        ("which has more features", "compare"),
        ("which one has better battery", "compare"),
        ("compare specifications", "compare"),
        ("what are the differences", "compare"),
        ("head to head comparison", "compare"),
        ("side by side comparison", "compare"),
        ("which gives better performance", "compare"),
        ("compare quality of both", "compare"),
        ("which is more durable", "compare"),
        ("which offers better value", "compare"),
        ("review comparison between", "compare"),
        ("better option among these", "compare"),
        ("which suits me better", "compare"),
        ("compare features of both", "compare"),
        ("which should i prefer", "compare"),
        ("tell me which is better", "compare"),
        ("analyze both products", "compare"),

        # ============== FILTER INTENT (45+ examples) ==============
        ("under 10000", "filter"),
        ("price below 5000", "filter"),
        ("only samsung products", "filter"),
        ("filter by brand", "filter"),
        ("show cheap options", "filter"),
        ("affordable phones", "filter"),
        ("budget laptops", "filter"),
        ("premium products only", "filter"),
        ("rating above 4", "filter"),
        ("best rated products", "filter"),
        ("less than 15000 rupees", "filter"),
        ("within my budget", "filter"),
        ("high end products", "filter"),
        ("sort by price", "filter"),
        ("only apple products", "filter"),
        ("filter by price low to high", "filter"),
        ("sort by rating", "filter"),
        ("show only 5 star products", "filter"),
        ("filter electronics only", "filter"),
        ("show items on sale", "filter"),
        ("discounted products", "filter"),
        ("show only new arrivals", "filter"),
        ("filter by color black", "filter"),
        ("only 128gb storage", "filter"),
        ("8gb ram phones only", "filter"),
        ("show flagship phones", "filter"),
        ("entry level laptops", "filter"),
        ("mid range smartphones", "filter"),
        ("luxury watches only", "filter"),
        ("filter by size medium", "filter"),
        ("men's products only", "filter"),
        ("women's clothing filter", "filter"),
        ("kids section only", "filter"),
        ("apply price filter", "filter"),
        ("narrow down results", "filter"),
        ("refine search", "filter"),
        ("customize filters", "filter"),
        ("set budget limit", "filter"),
        ("maximum price 20000", "filter"),
        ("minimum rating 4 stars", "filter"),
        ("brand filter samsung", "filter"),
        ("category electronics", "filter"),
        ("in stock items only", "filter"),
        ("fast delivery products", "filter"),
        ("free shipping items", "filter"),

        # ============== GREETING INTENT (25+ examples) ==============
        ("hello", "greeting"),
        ("hi there", "greeting"),
        ("hey", "greeting"),
        ("good morning", "greeting"),
        ("good evening", "greeting"),
        ("hi", "greeting"),
        ("namaste", "greeting"),
        ("hola", "greeting"),
        ("greetings", "greeting"),
        ("howdy", "greeting"),
        ("good afternoon", "greeting"),
        ("hey there", "greeting"),
        ("hello there", "greeting"),
        ("hi buddy", "greeting"),
        ("hey bot", "greeting"),
        ("hello bot", "greeting"),
        ("good day", "greeting"),
        ("whats up", "greeting"),
        ("sup", "greeting"),
        ("yo", "greeting"),
        ("hii", "greeting"),
        ("hiiii", "greeting"),
        ("hellooo", "greeting"),
        ("heya", "greeting"),
        ("wassup", "greeting"),

        # ============== HELP INTENT (30+ examples) ==============
        ("help me", "help"),
        ("what can you do", "help"),
        ("how does this work", "help"),
        ("i need assistance", "help"),
        ("guide me", "help"),
        ("how to use this", "help"),
        ("what are your features", "help"),
        ("help me find something", "help"),
        ("i am confused", "help"),
        ("can you assist me", "help"),
        ("how to search products", "help"),
        ("how do i order", "help"),
        ("explain your features", "help"),
        ("what can i ask you", "help"),
        ("give me instructions", "help"),
        ("how to use filters", "help"),
        ("tutorial please", "help"),
        ("show me how this works", "help"),
        ("i don't understand", "help"),
        ("need help with shopping", "help"),
        ("assist me please", "help"),
        ("can you help", "help"),
        ("i need guidance", "help"),
        ("what should i do", "help"),
        ("how do i get started", "help"),
        ("explain how to shop", "help"),
        ("what features do you have", "help"),
        ("how can you help me", "help"),
        ("guide me through", "help"),
        ("help with navigation", "help"),

        # ============== RECOMMENDATION INTENT (40+ examples) ==============
        ("recommend something", "recommendation"),
        ("suggest products", "recommendation"),
        ("what do you recommend", "recommendation"),
        ("give me suggestions", "recommendation"),
        ("best products for me", "recommendation"),
        ("personalized recommendations", "recommendation"),
        ("what should i buy", "recommendation"),
        ("suggest something good", "recommendation"),
        ("recommend a phone", "recommendation"),
        ("what would you recommend", "recommendation"),
        ("suggest me something", "recommendation"),
        ("any recommendations", "recommendation"),
        ("recommend me a laptop", "recommendation"),
        ("suggest best headphones", "recommendation"),
        ("what's good for gaming", "recommendation"),
        ("recommend for students", "recommendation"),
        ("suggest gift options", "recommendation"),
        ("what should i get", "recommendation"),
        ("recommend based on my history", "recommendation"),
        ("personalized suggestions", "recommendation"),
        ("curated picks for me", "recommendation"),
        ("what's trending", "recommendation"),
        ("popular products", "recommendation"),
        ("best sellers", "recommendation"),
        ("top picks", "recommendation"),
        ("editor's choice", "recommendation"),
        ("recommended for you", "recommendation"),
        ("suggest within my budget", "recommendation"),
        ("recommend premium options", "recommendation"),
        ("suggest affordable alternatives", "recommendation"),
        ("what's your recommendation", "recommendation"),
        ("give me your best picks", "recommendation"),
        ("suggest something similar", "recommendation"),
        ("recommend alternatives", "recommendation"),
        ("best options in this category", "recommendation"),
        ("top rated suggestions", "recommendation"),
        ("popular recommendations", "recommendation"),
        ("suggest something new", "recommendation"),
        ("recommend latest products", "recommendation"),
        ("best bang for buck", "recommendation"),

        # ============== INQUIRY INTENT (35+ examples) ==============
        ("how much does this cost", "inquiry"),
        ("is this in stock", "inquiry"),
        ("what's the price of iphone", "inquiry"),
        ("when will it be back in stock", "inquiry"),
        ("what is the cost", "inquiry"),
        ("price please", "inquiry"),
        ("how much is this", "inquiry"),
        ("what does it cost", "inquiry"),
        ("is it available", "inquiry"),
        ("check availability", "inquiry"),
        ("is this product available", "inquiry"),
        ("when will it arrive", "inquiry"),
        ("delivery time", "inquiry"),
        ("shipping cost", "inquiry"),
        ("what are the specifications", "inquiry"),
        ("product details please", "inquiry"),
        ("tell me about this product", "inquiry"),
        ("what are the features", "inquiry"),
        ("is there warranty", "inquiry"),
        ("return policy", "inquiry"),
        ("can i return this", "inquiry"),
        ("exchange possible", "inquiry"),
        ("what colors available", "inquiry"),
        ("size options", "inquiry"),
        ("variants available", "inquiry"),
        ("does it have warranty", "inquiry"),
        ("how long is the warranty", "inquiry"),
        ("genuine product", "inquiry"),
        ("is it original", "inquiry"),
        ("seller information", "inquiry"),
        ("where is it shipped from", "inquiry"),
        ("estimated delivery date", "inquiry"),
        ("cod available", "inquiry"),
        ("cash on delivery", "inquiry"),
        ("emi options", "inquiry"),

        # ============== REFINE INTENT (30+ examples) ==============
        ("show me cheaper ones", "refine"),
        ("any more options", "refine"),
        ("something else", "refine"),
        ("different color", "refine"),
        ("show more", "refine"),
        ("more options please", "refine"),
        ("anything cheaper", "refine"),
        ("something expensive", "refine"),
        ("different brand", "refine"),
        ("other options", "refine"),
        ("show alternatives", "refine"),
        ("similar products", "refine"),
        ("more like this", "refine"),
        ("show me more", "refine"),
        ("next page", "refine"),
        ("load more", "refine"),
        ("other colors", "refine"),
        ("different size", "refine"),
        ("larger screen", "refine"),
        ("smaller option", "refine"),
        ("more storage", "refine"),
        ("better camera", "refine"),
        ("longer battery", "refine"),
        ("lighter weight", "refine"),
        ("other variants", "refine"),
        ("show different ones", "refine"),
        ("not this one", "refine"),
        ("try something else", "refine"),
        ("show newer models", "refine"),
        ("older version", "refine"),

        # ============== GENERAL INTENT (30+ examples) ==============
        ("thank you", "general"),
        ("thanks", "general"),
        ("goodbye", "general"),
        ("bye", "general"),
        ("ok", "general"),
        ("nice", "general"),
        ("great", "general"),
        ("awesome", "general"),
        ("cool", "general"),
        ("how are you", "general"),
        ("that's helpful", "general"),
        ("okay thanks", "general"),
        ("see you later", "general"),
        ("take care", "general"),
        ("nevermind", "general"),
        ("thank you so much", "general"),
        ("thanks a lot", "general"),
        ("bye bye", "general"),
        ("good bye", "general"),
        ("see you", "general"),
        ("later", "general"),
        ("alright", "general"),
        ("fine", "general"),
        ("got it", "general"),
        ("understood", "general"),
        ("makes sense", "general"),
        ("i see", "general"),
        ("no problem", "general"),
        ("no worries", "general"),
        ("all good", "general"),
    ]

    def __init__(self):
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=(1, 3),
                max_features=2000,
                stop_words="english",
                min_df=1
            )),
            ("clf", MultinomialNB(alpha=0.1))
        ])
        self.is_trained = False

    def train(self):
        """Train the intent classifier."""
        texts = [text for text, _ in self.TRAINING_DATA]
        labels = [label for _, label in self.TRAINING_DATA]

        self.pipeline.fit(texts, labels)
        self.is_trained = True

    def predict(self, text: str) -> Tuple[str, float]:
        """Predict intent for a query with dynamic confidence thresholds."""
        if not self.is_trained:
            self.train()

        text_lower = text.lower()
        proba = self.pipeline.predict_proba([text_lower])[0]
        intent_idx = np.argmax(proba)
        confidence = proba[intent_idx]
        intent = self.pipeline.classes_[intent_idx]

        # Check for strong signals in the query
        has_product_keyword = any(kw in text_lower for kw in self.PRODUCT_KEYWORDS)
        has_action_verb = any(v in text_lower for v in self.ACTION_VERBS)
        has_price_indicator = any(p in text_lower for p in ["under", "below", "above", "rs", "rupee", "₹", "budget", "price"])
        has_comparison_word = any(c in text_lower for c in ["vs", "versus", "or", "better", "compare", "difference"])

        # Dynamic threshold based on query characteristics
        if has_product_keyword or has_action_verb or has_price_indicator:
            threshold = 0.25  # Lower threshold for clear product queries
        else:
            threshold = 0.4  # Higher threshold for ambiguous queries

        # Handle low confidence with intelligent fallback
        if confidence < threshold:
            if has_comparison_word and has_product_keyword:
                return "compare", max(confidence, 0.45)
            if has_price_indicator:
                return "filter", max(confidence, 0.45)
            if has_product_keyword:
                return "search", max(confidence, 0.45)
            return "general", confidence

        # Boost confidence for very clear intents
        if intent == "search" and has_product_keyword:
            confidence = min(confidence + 0.1, 1.0)
        if intent == "compare" and has_comparison_word:
            confidence = min(confidence + 0.1, 1.0)
        if intent == "filter" and has_price_indicator:
            confidence = min(confidence + 0.1, 1.0)

        return intent, float(confidence)


class EntityExtractor:
    """Enhanced entity extractor with better patterns and features."""

    def __init__(self):
        # Price patterns (comprehensive)
        self.price_patterns = [
            r"(?:under|below|less than|max|maximum|upto|up to|within|beneath)\s*(?:rs\.?|rupees?|inr|₹)?\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*(?:k|thousand)?",
            r"(?:rs\.?|rupees?|inr|₹)\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*(?:k|thousand)?\s*(?:or less|or below|max|budget)?",
            r"(\d+(?:,\d+)?(?:\.\d+)?)\s*(?:k|thousand)?\s*(?:rs\.?|rupees?|inr|₹)?\s*(?:budget|max|maximum)?",
            r"(?:above|over|more than|min|minimum|at least|starting)\s*(?:rs\.?|rupees?|inr|₹)?\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*(?:k|thousand)?",
            r"(?:between|from)\s*(?:rs\.?|rupees?|inr|₹)?\s*(\d+(?:,\d+)?)\s*(?:k|thousand)?\s*(?:to|and|-)\s*(?:rs\.?|rupees?|inr|₹)?\s*(\d+(?:,\d+)?)\s*(?:k|thousand)?",
            r"budget\s*(?:is|of)?\s*(?:rs\.?|rupees?|inr|₹)?\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*(?:k|thousand)?",
        ]

        # Category mappings (expanded)
        self.category_mappings = {
            # Electronics - Phones & Accessories
            "phone": "Electronics", "phones": "Electronics",
            "mobile": "Electronics", "mobiles": "Electronics",
            "smartphone": "Electronics", "smartphones": "Electronics",
            "iphone": "Electronics", "android": "Electronics",
            "cell phone": "Electronics", "cellphone": "Electronics",
            "phone case": "Electronics", "phone cover": "Electronics",
            "screen protector": "Electronics", "tempered glass": "Electronics",
            "charger": "Electronics", "charging cable": "Electronics",
            "powerbank": "Electronics", "power bank": "Electronics",
            # Electronics - Computers
            "laptop": "Electronics", "laptops": "Electronics",
            "notebook": "Electronics", "macbook": "Electronics",
            "computer": "Electronics", "computers": "Electronics",
            "pc": "Electronics", "desktop": "Electronics",
            "gaming laptop": "Electronics", "chromebook": "Electronics",
            "monitor": "Electronics", "monitors": "Electronics",
            "keyboard": "Electronics", "keyboards": "Electronics",
            "mouse": "Electronics", "mice": "Electronics",
            "webcam": "Electronics", "usb hub": "Electronics",
            "hard drive": "Electronics", "ssd": "Electronics", "hdd": "Electronics",
            "pendrive": "Electronics", "pen drive": "Electronics", "flash drive": "Electronics",
            "memory card": "Electronics", "sd card": "Electronics",
            # Electronics - TVs & Entertainment
            "tv": "Electronics", "television": "Electronics",
            "smart tv": "Electronics", "led tv": "Electronics",
            "oled tv": "Electronics", "qled tv": "Electronics",
            "projector": "Electronics", "home theater": "Electronics",
            "soundbar": "Electronics", "streaming device": "Electronics",
            "fire stick": "Electronics", "chromecast": "Electronics",
            "roku": "Electronics", "set top box": "Electronics",
            # Electronics - Tablets & Readers
            "tablet": "Electronics", "tablets": "Electronics",
            "ipad": "Electronics", "kindle": "Electronics", "e-reader": "Electronics",
            # Electronics - Audio
            "headphones": "Electronics", "headphone": "Electronics",
            "earphones": "Electronics", "earbuds": "Electronics",
            "airpods": "Electronics", "wireless earbuds": "Electronics",
            "tws": "Electronics", "neckband": "Electronics",
            "speaker": "Electronics", "speakers": "Electronics",
            "bluetooth speaker": "Electronics", "portable speaker": "Electronics",
            "home audio": "Electronics", "amplifier": "Electronics",
            # Electronics - Cameras
            "camera": "Electronics", "cameras": "Electronics",
            "dslr": "Electronics", "mirrorless": "Electronics",
            "action camera": "Electronics", "gopro": "Electronics",
            "drone": "Electronics", "gimbal": "Electronics",
            "tripod": "Electronics", "camera lens": "Electronics",
            # Electronics - Wearables
            "smartwatch": "Electronics", "smart watch": "Electronics",
            "fitness band": "Electronics", "fitness tracker": "Electronics",
            "watch": "Electronics", "watches": "Electronics",
            "vr headset": "Electronics", "virtual reality": "Electronics",
            # Electronics - Gaming
            "gaming": "Electronics", "console": "Electronics",
            "playstation": "Electronics", "ps5": "Electronics", "ps4": "Electronics",
            "xbox": "Electronics", "nintendo": "Electronics", "switch": "Electronics",
            "gaming controller": "Electronics", "joystick": "Electronics",
            # Electronics - Networking
            "router": "Electronics", "wifi router": "Electronics",
            "modem": "Electronics", "range extender": "Electronics",
            "mesh router": "Electronics",
            # Electronics - Printers
            "printer": "Electronics", "printers": "Electronics",
            "scanner": "Electronics", "ink cartridge": "Electronics",

            # Clothing - Tops
            "shirt": "Clothing", "shirts": "Clothing",
            "tshirt": "Clothing", "t-shirt": "Clothing",
            "t shirt": "Clothing", "top": "Clothing", "tops": "Clothing",
            "polo": "Clothing", "polo shirt": "Clothing",
            "blouse": "Clothing", "crop top": "Clothing",
            "sweater": "Clothing", "pullover": "Clothing",
            "hoodie": "Clothing", "sweatshirt": "Clothing",
            "cardigan": "Clothing", "vest": "Clothing",
            # Clothing - Bottoms
            "jeans": "Clothing", "pants": "Clothing",
            "trousers": "Clothing", "shorts": "Clothing",
            "skirt": "Clothing", "leggings": "Clothing",
            "track pants": "Clothing", "joggers": "Clothing",
            "cargo pants": "Clothing", "chinos": "Clothing",
            # Clothing - Outerwear
            "jacket": "Clothing", "jackets": "Clothing",
            "coat": "Clothing", "blazer": "Clothing",
            "suit": "Clothing", "formal wear": "Clothing",
            "raincoat": "Clothing", "windbreaker": "Clothing",
            "parka": "Clothing", "overcoat": "Clothing",
            # Clothing - Dresses
            "dress": "Clothing", "dresses": "Clothing",
            "gown": "Clothing", "maxi dress": "Clothing",
            "midi dress": "Clothing", "mini dress": "Clothing",
            # Clothing - Traditional
            "kurta": "Clothing", "saree": "Clothing", "sari": "Clothing",
            "ethnic wear": "Clothing", "traditional": "Clothing",
            "lehenga": "Clothing", "sherwani": "Clothing",
            "salwar": "Clothing", "kurti": "Clothing",
            # Clothing - Footwear
            "shoes": "Clothing", "shoe": "Clothing",
            "sneakers": "Clothing", "boots": "Clothing",
            "sandals": "Clothing", "footwear": "Clothing",
            "heels": "Clothing", "flats": "Clothing",
            "loafers": "Clothing", "slippers": "Clothing",
            "flip flops": "Clothing", "sports shoes": "Clothing",
            "running shoes": "Clothing", "formal shoes": "Clothing",
            # Clothing - General
            "clothes": "Clothing", "clothing": "Clothing",
            "apparel": "Clothing", "fashion": "Clothing",
            "innerwear": "Clothing", "lingerie": "Clothing",
            "sleepwear": "Clothing", "nightwear": "Clothing",
            "swimwear": "Clothing", "activewear": "Clothing",

            # Home & Kitchen - Large Appliances
            "kitchen": "Home & Kitchen", "home": "Home & Kitchen",
            "appliance": "Home & Kitchen", "appliances": "Home & Kitchen",
            "refrigerator": "Home & Kitchen", "fridge": "Home & Kitchen",
            "washing machine": "Home & Kitchen", "washer": "Home & Kitchen",
            "dryer": "Home & Kitchen", "dishwasher": "Home & Kitchen",
            "air conditioner": "Home & Kitchen", "ac": "Home & Kitchen",
            "split ac": "Home & Kitchen", "window ac": "Home & Kitchen",
            # Home & Kitchen - Small Appliances
            "mixer": "Home & Kitchen", "grinder": "Home & Kitchen",
            "blender": "Home & Kitchen", "juicer": "Home & Kitchen",
            "microwave": "Home & Kitchen", "oven": "Home & Kitchen",
            "toaster": "Home & Kitchen", "sandwich maker": "Home & Kitchen",
            "kettle": "Home & Kitchen", "coffee maker": "Home & Kitchen",
            "air fryer": "Home & Kitchen", "induction": "Home & Kitchen",
            "stove": "Home & Kitchen", "gas stove": "Home & Kitchen",
            "cooker": "Home & Kitchen", "pressure cooker": "Home & Kitchen",
            "rice cooker": "Home & Kitchen", "slow cooker": "Home & Kitchen",
            # Home & Kitchen - Climate Control
            "fan": "Home & Kitchen", "ceiling fan": "Home & Kitchen",
            "table fan": "Home & Kitchen", "tower fan": "Home & Kitchen",
            "air cooler": "Home & Kitchen", "heater": "Home & Kitchen",
            "room heater": "Home & Kitchen", "geyser": "Home & Kitchen",
            "water heater": "Home & Kitchen",
            # Home & Kitchen - Cleaning
            "vacuum": "Home & Kitchen", "vacuum cleaner": "Home & Kitchen",
            "robot vacuum": "Home & Kitchen", "mop": "Home & Kitchen",
            "steam mop": "Home & Kitchen",
            # Home & Kitchen - Water
            "air purifier": "Home & Kitchen", "water purifier": "Home & Kitchen",
            "ro purifier": "Home & Kitchen", "water filter": "Home & Kitchen",
            "humidifier": "Home & Kitchen", "dehumidifier": "Home & Kitchen",
            # Home & Kitchen - Laundry
            "iron": "Home & Kitchen", "steam iron": "Home & Kitchen",
            "garment steamer": "Home & Kitchen",
            # Home & Kitchen - Decor & Furniture
            "furniture": "Home & Kitchen", "sofa": "Home & Kitchen",
            "bed": "Home & Kitchen", "mattress": "Home & Kitchen",
            "table": "Home & Kitchen", "chair": "Home & Kitchen",
            "lamp": "Home & Kitchen", "lighting": "Home & Kitchen",
            "curtains": "Home & Kitchen", "bedsheet": "Home & Kitchen",

            # Books
            "book": "Books", "books": "Books",
            "novel": "Books", "novels": "Books",
            "textbook": "Books", "ebook": "Books",
            "comic": "Books", "manga": "Books",
            "magazine": "Books", "fiction": "Books",
            "non-fiction": "Books", "autobiography": "Books",
            "biography": "Books", "self-help": "Books",
            "academic": "Books", "educational": "Books",

            # Beauty & Personal Care
            "beauty": "Beauty", "cosmetics": "Beauty",
            "makeup": "Beauty", "skincare": "Beauty",
            "cream": "Beauty", "lotion": "Beauty",
            "perfume": "Beauty", "fragrance": "Beauty",
            "deodorant": "Beauty", "body spray": "Beauty",
            "shampoo": "Beauty", "conditioner": "Beauty",
            "hair oil": "Beauty", "hair serum": "Beauty",
            "serum": "Beauty", "moisturizer": "Beauty",
            "sunscreen": "Beauty", "face wash": "Beauty",
            "lipstick": "Beauty", "foundation": "Beauty",
            "mascara": "Beauty", "eyeliner": "Beauty",
            "nail polish": "Beauty", "nail paint": "Beauty",
            "trimmer": "Beauty", "shaver": "Beauty",
            "epilator": "Beauty", "hair dryer": "Beauty",
            "straightener": "Beauty", "curler": "Beauty",

            # Sports & Fitness
            "sports": "Sports", "fitness": "Sports",
            "gym": "Sports", "workout": "Sports",
            "exercise": "Sports", "yoga": "Sports", "yoga mat": "Sports",
            "cricket": "Sports", "cricket bat": "Sports", "cricket ball": "Sports",
            "football": "Sports", "soccer": "Sports",
            "badminton": "Sports", "badminton racket": "Sports",
            "tennis": "Sports", "tennis racket": "Sports",
            "basketball": "Sports", "volleyball": "Sports",
            "running": "Sports", "cycling": "Sports", "cycle": "Sports",
            "swimming": "Sports", "swimsuit": "Sports",
            "dumbbell": "Sports", "weights": "Sports",
            "treadmill": "Sports", "exercise bike": "Sports",
            "protein powder": "Sports", "supplements": "Sports",

            # Toys & Games
            "toy": "Toys", "toys": "Toys",
            "game": "Toys", "games": "Toys",
            "puzzle": "Toys", "puzzles": "Toys",
            "lego": "Toys", "building blocks": "Toys",
            "doll": "Toys", "dolls": "Toys",
            "action figure": "Toys", "superhero": "Toys",
            "board game": "Toys", "card game": "Toys",
            "educational toy": "Toys", "learning toy": "Toys",
            "remote control": "Toys", "rc car": "Toys",
            "stuffed toy": "Toys", "soft toy": "Toys",

            # Grocery
            "grocery": "Grocery", "groceries": "Grocery",
            "food": "Grocery", "snacks": "Grocery",
            "beverages": "Grocery", "drinks": "Grocery",
            "biscuits": "Grocery", "cookies": "Grocery",
            "chocolate": "Grocery", "chips": "Grocery",
            "noodles": "Grocery", "pasta": "Grocery",
            "rice": "Grocery", "dal": "Grocery", "lentils": "Grocery",
            "oil": "Grocery", "ghee": "Grocery",
            "spices": "Grocery", "masala": "Grocery",
            "tea": "Grocery", "coffee": "Grocery",
            "milk": "Grocery", "dairy": "Grocery",
            "juice": "Grocery", "soft drink": "Grocery",

            # Bags & Luggage
            "bag": "Bags", "bags": "Bags",
            "backpack": "Bags", "laptop bag": "Bags",
            "handbag": "Bags", "purse": "Bags",
            "wallet": "Bags", "clutch": "Bags",
            "luggage": "Bags", "suitcase": "Bags",
            "trolley": "Bags", "travel bag": "Bags",
            "duffel bag": "Bags", "gym bag": "Bags",

            # Jewelry & Accessories
            "jewelry": "Jewelry", "jewellery": "Jewelry",
            "necklace": "Jewelry", "pendant": "Jewelry",
            "earrings": "Jewelry", "ring": "Jewelry", "rings": "Jewelry",
            "bracelet": "Jewelry", "bangle": "Jewelry",
            "chain": "Jewelry", "anklet": "Jewelry",
            "sunglasses": "Accessories", "eyewear": "Accessories",
            "belt": "Accessories", "belts": "Accessories",
            "tie": "Accessories", "ties": "Accessories",
            "scarf": "Accessories", "cap": "Accessories", "hat": "Accessories",
        }

        # Brand patterns (expanded)
        self.brands = []
        for brand_list in CATEGORIES.values():
            self.brands.extend([b.lower() for b in brand_list])

        # Add more common brands (significantly expanded)
        additional_brands = [
            # Smartphones
            "apple", "samsung", "oneplus", "xiaomi", "redmi", "realme", "oppo", "vivo",
            "nokia", "motorola", "google", "pixel", "nothing", "iqoo", "poco", "infinix",
            "tecno", "lava", "micromax", "honor", "huawei", "zte", "meizu",
            # Laptops & Computers
            "hp", "dell", "lenovo", "asus", "acer", "msi", "microsoft", "surface",
            "alienware", "razer", "gigabyte", "toshiba", "fujitsu", "vaio",
            # TVs & Electronics
            "sony", "lg", "panasonic", "philips", "haier", "whirlpool", "bosch",
            "tcl", "hisense", "vu", "mi", "thomson", "sanyo", "toshiba", "sharp",
            # Audio
            "boat", "jbl", "bose", "sennheiser", "audio technica", "marshall",
            "skullcandy", "beats", "harman kardon", "bang olufsen", "anker", "soundcore",
            "noise", "boult", "mivi", "zebronics", "ptron", "oneodio",
            # Wearables
            "fire-boltt", "amazfit", "garmin", "fitbit", "fossil", "titan",
            "casio", "timex", "fastrack", "sonata", "tissot", "citizen",
            # Clothing & Footwear
            "nike", "adidas", "puma", "reebok", "skechers", "woodland", "bata",
            "levis", "wrangler", "lee", "pepe jeans", "us polo", "tommy hilfiger",
            "calvin klein", "h&m", "zara", "uniqlo", "forever 21", "gap",
            "bewakoof", "the souled store", "roadster", "hrx", "wrogn", "fbb",
            "allen solly", "van heusen", "peter england", "raymond", "louis philippe",
            "flying machine", "killer", "spykar", "monte carlo", "indian terrain",
            # Accessories
            "belkin", "spigen", "otterbox", "esr", "ringke", "uag",
            # Home Appliances
            "prestige", "hawkins", "bajaj", "crompton", "havells", "orient",
            "godrej", "voltas", "bluestar", "daikin", "carrier", "hitachi",
            "ifb", "lloyd", "onida", "videocon", "eureka forbes", "aquaguard",
            # Beauty & Personal Care
            "loreal", "nivea", "dove", "garnier", "maybelline", "lakme",
            "nykaa", "mamaearth", "wow", "mcaffeine", "plum", "biotique",
            "himalaya", "patanjali", "dabur", "colgate", "oral-b", "gillette",
            # Cameras
            "canon", "nikon", "fujifilm", "gopro", "dji", "insta360",
        ]
        self.brands.extend(additional_brands)
        self.brands = list(set(self.brands))

        # Brand aliases for common misspellings and variations
        self.brand_aliases = {
            "samung": "samsung", "samsang": "samsung", "sumsung": "samsung",
            "appel": "apple", "aple": "apple", "iphone": "apple",
            "1plus": "oneplus", "one plus": "oneplus", "1+": "oneplus",
            "mi": "xiaomi", "redme": "redmi", "realmi": "realme",
            "opoo": "oppo", "vevo": "vivo",
            "noikia": "nokia", "motarola": "motorola", "moto": "motorola",
            "googel": "google", "pixle": "pixel",
            "delll": "dell", "lenova": "lenovo", "asuss": "asus",
            "sonny": "sony", "soney": "sony", "phillps": "philips",
            "baat": "boat", "boAt": "boat", "jable": "jbl",
            "nikey": "nike", "addidas": "adidas", "addidas": "adidas", "pumma": "puma",
            "leevies": "levis", "levies": "levis", "leavis": "levis",
            "loreal": "loreal", "maybaline": "maybelline", "lakmay": "lakme",
        }

        # Feature keywords (expanded)
        self.feature_keywords = {
            "camera": ["camera", "megapixel", "mp", "photo", "photography", "selfie", "portrait"],
            "battery": ["battery", "mah", "long lasting", "battery life", "fast charging", "quick charge"],
            "display": ["display", "screen", "amoled", "oled", "lcd", "retina", "hd", "4k", "fhd", "qhd"],
            "storage": ["storage", "gb", "tb", "memory", "rom", "internal storage"],
            "ram": ["ram", "memory", "gb ram"],
            "processor": ["processor", "cpu", "snapdragon", "mediatek", "intel", "amd", "m1", "m2", "chip"],
            "connectivity": ["5g", "4g", "lte", "wifi", "bluetooth", "nfc", "usb-c", "wireless"],
            "build": ["waterproof", "water resistant", "dustproof", "ip68", "ip67", "rugged", "durable"],
            "audio": ["dolby", "stereo", "bass", "noise cancelling", "anc", "surround sound"],
            "design": ["slim", "lightweight", "thin", "compact", "portable", "foldable"],
            "quality": ["premium", "flagship", "professional", "high end", "budget", "affordable", "value"],
            "special": ["gaming", "professional", "student", "business", "travel", "outdoor"],
        }

        # Sentiment words for filtering
        self.positive_words = ["good", "best", "great", "excellent", "amazing", "top", "premium", "quality"]
        self.negative_words = ["cheap", "budget", "affordable", "low cost", "economical", "inexpensive"]

    def extract(self, text: str) -> Dict:
        """Extract all entities from a query."""
        text_lower = text.lower()

        # Extract features with negation handling
        wanted_features, excluded_features = self._extract_features_with_negation(text_lower)

        entities = {
            "category": self._extract_category(text_lower),
            "brand": self._extract_brand(text_lower),
            "price": self._extract_price(text_lower),
            "features": wanted_features,
            "excluded_features": excluded_features,
            "rating": self._extract_rating(text_lower),
            "sort": self._extract_sort(text_lower),
            "quality_preference": self._extract_quality_preference(text_lower),
            "quantity": self._extract_quantity(text_lower),
            "color": self._extract_color(text_lower),
            "size": self._extract_size(text_lower),
            "gender": self._extract_gender(text_lower),
            "discount": self._extract_discount(text_lower),
            "condition": self._extract_condition(text_lower),
        }

        return entities

    def _extract_category(self, text: str) -> Optional[str]:
        """Extract product category from text."""
        # Check for multi-word categories first
        multi_word_cats = ["smart tv", "wireless earbuds", "bluetooth speaker", "fitness band",
                          "smart watch", "power bank", "pressure cooker", "washing machine",
                          "air purifier", "water purifier", "air conditioner", "coffee maker",
                          "board game", "action figure", "educational toy"]
        for cat in multi_word_cats:
            if cat in text:
                return self.category_mappings.get(cat)

        # Then check single-word mappings
        for keyword, category in self.category_mappings.items():
            # Use word boundary matching for better accuracy
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text):
                return category
        return None

    def _extract_brand(self, text: str) -> Optional[str]:
        """Extract brand name from text with fuzzy matching support."""
        # First check brand aliases (handles common misspellings)
        words = text.split()
        for word in words:
            word_lower = word.lower().strip('.,!?')
            if word_lower in self.brand_aliases:
                return self._normalize_brand(self.brand_aliases[word_lower])

        # Exact match for multi-word brands first (check longer brands first)
        for brand in sorted(self.brands, key=len, reverse=True):
            pattern = r'\b' + re.escape(brand) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                return self._normalize_brand(brand)

        # Fuzzy matching for typos (only for words 5+ chars and brand-like words)
        # Skip common words that shouldn't be matched to brands
        skip_words = {"hello", "there", "please", "thanks", "would", "could", "should",
                      "about", "which", "where", "their", "other", "under", "below",
                      "above", "price", "cheap", "great", "phone", "watch", "shoes"}
        for word in words:
            word_lower = word.lower().strip('.,!?')
            if len(word_lower) >= 5 and word_lower not in skip_words:
                best_match = self._fuzzy_brand_match(word_lower)
                if best_match:
                    return self._normalize_brand(best_match)

        return None

    def _fuzzy_brand_match(self, word: str, threshold: float = 0.80) -> Optional[str]:
        """Find closest brand match using character similarity."""
        best_match = None
        best_score = threshold

        for brand in self.brands:
            # Skip if length difference is too big
            if abs(len(word) - len(brand)) > 2:
                continue
            # Only fuzzy match brands of similar length
            if len(brand) < 4:
                continue

            score = self._similarity_score(word, brand.lower())
            if score > best_score:
                best_score = score
                best_match = brand

        return best_match

    def _similarity_score(self, s1: str, s2: str) -> float:
        """Calculate similarity score between two strings."""
        if not s1 or not s2:
            return 0.0

        # Use a simple character matching algorithm
        len1, len2 = len(s1), len(s2)
        max_len = max(len1, len2)

        # Count matching characters at same positions
        matches = sum(c1 == c2 for c1, c2 in zip(s1, s2))

        # Count matching characters at adjacent positions
        for i, c1 in enumerate(s1):
            if i < len2 - 1 and c1 == s2[i + 1]:
                matches += 0.5
            if i > 0 and i - 1 < len2 and c1 == s2[i - 1]:
                matches += 0.5

        return matches / max_len

    def _normalize_brand(self, brand: str) -> str:
        """Normalize brand name with proper capitalization."""
        # Special case brands that should be all caps
        upper_brands = ["hp", "lg", "jbl", "msi", "iqoo", "tcl", "zte", "dji", "bbc", "ibm", "usa", "uag"]
        if brand.lower() in upper_brands:
            return brand.upper()

        # Special case brands with specific capitalization
        special_brands = {
            "oneplus": "OnePlus", "iphone": "iPhone", "ipad": "iPad",
            "macbook": "MacBook", "airpods": "AirPods", "imac": "iMac",
            "youtube": "YouTube", "playstation": "PlayStation", "xbox": "Xbox",
            "loreal": "L'Oreal", "h&m": "H&M", "fire-boltt": "Fire-Boltt",
            "boat": "boAt", "mi": "Mi"
        }
        if brand.lower() in special_brands:
            return special_brands[brand.lower()]

        return brand.title()

    def _extract_price(self, text: str) -> Dict:
        """Extract price constraints from text with proper k/lakh handling."""
        price_info = {"min": None, "max": None}

        # Skip if text contains size/storage indicators with the number
        size_exclusion = r'\d+\s*(?:gb|tb|inch|inches|"|ram|mp|megapixel|core)'
        if re.search(size_exclusion, text, re.IGNORECASE):
            # Remove size-related numbers before price extraction
            text_for_price = re.sub(r'\d+\s*(?:gb|tb|inch|inches|"|ram|mp|megapixel|core)\b', '', text, flags=re.IGNORECASE)
        else:
            text_for_price = text

        # Pattern for "k" suffix (e.g., "20k", "15K", "10.5k")
        k_pattern = r'(\d+(?:\.\d+)?)\s*k\b'

        # Pattern for lakhs (e.g., "5 lakh", "2L", "3 lac")
        lakh_pattern = r'(\d+(?:\.\d+)?)\s*(?:lakh|lakhs|lac|lacs|L)\b'

        # Pattern for plain numbers with optional currency (only match reasonable price-like numbers)
        plain_pattern = r'(?:rs\.?|rupees?|inr|₹)\s*(\d{3,}(?:,\d{3})*(?:\.\d+)?)|(\d{4,}(?:,\d{3})*(?:\.\d+)?)\s*(?:rs\.?|rupees?|inr|₹)?'

        # Pattern for range (e.g., "10000 to 20000", "10k-20k")
        range_pattern = r'(\d+(?:\.\d+)?)\s*(?:k)?\s*(?:to|-|and)\s*(\d+(?:\.\d+)?)\s*(?:k)?'

        # Check for range patterns first
        range_match = re.search(range_pattern, text_for_price, re.IGNORECASE)
        if range_match:
            min_val = float(range_match.group(1).replace(",", ""))
            max_val = float(range_match.group(2).replace(",", ""))
            # Determine if "k" applies
            match_text = text_for_price[range_match.start():range_match.end()+3].lower()
            if "k" in match_text:
                if min_val < 1000:
                    min_val *= 1000
                if max_val < 1000:
                    max_val *= 1000
            price_info["min"] = min_val
            price_info["max"] = max_val
            return price_info

        # Check for lakh values first (higher priority)
        lakh_match = re.search(lakh_pattern, text_for_price, re.IGNORECASE)
        if lakh_match:
            price_val = float(lakh_match.group(1)) * 100000
            if self._is_max_price_context(text_for_price, lakh_match.start()):
                price_info["max"] = price_val
            elif self._is_min_price_context(text_for_price, lakh_match.start()):
                price_info["min"] = price_val
            else:
                price_info["max"] = price_val  # Default to max
            return price_info

        # Check for "k" suffix values
        k_match = re.search(k_pattern, text_for_price, re.IGNORECASE)
        if k_match:
            price_val = float(k_match.group(1)) * 1000
            if self._is_max_price_context(text_for_price, k_match.start()):
                price_info["max"] = price_val
            elif self._is_min_price_context(text_for_price, k_match.start()):
                price_info["min"] = price_val
            else:
                price_info["max"] = price_val  # Default to max
            return price_info

        # Check for plain number patterns with context
        for pattern in self.price_patterns[:4]:
            match = re.search(pattern, text_for_price, re.IGNORECASE)
            if match:
                price_str = match.group(1) if match.group(1) else match.group(2) if len(match.groups()) > 1 else None
                if price_str:
                    price_val = float(price_str.replace(",", ""))
                    # Only consider as price if it's a reasonable price value (>100)
                    if price_val >= 100:
                        if self._is_max_price_context(text_for_price, match.start()):
                            price_info["max"] = price_val
                        elif self._is_min_price_context(text_for_price, match.start()):
                            price_info["min"] = price_val
                        else:
                            price_info["max"] = price_val  # Default to max
                        break

        return price_info

    def _is_max_price_context(self, text: str, pos: int) -> bool:
        """Check if the price context indicates maximum price."""
        prefix = text[:pos].lower()
        max_words = ["under", "below", "less than", "max", "maximum", "upto", "up to",
                     "within", "beneath", "not more than", "budget", "affordable"]
        return any(word in prefix[-30:] for word in max_words)

    def _is_min_price_context(self, text: str, pos: int) -> bool:
        """Check if the price context indicates minimum price."""
        prefix = text[:pos].lower()
        min_words = ["above", "over", "more than", "min", "minimum", "at least",
                     "starting", "from", "premium", "not less than"]
        return any(word in prefix[-30:] for word in min_words)

    def _parse_price_value(self, price_str: str, context: str = "") -> float:
        """Parse price string to float value."""
        if not price_str:
            return None
        price_str = price_str.replace(",", "").strip()
        try:
            return float(price_str)
        except ValueError:
            return None

    def _extract_features(self, text: str) -> List[str]:
        """Extract desired features from text."""
        found_features = []
        for category, keywords in self.feature_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    found_features.append(category)
                    break
        return list(set(found_features))

    def _extract_rating(self, text: str) -> Optional[float]:
        """Extract minimum rating requirement."""
        rating_patterns = [
            r"(?:rating|rated)\s*(?:above|over|at least|minimum|min)?\s*(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*(?:star|stars)\s*(?:rating|rated)?",
            r"(?:above|over|at least|minimum|min)\s*(\d+(?:\.\d+)?)\s*(?:star|stars)?",
            r"top\s*rated",
            r"highly\s*rated",
            r"best\s*rated",
        ]

        # Check for qualitative rating requests
        if any(phrase in text for phrase in ["top rated", "highly rated", "best rated"]):
            return 4.0

        for pattern in rating_patterns[:3]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                rating = float(match.group(1))
                if 0 <= rating <= 5:
                    return rating
        return None

    def _extract_sort(self, text: str) -> Optional[str]:
        """Extract sorting preference."""
        if any(word in text for word in ["cheap", "cheapest", "low price", "lowest price", "budget friendly"]):
            return "price_asc"
        if any(word in text for word in ["expensive", "premium", "high end", "luxury", "costly"]):
            return "price_desc"
        if any(word in text for word in ["popular", "best seller", "top rated", "highest rated", "most rated", "best reviewed"]):
            return "rating_desc"
        if any(word in text for word in ["new", "latest", "newest", "recent", "just launched", "new arrival"]):
            return "newest"
        return None

    def _extract_quality_preference(self, text: str) -> Optional[str]:
        """Extract quality/budget preference."""
        if any(word in text for word in self.positive_words):
            return "premium"
        if any(word in text for word in self.negative_words):
            return "budget"
        return None

    def _extract_quantity(self, text: str) -> Optional[int]:
        """Extract quantity from text."""
        quantity_patterns = [
            r"(\d+)\s*(?:pieces|units|items|nos|numbers)",
            r"(?:need|want|buy|get)\s*(\d+)",
        ]
        for pattern in quantity_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None

    def _extract_color(self, text: str) -> Optional[str]:
        """Extract color preference."""
        colors = ["black", "white", "blue", "red", "green", "gold", "silver",
                  "grey", "gray", "pink", "purple", "orange", "yellow", "brown",
                  "rose gold", "space grey", "midnight", "starlight", "navy",
                  "maroon", "beige", "cream", "teal", "coral"]
        for color in sorted(colors, key=len, reverse=True):  # Check longer colors first
            if color in text:
                return color.title()
        return None

    def _extract_size(self, text: str) -> Optional[Dict]:
        """Extract size specifications for various product types."""
        size_info = {}

        # Screen size pattern (e.g., "13 inch", "55\"", "6.7 inches")
        screen_pattern = r'(\d+(?:\.\d+)?)\s*(?:inch|"|inches|in)\b'
        screen_match = re.search(screen_pattern, text, re.IGNORECASE)
        if screen_match:
            size_info["screen_inches"] = float(screen_match.group(1))

        # Storage pattern (e.g., "256GB", "1TB", "512 gb")
        storage_pattern = r'(\d+)\s*(?:gb|tb)\b'
        storage_match = re.search(storage_pattern, text, re.IGNORECASE)
        if storage_match:
            value = int(storage_match.group(1))
            unit = "TB" if "tb" in text[storage_match.start():storage_match.end()].lower() else "GB"
            size_info["storage"] = f"{value}{unit}"

        # RAM pattern (e.g., "8GB RAM", "16 gb ram")
        ram_pattern = r'(\d+)\s*(?:gb)?\s*ram\b'
        ram_match = re.search(ram_pattern, text, re.IGNORECASE)
        if ram_match:
            size_info["ram_gb"] = int(ram_match.group(1))

        # Clothing size pattern - must be standalone words, not part of possessives
        # Use word boundaries and exclude possessive patterns
        clothing_sizes = {
            "xxs": "XXS", "xs": "XS", "xl": "XL", "xxl": "XXL", "xxxl": "XXXL",
            "small": "Small", "medium": "Medium", "large": "Large",
            "extra large": "Extra Large", "free size": "Free Size"
        }
        for size_key, size_val in clothing_sizes.items():
            # Only match standalone size words, not "'s" possessives
            pattern = r'(?<![\'a-z])' + re.escape(size_key) + r'(?![a-z])'
            if re.search(pattern, text, re.IGNORECASE):
                size_info["clothing"] = size_val
                break

        # Also check for single letter sizes preceded by "size"
        single_letter_pattern = r'\bsize\s+([smlSML])\b'
        single_match = re.search(single_letter_pattern, text, re.IGNORECASE)
        if single_match and "clothing" not in size_info:
            size_info["clothing"] = single_match.group(1).upper()

        # Shoe size pattern (e.g., "size 9", "UK 10", "US 11")
        shoe_pattern = r'(?:shoe\s+)?(?:size|uk|us|eu)\s*(\d+(?:\.\d+)?)'
        shoe_match = re.search(shoe_pattern, text, re.IGNORECASE)
        if shoe_match:
            size_info["shoe"] = shoe_match.group(1)

        return size_info if size_info else None

    def _extract_gender(self, text: str) -> Optional[str]:
        """Extract gender/audience from query."""
        # Check for women first (since "women" contains "men")
        women_keywords = ["women's", "womens", "woman's", "female", "for women",
                         "girls", "girl's", "ladies", "lady", "her", "woman"]
        men_keywords = ["men's", "mens", "man's", "male", "for men", "boys",
                       "boy's", "gents", "gentleman", "his"]
        kids_keywords = ["kids", "children", "child", "kid's", "children's",
                        "baby", "toddler", "infant", "junior"]
        unisex_keywords = ["unisex", "gender neutral", "all gender"]

        # Check longer/more specific keywords first
        for keyword in sorted(women_keywords, key=len, reverse=True):
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                return "women"
        for keyword in sorted(men_keywords, key=len, reverse=True):
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                return "men"
        for keyword in sorted(kids_keywords, key=len, reverse=True):
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                return "kids"
        for keyword in unisex_keywords:
            if keyword in text:
                return "unisex"
        return None

    def _extract_discount(self, text: str) -> Optional[Dict]:
        """Check if user wants discounted items and extract discount details."""
        discount_info = {}

        # Check for general discount/sale keywords
        discount_keywords = ["discount", "sale", "offer", "deal", "off",
                           "clearance", "reduced", "bargain", "promo", "coupon"]
        has_discount = any(word in text for word in discount_keywords)

        # Extract specific discount percentage (e.g., "50% off", "30 percent discount")
        percent_pattern = r'(\d+)\s*(?:%|percent)\s*(?:off|discount)?'
        percent_match = re.search(percent_pattern, text, re.IGNORECASE)
        if percent_match:
            discount_info["min_discount_percent"] = int(percent_match.group(1))
            has_discount = True

        if has_discount:
            discount_info["wants_discount"] = True
            return discount_info
        return None

    def _extract_condition(self, text: str) -> Optional[str]:
        """Extract product condition preference."""
        conditions = {
            "new": ["new", "brand new", "sealed", "unopened", "fresh"],
            "refurbished": ["refurbished", "renewed", "reconditioned", "restored"],
            "used": ["used", "second hand", "pre-owned", "preowned"],
            "open_box": ["open box", "open-box", "unboxed"]
        }

        for condition, keywords in conditions.items():
            for keyword in keywords:
                if keyword in text:
                    return condition
        return None

    def _extract_features_with_negation(self, text: str) -> Tuple[List[str], List[str]]:
        """Extract wanted and excluded features from text."""
        wanted = []
        excluded = []

        # Identify negated words/phrases
        negation_patterns = [
            r'without\s+(\w+)',
            r'no\s+(\w+)',
            r"don't\s+(?:want|need)\s+(\w+)",
            r"doesn't\s+(?:have|need)\s+(\w+)",
            r'except\s+(\w+)',
            r'not\s+(?:with|having)\s+(\w+)',
        ]

        negated_words = set()
        for pattern in negation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            negated_words.update(word.lower() for word in matches)

        # Extract features, categorizing them as wanted or excluded
        for category, keywords in self.feature_keywords.items():
            category_found = False
            for keyword in keywords:
                if keyword in text:
                    # Check if this keyword is negated
                    if keyword in negated_words or any(neg in negated_words for neg in keyword.split()):
                        excluded.append(category)
                    else:
                        wanted.append(category)
                    category_found = True
                    break

        return list(set(wanted)), list(set(excluded))


class ResponseGenerator:
    """Generates intelligent, natural, context-aware responses."""

    def __init__(self):
        # Greeting templates by user type
        self.greeting_templates = {
            "new_user": [
                "Hello! Welcome to ShopAI. I'm here to help you find the perfect products. What are you looking for today?",
                "Hi there! I'm your personal shopping assistant. Tell me what you need, and I'll find the best options for you!",
                "Welcome! I'm excited to help you shop. Just tell me what you're looking for!",
            ],
            "returning_user": [
                "Hey{name}! Good to see you again. What can I help you find today?",
                "Welcome back{name}! Ready to discover something new?",
                "Hi{name}! Nice to have you back. What are you shopping for?",
            ],
            "frequent_user": [
                "Hey{name}! Your favorite shopping assistant here. What do you need?",
                "Welcome back{name}! Let's find something great for you.",
                "Hi{name}! Ready when you are.",
            ]
        }

        # Response starters by intent
        self.intent_openers = {
            "search": [
                "Great! Here are the best matches for your search:",
                "I found some excellent options that fit your needs:",
                "Perfect! Here are products that match what you're looking for:",
                "Awesome! Check out these highly-rated options:",
            ],
            "buy": [
                "Excellent choice! Here are your best options:",
                "Smart selection! Let me show you the perfect fit:",
                "Great idea! Here are the top candidates:",
                "Perfect! Here's what I recommend:",
            ],
            "compare": [
                "Let me break down the key differences:",
                "Here's a detailed comparison to help you decide:",
                "Great question! Here's how they stack up:",
                "Side-by-side comparison coming right up:",
            ],
            "filter": [
                "Perfect filters! Here are your refined options:",
                "Narrowing down nicely! Here's what matches:",
                "Excellent criteria! Check these out:",
                "Smart filtering! Here's what I found:",
            ],
            "recommendation": [
                "Based on your shopping history, I think you'll love these:",
                "My AI-powered picks just for you:",
                "Perfect for your interests! Check these out:",
                "Tailored recommendations based on your preferences:",
            ],
            "refine": [
                "Absolutely! Here are more options:",
                "Sure thing! Let me show you alternatives:",
                "Good call! Here are other great choices:",
                "Got it! Here are more options to explore:",
            ],
            "inquiry": [
                "Great question! Here's what I found:",
                "Let me help with that:",
                "Perfect - I have that info for you:",
                "Absolutely! Here's the breakdown:",
            ]
        }

        # Refinement acknowledgments
        self.refinement_acks = [
            "Got it! 👍",
            "Sure thing",
            "Absolutely",
            "Perfect, filtering now",
            "Understood, let me adjust",
            "Smart choice!",
            "Great idea",
        ]

        # Context connectors
        self.context_connectors = [
            "Continuing from your search",
            "Based on what you were looking at",
            "Building on your interests",
            "Following up from your last search",
            "Staying on the same track",
            "Related to what you just browsed",
            "Keeping your preferences in mind",
        ]

        self.help_responses = [
            """I'm your personal shopping assistant! Here's what I can help you with:

📱 **Find Products**: "Show me phones under 15000" or "Find affordable Samsung laptops with good processor"
⚖️ **Compare Items**: "Compare iPhone 15 vs Samsung S24" or "Which laptop is best for coding?"
🎯 **Smart Filters**: "Budget gaming phones" or "Top rated wireless earbuds under 3000"
💡 **Get Recommendations**: "Recommend something for fitness tracking" or "Best value smartphone 2026"
🔄 **Refine Search**: "Show cheaper options" or "Any other brands?"

I'm powered by AI that learns your preferences. The more you shop, the better my recommendations!""",
        ]

        self.farewell_responses = [
            "Thanks for shopping! Your personalized recommendations will be waiting when you return. 👋",
            "Great chatting with you! I've noted your preferences for next time. See you soon! 🛍️",
            "Happy shopping! Feel free to ask anytime - I'm always here to help. Goodbye! 👍",
            "Thanks for using ShopAI! Come back soon - I'll have even better recommendations for you. 😊",
        ]

        self.thanks_responses = [
            "You're welcome! 😊 Need help refining your search or comparing options?",
            "Happy to help! Want me to find something specific or compare products?",
            "My pleasure! Ask me anything - I can help you find deals, compare brands, or get recommendations.",
            "Glad I could assist! Ready to explore more options or narrow down your choices?",
        ]

        self.no_results_responses = [
            "Hmm, no exact matches for that combination, but here are some fantastic alternatives I found:",
            "Your criteria is pretty specific! Here are similar products that might interest you:",
            "Couldn't find an exact match, but these come close and offer great value:",
            "That's a tough combination! Here are the best alternatives I can recommend:",
        ]

    def generate(
        self,
        intent: str,
        entities: Dict,
        num_results: int = 0,
        context: "ConversationContext" = None,
        user_profile: "UserConversationProfile" = None
    ) -> str:
        """Generate a natural, context-aware response."""

        # Handle greeting with personalization
        if intent == "greeting":
            return self._generate_greeting(user_profile)

        if intent == "help":
            return random.choice(self.help_responses)

        if intent == "general":
            return self._handle_general(entities)

        # Handle no results case early
        if num_results == 0:
            return random.choice(self.no_results_responses)

        # Build contextual response for product queries
        response_parts = []

        # 1. For refinements, use acknowledgment if context indicates it
        if context and context.is_refinement:
            ack = self._acknowledge_refinement(entities, context)
            response_parts.append(ack)
            # Add opener after acknowledgment
            opener = self._get_intent_opener(intent, entities, num_results, user_profile)
            if opener and "here" not in opener.lower():
                response_parts.append(opener)
        elif context and context.references_previous:
            response_parts.append(random.choice(self.context_connectors) + ".")
            opener = self._get_intent_opener(intent, entities, num_results, user_profile)
            response_parts.append(opener)
        else:
            # Add opening based on intent
            opener = self._get_intent_opener(intent, entities, num_results, user_profile)
            response_parts.append(opener)

        # 2. Add smart summary of what we found
        summary = self._generate_result_summary(entities, num_results)
        if summary and intent in ["search", "recommendation", "filter", "refine"]:
            response_parts.append(summary)

        # 3. Mention key filters naturally (if verbose mode)
        if user_profile and user_profile.verbosity_preference != "brief":
            filter_mention = self._describe_filters(entities)
            if filter_mention:
                response_parts.append(filter_mention)

        # 4. Add helpful suggestions based on results and intent
        tips = self._generate_helpful_tips(intent, entities, num_results)
        if tips:
            response_parts.append(tips)

        # 5. Add encouragement for engagement
        if user_profile and user_profile.interaction_count < 3 and num_results >= 3:
            response_parts.append("💡 Pro tip: Click products to compare or ask me to find alternatives!")

        # Join response parts with better punctuation
        if len(response_parts) <= 2:
            return " ".join(response_parts)
        else:
            # Join first parts with periods/semicolons, last part as is
            main_parts = response_parts[:-1]
            last_part = response_parts[-1]
            main_response = " ".join(main_parts)
            if not main_response.endswith((".", "!", "?")):
                main_response += "."
            return main_response + " " + last_part

        return " ".join(response_parts)

    def _generate_greeting(self, user_profile: "UserConversationProfile" = None) -> str:
        """Generate personalized greeting based on user history."""
        name_part = ""

        if user_profile:
            if user_profile.display_name:
                name_part = f", {user_profile.display_name}"

            # Choose template based on interaction history
            if user_profile.interaction_count == 0:
                templates = self.greeting_templates["new_user"]
            elif user_profile.interaction_count > 20:
                templates = self.greeting_templates["frequent_user"]
            else:
                templates = self.greeting_templates["returning_user"]
        else:
            templates = self.greeting_templates["new_user"]

        template = random.choice(templates)
        greeting = template.format(name=name_part)
        
        # Add context if frequent user
        if user_profile and user_profile.interaction_count > 10:
            if user_profile.top_categories:
                greeting += f" I've learned you love {user_profile.top_categories[0]}!"
        
        return greeting

    def _handle_general(self, entities: Dict) -> str:
        """Handle general intent responses."""
        query_lower = entities.get("original_query", "").lower()

        if any(word in query_lower for word in ["thank", "thanks"]):
            return random.choice(self.thanks_responses)
        if any(word in query_lower for word in ["bye", "goodbye", "see you", "later"]):
            return random.choice(self.farewell_responses)

        return "Is there something specific I can help you find? Just tell me what you're looking for!"

    def _acknowledge_refinement(self, entities: Dict, context: "ConversationContext") -> str:
        """Acknowledge when user refines their search."""
        ack = random.choice(self.refinement_acks)
        changes = []

        # Describe what changed
        if entities.get("price"):
            price = entities["price"]
            if price.get("max"):
                changes.append(f"under Rs {price['max']:,.0f}")
            if price.get("min"):
                changes.append(f"above Rs {price['min']:,.0f}")

        if entities.get("brand") and entities["brand"] != context.last_brand:
            changes.append(f"{entities['brand']} products")

        if entities.get("features"):
            changes.append(f"with {entities['features'][0]}")

        if changes:
            return f"{ack}, filtering to {' and '.join(changes)}."
        return f"{ack}."

    def _get_intent_opener(
        self,
        intent: str,
        entities: Dict,
        num_results: int,
        user_profile: "UserConversationProfile" = None
    ) -> str:
        """Get appropriate opener based on intent and context."""

        # Brief mode for frequent users
        if user_profile and user_profile.verbosity_preference == "brief":
            category = entities.get("category", "products").lower()
            brand = entities.get("brand")
            if brand:
                return f"{brand} {category}:"
            return f"{category.title()}:"

        # Get base opener
        openers = self.intent_openers.get(intent, ["Here's what I found:"])
        opener = random.choice(openers)

        # Enhance for search intent with context
        if intent == "search":
            category = entities.get("category", "products").lower()
            brand = entities.get("brand")
            price = entities.get("price", {})
            
            # Build context string
            context_parts = []
            if brand:
                context_parts.append(f"{brand} {category}")
            else:
                context_parts.append(category)
            
            if price.get("max"):
                context_parts.append(f"under Rs {price['max']:,.0f}")
            
            if context_parts:
                return f"Perfect! Here are the best {' '.join(context_parts)}:"
            
        # Enhance for compare intent
        elif intent == "compare":
            brands = [entities.get("brand")] if entities.get("brand") else []
            if brands[0]:
                return f"Let me show you how these options compare!"
                
        # Enhance for recommendation intent
        elif intent == "recommendation":
            if user_profile and user_profile.interaction_count > 5:
                return f"Based on what you've shopped before, I think you'll love these:"
            return opener

        return opener

    def _describe_filters(self, entities: Dict) -> str:
        """Describe applied filters naturally."""
        filters = []

        price = entities.get("price", {})
        if price.get("max") and price.get("min"):
            filters.append(f"Rs {price['min']:,.0f}-{price['max']:,.0f}")
        elif price.get("max"):
            filters.append(f"under Rs {price['max']:,.0f}")
        elif price.get("min"):
            filters.append(f"above Rs {price['min']:,.0f}")

        if entities.get("brand"):
            filters.append(entities["brand"])

        features = entities.get("features", [])
        if features:
            filters.append(f"with {features[0]}")

        if entities.get("gender"):
            filters.append(f"for {entities['gender']}")

        if entities.get("discount"):
            filters.append("on sale")

        if filters:
            return f"Filters: {', '.join(filters)}."
        return ""

    def _generate_result_summary(self, entities: Dict, num_results: int) -> str:
        """Generate a smart summary of results found."""
        if num_results < 1:
            return ""
        if num_results == 1:
            return "Found 1 great option."
        if num_results < 3:
            return f"Found {num_results} great options."
        
        category = entities.get("category", "").lower()
        brand = entities.get("brand")
        price = entities.get("price", {})
        
        summary_parts = []
        
        # Build result count statement
        showing = min(num_results, 10)
        if showing < num_results:
            summary_parts.append(f"Found {num_results} matches, showing top {showing}:")
        else:
            summary_parts.append(f"Found {num_results} perfect matches:")
        
        return " ".join(summary_parts)

    def _generate_helpful_tips(self, intent: str, entities: Dict, num_results: int) -> str:
        """Generate context-aware tips for the user."""
        tips = []
        
        if intent == "search" and num_results > 3:
            tips.append("Want to see cheaper options or try a different brand?")
        elif intent == "recommendation" and num_results > 2:
            tips.append("These are my AI-powered picks based on your preferences!")
        elif intent == "filter" and num_results > 5:
            tips.append("You can further filter by rating or availability.")
        elif intent == "compare":
            tips.append("Click on any product to see full specifications and customer reviews.")
        elif intent == "buy" and num_results > 2:
            tips.append("Compare the options or ask for specific recommendations!")
        
        if tips:
            return " ".join(random.sample(tips, 1))
        return ""


# Import for type hints (placed here to avoid circular imports)
try:
    from services.conversation_memory import ConversationContext, UserConversationProfile
except ImportError:
    ConversationContext = None
    UserConversationProfile = None


class NLPProcessor:
    """Main NLP processor with conversation memory and learning capabilities."""

    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.response_generator = ResponseGenerator()
        self.conversation_context = {}  # Legacy context storage

        # New: Conversation memory and learning
        self._memory_service = None
        self._learner = None
        self._initialized = False

    def _ensure_memory_initialized(self):
        """Lazy initialization of memory service."""
        if not self._initialized:
            try:
                from services.conversation_memory import get_memory_service
                from services.conversation_learner import get_conversation_learner
                self._memory_service = get_memory_service()
                self._learner = get_conversation_learner()
                self._initialized = True
            except Exception as e:
                print(f"Warning: Could not initialize conversation memory: {e}")
                self._initialized = True  # Don't retry on every call

    def process(self, query: str, user_id: str = None) -> Dict:
        """Process a user query with full context awareness."""
        self._ensure_memory_initialized()

        # Get intent
        intent, confidence = self.intent_classifier.predict(query)

        # Get entities
        entities = self.entity_extractor.extract(query)
        entities["original_query"] = query

        # Get conversation context (new system)
        context = None
        user_profile = None

        if user_id and self._memory_service:
            context = self._memory_service.get_conversation_context(user_id)
            user_profile = self._memory_service.get_user_profile(user_id)

            # Detect if this is a refinement
            if context.last_intent and context.last_category:
                if self._is_refinement_query(query, context):
                    context.is_refinement = True

            # Detect reference to previous products
            if self._references_previous(query):
                context.references_previous = True

            # Apply context to fill missing entities
            entities = self._apply_context_enhanced(entities, context)

        # Legacy context support
        elif user_id and user_id in self.conversation_context:
            entities = self._apply_context(entities, self.conversation_context[user_id])

        # Resolve product references (e.g., "the first one")
        if context and context.products_shown:
            resolved = self._resolve_references(query, context)
            if resolved:
                entities.update(resolved)

        # Build filters for recommendation engine
        filters = self._build_filters(entities)

        # Generate contextual response
        response = self.response_generator.generate(intent, entities, 0, context, user_profile)

        # Update conversation context
        if user_id:
            self._update_context(user_id, intent, entities)

        return {
            "original_query": query,
            "intent": intent,
            "intent_confidence": confidence,
            "entities": entities,
            "filters": filters,
            "response": response,
            "requires_products": intent in ["search", "buy", "compare", "filter", "recommendation", "refine", "inquiry"],
            "context": context,
            "user_profile": user_profile
        }

    def record_turn(
        self,
        user_id: str,
        query: str,
        intent: str,
        confidence: float,
        entities: Dict,
        products_shown: List[str],
        response: str
    ) -> None:
        """Record a conversation turn for learning."""
        self._ensure_memory_initialized()

        if not self._memory_service or not user_id:
            return

        try:
            from services.conversation_memory import ConversationTurn
            from datetime import datetime

            turn = ConversationTurn(
                timestamp=datetime.now(),
                user_query=query,
                intent=intent,
                intent_confidence=confidence,
                entities=entities,
                products_shown=products_shown,
                response_text=response
            )

            # Add turn to memory
            self._memory_service.add_turn(user_id, turn)

            # Learn from turn
            if self._learner:
                session = self._memory_service.get_or_create_session(user_id)
                profile = self._memory_service.get_user_profile(user_id)
                self._learner.learn_from_turn(turn, session, profile)
                self._memory_service.update_user_profile(profile)

        except Exception as e:
            print(f"Warning: Could not record turn: {e}")

    def generate_response(self, intent: str, entities: Dict, num_results: int = 0,
                         context=None, user_profile=None) -> str:
        """Generate response with results context."""
        return self.response_generator.generate(intent, entities, num_results, context, user_profile)

    def _is_refinement_query(self, query: str, context) -> bool:
        """Detect if query is refining a previous search."""
        query_lower = query.lower()

        # Refinement keywords
        refinement_words = ["cheaper", "expensive", "more", "less", "different",
                          "another", "other", "else", "instead", "also", "under",
                          "above", "below", "within", "better", "similar"]

        if any(word in query_lower for word in refinement_words):
            return True

        # Short query that adds constraints
        words = query_lower.split()
        if len(words) <= 4 and context.last_category:
            return True

        return False

    def _references_previous(self, query: str) -> bool:
        """Check if query references previous results."""
        query_lower = query.lower()

        reference_patterns = [
            "first one", "second one", "third one", "last one",
            "that one", "this one", "the one",
            "show me more", "tell me about", "details of",
            "compare these", "similar to"
        ]

        return any(pattern in query_lower for pattern in reference_patterns)

    def _resolve_references(self, query: str, context) -> Dict:
        """Resolve references to previous products."""
        resolved = {}
        query_lower = query.lower()

        if not context.products_shown:
            return resolved

        # Ordinal references
        ordinal_map = {
            "first": 0, "1st": 0,
            "second": 1, "2nd": 1,
            "third": 2, "3rd": 2,
            "fourth": 3, "4th": 3,
            "fifth": 4, "5th": 4,
            "last": -1
        }

        for word, index in ordinal_map.items():
            if word in query_lower and ("one" in query_lower or "option" in query_lower or "product" in query_lower):
                try:
                    resolved["referenced_product_id"] = context.products_shown[index]
                    resolved["reference_type"] = "ordinal"
                except IndexError:
                    pass
                break

        # Price preference references
        if "cheaper" in query_lower or "less expensive" in query_lower:
            resolved["price_preference"] = "lower"
            resolved["reference_to_shown"] = True
        elif "expensive" in query_lower or "premium" in query_lower or "better" in query_lower:
            resolved["price_preference"] = "higher"
            resolved["reference_to_shown"] = True

        return resolved

    def _apply_context_enhanced(self, entities: Dict, context) -> Dict:
        """Apply conversation context with enhanced logic."""
        if not context:
            return entities

        # Apply last category if not specified
        if not entities.get("category") and context.last_category:
            entities["category"] = context.last_category

        # Apply last brand if not specified
        if not entities.get("brand") and context.last_brand:
            entities["brand"] = context.last_brand

        # Apply last price range for refinement queries
        if context.is_refinement and not entities.get("price") and context.last_price_range:
            entities["price"] = context.last_price_range

        return entities

    def _apply_context(self, entities: Dict, context: Dict) -> Dict:
        """Apply conversation context to fill missing entities (legacy)."""
        if not entities.get("category") and context.get("last_category"):
            entities["category"] = context["last_category"]

        if not entities.get("brand") and context.get("last_brand"):
            entities["brand"] = context["last_brand"]

        return entities

    def _update_context(self, user_id: str, intent: str, entities: Dict):
        """Update conversation context for user."""
        if user_id not in self.conversation_context:
            self.conversation_context[user_id] = {}

        context = self.conversation_context[user_id]

        if entities.get("category"):
            context["last_category"] = entities["category"]
        if entities.get("brand"):
            context["last_brand"] = entities["brand"]
        context["last_intent"] = intent

    def _build_filters(self, entities: Dict) -> Dict:
        """Build filters dictionary for recommendation engine."""
        filters = {}

        if entities.get("category"):
            filters["category"] = entities["category"]

        if entities.get("brand"):
            filters["brand"] = entities["brand"]

        price = entities.get("price", {})
        if price.get("min"):
            filters["min_price"] = price["min"]
        if price.get("max"):
            filters["max_price"] = price["max"]

        if entities.get("rating"):
            filters["min_rating"] = entities["rating"]

        return filters

    def clear_context(self, user_id: str):
        """Clear conversation context for a user."""
        if user_id in self.conversation_context:
            del self.conversation_context[user_id]

    def save(self, path: str = None):
        """Save NLP models."""
        path = path or str(MODELS_DIR / "nlp_processor.pkl")
        with open(path, "wb") as f:
            pickle.dump(self, f)
        print(f"NLP processor saved to {path}")

    @staticmethod
    def load(path: str = None) -> "NLPProcessor":
        """Load NLP models."""
        path = path or str(MODELS_DIR / "nlp_processor.pkl")
        with open(path, "rb") as f:
            return pickle.load(f)


# Singleton instance
_nlp_processor: Optional[NLPProcessor] = None


def get_nlp_processor() -> NLPProcessor:
    """Get or create singleton NLP processor."""
    global _nlp_processor
    if _nlp_processor is None:
        _nlp_processor = NLPProcessor()
        _nlp_processor.intent_classifier.train()
    return _nlp_processor


if __name__ == "__main__":
    # Test NLP processor with comprehensive test cases
    nlp = NLPProcessor()
    nlp.intent_classifier.train()

    print("=" * 70)
    print("Testing Enhanced NLP Processor")
    print("=" * 70)

    # Test queries organized by feature
    test_cases = {
        "Basic Intents": [
            "Hello!",
            "What can you help me with?",
            "Show me phones",
            "I want to buy a laptop",
            "Compare iPhone vs Samsung",
            "Thanks for the help!",
        ],
        "Price Parsing (k/lakh)": [
            "phones under 20k",
            "laptops below 50000",
            "tv under 5 lakh",
            "budget between 10k to 20k",
            "mobiles above 15000",
        ],
        "Fuzzy Brand Matching": [
            "samung phone",  # Samsung typo
            "addidas shoes",  # Adidas typo
            "1plus mobile",  # OnePlus variation
            "sonny headphones",  # Sony typo
        ],
        "New Entity Types": [
            "13 inch laptop",
            "men's shoes under 2000",
            "women's dresses on sale",
            "kids toys",
            "8gb ram phone",
            "256gb storage laptop",
        ],
        "Negation Handling": [
            "phone without camera",
            "laptop no gaming",
            "don't want wireless",
        ],
        "New Intents": [
            "how much does iPhone cost",  # inquiry
            "show me cheaper ones",  # refine
            "is this in stock",  # inquiry
            "any more options",  # refine
        ],
        "Color & Discount": [
            "black phone under 15000",
            "products on sale",
            "50% off deals",
            "rose gold watch",
        ],
    }

    for category, queries in test_cases.items():
        print(f"\n{'='*70}")
        print(f" {category}")
        print("=" * 70)

        for query in queries:
            result = nlp.process(query)
            print(f"\nQuery: \"{query}\"")
            print(f"  Intent: {result['intent']} ({result['intent_confidence']:.2f})")

            # Print relevant entities only
            entities = {k: v for k, v in result['entities'].items()
                       if v and k != 'original_query'}
            if entities:
                print(f"  Entities: {entities}")

            if result['filters']:
                print(f"  Filters: {result['filters']}")

    print("\n" + "=" * 70)
    print("NLP Testing Complete!")
    print("=" * 70)
