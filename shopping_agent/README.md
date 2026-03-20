# Personal Shopping Agent

An intelligent, production-ready shopping assistant system powered by NLP and Machine Learning. This system understands natural language queries, provides personalized product recommendations, and adapts to user behavior in real-time.

## Features

- **NLP-Powered Chat Interface**: Understands natural language queries with intent classification and entity extraction
- **Hybrid Recommendation Engine**: Combines Collaborative Filtering (SVD) and Content-Based Filtering
- **Real-Time Personalization**: Tracks user behavior and dynamically updates preferences
- **Cold-Start Handling**: Intelligent fallback to popular items for new users
- **RESTful API**: Production-ready FastAPI backend with comprehensive endpoints

## Project Structure

```
shopping_agent/
├── api/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   └── models.py         # Pydantic request/response models
├── data/                 # Generated datasets (CSV files)
├── models/
│   ├── __init__.py
│   ├── recommender.py    # Hybrid recommendation engine
│   └── evaluation.py     # Model evaluation metrics
├── services/
│   ├── __init__.py
│   ├── dataset_generator.py    # Synthetic data generation
│   ├── data_preprocessor.py    # Data cleaning & feature engineering
│   ├── nlp_processor.py        # Intent classification & entity extraction
│   ├── personalization.py      # User profile management
│   └── recommendation_pipeline.py  # End-to-end pipeline
├── utils/
│   ├── __init__.py
│   └── config.py         # Configuration settings
├── main.py               # CLI entry point
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Install Dependencies

```bash
cd shopping_agent
pip install -r requirements.txt
```

### 2. Generate Data and Train Models

```bash
# Run all setup steps
python main.py all

# Or run individually:
python main.py generate    # Generate synthetic datasets
python main.py preprocess  # Run preprocessing pipeline
python main.py train       # Train models
```

### 3. Start the API Server

```bash
python main.py serve
```

The API will be available at `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### 4. Interactive Testing

```bash
python main.py interact
```

## API Endpoints

### Chat (NLP-powered)
```bash
POST /chat
{
    "user_id": "U00001",
    "message": "I want a phone under 15000 with good camera",
    "top_n": 10
}
```

### Get Recommendations
```bash
GET /recommend?user_id=U00001&top_n=10&category=Electronics&max_price=20000
```

### Browse Products
```bash
GET /products?category=Electronics&brand=Samsung&limit=50
```

### Similar Products
```bash
GET /products/P00001/similar?top_n=10
```

### User Profile
```bash
GET /user/U00001/profile
```

### Record Interaction
```bash
POST /interaction
{
    "user_id": "U00001",
    "product_id": "P00001",
    "action": "purchase",
    "rating": 4.5
}
```

### Update User Preferences
```bash
POST /user/update
{
    "user_id": "U00001",
    "preferences": {
        "favorite_categories": {"Electronics": 10},
        "brand_affinity": {"Samsung": 8}
    }
}
```

## Example Usage

### Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Chat with the shopping assistant
response = requests.post(f"{BASE_URL}/chat", json={
    "user_id": "U00001",
    "message": "Show me Samsung laptops under 50000",
    "top_n": 5
})
result = response.json()

print(f"Intent: {result['intent']}")
print(f"Response: {result['response']}")
for rec in result['recommendations']:
    print(f"- {rec['name']}: ₹{rec['price']}")
```

### cURL Examples

```bash
# Chat endpoint
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"U00001","message":"I want headphones under 5000","top_n":5}'

# Get recommendations
curl "http://localhost:8000/recommend?user_id=U00001&top_n=5&category=Electronics"

# Get products
curl "http://localhost:8000/products?category=Electronics&limit=10"

# Health check
curl "http://localhost:8000/health"
```

## System Components

### 1. Dataset Generator
- Generates realistic users (2,000), products (5,000), and interactions (50,000+)
- Simulates real-world shopping behavior
- Includes noise and missing values for realism

### 2. Data Preprocessor
- Cleans and normalizes data
- Creates user and product embeddings using TF-IDF
- Builds interaction matrix with recency weighting
- Engineers features like purchase frequency and conversion rates

### 3. Hybrid Recommendation Engine
- **Collaborative Filtering**: Matrix Factorization using SVD
- **Content-Based Filtering**: TF-IDF embeddings with cosine similarity
- **Hybrid Strategy**: Weighted combination (70% CF, 30% Content)
- Handles cold-start with popularity fallback

### 4. NLP Processor
- **Intent Classification**: ML-based classifier (Naive Bayes + TF-IDF)
  - Intents: search, buy, compare, filter, general
- **Entity Extraction**: Rule-based extraction for:
  - Categories, brands, price ranges
  - Product features, ratings, sorting preferences

### 5. Personalization Engine
- Real-time user profile tracking
- Recency-weighted preference updates
- Tracks: favorite categories, brand affinity, spending patterns

### 6. API Layer
- FastAPI with async support
- Pydantic validation
- In-memory caching for performance
- Comprehensive error handling

## Evaluation Metrics

Run model evaluation:
```bash
python main.py evaluate
```

Metrics calculated:
- **Precision@K**: Relevant items in top-K recommendations
- **Recall@K**: % of relevant items retrieved
- **NDCG@K**: Normalized Discounted Cumulative Gain
- **MAP@K**: Mean Average Precision
- **Hit Rate**: At least one relevant recommendation
- **Coverage**: % of catalog recommended
- **Diversity**: Category variety in recommendations

## Configuration

Edit `utils/config.py` to customize:

```python
DATASET_CONFIG = {
    "num_users": 2000,
    "num_products": 5000,
    "num_interactions": 50000,
}

MODEL_CONFIG = {
    "embedding_dim": 50,
    "svd_n_factors": 100,
    "content_weight": 0.3,
    "collaborative_weight": 0.7,
    "top_n_recommendations": 10,
}

NLP_CONFIG = {
    "confidence_threshold": 0.6,
}
```

## Sample NLP Queries

The system understands queries like:
- "I want a phone under 15000 with good camera"
- "Show me Samsung laptops"
- "Find affordable Nike shoes"
- "Compare iPhone and Samsung phones"
- "Best headphones under 5000 rupees"
- "Premium smartwatches with good battery"

## Performance Optimization

- **Caching**: LRU cache with TTL for recommendations
- **Batch Processing**: Efficient matrix operations
- **Lazy Loading**: Models loaded on demand
- **Pre-computed Similarities**: Content similarity pre-calculated

## License

MIT License


Login with: admin@shopai.com / admin123456

Test User :: test@example.com / test123456