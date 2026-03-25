"""
Flask Backend for Personal Shopping Agent
Provides REST APIs for chat, recommendations, and feedback
Supports both LSTM and Ollama chatbot backends
"""

import os
import sys
import json
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import pandas as pd
import numpy as np
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.nlp_preprocessing import TextPreprocessor, EntityExtractor
from utils.recommendation_engine import HybridRecommender
from utils.session_manager import UserSessionManager
from utils.response_generator import (
    ResponseGenerator, generate_response, handle_context,
    personalize_response, get_follow_up
)
from models.lstm_model import LSTMIntentClassifier, ChatbotModel

# Try importing Ollama chatbot
try:
    from utils.ollama_chatbot import OllamaChatbot, test_ollama_connection
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

app = Flask(__name__)
app.secret_key = 'shopping_agent_secret_key_2024'
CORS(app)

# Configuration - Set to 'ollama' or 'lstm'
CHATBOT_BACKEND = os.environ.get('CHATBOT_BACKEND', 'ollama')  # Default to Ollama
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3')  # Default model

# Global variables for models
recommender = None
chatbot = None
ollama_chatbot = None
session_manager = None
products_df = None
response_gen = None


def load_models():
    """Load all models and data"""
    global recommender, chatbot, ollama_chatbot, session_manager, products_df, response_gen

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    models_dir = os.path.join(base_dir, 'models')

    print("="*60)
    print("Loading Personal Shopping Agent")
    print("="*60)

    # Load datasets
    print("\n1. Loading datasets...")
    users_df = pd.read_csv(os.path.join(data_dir, 'users.csv'))
    products_df = pd.read_csv(os.path.join(data_dir, 'products.csv'))
    interactions_df = pd.read_csv(os.path.join(data_dir, 'interactions.csv'))

    print(f"   Users: {len(users_df)}")
    print(f"   Products: {len(products_df)}")
    print(f"   Interactions: {len(interactions_df)}")

    # Initialize recommendation system
    print("\n2. Initializing Recommendation System...")
    recommender = HybridRecommender(cf_weight=0.6, cb_weight=0.4)
    recommender.fit(users_df, products_df, interactions_df)

    # Initialize chatbot
    print("\n3. Initializing Chatbot...")
    print(f"   Configured backend: {CHATBOT_BACKEND.upper()}")

    # Try Ollama first if configured
    if CHATBOT_BACKEND == 'ollama' and OLLAMA_AVAILABLE:
        print(f"   Checking Ollama connection (model: {OLLAMA_MODEL})...")
        if test_ollama_connection(OLLAMA_MODEL):
            print(f"   Initializing Ollama chatbot...")
            ollama_chatbot = OllamaChatbot(products_df, model=OLLAMA_MODEL)
            print("   Ollama chatbot ready!")
        else:
            print(f"   WARNING: Ollama not running or model '{OLLAMA_MODEL}' not found")
            print("   Tip: Run 'ollama serve' and 'ollama pull llama3'")
            ollama_chatbot = None
    else:
        ollama_chatbot = None

    # Load LSTM as fallback or primary
    if CHATBOT_BACKEND == 'lstm' or ollama_chatbot is None:
        print("   Loading LSTM Chatbot Model...")
        model_path = os.path.join(models_dir, 'intent_model.keras')
        preprocessor_path = os.path.join(models_dir, 'preprocessor.pkl')

        if os.path.exists(model_path) and os.path.exists(preprocessor_path):
            preprocessor = TextPreprocessor()
            preprocessor.load(preprocessor_path)

            config_path = model_path.replace('.keras', '_config.json')
            intent_model = LSTMIntentClassifier(
                vocab_size=preprocessor.vocab_size,
                num_intents=len(preprocessor.intent_to_index)
            )
            intent_model.load(model_path, config_path if os.path.exists(config_path) else None)

            entity_extractor = EntityExtractor()
            chatbot = ChatbotModel(preprocessor, entity_extractor, intent_model)
            print("   LSTM model loaded successfully!")
        else:
            print("   WARNING: LSTM model not found.")
            chatbot = None

    # Initialize session manager
    print("\n4. Initializing Session Manager...")
    session_manager = UserSessionManager(recommender)

    # Initialize advanced response generator
    print("\n5. Initializing Advanced Response Generator...")
    response_gen = ResponseGenerator()
    print("   Response generator ready!")

    # Print active backend status
    if ollama_chatbot:
        active_backend = f"Ollama ({OLLAMA_MODEL})"
    elif chatbot:
        active_backend = "LSTM"
    else:
        active_backend = "None"
    print(f"\n   Active chatbot backend: {active_backend}")

    print("\n" + "="*60)
    print("Shopping Agent Ready!")
    print("="*60 + "\n")


# ============================================
# API ROUTES
# ============================================

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Chat API endpoint
    Processes user messages using Ollama or LSTM model
    """
    global chatbot, ollama_chatbot, recommender, session_manager, response_gen

    data = request.json
    message = data.get('message', '')
    user_id = data.get('user_id', 'GUEST_001')

    if not message:
        return jsonify({
            'success': False,
            'error': 'No message provided'
        }), 400

    response_data = {
        'success': True,
        'message': message,
        'intent': 'unknown',
        'confidence': 0.0,
        'entities': {},
        'response': '',
        'products': [],
        'action': None,
        'follow_up': None,
        'backend': 'none'
    }

    try:
        # Use Ollama chatbot if available
        if ollama_chatbot is not None:
            result = ollama_chatbot.process_message(message, user_id)

            response_data['success'] = result['success']
            response_data['response'] = result['response']
            response_data['intent'] = result['intent']
            response_data['confidence'] = result['confidence']
            response_data['entities'] = result['entities']
            response_data['products'] = result.get('products', [])
            response_data['backend'] = 'ollama'

            # Track search in session manager if products returned
            if result.get('products') and session_manager:
                product_ids = [p.get('product_id') for p in result['products'] if p.get('product_id')]
                if product_ids:
                    session_manager.track_search(user_id, message, [(pid, 1.0) for pid in product_ids])

        # Fall back to LSTM model
        elif chatbot:
            result = chatbot.process_message(message)

            intent = result['intent']
            confidence = result['confidence']
            entities = result['entities']

            response_data['intent'] = intent
            response_data['confidence'] = confidence
            response_data['entities'] = entities
            response_data['backend'] = 'lstm'

            # Handle context continuation
            context_result = handle_context(
                message,
                {'user_id': user_id},
                intent,
                entities
            )

            if context_result['is_continuation']:
                entities = context_result['entities']
                response_data['entities'] = entities
                response_data['is_follow_up'] = True

            cart_count = len(session_manager.get_cart(user_id))

            # Handle different intents
            products = []
            feedback_type = None

            if intent in ['search_product', 'category_recommendation']:
                category = entities.get('category')
                max_price = entities.get('price')

                if category:
                    recs = recommender.recommend(user_id, n=6, category=category, max_price=max_price)
                else:
                    recs = recommender.search_products(message, n=6, max_price=max_price)

                product_ids = [r[0] for r in recs]
                products = get_product_list(product_ids)

                if session_manager:
                    session_manager.track_search(user_id, message, recs)

            elif intent == 'price_query':
                max_price = entities.get('price')
                category = entities.get('category')
                recs = recommender.recommend(user_id, n=6, category=category, max_price=max_price)
                product_ids = [r[0] for r in recs]
                products = get_product_list(product_ids)

            elif intent == 'recommendation':
                recs = session_manager.get_dynamic_recommendations(user_id, n=6)
                product_ids = [r[0] for r in recs]
                products = get_product_list(product_ids)

            elif intent == 'deals':
                deals = session_manager.get_personalized_deals(user_id, n=6)
                products = get_product_list(deals)

            elif intent == 'cart_view':
                cart = session_manager.get_cart(user_id)
                products = get_product_list(cart)

            elif intent == 'feedback':
                message_lower = message.lower()
                if any(word in message_lower for word in ['like', 'love', 'good', 'great', 'awesome']):
                    feedback_type = 'like'
                else:
                    feedback_type = 'dislike'

            # Generate response
            gen_response = generate_response(
                intent=intent,
                entities=entities,
                confidence=confidence,
                user_id=user_id,
                message=message,
                cart_count=cart_count,
                products_count=len(products),
                feedback_type=feedback_type
            )

            response_data['response'] = gen_response['text']
            response_data['action'] = gen_response['action']
            response_data['follow_up'] = gen_response.get('follow_up')
            response_data['products'] = products

            if gen_response.get('confidence_note'):
                response_data['confidence_note'] = gen_response['confidence_note']

        else:
            response_data['response'] = "I'm having trouble processing your request. Please try again."
            response_data['action'] = 'message_only'

    except Exception as e:
        print(f"Chat error: {str(e)}")
        import traceback
        traceback.print_exc()
        response_data['success'] = False
        response_data['error'] = str(e)
        response_data['response'] = "Oops! Something went wrong. Let me try again..."

    return jsonify(response_data)


@app.route('/api/recommend', methods=['POST'])
def recommend():
    """Recommendation API endpoint"""
    global recommender, session_manager

    data = request.json
    user_id = data.get('user_id', 'GUEST_001')
    n = data.get('n', 10)
    category = data.get('category')
    max_price = data.get('max_price')

    try:
        context = {}
        if category:
            context['category'] = category
        if max_price:
            context['max_price'] = float(max_price)

        recommendations = session_manager.get_dynamic_recommendations(
            user_id, n=n, context=context if context else None
        )

        product_ids = [r[0] for r in recommendations]
        products = get_product_list(product_ids)

        for i, product in enumerate(products):
            product['recommendation_score'] = round(recommendations[i][1], 2)

        return jsonify({
            'success': True,
            'user_id': user_id,
            'recommendations': products
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/feedback', methods=['POST'])
def feedback():
    """Feedback API endpoint"""
    global session_manager

    data = request.json
    user_id = data.get('user_id', 'GUEST_001')
    product_id = data.get('product_id')
    feedback_type = data.get('feedback_type')
    rating = data.get('rating')

    if not product_id or not feedback_type:
        return jsonify({'success': False, 'error': 'product_id and feedback_type required'}), 400

    try:
        session_manager.record_feedback(user_id, product_id, feedback_type, rating)
        return jsonify({
            'success': True,
            'message': 'Feedback recorded successfully',
            'user_id': user_id,
            'product_id': product_id,
            'feedback_type': feedback_type
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    """Add product to cart"""
    global session_manager

    data = request.json
    user_id = data.get('user_id', 'GUEST_001')
    product_id = data.get('product_id')

    if not product_id:
        return jsonify({'success': False, 'error': 'product_id required'}), 400

    try:
        cart = session_manager.add_to_cart(user_id, product_id)
        products = get_product_list(cart)
        return jsonify({
            'success': True,
            'message': 'Product added to cart',
            'cart': products,
            'cart_count': len(cart)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/cart/remove', methods=['POST'])
def remove_from_cart():
    """Remove product from cart"""
    global session_manager

    data = request.json
    user_id = data.get('user_id', 'GUEST_001')
    product_id = data.get('product_id')

    if not product_id:
        return jsonify({'success': False, 'error': 'product_id required'}), 400

    try:
        cart = session_manager.remove_from_cart(user_id, product_id)
        products = get_product_list(cart)
        return jsonify({
            'success': True,
            'message': 'Product removed from cart',
            'cart': products,
            'cart_count': len(cart)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/cart', methods=['GET'])
def get_cart():
    """Get user's cart"""
    global session_manager

    user_id = request.args.get('user_id', 'GUEST_001')

    try:
        cart = session_manager.get_cart(user_id)
        products = get_product_list(cart)
        total = sum(p['price'] * (1 - p['discount_percent']/100) for p in products)

        return jsonify({
            'success': True,
            'cart': products,
            'cart_count': len(cart),
            'total': round(total, 2)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/product/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get product details"""
    global recommender, session_manager

    try:
        product = recommender.get_product_details(product_id)

        if product:
            user_id = request.args.get('user_id', 'GUEST_001')
            session_manager.track_view(user_id, product_id)

            similar = recommender.cb_model.get_similar_products(product_id, n=4)
            similar_products = get_product_list([s[0] for s in similar])

            return jsonify({
                'success': True,
                'product': product,
                'similar_products': similar_products
            })
        else:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/products/search', methods=['GET'])
def search_products():
    """Search products"""
    global recommender, session_manager

    query = request.args.get('q', '')
    max_price = request.args.get('max_price')
    n = int(request.args.get('n', 12))
    user_id = request.args.get('user_id', 'GUEST_001')

    try:
        if max_price:
            max_price = float(max_price)

        results = recommender.search_products(query, n=n, max_price=max_price)
        product_ids = [r[0] for r in results]
        products = get_product_list(product_ids)

        session_manager.track_search(user_id, query, results)

        return jsonify({
            'success': True,
            'query': query,
            'results': products,
            'count': len(products)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/click', methods=['POST'])
def track_click():
    """Track product click"""
    global session_manager

    data = request.json
    user_id = data.get('user_id', 'GUEST_001')
    product_id = data.get('product_id')

    if not product_id:
        return jsonify({'success': False, 'error': 'product_id required'}), 400

    try:
        session_manager.track_click(user_id, product_id)
        return jsonify({'success': True, 'message': 'Click tracked'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/user/stats', methods=['GET'])
def get_user_stats():
    """Get user session statistics"""
    global session_manager, recommender

    user_id = request.args.get('user_id', 'GUEST_001')

    try:
        stats = session_manager.get_session_stats(user_id)
        preferred_categories = recommender.get_user_preferred_categories(user_id, n=3)

        return jsonify({
            'success': True,
            'user_id': user_id,
            'stats': stats,
            'preferred_categories': preferred_categories
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all product categories"""
    global recommender

    try:
        categories = recommender.products_df['category'].unique().tolist()
        return jsonify({'success': True, 'categories': sorted(categories)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_product_list(product_ids):
    """Get list of products with full details"""
    global recommender

    products = []
    for pid in product_ids:
        product = recommender.get_product_details(pid)
        if product:
            clean_product = {}
            for key, value in product.items():
                if isinstance(value, np.integer):
                    clean_product[key] = int(value)
                elif isinstance(value, np.floating):
                    clean_product[key] = float(value)
                else:
                    clean_product[key] = value
            products.append(clean_product)

    return products


# ============================================
# CHATBOT STATUS API
# ============================================

@app.route('/api/chatbot/status', methods=['GET'])
def chatbot_status():
    """Get current chatbot backend status"""
    global chatbot, ollama_chatbot

    return jsonify({
        'success': True,
        'ollama_available': ollama_chatbot is not None,
        'lstm_available': chatbot is not None,
        'active_backend': 'ollama' if ollama_chatbot else ('lstm' if chatbot else 'none'),
        'ollama_model': OLLAMA_MODEL if ollama_chatbot else None,
        'configured_backend': CHATBOT_BACKEND
    })


# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    load_models()
    app.run(debug=True, host='0.0.0.0', port=5000)
