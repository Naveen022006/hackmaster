"""
Personal Shopping Agent - Main Entry Point

This script provides a command-line interface to:
1. Generate datasets
2. Train models
3. Run the API server
4. Evaluate models
5. Test the system interactively
"""
import argparse
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)


def generate_datasets():
    """Generate synthetic datasets."""
    print("Generating datasets...")
    from services.dataset_generator import DatasetGenerator

    generator = DatasetGenerator()
    users, products, interactions = generator.generate_all_datasets()

    print("\n--- Dataset Statistics ---")
    print(f"Users: {len(users)} rows")
    print(f"Products: {len(products)} rows")
    print(f"Interactions: {len(interactions)} rows")
    print(f"\nAction distribution:\n{interactions['action'].value_counts()}")


def preprocess_data():
    """Run data preprocessing pipeline."""
    print("Running preprocessing pipeline...")
    from services.data_preprocessor import DataPreprocessor

    preprocessor = DataPreprocessor()
    data = preprocessor.preprocess_all()

    print("\n--- Preprocessed Data Summary ---")
    print(f"User features: {data['users'].columns.tolist()}")
    print(f"Product features: {data['products'].columns.tolist()}")
    print(f"Interaction matrix shape: {data['interaction_matrix'].shape}")
    print(f"Product embeddings shape: {data['product_embeddings'].shape}")


def train_models():
    """Train recommendation models."""
    print("Training models...")
    import pandas as pd
    from services.data_preprocessor import DataPreprocessor
    from models.recommender import HybridRecommender
    from utils.config import DATA_DIR

    # Load preprocessed data
    preprocessor = DataPreprocessor()
    try:
        data = preprocessor.load_preprocessed_data()
    except FileNotFoundError:
        print("Preprocessed data not found. Running preprocessing first...")
        data = preprocessor.preprocess_all()

    interactions_df = pd.read_csv(DATA_DIR / "interactions_processed.csv")
    interactions_df["timestamp"] = pd.to_datetime(interactions_df["timestamp"])

    # Train hybrid recommender
    recommender = HybridRecommender()
    recommender.fit(
        interaction_matrix=data["interaction_matrix"],
        product_embeddings=data["product_embeddings"],
        users_df=data["users"],
        products_df=data["products"],
        interactions_df=interactions_df
    )
    recommender.save()

    # Train NLP processor
    from services.nlp_processor import NLPProcessor
    nlp = NLPProcessor()
    nlp.intent_classifier.train()
    nlp.save()

    print("\nModels trained and saved successfully!")


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI server."""
    import uvicorn
    print(f"Starting server at http://{host}:{port}")
    print("API documentation available at http://localhost:8000/docs")
    uvicorn.run("api.main:app", host=host, port=port, reload=False)


def evaluate_models():
    """Run model evaluation."""
    from models.evaluation import run_evaluation
    run_evaluation()


def interactive_test():
    """Run interactive testing."""
    print("\n" + "=" * 60)
    print("PERSONAL SHOPPING AGENT - Interactive Test")
    print("=" * 60)

    from services.recommendation_pipeline import RecommendationPipeline
    import pandas as pd
    from utils.config import DATA_DIR

    # Initialize pipeline
    print("\nInitializing system...")
    pipeline = RecommendationPipeline()
    pipeline.initialize()

    # Get a test user
    users_df = pd.read_csv(DATA_DIR / "users_processed.csv")
    test_user_id = users_df["user_id"].iloc[0]

    print(f"\nUsing test user: {test_user_id}")
    print("\nCommands:")
    print("  - Type a shopping query (e.g., 'I want a phone under 15000')")
    print("  - Type 'profile' to see user profile")
    print("  - Type 'quit' to exit")
    print("-" * 60)

    while True:
        try:
            query = input("\nYou: ").strip()

            if not query:
                continue

            if query.lower() == "quit":
                print("Goodbye!")
                break

            if query.lower() == "profile":
                profile = pipeline.get_user_preferences(test_user_id)
                print("\n--- User Profile ---")
                for key, value in profile.items():
                    print(f"{key}: {value}")
                continue

            # Process query
            result = pipeline.process_query(
                user_id=test_user_id,
                query=query,
                top_n=5
            )

            print(f"\nAssistant: {result['response']}")
            print(f"[Intent: {result['intent']} | Confidence: {result['intent_confidence']:.2f}]")

            if result["recommendations"]:
                print("\nRecommendations:")
                for i, rec in enumerate(result["recommendations"], 1):
                    rating_str = f"Rating: {rec['rating']:.1f}" if rec.get('rating') else "No rating"
                    print(f"  {i}. {rec['name']}")
                    print(f"     {rec['category']} | {rec['brand']} | ₹{rec['price']:,.0f} | {rating_str}")

            print(f"\n[Latency: {result['latency_ms']:.1f}ms | Cached: {result['cached']}]")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def run_frontend(port: int = 3000):
    """Run the frontend server."""
    import http.server
    import socketserver
    import webbrowser
    from pathlib import Path

    frontend_dir = Path(__file__).parent / "frontend"

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(frontend_dir), **kwargs)

        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-store')
            super().end_headers()

        def log_message(self, format, *args):
            pass  # Suppress logs

    print(f"Frontend server running at http://localhost:{port}")
    with socketserver.TCPServer(("", port), Handler) as httpd:
        try:
            webbrowser.open(f'http://localhost:{port}')
        except:
            pass
        httpd.serve_forever()


def run_full_app():
    """Run both API and frontend servers."""
    import subprocess
    import threading
    import time

    print("\n" + "="*60)
    print("PERSONAL SHOPPING AGENT - Full Application")
    print("="*60)

    # Start API server in a thread
    def start_api():
        import uvicorn
        uvicorn.run("api.main:app", host="0.0.0.0", port=8000, log_level="warning")

    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()

    print("\nAPI Server: http://localhost:8000")
    print("API Docs:   http://localhost:8000/docs")

    time.sleep(2)  # Wait for API to start

    # Start frontend
    print("Frontend:   http://localhost:3000")
    print("\nPress Ctrl+C to stop both servers")
    print("="*60 + "\n")

    run_frontend(3000)


def main():
    parser = argparse.ArgumentParser(
        description="Personal Shopping Agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py generate    # Generate synthetic datasets
  python main.py preprocess  # Run preprocessing pipeline
  python main.py train       # Train all models
  python main.py serve       # Start API server only
  python main.py frontend    # Start frontend server only
  python main.py run         # Start both API + Frontend
  python main.py evaluate    # Evaluate model performance
  python main.py interact    # Interactive CLI mode
  python main.py all         # Run everything (generate, preprocess, train)
        """
    )

    parser.add_argument(
        "command",
        choices=["generate", "preprocess", "train", "serve", "frontend", "run", "evaluate", "interact", "all"],
        help="Command to run"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Server host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port (default: 8000)"
    )

    args = parser.parse_args()

    if args.command == "generate":
        generate_datasets()
    elif args.command == "preprocess":
        preprocess_data()
    elif args.command == "train":
        train_models()
    elif args.command == "serve":
        run_server(args.host, args.port)
    elif args.command == "frontend":
        run_frontend(3000)
    elif args.command == "run":
        run_full_app()
    elif args.command == "evaluate":
        evaluate_models()
    elif args.command == "interact":
        interactive_test()
    elif args.command == "all":
        generate_datasets()
        preprocess_data()
        train_models()
        print("\n" + "=" * 60)
        print("Setup complete!")
        print("Run 'python main.py run' to start the full application.")
        print("=" * 60)


if __name__ == "__main__":
    main()
