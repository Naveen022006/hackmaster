"""
LSTM-based Intent Classification and Entity Extraction Model
Uses TensorFlow/Keras for building the neural network
"""

import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import (
    Input, Embedding, LSTM, Dense, Dropout, Bidirectional,
    GlobalMaxPooling1D, Concatenate
)
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.utils import to_categorical
import os
import json


class LSTMIntentClassifier:
    """LSTM model for intent classification"""

    def __init__(self, vocab_size, embedding_dim=128, lstm_units=64,
                 max_sequence_length=20, num_intents=13):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.lstm_units = lstm_units
        self.max_sequence_length = max_sequence_length
        self.num_intents = num_intents
        self.model = None
        self.history = None

    def build_model(self):
        """Build the LSTM model architecture"""

        # Input layer
        input_layer = Input(shape=(self.max_sequence_length,), name='input')

        # Embedding layer
        embedding = Embedding(
            input_dim=self.vocab_size,
            output_dim=self.embedding_dim,
            input_length=self.max_sequence_length,
            name='embedding'
        )(input_layer)

        # Bidirectional LSTM layers
        lstm1 = Bidirectional(
            LSTM(self.lstm_units, return_sequences=True, dropout=0.2),
            name='bilstm_1'
        )(embedding)

        lstm2 = Bidirectional(
            LSTM(self.lstm_units // 2, return_sequences=True, dropout=0.2),
            name='bilstm_2'
        )(lstm1)

        # Global max pooling
        pooled = GlobalMaxPooling1D(name='global_max_pool')(lstm2)

        # Dense layers
        dense1 = Dense(64, activation='relu', name='dense_1')(pooled)
        dropout1 = Dropout(0.3, name='dropout_1')(dense1)

        dense2 = Dense(32, activation='relu', name='dense_2')(dropout1)
        dropout2 = Dropout(0.2, name='dropout_2')(dense2)

        # Output layer for intent classification
        output = Dense(self.num_intents, activation='softmax', name='intent_output')(dropout2)

        # Create model
        self.model = Model(inputs=input_layer, outputs=output, name='intent_classifier')

        # Compile model
        self.model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )

        print("Model built successfully!")
        self.model.summary()

        return self.model

    def train(self, X_train, y_train, X_val=None, y_val=None,
              epochs=50, batch_size=32, model_path=None):
        """Train the model"""

        if self.model is None:
            self.build_model()

        # Convert labels to one-hot encoding
        y_train_cat = to_categorical(y_train, num_classes=self.num_intents)

        callbacks = [
            EarlyStopping(
                monitor='val_loss' if X_val is not None else 'loss',
                patience=5,
                restore_best_weights=True,
                verbose=1
            )
        ]

        if model_path:
            callbacks.append(
                ModelCheckpoint(
                    model_path,
                    monitor='val_loss' if X_val is not None else 'loss',
                    save_best_only=True,
                    verbose=1
                )
            )

        validation_data = None
        if X_val is not None and y_val is not None:
            y_val_cat = to_categorical(y_val, num_classes=self.num_intents)
            validation_data = (X_val, y_val_cat)

        self.history = self.model.fit(
            X_train, y_train_cat,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )

        return self.history

    def predict(self, X):
        """Predict intent for input sequences"""
        if self.model is None:
            raise ValueError("Model not built or loaded")

        predictions = self.model.predict(X, verbose=0)
        return predictions

    def predict_intent(self, X):
        """Predict intent class for input sequences"""
        predictions = self.predict(X)
        return np.argmax(predictions, axis=1)

    def predict_with_confidence(self, X):
        """Predict intent with confidence scores"""
        predictions = self.predict(X)
        intent_indices = np.argmax(predictions, axis=1)
        confidences = np.max(predictions, axis=1)
        return intent_indices, confidences

    def save(self, model_path, config_path=None):
        """Save model and configuration"""
        self.model.save(model_path)
        print(f"Model saved to {model_path}")

        if config_path:
            config = {
                'vocab_size': self.vocab_size,
                'embedding_dim': self.embedding_dim,
                'lstm_units': self.lstm_units,
                'max_sequence_length': self.max_sequence_length,
                'num_intents': self.num_intents
            }
            with open(config_path, 'w') as f:
                json.dump(config, f)
            print(f"Configuration saved to {config_path}")

    def load(self, model_path, config_path=None):
        """Load model and configuration"""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            self.vocab_size = config['vocab_size']
            self.embedding_dim = config['embedding_dim']
            self.lstm_units = config['lstm_units']
            self.max_sequence_length = config['max_sequence_length']
            self.num_intents = config['num_intents']

        self.model = load_model(model_path)
        print(f"Model loaded from {model_path}")


class ChatbotModel:
    """Complete chatbot model combining LSTM intent classifier with entity extraction"""

    def __init__(self, preprocessor, entity_extractor, intent_model=None):
        self.preprocessor = preprocessor
        self.entity_extractor = entity_extractor
        self.intent_model = intent_model

    def process_message(self, message):
        """Process a user message and return intent, entities, and confidence"""

        # Extract entities using rule-based extractor (for structured data)
        entities = self.entity_extractor.extract_all(message)

        # Convert message to sequence for LSTM
        sequence = self.preprocessor.texts_to_sequences([message])

        # Predict intent using LSTM
        intent_idx, confidence = self.intent_model.predict_with_confidence(sequence)
        intent_idx = intent_idx[0]
        confidence = float(confidence[0])

        # Get intent label
        intent = self.preprocessor.index_to_intent_label(intent_idx)

        return {
            'intent': intent,
            'confidence': confidence,
            'entities': entities,
            'original_message': message
        }

    def get_response_template(self, intent, entities):
        """Get response template based on intent and entities"""

        templates = {
            'greeting': [
                "Hello! Welcome to our shopping assistant. How can I help you today?",
                "Hi there! I'm here to help you find great products. What are you looking for?",
                "Hey! Ready to help you shop. What can I assist you with?"
            ],
            'goodbye': [
                "Thank you for shopping with us! Have a great day!",
                "Goodbye! Come back soon for more great deals!",
                "See you later! Happy shopping!"
            ],
            'search_product': [
                f"I'll search for {entities.get('category', 'products')} for you.",
                f"Looking for the best {entities.get('category', 'items')} in our catalog.",
                f"Let me find some great {entities.get('category', 'products')} for you."
            ],
            'price_query': [
                f"Searching for products under ${entities.get('price', 100)}.",
                f"Finding affordable options within your budget of ${entities.get('price', 100)}.",
                f"Let me filter products under ${entities.get('price', 100)} for you."
            ],
            'recommendation': [
                "Based on your preferences, here are my top recommendations!",
                "I've curated some products just for you!",
                "Here are personalized recommendations based on your history."
            ],
            'category_recommendation': [
                f"Here are the best {entities.get('category', 'products')} I recommend!",
                f"Top picks in {entities.get('category', 'this category')} for you.",
                f"Check out these highly-rated {entities.get('category', 'items')}!"
            ],
            'cart_add': [
                "Added to your cart! Would you like to continue shopping?",
                "Great choice! The item has been added to your cart.",
                "Done! Check your cart to review your selections."
            ],
            'cart_view': [
                "Here's what's in your shopping cart.",
                "Let me show you your cart contents.",
                "Your shopping cart:"
            ],
            'order_status': [
                "Let me check the status of your orders.",
                "Here's the latest update on your orders.",
                "Tracking your order status now."
            ],
            'help': [
                "I can help you search products, get recommendations, manage your cart, and more!",
                "Here's what I can do: search products, recommend items, show deals, track orders.",
                "I'm your shopping assistant! Ask me to find products, show deals, or get recommendations."
            ],
            'feedback': [
                "Thanks for your feedback! I'll use it to improve your recommendations.",
                "I appreciate your input! This helps me serve you better.",
                "Feedback noted! Your preferences have been updated."
            ],
            'compare': [
                "Let me compare these products for you.",
                "Here's a comparison of your selected items.",
                "Comparing products based on features and price."
            ],
            'deals': [
                "Here are today's best deals!",
                "Check out these amazing discounts!",
                "Hot deals just for you!"
            ]
        }

        import random
        responses = templates.get(intent, ["I'm here to help! What would you like to do?"])
        return random.choice(responses)


def train_intent_model(chatbot_data_path, model_save_path, preprocessor_save_path):
    """Train the LSTM intent classification model"""

    import pandas as pd
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from utils.nlp_preprocessing import TextPreprocessor

    # Load training data
    print("Loading chatbot training data...")
    df = pd.read_csv(chatbot_data_path)

    texts = df['text'].tolist()
    intents = df['intent'].tolist()

    # Initialize preprocessor
    preprocessor = TextPreprocessor(max_vocab_size=5000, max_sequence_length=20)

    # Build vocabulary and intent mapping
    preprocessor.build_vocabulary(texts)
    preprocessor.build_intent_mapping(intents)

    # Convert to sequences
    X = preprocessor.texts_to_sequences(texts)
    y = preprocessor.intents_to_indices(intents)

    # Split data
    from sklearn.model_selection import train_test_split
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"\nTraining samples: {len(X_train)}")
    print(f"Validation samples: {len(X_val)}")
    print(f"Vocabulary size: {preprocessor.vocab_size}")
    print(f"Number of intents: {len(preprocessor.intent_to_index)}")

    # Build and train model
    model = LSTMIntentClassifier(
        vocab_size=preprocessor.vocab_size,
        embedding_dim=128,
        lstm_units=64,
        max_sequence_length=preprocessor.max_sequence_length,
        num_intents=len(preprocessor.intent_to_index)
    )

    model.build_model()

    print("\nTraining LSTM model...")
    model.train(
        X_train, y_train,
        X_val, y_val,
        epochs=50,
        batch_size=32,
        model_path=model_save_path
    )

    # Save preprocessor
    preprocessor.save(preprocessor_save_path)

    # Evaluate
    y_pred = model.predict_intent(X_val)
    accuracy = np.mean(y_pred == y_val)
    print(f"\nValidation Accuracy: {accuracy:.4f}")

    # Save model config
    config_path = model_save_path.replace('.keras', '_config.json').replace('.h5', '_config.json')
    model.save(model_save_path, config_path)

    return model, preprocessor


if __name__ == '__main__':
    # Training script
    import os

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, 'data', 'chatbot_data.csv')
    model_path = os.path.join(base_dir, 'models', 'intent_model.keras')
    preprocessor_path = os.path.join(base_dir, 'models', 'preprocessor.pkl')

    # Check if data exists
    if not os.path.exists(data_path):
        print(f"Training data not found at {data_path}")
        print("Please run generate_datasets.py first")
    else:
        train_intent_model(data_path, model_path, preprocessor_path)
