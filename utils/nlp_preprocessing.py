"""
NLP Preprocessing Utilities for LSTM Chatbot
Handles text cleaning, tokenization, and sequence preparation
"""

import numpy as np
import re
import pickle
import os
from collections import Counter


class TextPreprocessor:
    """Text preprocessing for LSTM model"""

    def __init__(self, max_vocab_size=5000, max_sequence_length=20):
        self.max_vocab_size = max_vocab_size
        self.max_sequence_length = max_sequence_length
        self.word_to_index = {}
        self.index_to_word = {}
        self.intent_to_index = {}
        self.index_to_intent = {}
        self.vocab_size = 0

    def clean_text(self, text):
        """Clean and normalize text"""
        # Convert to lowercase
        text = text.lower().strip()
        # Remove special characters but keep alphanumeric and spaces
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def tokenize(self, text):
        """Simple word tokenization"""
        return text.split()

    def build_vocabulary(self, texts):
        """Build vocabulary from training texts"""
        word_counts = Counter()

        for text in texts:
            cleaned = self.clean_text(text)
            tokens = self.tokenize(cleaned)
            word_counts.update(tokens)

        # Reserve indices for special tokens
        self.word_to_index = {'<PAD>': 0, '<UNK>': 1}

        # Add most common words
        most_common = word_counts.most_common(self.max_vocab_size - 2)
        for idx, (word, _) in enumerate(most_common, start=2):
            self.word_to_index[word] = idx

        self.index_to_word = {idx: word for word, idx in self.word_to_index.items()}
        self.vocab_size = len(self.word_to_index)

        print(f"Vocabulary built with {self.vocab_size} unique words")
        return self.word_to_index

    def build_intent_mapping(self, intents):
        """Build intent label mapping"""
        unique_intents = sorted(list(set(intents)))
        self.intent_to_index = {intent: idx for idx, intent in enumerate(unique_intents)}
        self.index_to_intent = {idx: intent for intent, idx in self.intent_to_index.items()}
        print(f"Intent mapping built with {len(unique_intents)} intents")
        return self.intent_to_index

    def text_to_sequence(self, text):
        """Convert text to sequence of indices"""
        cleaned = self.clean_text(text)
        tokens = self.tokenize(cleaned)
        sequence = []

        for token in tokens:
            if token in self.word_to_index:
                sequence.append(self.word_to_index[token])
            else:
                sequence.append(self.word_to_index['<UNK>'])

        return sequence

    def pad_sequence(self, sequence, max_length=None):
        """Pad or truncate sequence to fixed length"""
        if max_length is None:
            max_length = self.max_sequence_length

        if len(sequence) > max_length:
            return sequence[:max_length]
        else:
            return sequence + [0] * (max_length - len(sequence))

    def texts_to_sequences(self, texts):
        """Convert multiple texts to padded sequences"""
        sequences = []
        for text in texts:
            seq = self.text_to_sequence(text)
            padded_seq = self.pad_sequence(seq)
            sequences.append(padded_seq)
        return np.array(sequences)

    def intents_to_indices(self, intents):
        """Convert intent labels to indices"""
        return np.array([self.intent_to_index[intent] for intent in intents])

    def index_to_intent_label(self, index):
        """Convert index back to intent label"""
        return self.index_to_intent.get(index, 'unknown')

    def save(self, filepath):
        """Save preprocessor state"""
        state = {
            'word_to_index': self.word_to_index,
            'index_to_word': self.index_to_word,
            'intent_to_index': self.intent_to_index,
            'index_to_intent': self.index_to_intent,
            'vocab_size': self.vocab_size,
            'max_vocab_size': self.max_vocab_size,
            'max_sequence_length': self.max_sequence_length
        }
        with open(filepath, 'wb') as f:
            pickle.dump(state, f)
        print(f"Preprocessor saved to {filepath}")

    def load(self, filepath):
        """Load preprocessor state"""
        with open(filepath, 'rb') as f:
            state = pickle.load(f)

        self.word_to_index = state['word_to_index']
        self.index_to_word = state['index_to_word']
        self.intent_to_index = state['intent_to_index']
        self.index_to_intent = state['index_to_intent']
        self.vocab_size = state['vocab_size']
        self.max_vocab_size = state['max_vocab_size']
        self.max_sequence_length = state['max_sequence_length']
        print(f"Preprocessor loaded from {filepath}")


class EntityExtractor:
    """Extract entities from user messages"""

    def __init__(self):
        # Main categories matching the dataset (must match products.csv exactly)
        self.categories = [
            'electronics', 'clothing', 'home & kitchen', 'sports', 'beauty',
            'books', 'toys', 'grocery'
        ]

        # Category aliases - maps variations to standard category names
        self.category_aliases = {
            # Electronics
            'phone': 'electronics',
            'phones': 'electronics',
            'mobile': 'electronics',
            'mobiles': 'electronics',
            'smartphone': 'electronics',
            'smartphones': 'electronics',
            'computer': 'electronics',
            'computers': 'electronics',
            'notebook': 'electronics',
            'laptop': 'electronics',
            'laptops': 'electronics',
            'earphones': 'electronics',
            'earbuds': 'electronics',
            'headphones': 'electronics',
            'television': 'electronics',
            'televisions': 'electronics',
            'tv': 'electronics',
            'smart tv': 'electronics',
            'tablet': 'electronics',
            'tablets': 'electronics',
            'ipad': 'electronics',
            'smartwatch': 'electronics',
            'smartwatches': 'electronics',
            'power bank': 'electronics',
            'speaker': 'electronics',
            'speakers': 'electronics',
            'camera': 'electronics',
            'cameras': 'electronics',
            # Clothing
            'clothes': 'clothing',
            'apparel': 'clothing',
            'wear': 'clothing',
            'shirt': 'clothing',
            'shirts': 'clothing',
            'tshirt': 'clothing',
            'tshirts': 'clothing',
            't-shirt': 'clothing',
            't-shirts': 'clothing',
            'jean': 'clothing',
            'jeans': 'clothing',
            'pants': 'clothing',
            'trousers': 'clothing',
            'dress': 'clothing',
            'dresses': 'clothing',
            'jacket': 'clothing',
            'jackets': 'clothing',
            'coat': 'clothing',
            'coats': 'clothing',
            'hoodie': 'clothing',
            'hoodies': 'clothing',
            'shoe': 'clothing',
            'shoes': 'clothing',
            'footwear': 'clothing',
            'sneaker': 'clothing',
            'sneakers': 'clothing',
            'formal': 'clothing',
            'polo': 'clothing',
            # Home & Kitchen
            'kitchen': 'home & kitchen',
            'home': 'home & kitchen',
            'appliances': 'home & kitchen',
            'appliance': 'home & kitchen',
            'microwave': 'home & kitchen',
            'microwave oven': 'home & kitchen',
            'fryer': 'home & kitchen',
            'air fryer': 'home & kitchen',
            'purifier': 'home & kitchen',
            'water purifier': 'home & kitchen',
            'mixer': 'home & kitchen',
            'grinder': 'home & kitchen',
            'kettle': 'home & kitchen',
            'washing machine': 'home & kitchen',
            'furniture': 'home & kitchen',
            # Sports
            'sport': 'sports',
            'fitness': 'sports',
            'gym': 'sports',
            'exercise': 'sports',
            'workout': 'sports',
            'running': 'sports',
            'cycling': 'sports',
            'swimming': 'sports',
            'tennis': 'sports',
            'yoga': 'sports',
            'dumbbell': 'sports',
            'dumbbells': 'sports',
            'racket': 'sports',
            'helmet': 'sports',
            'goggles': 'sports',
            # Beauty
            'cosmetics': 'beauty',
            'makeup': 'beauty',
            'makeup kit': 'beauty',
            'skincare': 'beauty',
            'skin care': 'beauty',
            'lipstick': 'beauty',
            'serum': 'beauty',
            'face wash': 'beauty',
            'sunscreen': 'beauty',
            'hair oil': 'beauty',
            'fragrance': 'beauty',
            'perfume': 'beauty',
            'cologne': 'beauty',
            # Books
            'book': 'books',
            'reading': 'books',
            'novel': 'books',
            'novels': 'books',
            'fiction': 'books',
            'textbook': 'books',
            'textbooks': 'books',
            'self help': 'books',
            'biography': 'books',
            'history': 'books',
            'science': 'books',
            # Toys
            'toy': 'toys',
            'games': 'toys',
            'game': 'toys',
            'lego': 'toys',
            'doll': 'toys',
            'dolls': 'toys',
            'puzzle': 'toys',
            'puzzles': 'toys',
            'board game': 'toys',
            'remote control': 'toys',
            'building blocks': 'toys',
            'educational': 'toys',
            # Grocery
            'groceries': 'grocery',
            'food': 'grocery',
            'foods': 'grocery',
            'snacks': 'grocery',
            'snack': 'grocery',
            'beverages': 'grocery',
            'drinks': 'grocery',
            'tea': 'grocery',
            'coffee': 'grocery',
            'honey': 'grocery',
            'cereal': 'grocery',
            'spices': 'grocery',
            'chocolate': 'grocery',
            'oil': 'grocery',
            'cooking oil': 'grocery',
            'rice': 'grocery',
            'flour': 'grocery'
        }

    def extract_price(self, text):
        """Extract price from text"""
        text = text.lower()

        # Pattern for price extraction
        patterns = [
            r'\$?\s*(\d+(?:\.\d{2})?)',  # $100 or 100 or 100.00
            r'under\s+\$?\s*(\d+)',      # under $100
            r'below\s+\$?\s*(\d+)',      # below 100
            r'less\s+than\s+\$?\s*(\d+)', # less than 100
            r'budget\s+(?:of\s+)?\$?\s*(\d+)', # budget of 100
            r'within\s+\$?\s*(\d+)',     # within 100
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        return None

    def extract_category(self, text):
        """Extract category from text"""
        text = text.lower()
        words = text.split()

        # Check for exact category matches
        for word in words:
            if word in self.categories:
                return word.title() if word != 'home & kitchen' else 'Home & Kitchen'
            if word in self.category_aliases:
                cat = self.category_aliases[word]
                return cat.title() if cat != 'home & kitchen' else 'Home & Kitchen'

        # Check for multi-word categories
        for category in self.categories:
            if category in text:
                return category.title() if category != 'home & kitchen' else 'Home & Kitchen'

        return None

    def extract_all(self, text):
        """Extract all entities from text"""
        return {
            'category': self.extract_category(text),
            'price': self.extract_price(text)
        }


if __name__ == '__main__':
    # Test the preprocessor
    preprocessor = TextPreprocessor()

    test_texts = [
        "Show me electronics under 100 dollars",
        "I want to buy some shoes",
        "Recommend me good laptops",
        "Hello there!",
        "What's in my cart?"
    ]

    test_intents = ['search_product', 'search_product', 'recommendation', 'greeting', 'cart_view']

    # Build vocabulary
    preprocessor.build_vocabulary(test_texts)
    preprocessor.build_intent_mapping(test_intents)

    # Test conversion
    sequences = preprocessor.texts_to_sequences(test_texts)
    print("\nTest sequences:")
    for text, seq in zip(test_texts, sequences):
        print(f"  {text} -> {seq}")

    # Test entity extraction
    extractor = EntityExtractor()
    print("\nEntity extraction tests:")
    for text in test_texts:
        entities = extractor.extract_all(text)
        print(f"  {text} -> {entities}")
