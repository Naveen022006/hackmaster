"""
Synthetic Dataset Generator for Personal Shopping Agent
Generates: users.csv, products.csv, interactions.csv, chatbot_data.csv
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# ============================================
# USERS DATASET
# ============================================
def generate_users(n_users=500):
    """Generate synthetic user data"""

    first_names = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Emily', 'Chris', 'Lisa',
                   'Tom', 'Anna', 'James', 'Emma', 'Robert', 'Olivia', 'William', 'Sophia',
                   'Daniel', 'Isabella', 'Matthew', 'Mia', 'Anthony', 'Charlotte', 'Mark',
                   'Amelia', 'Steven', 'Harper', 'Andrew', 'Evelyn', 'Joshua', 'Abigail']

    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
                  'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez',
                  'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin']

    age_groups = ['18-24', '25-34', '35-44', '45-54', '55-64', '65+']
    genders = ['Male', 'Female', 'Other']
    locations = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix',
                 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose']

    preferred_categories = ['Electronics', 'Clothing', 'Home & Kitchen', 'Sports',
                           'Beauty', 'Books', 'Toys', 'Jewelry', 'Automotive', 'Garden']

    users = []
    for i in range(1, n_users + 1):
        user = {
            'user_id': f'U{i:04d}',
            'name': f"{random.choice(first_names)} {random.choice(last_names)}",
            'email': f"user{i}@email.com",
            'age_group': random.choice(age_groups),
            'gender': random.choice(genders),
            'location': random.choice(locations),
            'preferred_categories': '|'.join(random.sample(preferred_categories, k=random.randint(1, 4))),
            'account_created': (datetime.now() - timedelta(days=random.randint(1, 730))).strftime('%Y-%m-%d'),
            'loyalty_points': random.randint(0, 5000),
            'total_purchases': random.randint(0, 100)
        }
        users.append(user)

    return pd.DataFrame(users)


# ============================================
# PRODUCTS DATASET
# ============================================
def generate_products(n_products=1000):
    """Generate synthetic product data"""

    categories = {
        'Electronics': {
            'subcategories': ['Smartphones', 'Laptops', 'Headphones', 'Tablets', 'Cameras', 'Smartwatches'],
            'brands': ['TechPro', 'ElectroMax', 'DigiWorld', 'SmartGear', 'FutureTech'],
            'price_range': (50, 2000),
            'adjectives': ['premium', 'wireless', 'portable', 'high-performance', 'smart', 'compact']
        },
        'Clothing': {
            'subcategories': ['T-Shirts', 'Jeans', 'Dresses', 'Jackets', 'Shoes', 'Accessories'],
            'brands': ['FashionHub', 'StyleMaster', 'TrendyWear', 'ClassicFit', 'UrbanStyle'],
            'price_range': (15, 300),
            'adjectives': ['comfortable', 'stylish', 'casual', 'formal', 'trendy', 'classic']
        },
        'Home & Kitchen': {
            'subcategories': ['Cookware', 'Appliances', 'Furniture', 'Decor', 'Bedding', 'Storage'],
            'brands': ['HomeEssentials', 'KitchenPro', 'CozyLiving', 'ModernHome', 'ComfortZone'],
            'price_range': (20, 500),
            'adjectives': ['durable', 'elegant', 'modern', 'space-saving', 'eco-friendly', 'premium']
        },
        'Sports': {
            'subcategories': ['Fitness Equipment', 'Sportswear', 'Outdoor Gear', 'Yoga', 'Running', 'Swimming'],
            'brands': ['FitLife', 'SportMax', 'ActiveGear', 'AthletePro', 'EndurancePlus'],
            'price_range': (20, 400),
            'adjectives': ['lightweight', 'professional', 'ergonomic', 'breathable', 'durable', 'flexible']
        },
        'Beauty': {
            'subcategories': ['Skincare', 'Makeup', 'Haircare', 'Fragrances', 'Nail Care', 'Tools'],
            'brands': ['GlowUp', 'BeautyBliss', 'PureSkin', 'LuxeCosmetics', 'NaturalGlow'],
            'price_range': (10, 200),
            'adjectives': ['organic', 'hydrating', 'long-lasting', 'natural', 'luxurious', 'gentle']
        },
        'Books': {
            'subcategories': ['Fiction', 'Non-Fiction', 'Self-Help', 'Science', 'Biography', 'Children'],
            'brands': ['PageTurner', 'BookWorm', 'LiteraryPress', 'WisdomBooks', 'StoryTime'],
            'price_range': (10, 50),
            'adjectives': ['bestselling', 'award-winning', 'inspiring', 'educational', 'captivating', 'classic']
        },
        'Toys': {
            'subcategories': ['Educational', 'Action Figures', 'Board Games', 'Puzzles', 'Outdoor', 'Dolls'],
            'brands': ['FunTime', 'PlayMaster', 'KidJoy', 'ToyWorld', 'HappyPlay'],
            'price_range': (10, 150),
            'adjectives': ['interactive', 'educational', 'colorful', 'safe', 'creative', 'fun']
        },
        'Jewelry': {
            'subcategories': ['Necklaces', 'Rings', 'Bracelets', 'Earrings', 'Watches', 'Anklets'],
            'brands': ['GoldCraft', 'SilverShine', 'GemStone', 'LuxeJewels', 'ElegantPieces'],
            'price_range': (30, 1000),
            'adjectives': ['elegant', 'handcrafted', 'sparkling', 'timeless', 'delicate', 'luxurious']
        },
        'Automotive': {
            'subcategories': ['Car Accessories', 'Tools', 'Electronics', 'Cleaning', 'Parts', 'Safety'],
            'brands': ['AutoPro', 'CarCare', 'DriveMax', 'RoadMaster', 'VehicleGuard'],
            'price_range': (15, 500),
            'adjectives': ['durable', 'universal', 'professional', 'heavy-duty', 'precision', 'reliable']
        },
        'Garden': {
            'subcategories': ['Plants', 'Tools', 'Furniture', 'Decor', 'Irrigation', 'Planters'],
            'brands': ['GreenThumb', 'GardenPro', 'NatureCare', 'BloomMaster', 'OutdoorLiving'],
            'price_range': (10, 300),
            'adjectives': ['weather-resistant', 'eco-friendly', 'decorative', 'durable', 'organic', 'compact']
        }
    }

    products = []
    product_id = 1

    for category, info in categories.items():
        n_category_products = n_products // len(categories)

        for _ in range(n_category_products):
            subcategory = random.choice(info['subcategories'])
            brand = random.choice(info['brands'])
            adj = random.choice(info['adjectives'])

            price = round(random.uniform(*info['price_range']), 2)

            # Generate description
            description = f"{adj.capitalize()} {subcategory.lower()} from {brand}. "
            description += f"Perfect for those who value quality and style. "
            description += f"This {category.lower()} product offers excellent value for money."

            product = {
                'product_id': f'P{product_id:04d}',
                'name': f"{brand} {adj.capitalize()} {subcategory}",
                'category': category,
                'subcategory': subcategory,
                'brand': brand,
                'price': price,
                'description': description,
                'rating': round(random.uniform(3.0, 5.0), 1),
                'num_reviews': random.randint(10, 5000),
                'stock': random.randint(0, 500),
                'discount_percent': random.choice([0, 0, 0, 5, 10, 15, 20, 25, 30]),
                'tags': f"{category}|{subcategory}|{brand}|{adj}"
            }
            products.append(product)
            product_id += 1

    return pd.DataFrame(products)


# ============================================
# INTERACTIONS DATASET
# ============================================
def generate_interactions(users_df, products_df, n_interactions=5000):
    """Generate synthetic user-product interactions"""

    interaction_types = ['view', 'click', 'add_to_cart', 'purchase', 'search', 'wishlist']

    interactions = []

    for _ in range(n_interactions):
        user = users_df.sample(1).iloc[0]
        product = products_df.sample(1).iloc[0]

        # Weight interaction types
        weights = [0.35, 0.25, 0.15, 0.10, 0.10, 0.05]
        interaction_type = random.choices(interaction_types, weights=weights)[0]

        # Generate timestamp
        days_ago = random.randint(0, 90)
        hours_ago = random.randint(0, 23)
        timestamp = datetime.now() - timedelta(days=days_ago, hours=hours_ago)

        # Rating only for purchases
        rating = None
        if interaction_type == 'purchase':
            rating = random.randint(1, 5)

        interaction = {
            'interaction_id': len(interactions) + 1,
            'user_id': user['user_id'],
            'product_id': product['product_id'],
            'interaction_type': interaction_type,
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'rating': rating,
            'session_id': f"S{random.randint(1, 1000):04d}",
            'device': random.choice(['mobile', 'desktop', 'tablet']),
            'search_query': product['category'].lower() if interaction_type == 'search' else None
        }
        interactions.append(interaction)

    return pd.DataFrame(interactions)


# ============================================
# CHATBOT TRAINING DATA
# ============================================
def generate_chatbot_data():
    """Generate training data for LSTM chatbot"""

    intents = {
        'greeting': {
            'patterns': [
                'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening',
                'hi there', 'hello there', 'hey there', 'greetings', 'howdy',
                'what\'s up', 'sup', 'yo', 'hiya', 'hello bot', 'hi bot',
                'good day', 'hey bot', 'hello shopping assistant'
            ],
            'entities': []
        },
        'goodbye': {
            'patterns': [
                'bye', 'goodbye', 'see you later', 'see ya', 'take care',
                'bye bye', 'good night', 'have a nice day', 'until next time',
                'catch you later', 'farewell', 'see you soon', 'bye for now',
                'gotta go', 'talk to you later', 'peace out', 'later'
            ],
            'entities': []
        },
        'search_product': {
            'patterns': [
                'show me {category}', 'i want to buy {category}', 'looking for {category}',
                'find me {category}', 'search for {category}', 'i need {category}',
                'can you show me {category}', 'do you have {category}',
                'i\'m looking for {category}', 'show {category}', 'find {category}',
                'get me {category}', 'i want {category}', 'search {category}',
                'browse {category}', 'look for {category}', 'need {category}',
                'want to see {category}', 'display {category}', 'show me some {category}'
            ],
            'entities': ['category']
        },
        'price_query': {
            'patterns': [
                'show me products under {price}', 'items below {price}',
                'products under {price} dollars', 'cheap {category} under {price}',
                'affordable items under {price}', 'budget friendly under {price}',
                'what can i get for {price}', 'products less than {price}',
                'show me {category} under {price}', 'find {category} below {price}',
                'i have a budget of {price}', '{category} within {price}',
                'items costing less than {price}', 'cheap products under {price}',
                'show budget {category} under {price}'
            ],
            'entities': ['price', 'category']
        },
        'recommendation': {
            'patterns': [
                'recommend something', 'what do you suggest', 'suggest something',
                'recommend products', 'give me recommendations', 'what should i buy',
                'suggest me something', 'any recommendations', 'best products for me',
                'personalized recommendations', 'what\'s popular', 'trending products',
                'top picks for me', 'suggest based on my history', 'recommended for me',
                'what do you recommend', 'suggest something for me', 'help me choose'
            ],
            'entities': []
        },
        'category_recommendation': {
            'patterns': [
                'recommend {category}', 'suggest {category}', 'best {category}',
                'top {category}', 'popular {category}', 'recommend me {category}',
                'suggest some {category}', 'good {category}', 'nice {category}',
                'quality {category}', 'best {category} for me', 'top rated {category}',
                'highly rated {category}', 'premium {category}', 'affordable {category}'
            ],
            'entities': ['category']
        },
        'cart_add': {
            'patterns': [
                'add to cart', 'add this to cart', 'put in cart', 'add to my cart',
                'i want to buy this', 'add it', 'add to basket', 'add this',
                'put this in my cart', 'save to cart', 'add this product',
                'i\'ll take it', 'add one', 'buy this', 'purchase this'
            ],
            'entities': []
        },
        'cart_view': {
            'patterns': [
                'show my cart', 'view cart', 'what\'s in my cart', 'my cart',
                'show cart', 'open cart', 'see my cart', 'cart contents',
                'what do i have in cart', 'display cart', 'check cart',
                'shopping cart', 'basket', 'view my basket', 'show basket'
            ],
            'entities': []
        },
        'order_status': {
            'patterns': [
                'where is my order', 'track my order', 'order status',
                'when will my order arrive', 'delivery status', 'track order',
                'shipping status', 'order tracking', 'my orders', 'order history',
                'check order status', 'when is delivery', 'track my package',
                'package status', 'shipment status', 'where is my package'
            ],
            'entities': []
        },
        'help': {
            'patterns': [
                'help', 'help me', 'i need help', 'can you help',
                'assist me', 'assistance', 'support', 'how does this work',
                'what can you do', 'how to use', 'guide me', 'tutorial',
                'how do i', 'instructions', 'what are your features',
                'capabilities', 'what do you offer', 'how can you help'
            ],
            'entities': []
        },
        'feedback': {
            'patterns': [
                'i like this', 'i don\'t like this', 'this is good', 'this is bad',
                'great product', 'terrible product', 'love it', 'hate it',
                'not interested', 'show me more like this', 'less of this',
                'perfect', 'not what i wanted', 'exactly what i need',
                'thumbs up', 'thumbs down', 'rate this', 'give feedback'
            ],
            'entities': []
        },
        'compare': {
            'patterns': [
                'compare products', 'compare these', 'which is better',
                'difference between', 'compare {category}', 'vs',
                'which one should i buy', 'help me decide', 'comparison',
                'what\'s the difference', 'better option', 'pros and cons',
                'which is cheaper', 'which has better reviews'
            ],
            'entities': ['category']
        },
        'deals': {
            'patterns': [
                'show me deals', 'any discounts', 'sales', 'offers',
                'special offers', 'discounted products', 'deals of the day',
                'best deals', 'on sale', 'clearance', 'promotions',
                'coupon', 'promo code', 'discount code', 'cheap deals',
                'bargains', 'flash sale', 'today\'s deals'
            ],
            'entities': []
        }
    }

    # Categories for entity replacement
    categories = ['electronics', 'clothing', 'home & kitchen', 'sports', 'beauty',
                  'books', 'toys', 'jewelry', 'automotive', 'garden', 'smartphones',
                  'laptops', 'headphones', 'shoes', 'watches', 'bags', 'furniture']

    prices = ['50', '100', '200', '500', '1000', '20', '30', '150', '300', '75']

    chatbot_data = []

    for intent, data in intents.items():
        for pattern in data['patterns']:
            # Generate multiple variations
            if '{category}' in pattern and '{price}' in pattern:
                # Both category and price
                for cat in random.sample(categories, min(5, len(categories))):
                    for price in random.sample(prices, min(3, len(prices))):
                        text = pattern.replace('{category}', cat).replace('{price}', price)
                        chatbot_data.append({
                            'text': text,
                            'intent': intent,
                            'entities': f"category:{cat}|price:{price}"
                        })
            elif '{category}' in pattern:
                # Category only
                for cat in random.sample(categories, min(8, len(categories))):
                    text = pattern.replace('{category}', cat)
                    chatbot_data.append({
                        'text': text,
                        'intent': intent,
                        'entities': f"category:{cat}"
                    })
            elif '{price}' in pattern:
                # Price only
                for price in random.sample(prices, min(5, len(prices))):
                    text = pattern.replace('{price}', price)
                    chatbot_data.append({
                        'text': text,
                        'intent': intent,
                        'entities': f"price:{price}"
                    })
            else:
                # No entities
                chatbot_data.append({
                    'text': pattern,
                    'intent': intent,
                    'entities': ''
                })

    return pd.DataFrame(chatbot_data)


# ============================================
# MAIN EXECUTION
# ============================================
if __name__ == '__main__':
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print("Generating synthetic datasets...")

    # Generate users
    print("1. Generating users.csv...")
    users_df = generate_users(500)
    users_df.to_csv(os.path.join(script_dir, 'users.csv'), index=False)
    print(f"   Created {len(users_df)} users")

    # Generate products
    print("2. Generating products.csv...")
    products_df = generate_products(1000)
    products_df.to_csv(os.path.join(script_dir, 'products.csv'), index=False)
    print(f"   Created {len(products_df)} products")

    # Generate interactions
    print("3. Generating interactions.csv...")
    interactions_df = generate_interactions(users_df, products_df, 5000)
    interactions_df.to_csv(os.path.join(script_dir, 'interactions.csv'), index=False)
    print(f"   Created {len(interactions_df)} interactions")

    # Generate chatbot data
    print("4. Generating chatbot_data.csv...")
    chatbot_df = generate_chatbot_data()
    chatbot_df.to_csv(os.path.join(script_dir, 'chatbot_data.csv'), index=False)
    print(f"   Created {len(chatbot_df)} chatbot training samples")

    print("\nAll datasets generated successfully!")
    print(f"\nFiles created in: {script_dir}")
