"""
Dataset Integration Script
Integrates user-provided products.csv and generates compatible datasets
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os
import shutil

np.random.seed(42)
random.seed(42)


def analyze_products(products_df):
    """Analyze the products dataset"""
    print("\n" + "="*60)
    print("PRODUCTS DATASET ANALYSIS")
    print("="*60)

    print(f"\nTotal Products: {len(products_df)}")
    print(f"Columns: {products_df.columns.tolist()}")

    print(f"\n--- Categories ({products_df['category'].nunique()}) ---")
    print(products_df['category'].value_counts())

    print(f"\n--- Top Brands ---")
    print(products_df['brand'].value_counts().head(10))

    print(f"\n--- Price Statistics ---")
    print(f"  Min: ${products_df['price'].min():.2f}")
    print(f"  Max: ${products_df['price'].max():.2f}")
    print(f"  Mean: ${products_df['price'].mean():.2f}")
    print(f"  Median: ${products_df['price'].median():.2f}")

    print(f"\n--- Rating Statistics ---")
    print(f"  Min: {products_df['rating'].min():.1f}")
    print(f"  Max: {products_df['rating'].max():.1f}")
    print(f"  Mean: {products_df['rating'].mean():.2f}")
    print(f"  Missing: {products_df['rating'].isnull().sum()}")

    return {
        'categories': products_df['category'].unique().tolist(),
        'brands': products_df['brand'].unique().tolist(),
        'price_range': (products_df['price'].min(), products_df['price'].max())
    }


def preprocess_products(products_df):
    """Preprocess products dataset to match our schema"""
    print("\nPreprocessing products dataset...")

    df = products_df.copy()

    # Fill missing ratings with category average
    df['rating'] = df.groupby('category')['rating'].transform(
        lambda x: x.fillna(x.mean())
    )
    # Fill any remaining NaN with overall mean
    df['rating'] = df['rating'].fillna(df['rating'].mean())
    df['rating'] = df['rating'].round(1)

    # Add missing columns for compatibility
    if 'subcategory' not in df.columns:
        # Generate subcategories based on product names
        df['subcategory'] = df.apply(
            lambda x: extract_subcategory(x['name'], x['category']),
            axis=1
        )

    if 'num_reviews' not in df.columns:
        # Generate random review counts based on rating
        df['num_reviews'] = df['rating'].apply(
            lambda r: random.randint(int(r * 50), int(r * 500))
        )

    if 'stock' not in df.columns:
        df['stock'] = np.random.randint(0, 500, size=len(df))

    if 'discount_percent' not in df.columns:
        # Random discounts (30% chance of discount)
        df['discount_percent'] = df.apply(
            lambda x: random.choice([0, 0, 0, 5, 10, 15, 20, 25, 30])
            if random.random() > 0.7 else 0,
            axis=1
        )

    if 'tags' not in df.columns:
        df['tags'] = df.apply(
            lambda x: f"{x['category']}|{x['brand']}|{x.get('subcategory', '')}",
            axis=1
        )

    print(f"  Added missing columns: subcategory, num_reviews, stock, discount_percent, tags")
    print(f"  Filled {products_df['rating'].isnull().sum()} missing ratings")

    return df


def extract_subcategory(name, category):
    """Extract subcategory from product name"""
    subcategories = {
        'Electronics': ['Smartphone', 'Laptop', 'TV', 'Camera', 'Tablet', 'Smartwatch',
                        'Power Bank', 'Bluetooth Speaker', 'Headphones'],
        'Clothing': ['T-Shirt', 'Jeans', 'Dress', 'Hoodie', 'Formal Shirt', 'Polo Shirt',
                     'Sneakers', 'Jacket'],
        'Home & Kitchen': ['Microwave', 'Air Fryer', 'Water Purifier', 'Mixer Grinder',
                           'Electric Kettle', 'Washing Machine', 'Vacuum Cleaner'],
        'Sports': ['Running Shoes', 'Cycling Helmet', 'Swimming Goggles', 'Fitness Band',
                   'Tennis Racket', 'Dumbbell Set', 'Yoga Mat'],
        'Beauty': ['Lipstick', 'Makeup Kit', 'Serum', 'Face Wash', 'Sunscreen',
                   'Hair Oil', 'Perfume'],
        'Books': ['Fiction', 'Non-Fiction', 'Self Help', 'Science Fiction', 'History',
                  'Biography', 'Children'],
        'Toys': ['Remote Control Car', 'Board Game', 'Doll House', 'Building Blocks',
                 'Educational Kit', 'Art Set', 'Musical Toy'],
        'Grocery': ['Rice', 'Flour', 'Cooking Oil', 'Tea', 'Honey', 'Cereal',
                    'Spices', 'Chocolate']
    }

    name_lower = name.lower()
    for subcat in subcategories.get(category, []):
        if subcat.lower() in name_lower:
            return subcat

    # Default subcategory
    return subcategories.get(category, ['General'])[0]


def generate_users(n_users=500, categories=None):
    """Generate synthetic user data"""
    print(f"\nGenerating {n_users} users...")

    first_names = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Emily', 'Chris', 'Lisa',
                   'Tom', 'Anna', 'James', 'Emma', 'Robert', 'Olivia', 'William', 'Sophia',
                   'Daniel', 'Isabella', 'Matthew', 'Mia', 'Anthony', 'Charlotte', 'Mark',
                   'Amelia', 'Steven', 'Harper', 'Andrew', 'Evelyn', 'Joshua', 'Abigail',
                   'Raj', 'Priya', 'Amit', 'Neha', 'Vikram', 'Anjali', 'Rahul', 'Pooja']

    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
                  'Davis', 'Rodriguez', 'Martinez', 'Sharma', 'Patel', 'Kumar', 'Singh',
                  'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin']

    age_groups = ['18-24', '25-34', '35-44', '45-54', '55-64', '65+']
    genders = ['Male', 'Female', 'Other']
    locations = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad',
                 'Pune', 'Ahmedabad', 'New York', 'Los Angeles', 'London', 'Singapore']

    if categories is None:
        categories = ['Electronics', 'Clothing', 'Home & Kitchen', 'Sports',
                      'Beauty', 'Books', 'Toys', 'Grocery']

    users = []
    for i in range(1, n_users + 1):
        user = {
            'user_id': f'U{i:04d}',
            'name': f"{random.choice(first_names)} {random.choice(last_names)}",
            'email': f"user{i}@email.com",
            'age_group': random.choice(age_groups),
            'gender': random.choice(genders),
            'location': random.choice(locations),
            'preferred_categories': '|'.join(random.sample(categories, k=random.randint(1, 4))),
            'account_created': (datetime.now() - timedelta(days=random.randint(1, 730))).strftime('%Y-%m-%d'),
            'loyalty_points': random.randint(0, 5000),
            'total_purchases': random.randint(0, 100)
        }
        users.append(user)

    return pd.DataFrame(users)


def generate_interactions(users_df, products_df, n_interactions=10000):
    """Generate synthetic user-product interactions"""
    print(f"\nGenerating {n_interactions} interactions...")

    interaction_types = ['view', 'click', 'add_to_cart', 'purchase', 'search', 'wishlist']
    weights = [0.35, 0.25, 0.15, 0.10, 0.10, 0.05]

    interactions = []
    user_ids = users_df['user_id'].tolist()
    product_ids = products_df['product_id'].tolist()

    # Create user preference mapping
    user_prefs = {}
    for _, user in users_df.iterrows():
        prefs = user['preferred_categories'].split('|')
        user_prefs[user['user_id']] = prefs

    # Create category to products mapping
    cat_products = {}
    for cat in products_df['category'].unique():
        cat_products[cat] = products_df[products_df['category'] == cat]['product_id'].tolist()

    for i in range(n_interactions):
        user_id = random.choice(user_ids)

        # 70% chance to select product from preferred category
        if random.random() < 0.7 and user_id in user_prefs:
            pref_cat = random.choice(user_prefs[user_id])
            if pref_cat in cat_products and cat_products[pref_cat]:
                product_id = random.choice(cat_products[pref_cat])
            else:
                product_id = random.choice(product_ids)
        else:
            product_id = random.choice(product_ids)

        interaction_type = random.choices(interaction_types, weights=weights)[0]

        days_ago = random.randint(0, 180)
        hours_ago = random.randint(0, 23)
        timestamp = datetime.now() - timedelta(days=days_ago, hours=hours_ago)

        rating = None
        if interaction_type == 'purchase':
            rating = random.choices([3, 4, 5, 4, 5], weights=[0.1, 0.2, 0.3, 0.2, 0.2])[0]

        product_info = products_df[products_df['product_id'] == product_id]
        search_query = None
        if interaction_type == 'search' and len(product_info) > 0:
            search_query = product_info.iloc[0]['category'].lower()

        interaction = {
            'interaction_id': i + 1,
            'user_id': user_id,
            'product_id': product_id,
            'interaction_type': interaction_type,
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'rating': rating,
            'session_id': f"S{random.randint(1, 2000):04d}",
            'device': random.choice(['mobile', 'desktop', 'tablet']),
            'search_query': search_query
        }
        interactions.append(interaction)

    return pd.DataFrame(interactions)


def generate_chatbot_data(categories=None):
    """Generate chatbot training data with actual categories"""
    print("\nGenerating chatbot training data...")

    if categories is None:
        categories = ['electronics', 'clothing', 'home & kitchen', 'sports',
                      'beauty', 'books', 'toys', 'grocery']
    else:
        categories = [c.lower() for c in categories]

    # Add common variations
    all_categories = categories + [
        'smartphones', 'laptops', 'tv', 'camera', 'headphones',
        'shirts', 'jeans', 'shoes', 'sneakers', 'dress',
        'kitchen', 'appliances', 'furniture',
        'fitness', 'gym', 'running', 'yoga',
        'makeup', 'skincare', 'perfume',
        'fiction', 'novels', 'textbooks',
        'games', 'dolls', 'lego',
        'food', 'snacks', 'beverages'
    ]

    intents = {
        'greeting': {
            'patterns': [
                'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening',
                'hi there', 'hello there', 'hey there', 'greetings', 'howdy',
                'what\'s up', 'sup', 'yo', 'hiya', 'hello bot', 'hi bot',
                'good day', 'hey bot', 'hello shopping assistant', 'namaste'
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
                'products under {price} rupees', 'cheap {category} under {price}',
                'affordable items under {price}', 'budget friendly under {price}',
                'what can i get for {price}', 'products less than {price}',
                'show me {category} under {price}', 'find {category} below {price}',
                'i have a budget of {price}', '{category} within {price}',
                'items costing less than {price}', 'cheap products under {price}',
                'show budget {category} under {price}', 'under {price}'
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
                'what do you recommend', 'suggest something for me', 'help me choose',
                'what\'s hot', 'best sellers', 'top rated'
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

    prices = ['100', '500', '1000', '2000', '5000', '10000', '50', '200', '300', '1500']

    chatbot_data = []

    for intent, data in intents.items():
        for pattern in data['patterns']:
            if '{category}' in pattern and '{price}' in pattern:
                for cat in random.sample(all_categories, min(8, len(all_categories))):
                    for price in random.sample(prices, min(4, len(prices))):
                        text = pattern.replace('{category}', cat).replace('{price}', price)
                        chatbot_data.append({
                            'text': text,
                            'intent': intent,
                            'entities': f"category:{cat}|price:{price}"
                        })
            elif '{category}' in pattern:
                for cat in random.sample(all_categories, min(10, len(all_categories))):
                    text = pattern.replace('{category}', cat)
                    chatbot_data.append({
                        'text': text,
                        'intent': intent,
                        'entities': f"category:{cat}"
                    })
            elif '{price}' in pattern:
                for price in random.sample(prices, min(6, len(prices))):
                    text = pattern.replace('{price}', price)
                    chatbot_data.append({
                        'text': text,
                        'intent': intent,
                        'entities': f"price:{price}"
                    })
            else:
                chatbot_data.append({
                    'text': pattern,
                    'intent': intent,
                    'entities': ''
                })

    return pd.DataFrame(chatbot_data)


def main():
    """Main integration function"""
    print("\n" + "="*60)
    print("DATASET INTEGRATION")
    print("="*60)

    # Paths
    source_path = r"d:\hackermaster\shopping_agent\data\products.csv"
    dest_dir = os.path.dirname(os.path.abspath(__file__))

    # Load source products
    print(f"\nLoading products from: {source_path}")
    products_df = pd.read_csv(source_path)

    # Analyze
    analysis = analyze_products(products_df)
    categories = analysis['categories']

    # Preprocess products
    products_df = preprocess_products(products_df)

    # Generate users
    users_df = generate_users(500, categories)

    # Generate interactions
    interactions_df = generate_interactions(users_df, products_df, 10000)

    # Generate chatbot data
    chatbot_df = generate_chatbot_data(categories)

    # Save all datasets
    print("\n" + "="*60)
    print("SAVING DATASETS")
    print("="*60)

    products_df.to_csv(os.path.join(dest_dir, 'products.csv'), index=False)
    print(f"  Saved products.csv ({len(products_df)} products)")

    users_df.to_csv(os.path.join(dest_dir, 'users.csv'), index=False)
    print(f"  Saved users.csv ({len(users_df)} users)")

    interactions_df.to_csv(os.path.join(dest_dir, 'interactions.csv'), index=False)
    print(f"  Saved interactions.csv ({len(interactions_df)} interactions)")

    chatbot_df.to_csv(os.path.join(dest_dir, 'chatbot_data.csv'), index=False)
    print(f"  Saved chatbot_data.csv ({len(chatbot_df)} samples)")

    print("\n" + "="*60)
    print("INTEGRATION COMPLETE!")
    print("="*60)

    return products_df, users_df, interactions_df, chatbot_df


if __name__ == '__main__':
    main()
