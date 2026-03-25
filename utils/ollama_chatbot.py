"""
Ollama-Powered Shopping Chatbot with RAG
Uses local LLM with product data for intelligent shopping assistance
"""

import requests
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import re
import os


class ProductIndexer:
    """Index and search products for RAG context"""

    def __init__(self, products_df: pd.DataFrame):
        self.products_df = products_df
        self.category_products = {}
        self._build_index()

    def _build_index(self):
        """Build category-wise product index"""
        for category in self.products_df['category'].unique():
            cat_products = self.products_df[self.products_df['category'] == category]
            self.category_products[category.lower()] = cat_products

        print(f"  Product index built with {len(self.category_products)} categories")

    def search_products(self,
                       query: str = None,
                       category: str = None,
                       max_price: float = None,
                       min_price: float = None,
                       limit: int = 10) -> pd.DataFrame:
        """Search products based on criteria"""
        results = self.products_df.copy()

        # Filter by category
        if category:
            cat_lower = category.lower()
            results = results[results['category'].str.lower() == cat_lower]

        # Filter by price range
        if max_price:
            results = results[results['price'] <= max_price]
        if min_price:
            results = results[results['price'] >= min_price]

        # Search by query in product name
        if query:
            query_lower = query.lower()
            results = results[results['name'].str.lower().str.contains(query_lower, na=False)]

        # Sort by relevance (discount + rating proxy)
        if 'discount_percent' in results.columns:
            results = results.sort_values('discount_percent', ascending=False)

        return results.head(limit)

    def get_category_summary(self, category: str) -> Dict:
        """Get summary stats for a category"""
        cat_lower = category.lower()
        if cat_lower in self.category_products:
            cat_df = self.category_products[cat_lower]
            return {
                'category': category,
                'total_products': len(cat_df),
                'min_price': cat_df['price'].min(),
                'max_price': cat_df['price'].max(),
                'avg_price': cat_df['price'].mean(),
                'top_brands': cat_df['name'].str.split().str[0].value_counts().head(5).to_dict()
            }
        return None

    def get_all_categories(self) -> List[str]:
        """Get list of all categories"""
        return list(self.products_df['category'].unique())


class EntityExtractorLocal:
    """Extract entities from user messages for Ollama chatbot"""

    def __init__(self):
        self.categories = [
            'electronics', 'clothing', 'home & kitchen', 'sports', 'beauty',
            'books', 'toys', 'grocery'
        ]

        self.category_aliases = {
            # Electronics
            'phone': 'electronics', 'phones': 'electronics', 'mobile': 'electronics',
            'smartphone': 'electronics', 'smartphones': 'electronics',
            'computer': 'electronics', 'computers': 'electronics',
            'laptop': 'electronics', 'laptops': 'electronics', 'notebook': 'electronics',
            'tablet': 'electronics', 'tablets': 'electronics', 'ipad': 'electronics',
            'tv': 'electronics', 'television': 'electronics', 'smart tv': 'electronics',
            'camera': 'electronics', 'cameras': 'electronics',
            'headphone': 'electronics', 'headphones': 'electronics', 'earphones': 'electronics',
            'earbuds': 'electronics', 'speaker': 'electronics', 'speakers': 'electronics',
            'smartwatch': 'electronics', 'watch': 'electronics', 'watches': 'electronics',
            'power bank': 'electronics', 'powerbank': 'electronics',
            # Clothing
            'clothes': 'clothing', 'apparel': 'clothing', 'wear': 'clothing',
            'shirt': 'clothing', 'shirts': 'clothing', 't-shirt': 'clothing',
            'tshirt': 'clothing', 'jeans': 'clothing', 'pants': 'clothing',
            'dress': 'clothing', 'dresses': 'clothing', 'jacket': 'clothing',
            'shoe': 'clothing', 'shoes': 'clothing', 'footwear': 'clothing',
            'sneakers': 'clothing', 'hoodie': 'clothing',
            # Home & Kitchen
            'kitchen': 'home & kitchen', 'home': 'home & kitchen',
            'appliance': 'home & kitchen', 'appliances': 'home & kitchen',
            'microwave': 'home & kitchen', 'fryer': 'home & kitchen',
            'mixer': 'home & kitchen', 'blender': 'home & kitchen',
            'furniture': 'home & kitchen', 'cookware': 'home & kitchen',
            # Sports
            'sport': 'sports', 'fitness': 'sports', 'gym': 'sports',
            'exercise': 'sports', 'workout': 'sports', 'yoga': 'sports',
            'running': 'sports', 'cycling': 'sports', 'dumbbell': 'sports',
            # Beauty
            'makeup': 'beauty', 'cosmetics': 'beauty', 'skincare': 'beauty',
            'perfume': 'beauty', 'fragrance': 'beauty', 'lipstick': 'beauty',
            # Books
            'book': 'books', 'novel': 'books', 'reading': 'books',
            'fiction': 'books', 'textbook': 'books',
            # Toys
            'toy': 'toys', 'game': 'toys', 'games': 'toys',
            'puzzle': 'toys', 'lego': 'toys', 'doll': 'toys',
            # Grocery
            'groceries': 'grocery', 'food': 'grocery', 'snack': 'grocery',
            'snacks': 'grocery', 'beverages': 'grocery', 'drinks': 'grocery',
        }

    def extract_category(self, text: str) -> Optional[str]:
        """Extract category from text"""
        text_lower = text.lower()
        words = text_lower.split()

        # Check aliases first
        for word in words:
            if word in self.category_aliases:
                cat = self.category_aliases[word]
                return cat.title() if cat != 'home & kitchen' else 'Home & Kitchen'

        # Check main categories
        for word in words:
            if word in self.categories:
                return word.title() if word != 'home & kitchen' else 'Home & Kitchen'

        # Check multi-word categories
        for category in self.categories:
            if category in text_lower:
                return category.title() if category != 'home & kitchen' else 'Home & Kitchen'

        return None

    def extract_price(self, text: str) -> Optional[float]:
        """Extract price from text"""
        text_lower = text.lower()

        patterns = [
            r'under\s+(?:rs\.?|rupees?)?\s*(\d+(?:,\d+)?(?:\.\d+)?)',
            r'below\s+(?:rs\.?|rupees?)?\s*(\d+(?:,\d+)?(?:\.\d+)?)',
            r'less\s+than\s+(?:rs\.?|rupees?)?\s*(\d+(?:,\d+)?(?:\.\d+)?)',
            r'within\s+(?:rs\.?|rupees?)?\s*(\d+(?:,\d+)?(?:\.\d+)?)',
            r'budget\s+(?:of\s+)?(?:rs\.?|rupees?)?\s*(\d+(?:,\d+)?(?:\.\d+)?)',
            r'(?:rs\.?|rupees?)\s*(\d+(?:,\d+)?(?:\.\d+)?)',
            r'(\d+(?:,\d+)?(?:\.\d+)?)\s*(?:rs\.?|rupees?)',
            r'\$\s*(\d+(?:,\d+)?(?:\.\d+)?)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    return float(price_str)
                except ValueError:
                    continue

        return None

    def extract_product_name(self, text: str) -> Optional[str]:
        """Extract specific product name from text"""
        text_lower = text.lower()

        # Common product keywords to search for
        product_keywords = [
            'laptop', 'phone', 'smartphone', 'tablet', 'tv', 'camera',
            'headphones', 'speaker', 'watch', 'smartwatch', 'earbuds'
        ]

        for keyword in product_keywords:
            if keyword in text_lower:
                return keyword

        return None


class OllamaChatbot:
    """Ollama-powered shopping chatbot with RAG"""

    def __init__(self,
                 products_df: pd.DataFrame,
                 model: str = "llama3",
                 ollama_url: str = "http://localhost:11434"):

        self.model = model
        self.ollama_url = ollama_url
        self.products_df = products_df

        # Initialize components
        self.product_indexer = ProductIndexer(products_df)
        self.entity_extractor = EntityExtractorLocal()

        # Conversation history per user
        self.conversations = {}

        # System prompt for shopping assistant
        self.system_prompt = self._build_system_prompt()

        print(f"  Ollama chatbot initialized with model: {model}")

    def _build_system_prompt(self) -> str:
        """Build the system prompt with store context"""
        categories = self.product_indexer.get_all_categories()

        return f"""You are a friendly and helpful shopping assistant for an online store.
Your job is to help customers find products, answer questions, and provide recommendations.

STORE INFORMATION:
- Categories available: {', '.join(categories)}
- Total products: {len(self.products_df)}
- Price range: Rs.{self.products_df['price'].min():.0f} to Rs.{self.products_df['price'].max():.0f}

GUIDELINES:
1. Be conversational, friendly, and helpful
2. When recommending products, mention the product name, price, and any discount
3. If asked about products not in your catalog, politely explain you don't have them
4. Always use Indian Rupees (Rs.) for prices
5. Keep responses concise but informative (2-4 sentences max unless listing products)
6. If unsure about a product, ask clarifying questions
7. Suggest related products when appropriate

RESPONSE FORMAT:
- For greetings: Be warm and ask how you can help
- For product queries: List relevant products with prices
- For recommendations: Provide 3-5 options with brief descriptions
- For comparisons: Highlight key differences
- For out of scope: Politely redirect to shopping topics"""

    def _get_product_context(self,
                            category: str = None,
                            max_price: float = None,
                            product_name: str = None,
                            limit: int = 8) -> str:
        """Get relevant product context for RAG"""
        products = self.product_indexer.search_products(
            query=product_name,
            category=category,
            max_price=max_price,
            limit=limit
        )

        if products.empty:
            return "No matching products found in the catalog."

        context_parts = ["\nRELEVANT PRODUCTS FROM CATALOG:"]
        for idx, row in products.iterrows():
            discount_info = f" ({row['discount_percent']}% off)" if row.get('discount_percent', 0) > 0 else ""
            context_parts.append(
                f"- {row['name']}: Rs.{row['price']:.0f}{discount_info} | Category: {row['category']}"
            )

        return "\n".join(context_parts)

    def _call_ollama(self, prompt: str, context: str = "") -> str:
        """Call Ollama API to generate response"""
        full_prompt = f"{self.system_prompt}\n\n{context}\n\nUser: {prompt}\n\nAssistant:"

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 300
                    }
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                return f"I'm having trouble connecting to my brain right now. Error: {response.status_code}"

        except requests.exceptions.ConnectionError:
            return "I'm unable to connect to the Ollama service. Please make sure Ollama is running (ollama serve)."
        except requests.exceptions.Timeout:
            return "The request took too long. Please try again with a simpler question."
        except Exception as e:
            return f"Something went wrong: {str(e)}"

    def _detect_intent(self, message: str) -> str:
        """Detect user intent from message"""
        message_lower = message.lower()

        # Greeting patterns
        if any(word in message_lower for word in ['hi', 'hello', 'hey', 'good morning', 'good evening']):
            return 'greeting'

        # Farewell patterns
        if any(word in message_lower for word in ['bye', 'goodbye', 'see you', 'thanks', 'thank you']):
            return 'farewell'

        # Price query patterns
        if any(word in message_lower for word in ['price', 'cost', 'how much', 'budget', 'under', 'below', 'cheap']):
            return 'price_query'

        # Recommendation patterns
        if any(word in message_lower for word in ['recommend', 'suggest', 'best', 'top', 'popular', 'good']):
            return 'recommendation'

        # Search patterns
        if any(word in message_lower for word in ['show', 'find', 'search', 'looking for', 'want', 'need', 'buy']):
            return 'search'

        # Comparison patterns
        if any(word in message_lower for word in ['compare', 'difference', 'vs', 'versus', 'better']):
            return 'comparison'

        # Help patterns
        if any(word in message_lower for word in ['help', 'how do', 'what can']):
            return 'help'

        return 'general'

    def process_message(self,
                       message: str,
                       user_id: str = "default") -> Dict:
        """Process user message and generate response"""

        # Extract entities
        category = self.entity_extractor.extract_category(message)
        price = self.entity_extractor.extract_price(message)
        product_name = self.entity_extractor.extract_product_name(message)

        # Detect intent
        intent = self._detect_intent(message)

        # Get relevant product context for RAG
        context = ""
        products_list = []

        if intent in ['search', 'recommendation', 'price_query', 'comparison'] or category:
            # Get product context
            context = self._get_product_context(
                category=category,
                max_price=price,
                product_name=product_name,
                limit=8
            )

            # Get actual products for API response
            products = self.product_indexer.search_products(
                query=product_name,
                category=category,
                max_price=price,
                limit=6
            )

            products_list = products.to_dict('records') if not products.empty else []

        # Generate response using Ollama
        response_text = self._call_ollama(message, context)

        # Store conversation history
        if user_id not in self.conversations:
            self.conversations[user_id] = []

        self.conversations[user_id].append({
            'user': message,
            'assistant': response_text,
            'intent': intent,
            'entities': {'category': category, 'price': price}
        })

        # Keep only last 10 exchanges
        if len(self.conversations[user_id]) > 10:
            self.conversations[user_id] = self.conversations[user_id][-10:]

        return {
            'success': True,
            'response': response_text,
            'intent': intent,
            'confidence': 0.95,  # Ollama doesn't provide confidence, using placeholder
            'entities': {
                'category': category,
                'price': price,
                'product_name': product_name
            },
            'products': products_list
        }

    def get_conversation_history(self, user_id: str) -> List[Dict]:
        """Get conversation history for a user"""
        return self.conversations.get(user_id, [])

    def clear_conversation(self, user_id: str):
        """Clear conversation history for a user"""
        if user_id in self.conversations:
            self.conversations[user_id] = []


def test_ollama_connection(model: str = "llama3",
                          ollama_url: str = "http://localhost:11434") -> bool:
    """Test if Ollama is running and model is available"""
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m.get('name', '').split(':')[0] for m in models]
            return model in model_names or f"{model}:latest" in [m.get('name', '') for m in models]
        return False
    except:
        return False
