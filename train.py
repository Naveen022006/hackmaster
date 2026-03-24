"""
Training and Setup Script for Personal Shopping Agent
Run this script to:
1. Integrate external dataset OR generate synthetic datasets
2. Train the LSTM intent classification model
3. Verify all components are working

Usage:
    python train.py                    # Generate synthetic data
    python train.py --use-external     # Use external products.csv
"""

import os
import sys
import argparse

# Add project directory to path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

# External dataset path
EXTERNAL_PRODUCTS_PATH = r"d:\hackermaster\shopping_agent\data\products.csv"


def setup_directories():
    """Create necessary directories"""
    dirs = [
        os.path.join(PROJECT_DIR, 'data'),
        os.path.join(PROJECT_DIR, 'models'),
        os.path.join(PROJECT_DIR, 'static', 'css'),
        os.path.join(PROJECT_DIR, 'static', 'js'),
        os.path.join(PROJECT_DIR, 'templates'),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    print("Directories created/verified.")


def integrate_external_dataset():
    """Integrate external products.csv and generate compatible datasets"""
    print("\n" + "="*60)
    print("STEP 1: Integrating External Dataset")
    print("="*60)

    import pandas as pd
    from data.integrate_dataset import (
        analyze_products, preprocess_products,
        generate_users, generate_interactions, generate_chatbot_data
    )

    data_dir = os.path.join(PROJECT_DIR, 'data')

    # Check if external dataset exists
    if not os.path.exists(EXTERNAL_PRODUCTS_PATH):
        print(f"External dataset not found at: {EXTERNAL_PRODUCTS_PATH}")
        print("Falling back to synthetic data generation...")
        return generate_synthetic_datasets()

    # Load external products
    print(f"\nLoading products from: {EXTERNAL_PRODUCTS_PATH}")
    products_df = pd.read_csv(EXTERNAL_PRODUCTS_PATH)

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
    print("\n" + "-"*40)
    print("Saving datasets...")

    products_df.to_csv(os.path.join(data_dir, 'products.csv'), index=False)
    print(f"  Saved products.csv ({len(products_df)} products)")

    users_df.to_csv(os.path.join(data_dir, 'users.csv'), index=False)
    print(f"  Saved users.csv ({len(users_df)} users)")

    interactions_df.to_csv(os.path.join(data_dir, 'interactions.csv'), index=False)
    print(f"  Saved interactions.csv ({len(interactions_df)} interactions)")

    chatbot_df.to_csv(os.path.join(data_dir, 'chatbot_data.csv'), index=False)
    print(f"  Saved chatbot_data.csv ({len(chatbot_df)} samples)")

    print("\nExternal dataset integrated successfully!")
    return users_df, products_df, interactions_df, chatbot_df


def generate_synthetic_datasets():
    """Generate synthetic datasets"""
    print("\n" + "="*60)
    print("STEP 1: Generating Synthetic Datasets")
    print("="*60)

    from data.generate_datasets import (
        generate_users, generate_products,
        generate_interactions, generate_chatbot_data
    )

    data_dir = os.path.join(PROJECT_DIR, 'data')

    # Generate users
    print("\n1. Generating users.csv...")
    users_df = generate_users(500)
    users_df.to_csv(os.path.join(data_dir, 'users.csv'), index=False)
    print(f"   Created {len(users_df)} users")

    # Generate products
    print("2. Generating products.csv...")
    products_df = generate_products(1000)
    products_df.to_csv(os.path.join(data_dir, 'products.csv'), index=False)
    print(f"   Created {len(products_df)} products")

    # Generate interactions
    print("3. Generating interactions.csv...")
    interactions_df = generate_interactions(users_df, products_df, 5000)
    interactions_df.to_csv(os.path.join(data_dir, 'interactions.csv'), index=False)
    print(f"   Created {len(interactions_df)} interactions")

    # Generate chatbot data
    print("4. Generating chatbot_data.csv...")
    chatbot_df = generate_chatbot_data()
    chatbot_df.to_csv(os.path.join(data_dir, 'chatbot_data.csv'), index=False)
    print(f"   Created {len(chatbot_df)} chatbot training samples")

    print("\nDatasets generated successfully!")
    return users_df, products_df, interactions_df, chatbot_df


def train_lstm_model():
    """Train the LSTM intent classification model"""
    print("\n" + "="*60)
    print("STEP 2: Training LSTM Intent Classification Model")
    print("="*60)

    import pandas as pd
    import numpy as np
    from sklearn.model_selection import train_test_split

    from utils.nlp_preprocessing import TextPreprocessor
    from models.lstm_model import LSTMIntentClassifier

    data_dir = os.path.join(PROJECT_DIR, 'data')
    models_dir = os.path.join(PROJECT_DIR, 'models')

    # Load chatbot data
    print("\nLoading chatbot training data...")
    df = pd.read_csv(os.path.join(data_dir, 'chatbot_data.csv'))

    texts = df['text'].tolist()
    intents = df['intent'].tolist()

    print(f"Total samples: {len(texts)}")
    print(f"Unique intents: {len(set(intents))}")

    # Initialize preprocessor
    print("\nBuilding vocabulary...")
    preprocessor = TextPreprocessor(max_vocab_size=5000, max_sequence_length=20)
    preprocessor.build_vocabulary(texts)
    preprocessor.build_intent_mapping(intents)

    # Convert to sequences
    X = preprocessor.texts_to_sequences(texts)
    y = preprocessor.intents_to_indices(intents)

    # Split data
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"\nTraining samples: {len(X_train)}")
    print(f"Validation samples: {len(X_val)}")
    print(f"Vocabulary size: {preprocessor.vocab_size}")
    print(f"Number of intents: {len(preprocessor.intent_to_index)}")

    # Build and train model
    print("\nBuilding LSTM model...")
    model = LSTMIntentClassifier(
        vocab_size=preprocessor.vocab_size,
        embedding_dim=128,
        lstm_units=64,
        max_sequence_length=preprocessor.max_sequence_length,
        num_intents=len(preprocessor.intent_to_index)
    )

    model.build_model()

    print("\nTraining LSTM model (this may take a few minutes)...")
    model_path = os.path.join(models_dir, 'intent_model.keras')

    model.train(
        X_train, y_train,
        X_val, y_val,
        epochs=50,
        batch_size=32,
        model_path=model_path
    )

    # Save preprocessor
    preprocessor_path = os.path.join(models_dir, 'preprocessor.pkl')
    preprocessor.save(preprocessor_path)

    # Save model config
    config_path = model_path.replace('.keras', '_config.json')
    model.save(model_path, config_path)

    # Evaluate
    y_pred = model.predict_intent(X_val)
    accuracy = np.mean(y_pred == y_val)
    print(f"\nValidation Accuracy: {accuracy:.4f}")

    # Test predictions
    print("\nSample predictions:")
    test_texts = [
        "hello there",
        "show me electronics",
        "recommend something for me",
        "products under 500 rupees",
        "add this to cart",
        "find me grocery items",
        "show sports products"
    ]

    for text in test_texts:
        seq = preprocessor.texts_to_sequences([text])
        pred_idx, conf = model.predict_with_confidence(seq)
        intent = preprocessor.index_to_intent_label(pred_idx[0])
        print(f"  '{text}' -> {intent} (confidence: {conf[0]:.2f})")

    print("\nLSTM model trained successfully!")
    return model, preprocessor


def test_recommendation_system():
    """Test the recommendation system"""
    print("\n" + "="*60)
    print("STEP 3: Testing Recommendation System")
    print("="*60)

    import pandas as pd
    from utils.recommendation_engine import HybridRecommender

    data_dir = os.path.join(PROJECT_DIR, 'data')

    # Load data
    users_df = pd.read_csv(os.path.join(data_dir, 'users.csv'))
    products_df = pd.read_csv(os.path.join(data_dir, 'products.csv'))
    interactions_df = pd.read_csv(os.path.join(data_dir, 'interactions.csv'))

    print(f"\nDataset Summary:")
    print(f"  Users: {len(users_df)}")
    print(f"  Products: {len(products_df)}")
    print(f"  Interactions: {len(interactions_df)}")
    print(f"  Categories: {products_df['category'].nunique()}")

    # Initialize and train
    recommender = HybridRecommender(cf_weight=0.6, cb_weight=0.4)
    recommender.fit(users_df, products_df, interactions_df)

    # Test recommendations
    test_user = users_df.iloc[0]['user_id']
    print(f"\nRecommendations for user {test_user}:")

    recs = recommender.recommend(test_user, n=5)
    for pid, score in recs:
        product = recommender.get_product_details(pid)
        name = product['name'][:45] + '...' if len(product['name']) > 45 else product['name']
        print(f"  {name} - Rs.{product['price']:.0f} (score: {score:.2f})")

    # Test search
    print("\nSearch test for 'smartphone':")
    search_results = recommender.search_products('smartphone', n=3)
    for pid, score in search_results:
        product = recommender.get_product_details(pid)
        name = product['name'][:45] + '...' if len(product['name']) > 45 else product['name']
        print(f"  {name} (relevance: {score:.2f})")

    # Test category filter
    print("\nRecommendations in 'Electronics' category:")
    cat_recs = recommender.recommend(test_user, n=3, category='Electronics')
    for pid, score in cat_recs:
        product = recommender.get_product_details(pid)
        name = product['name'][:45] + '...' if len(product['name']) > 45 else product['name']
        print(f"  {name} - Rs.{product['price']:.0f}")

    print("\nRecommendation system working correctly!")
    return recommender


def verify_setup():
    """Verify all components are set up correctly"""
    print("\n" + "="*60)
    print("STEP 4: Verifying Setup")
    print("="*60)

    data_dir = os.path.join(PROJECT_DIR, 'data')
    models_dir = os.path.join(PROJECT_DIR, 'models')

    checks = [
        ('users.csv', os.path.join(data_dir, 'users.csv')),
        ('products.csv', os.path.join(data_dir, 'products.csv')),
        ('interactions.csv', os.path.join(data_dir, 'interactions.csv')),
        ('chatbot_data.csv', os.path.join(data_dir, 'chatbot_data.csv')),
        ('intent_model.keras', os.path.join(models_dir, 'intent_model.keras')),
        ('preprocessor.pkl', os.path.join(models_dir, 'preprocessor.pkl')),
    ]

    all_good = True
    for name, path in checks:
        exists = os.path.exists(path)
        status = "OK" if exists else "MISSING"
        print(f"  {name}: {status}")
        if not exists:
            all_good = False

    if all_good:
        print("\nAll components verified! Setup complete.")
    else:
        print("\nSome components are missing. Please run setup again.")

    return all_good


def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description='Train Personal Shopping Agent')
    parser.add_argument('--use-external', action='store_true',
                       help='Use external products.csv dataset')
    parser.add_argument('--skip-training', action='store_true',
                       help='Skip LSTM model training')
    args = parser.parse_args()

    print("\n" + "="*60)
    print("PERSONAL SHOPPING AGENT - SETUP")
    print("="*60)

    # Setup directories
    setup_directories()

    # Generate or integrate datasets
    if args.use_external or os.path.exists(EXTERNAL_PRODUCTS_PATH):
        print("\nUsing external dataset...")
        integrate_external_dataset()
    else:
        print("\nGenerating synthetic datasets...")
        generate_synthetic_datasets()

    # Train LSTM model
    if not args.skip_training:
        train_lstm_model()

    # Test recommendation system
    test_recommendation_system()

    # Verify setup
    verify_setup()

    print("\n" + "="*60)
    print("SETUP COMPLETE!")
    print("="*60)
    print("\nTo start the application, run:")
    print("  python app.py")
    print("\nThen open http://localhost:5000 in your browser.")


if __name__ == '__main__':
    main()
