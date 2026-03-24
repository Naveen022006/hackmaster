"""
Flask Backend for Personal Shopping Agent
Provides REST APIs for chat, recommendations, and feedback
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
from models.lstm_model import LSTMIntentClassifier, ChatbotModel

app = Flask(__name__)
app.secret_key = 'shopping_agent_secret_key_2024'
CORS(app)

# Global variables for models
recommender = None
chatbot = None
session_manager = None
products_df = None


def load_models():
    """Load all models and data"""
    global recommender, chatbot, session_manager, products_df

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

    # Load LSTM chatbot model
    print("\n3. Loading LSTM Chatbot Model...")
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
        print("   WARNING: LSTM model not found. Please train the model first.")
        print(f"   Expected: {model_path}")
        chatbot = None

    # Initialize session manager
    print("\n4. Initializing Session Manager...")
    session_manager = UserSessionManager(recommender)

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
    Processes user messages using LSTM model
    """
    global chatbot, recommender, session_manager

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
        'action': None
    }

    try:
        if chatbot:
            # Process message with LSTM model
            result = chatbot.process_message(message)

            response_data['intent'] = result['intent']
            response_data['confidence'] = result['confidence']
            response_data['entities'] = result['entities']

            # Get response based on intent
            response_data['response'] = chatbot.get_response_template(
                result['intent'],
                result['entities']
            )

            # Handle different intents
            intent = result['intent']
            entities = result['entities']

            if intent in ['search_product', 'category_recommendation']:
                # Search for products
                category = entities.get('category')
                max_price = entities.get('price')

                if category:
                    recs = recommender.recommend(
                        user_id, n=6,
                        category=category,
                        max_price=max_price
                    )
                else:
                    recs = recommender.search_products(message, n=6, max_price=max_price)

                product_ids = [r[0] for r in recs]
                response_data['products'] = get_product_list(product_ids)
                response_data['action'] = 'show_products'

                # Track search
                if session_manager:
                    session_manager.track_search(user_id, message, recs)

            elif intent == 'price_query':
                max_price = entities.get('price')
                category = entities.get('category')

                recs = recommender.recommend(
                    user_id, n=6,
                    category=category,
                    max_price=max_price
                )
                product_ids = [r[0] for r in recs]
                response_data['products'] = get_product_list(product_ids)
                response_data['action'] = 'show_products'

            elif intent == 'recommendation':
                recs = session_manager.get_dynamic_recommendations(user_id, n=6)
                product_ids = [r[0] for r in recs]
                response_data['products'] = get_product_list(product_ids)
                response_data['action'] = 'show_products'

            elif intent == 'deals':
                deals = session_manager.get_personalized_deals(user_id, n=6)
                response_data['products'] = get_product_list(deals)
                response_data['action'] = 'show_products'

            elif intent == 'cart_view':
                cart = session_manager.get_cart(user_id)
                response_data['products'] = get_product_list(cart)
                response_data['action'] = 'show_cart'

            elif intent == 'help':
                response_data['action'] = 'show_help'

            elif intent in ['greeting', 'goodbye']:
                response_data['action'] = 'message_only'

        else:
            # Fallback when LSTM model not loaded
            response_data['response'] = "I'm having trouble processing your request. Please try again."
            response_data['action'] = 'message_only'

    except Exception as e:
        print(f"Chat error: {str(e)}")
        response_data['success'] = False
        response_data['error'] = str(e)
        response_data['response'] = "Sorry, I encountered an error. Please try again."

    return jsonify(response_data)


@app.route('/api/recommend', methods=['POST'])
def recommend():
    """
    Recommendation API endpoint
    Returns personalized product recommendations
    """
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
            user_id,
            n=n,
            context=context if context else None
        )

        product_ids = [r[0] for r in recommendations]
        products = get_product_list(product_ids)

        # Add recommendation scores
        for i, product in enumerate(products):
            product['recommendation_score'] = round(recommendations[i][1], 2)

        return jsonify({
            'success': True,
            'user_id': user_id,
            'recommendations': products
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/feedback', methods=['POST'])
def feedback():
    """
    Feedback API endpoint
    Records user feedback (like/dislike)
    """
    global session_manager

    data = request.json
    user_id = data.get('user_id', 'GUEST_001')
    product_id = data.get('product_id')
    feedback_type = data.get('feedback_type')  # 'like' or 'dislike'
    rating = data.get('rating')

    if not product_id or not feedback_type:
        return jsonify({
            'success': False,
            'error': 'product_id and feedback_type required'
        }), 400

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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    """Add product to cart"""
    global session_manager

    data = request.json
    user_id = data.get('user_id', 'GUEST_001')
    product_id = data.get('product_id')

    if not product_id:
        return jsonify({
            'success': False,
            'error': 'product_id required'
        }), 400

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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/cart/remove', methods=['POST'])
def remove_from_cart():
    """Remove product from cart"""
    global session_manager

    data = request.json
    user_id = data.get('user_id', 'GUEST_001')
    product_id = data.get('product_id')

    if not product_id:
        return jsonify({
            'success': False,
            'error': 'product_id required'
        }), 400

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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/product/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get product details"""
    global recommender

    try:
        product = recommender.get_product_details(product_id)

        if product:
            # Track view
            user_id = request.args.get('user_id', 'GUEST_001')
            session_manager.track_view(user_id, product_id)

            # Get similar products
            similar = recommender.cb_model.get_similar_products(product_id, n=4)
            similar_products = get_product_list([s[0] for s in similar])

            return jsonify({
                'success': True,
                'product': product,
                'similar_products': similar_products
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Product not found'
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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

        # Track search
        session_manager.track_search(user_id, query, results)

        return jsonify({
            'success': True,
            'query': query,
            'results': products,
            'count': len(products)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/click', methods=['POST'])
def track_click():
    """Track product click"""
    global session_manager

    data = request.json
    user_id = data.get('user_id', 'GUEST_001')
    product_id = data.get('product_id')

    if not product_id:
        return jsonify({
            'success': False,
            'error': 'product_id required'
        }), 400

    try:
        session_manager.track_click(user_id, product_id)

        return jsonify({
            'success': True,
            'message': 'Click tracked'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/user/stats', methods=['GET'])
def get_user_stats():
    """Get user session statistics"""
    global session_manager

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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all product categories"""
    global recommender

    try:
        categories = recommender.products_df['category'].unique().tolist()

        return jsonify({
            'success': True,
            'categories': sorted(categories)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
            # Convert numpy types to Python types
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
# MAIN
# ============================================

if __name__ == '__main__':
    load_models()
    app.run(debug=True, host='0.0.0.0', port=5000)
