# 🤖 Shopping Agent Chatbot - AI-Powered E-Commerce Assistant

A **Flask-based AI Shopping Assistant** that combines LSTM neural networks for natural language understanding, hybrid recommendation engine for personalized product suggestions, and real-time session management for seamless shopping experience.

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [System Architecture](#system-architecture)
- [Complete User Workflow](#complete-user-workflow)
- [Components](#components)
- [REST API Endpoints](#rest-api-endpoints)
- [Data Flow](#data-flow)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Datasets](#datasets)
- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [Performance Metrics](#performance-metrics)

---

## 🎯 Project Overview

The Shopping Agent Chatbot is an intelligent e-commerce assistant that understands user intent through LSTM-based NLP, extracts key entities (category, price), and provides personalized product recommendations using a hybrid approach combining collaborative filtering and content-based filtering.

### Key Capabilities:
- **Natural Language Understanding**: LSTM-based intent classification (13 intent types)
- **Intelligent Search**: Entity extraction for category and price filtering
- **Hybrid Recommendations**: 60% Collaborative Filtering + 40% Content-Based
- **Real-time Session Management**: Track user behavior, cart, feedback
- **Interactive Web Interface**: Chat, search, recommendations, cart management
- **Personalization**: Learns from user interactions to improve recommendations

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                         │
│              (Frontend - HTML/CSS/JavaScript)                │
│  Chat | Search | Recommendations | Cart | Categories        │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ↓ HTTP Requests (REST API)
                   │
┌──────────────────────────────────────────────────────────────┐
│                    FLASK BACKEND (app.py)                    │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              REST API Endpoints                         │ │
│  │  /api/chat          → Process user message             │ │
│  │  /api/recommend     → Get recommendations              │ │
│  │  /api/cart/*        → Cart operations                  │ │
│  │  /api/feedback      → Record feedback                  │ │
│  │  /api/products/*    → Search/details                   │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        ↓          ↓          ↓
   ┌────────┐ ┌──────────┐ ┌──────────────┐
   │  NLP   │ │LSTM Model│ │  Recommendation
   │Pipeline│ │Intent    │ │  Engine
   │        │ │Classifier│ │
   └────────┘ └──────────┘ └──────────────┘
        │          │          │
└────────────────────────────────────────────┐
│        SESSION MANAGER                     │
│  - Track user behavior                     │
│  - Manage cart/wishlist                    │
│  - Store feedback                          │
│  - Dynamic recommendations                 │
└────────────────────────────────────────────┘
        ↓
┌────────────────────────────────────────────┐
│         DATA LAYER (CSV Files)             │
│  - Products (5,000 items)                  │
│  - Users (500 profiles)                    │
│  - Interactions (10,000 records)           │
│  - Chatbot Training Data (758 samples)     │
└────────────────────────────────────────────┘
```

---

## 🔄 Complete User Workflow

### Step 1: User Types a Message
```
Input: "Show me laptops under $500"
```

### Step 2: Frontend Sends to Backend
```json
POST /api/chat
{
    "message": "Show me laptops under $500",
    "user_id": "GUEST_a3f5x7z1"
}
```

### Step 3: NLP Processing Pipeline

```
RAW TEXT: "Show me laptops under $500"
    ↓
TEXT PREPROCESSING (TextPreprocessor)
├─ clean_text()
│  └─ Lowercase, remove special chars, normalize whitespace
├─ tokenize()
│  └─ Split into words
├─ text_to_sequence()
│  └─ Convert words to token indices using vocab
└─ pad_sequence()
   └─ Pad/truncate to max_sequence_length (20 tokens)

RESULT: [45, 23, 234, 98, 150, 0, 0, ..., 0]  (20 tokens)
```

### Step 4: LSTM Intent Classification

```
LSTM Architecture:
┌─────────────────────────────────────┐
│ Input: Padded sequence (20 tokens)  │
├─────────────────────────────────────┤
│ Embedding Layer                     │
│ └─ 128-dimensional word vectors     │
├─────────────────────────────────────┤
│ Bidirectional LSTM-1                │
│ └─ 64 units, 20% dropout            │
├─────────────────────────────────────┤
│ Bidirectional LSTM-2                │
│ └─ 32 units, 20% dropout            │
├─────────────────────────────────────┤
│ Global Max Pooling                  │
│ └─ Extract max values               │
├─────────────────────────────────────┤
│ Dense Layer-1                       │
│ └─ 64 units, ReLU, 30% dropout      │
├─────────────────────────────────────┤
│ Dense Layer-2                       │
│ └─ 32 units, ReLU, 20% dropout      │
├─────────────────────────────────────┤
│ Output Layer (Softmax)              │
│ └─ 13 intent classes                │
└─────────────────────────────────────┘

OUTPUT:
{
    'intent': 'price_query',
    'confidence': 0.92
}
```

### Step 5: Entity Extraction

```
TEXT: "Show me laptops under $500"
    ↓
CATEGORY EXTRACTION (EntityExtractor)
├─ Pattern matching: look for known category keywords
├─ Alias mapping: "laptops" → "Electronics"
└─ Result: category = "Electronics"
    ↓
PRICE EXTRACTION
├─ Regex patterns: "under $500", "below 500", etc.
├─ Extract numeric value: 500.0
└─ Result: price = 500.0

ENTITIES DICT:
{
    'category': 'Electronics',
    'price': 500.0
}
```

### Step 6: Hybrid Recommendation Engine

```
COLLABORATIVE FILTERING (60% weight):
├─ Matrix Factorization:
│  └─ User factors × Item factors = interaction scores
├─ Get user's interaction history
├─ Find similar users' preferences
└─ Predict scores for all products

CONTENT-BASED FILTERING (40% weight):
├─ TF-IDF Vectorization:
│  └─ Create vectors from product features
├─ Get products user viewed/clicked
├─ Calculate cosine similarity with other products
└─ Get similar products

HYBRID COMBINATION:
final_score = 0.6 × CF_score + 0.4 × CB_score

FILTERS APPLIED:
├─ Category filter: only "Electronics"
├─ Price filter: price ≤ 500
├─ Exclude already interacted items
└─ Boost recent categories by +30%

FINAL RESULT:
Top 6 products sorted by combined score
[
  ('PROD_001_laptop', 0.87),
  ('PROD_012_laptop', 0.82),
  ('PROD_045_ultrabook', 0.78),
  ...
]
```

### Step 7: Response Generation

```
INTENT: 'price_query'
ENTITIES: {category: 'Electronics', price: 500}
    ↓
RESPONSE TEMPLATE SELECTION:
├─ Look up response templates for intent
├─ Randomly select one from template list
└─ Format with extracted entities

RESPONSE TEXT:
"Finding affordable options within your budget of $500."
```

### Step 8: Product Details Retrieval

```
PRODUCT_IDS: ['PROD_001_laptop', 'PROD_012_laptop', ...]
    ↓
FOR EACH PRODUCT_ID:
├─ Look up in products.csv
├─ Get details:
│  ├─ product_id, name, brand, category
│  ├─ price, discount_percent
│  ├─ rating, num_reviews
│  ├─ description, tags, stock
│  └─ Calculate final price after discount
├─ Convert numpy types to JSON-serializable
└─ Create product object

PRODUCT OBJECT:
{
  'product_id': 'PROD_001_laptop',
  'name': 'Dell XPS 13 Laptop',
  'price': 449.99,
  'rating': 4.7,
  'num_reviews': 520,
  'discount_percent': 10,
  'category': 'Electronics',
  'brand': 'Dell',
  'description': 'High-performance ultrabook...'
}
```

### Step 9: Session Tracking

```
USER INTERACTION TRACKING:

click → User viewed product details
view → User scrolled past product
search → User performed search query
add_to_cart → User added item to cart
feedback → User liked/disliked product

ACTIONS TAKEN:
├─ Track in user_click_history
├─ Update SessionManager.recommender.interactions_df
├─ Call recommender.update_interactions()
├─ Adjust user preference weights
└─ Store for future recommendations
```

### Step 10: Response Sent to Frontend

```json
{
  "success": true,
  "message": "Show me laptops under $500",
  "intent": "price_query",
  "confidence": 0.92,
  "entities": {
    "category": "Electronics",
    "price": 500.0
  },
  "response": "Finding affordable options within your budget of $500.",
  "products": [
    {
      "product_id": "PROD_001_laptop",
      "name": "Dell XPS 13 Laptop",
      "price": 449.99,
      "rating": 4.7,
      "discount_percent": 10,
      "category": "Electronics",
      "num_reviews": 520
    },
    ...
  ],
  "action": "show_products"
}
```

### Step 11: Frontend Displays Results

```
┌─────────────────────────────────────┐
│  Bot Says:                          │
│  "Finding affordable options within │
│   your budget of $500."             │
└─────────────────────────────────────┘

┌────────┬────────┬────────┐
│ Laptop │ Laptop │ Laptop │
│ $450   │ $499   │ $399   │
│ 4.7⭐  │ 4.5⭐  │ 4.8⭐  │
│ [+][-] │ [+][-] │ [+][-] │  ← Like/Dislike buttons
└────────┴────────┴────────┘
```

---

## 🧩 Components

### 1. **LSTM Intent Classifier** (`models/lstm_model.py`)

| Component | Details |
|-----------|---------|
| **Input Layer** | Sequence of 20 tokens |
| **Embedding** | 128-dimensional word embeddings |
| **BiLSTM-1** | 64 units, bidirectional, 20% dropout |
| **BiLSTM-2** | 32 units, bidirectional, 20% dropout |
| **Pooling** | Global Max Pooling |
| **Dense-1** | 64 units, ReLU activation, 30% dropout |
| **Dense-2** | 32 units, ReLU activation, 20% dropout |
| **Output** | 13 units, Softmax (13 intent classes) |
| **Training** | 758 samples, 50 epochs, batch_size=32 |
| **Loss** | Categorical Cross-Entropy |
| **Optimizer** | Adam (lr=0.001) |

**Intent Types (13 Total):**
1. `greeting` - Welcome messages
2. `goodbye` - Farewell responses
3. `search_product` - Search by query
4. `category_recommendation` - Browse category
5. `price_query` - Filter by price
6. `recommendation` - Personalized recommendations
7. `cart_add` - Add item confirmation
8. `cart_view` - Show cart contents
9. `order_status` - Check order status
10. `help` - Show available commands
11. `feedback` - Process like/dislike
12. `compare` - Compare products
13. `deals` - Show discounted items

### 2. **NLP Preprocessing** (`utils/nlp_preprocessing.py`)

**TextPreprocessor Class:**
- `clean_text()` - Lowercase, remove special chars, normalize whitespace
- `tokenize()` - Split into words
- `build_vocabulary()` - Create word-to-index mapping (max 5000 tokens)
- `build_intent_mapping()` - Map intents to indices
- `text_to_sequence()` - Convert text to token indices
- `pad_sequence()` - Pad/truncate to fixed length (20 tokens)
- `texts_to_sequences()` - Batch processing
- `save()/load()` - Persist preprocessor state with pickle

**EntityExtractor Class:**
- `extract_category()` - Regex + keyword matching (30+ category aliases)
- `extract_price()` - Pattern matching for price ($X, under $X, etc.)
- `extract_all()` - Extract all entities from text

### 3. **Hybrid Recommendation Engine** (`utils/recommendation_engine.py`)

#### Collaborative Filtering (CF)
```
Matrix Factorization:
- User-Item interaction matrix (500 × 5000)
- User factors (500 × 50)
- Item factors (5000 × 50)

Training Parameters:
- SGD with L2 regularization
- Learning rate: 0.01
- Regularization: 0.02
- Epochs: 20

Interaction Weights:
- purchase: 5.0
- add_to_cart: 4.0
- wishlist: 3.0
- click: 2.0
- view: 1.0
- search: 1.5
```

#### Content-Based Filtering (CB)
```
TF-IDF + Cosine Similarity:
- Features: name, category, subcategory, brand, description, tags
- Max features: 5000
- Ngrams: (1, 2)
- Similarity: cos_sim(tfidf_a, tfidf_b)
```

#### Hybrid Scoring
```
final_score = 0.6 × CF_score + 0.4 × CB_score

Applied Filters:
- Category filter (if specified)
- Price filter (max_price ≤ X)
- Exclude interacted items
- Boost recent categories (+30%)
```

### 4. **Session Manager** (`utils/session_manager.py`)

Manages user behavior tracking:
- `create_session()` - Initialize user session
- `track_click()` - Log product interactions
- `track_view()` - Log product views
- `track_search()` - Log search queries
- `add_to_cart()` / `remove_from_cart()` - Cart management
- `record_feedback()` - Like/dislike tracking with preference weight adjustment
- `get_dynamic_recommendations()` - Real-time recommendations with boost
- `get_personalized_deals()` - Category-specific discounted products
- `get_session_stats()` - User activity statistics

### 5. **Flask Backend** (`app.py`)

REST API server with 15+ endpoints:
- Chat processing
- Product recommendations
- Product search
- Cart management
- User feedback recording
- Session statistics

---

## 🔌 REST API Endpoints

### Chat Endpoint
```
POST /api/chat

Request:
{
    "message": "Show me laptops under $500",
    "user_id": "GUEST_a3f5x7z1"
}

Response:
{
    "success": true,
    "intent": "price_query",
    "confidence": 0.92,
    "entities": {"category": "Electronics", "price": 500.0},
    "response": "Finding affordable options...",
    "products": [...],
    "action": "show_products"
}
```

### Recommendation Endpoint
```
POST /api/recommend

Request:
{
    "user_id": "GUEST_a3f5x7z1",
    "n": 12,
    "category": "Electronics",
    "max_price": 500
}

Response:
{
    "success": true,
    "recommendations": [
        {
            "product_id": "PROD_001_laptop",
            "name": "Dell XPS 13",
            "price": 449.99,
            "recommendation_score": 0.87,
            ...
        },
        ...
    ]
}
```

### Cart Endpoints
```
POST /api/cart/add
POST /api/cart/remove
GET /api/cart?user_id=GUEST_xxx
```

### Product Search
```
GET /api/products/search?q=laptop&max_price=500&user_id=GUEST_xxx
```

### Product Details
```
GET /api/product/<product_id>?user_id=GUEST_xxx
```

### User Feedback
```
POST /api/feedback

Request:
{
    "user_id": "GUEST_a3f5x7z1",
    "product_id": "PROD_001_laptop",
    "feedback_type": "like",
    "rating": 5
}
```

### User Statistics
```
GET /api/user/stats?user_id=GUEST_xxx
```

### Categories
```
GET /api/categories

Response:
{
    "success": true,
    "categories": ["Electronics", "Clothing", "Home & Kitchen", ...]
}
```

---

## 📊 Data Flow

```
USER INPUT
    ↓
TEXT PREPROCESSING
├─ clean_text()
├─ tokenize()
├─ text_to_sequence()
└─ pad_sequence()
    ↓
LSTM INTENT CLASSIFICATION
├─ Embedding layer
├─ BiLSTM layers
├─ Dense layers
└─ Output: intent + confidence
    ↓
ENTITY EXTRACTION
├─ extract_category()
├─ extract_price()
└─ Return entities dict
    ↓
HYBRID RECOMMENDATION
├─ Collaborative Filtering path
├─ Content-Based path
├─ Hybrid scoring (60/40)
├─ Filtering (category, price)
└─ Top-N products
    ↓
RESPONSE GENERATION
├─ Select response template
├─ Format with entities
└─ Return response text
    ↓
PRODUCT DETAILS LOOKUP
├─ Get product info
├─ Calculate discounts
└─ Prepare JSON
    ↓
SESSION TRACKING
├─ Track click/view
├─ Update interactions
├─ Update preferences
└─ Store in session
    ↓
API RESPONSE (JSON)
├─ intent, confidence
├─ entities, response
├─ products, action
└─ Send to frontend
    ↓
FRONTEND DISPLAY
├─ Render bot message
├─ Display products
├─ Enable interactions
└─ Update UI
```

---

## 💻 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla) |
| **Backend** | Flask, Flask-CORS |
| **NLP/ML** | TensorFlow/Keras, scikit-learn |
| **Data Processing** | Pandas, NumPy |
| **Database** | CSV files (in-memory) |
| **Threading** | Python threading (thread-safe) |
| **API Format** | REST (JSON) |
| **Server** | Werkzeug (Flask dev server) |

---

## 📁 Project Structure

```
shopping_agent/
├── app.py                          # Flask backend entry point
├── requirements.txt                # Python dependencies
├── README.md                       # This file
│
├── models/
│   ├── __init__.py
│   ├── lstm_model.py              # LSTM intent classifier
│   ├── intent_model.keras         # Trained LSTM model weights
│   └── preprocessor.pkl           # Saved TextPreprocessor
│
├── utils/
│   ├── __init__.py
│   ├── nlp_preprocessing.py       # TextPreprocessor + EntityExtractor
│   ├── recommendation_engine.py   # Hybrid recommender system
│   └── session_manager.py         # User session management
│
├── templates/
│   └── index.html                 # HTML UI template
│
├── static/
│   ├── js/
│   │   └── app.js                 # Frontend JavaScript (1000+ lines)
│   └── css/
│       └── styles.css             # Styling
│
├── data/
│   ├── chatbot_data.csv           # LSTM training data (758 samples)
│   ├── products.csv               # Product catalog (5,000 items)
│   ├── users.csv                  # User profiles (500 users)
│   ├── interactions.csv           # User interactions (10,000 records)
│   └── generate_datasets.py       # Script to generate synthetic data
│
└── venv/                           # Virtual environment
```

---

## 📦 Datasets

| Dataset | Rows | Purpose |
|---------|------|---------|
| **chatbot_data.csv** | 758 | LSTM training data (text → intent) |
| **products.csv** | 5,000 | Product catalog with details |
| **users.csv** | 500 | User profiles for personalization |
| **interactions.csv** | 10,000 | User-product interactions |
| **Total** | **16,258** | - |

### Data Columns:

**products.csv:**
- product_id, name, brand, category, subcategory
- price, discount_percent, rating, num_reviews
- description, tags, stock

**users.csv:**
- user_id, name, email, created_at, preferences

**interactions.csv:**
- interaction_id, user_id, product_id, interaction_type
- timestamp, rating, session_id, device, search_query

**chatbot_data.csv:**
- text, intent

---

## 🚀 Installation

### 1. Clone/Navigate to Project
```bash
cd shopping_agent
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify Models & Data Exist
```bash
ls models/  # Should see: intent_model.keras, preprocessor.pkl
ls data/    # Should see: *.csv files
```

### 5. Run Application
```bash
python app.py
```

Output should show:
```
============================================================
Loading Personal Shopping Agent
============================================================
1. Loading datasets...
   Users: 500
   Products: 5000
   Interactions: 10000

2. Initializing Recommendation System...
   Training Collaborative Filtering model...
   Training Content-Based Filtering model...

3. Loading LSTM Chatbot Model...
   LSTM model loaded successfully!

4. Initializing Session Manager...

============================================================
Shopping Agent Ready!
============================================================
```

### 6. Access Web Interface
Open browser: `http://localhost:5000`

---

## 📖 Usage

### 1. Using Chat Interface

Type messages to interact:
```
"Show me electronics under $200"
"Recommend some books"
"What's in my cart?"
"Show me deals"
"Help"
"Find running shoes"
"Compare laptops"
```

### 2. Using Search

Type in search bar or use API:
```bash
curl "http://localhost:5000/api/products/search?q=laptop&max_price=500"
```

### 3. Shopping Features

**Browse by Category:**
- Click category cards in Recommendations tab
- See all products in that category

**Add to Cart:**
- Click "Add" button on product cards
- View/edit cart from cart icon
- See total price with discount applied

**Like/Dislike Products:**
- Click thumbs up/down icons
- Feedback immediately affects recommendations
- Preference weights get adjusted

**View Product Details:**
- Click product card to see full details
- View similar/recommended products
- Product ratings and review count

### 4. API Usage Example

```python
import requests

# Send chat message
response = requests.post('http://localhost:5000/api/chat', json={
    'message': 'Show me laptops under $500',
    'user_id': 'GUEST_a3f5x7z1'
})
data = response.json()
print(f"Intent: {data['intent']}")
print(f"Products: {len(data['products'])}")

# Get recommendations
response = requests.post('http://localhost:5000/api/recommend', json={
    'user_id': 'GUEST_a3f5x7z1',
    'n': 10,
    'category': 'Electronics',
    'max_price': 500
})
recommendations = response.json()['recommendations']
```

---

## ✨ Features

### Core Features
- ✅ **Natural Language Understanding** - LSTM-based intent classification
- ✅ **Entity Extraction** - Category and price extraction from user text
- ✅ **Hybrid Recommendations** - CF (60%) + CB (40%)
- ✅ **Product Search** - Full-text search with filtering
- ✅ **Shopping Cart** - Add/remove/view products
- ✅ **User Feedback** - Like/dislike tracking and adjustment
- ✅ **Real-time Session Management** - Track all user behavior
- ✅ **Personalized Deals** - Category-specific discounted items
- ✅ **Product Comparison** - Show similar products
- ✅ **Category Browsing** - Browse by product category
- ✅ **User Statistics** - Track user activity

### Advanced Features
- 🤖 **13 Intent Types** - Comprehensive conversation coverage
- 🎯 **Dynamic Recommendations** - Boost based on recent clicks
- 📊 **Multi-weighted Interactions** - Different weights for different actions
- 🔄 **Real-time Updates** - Instant preference weight adjustments
- 🧵 **Thread-safe Operations** - Concurrent user handling with locks
- 📱 **Responsive UI** - Works on desktop and mobile devices

---

## 📈 Performance Metrics

| Metric | Value |
|--------|-------|
| **Product Catalog** | 5,000 items |
| **User Profiles** | 500 users |
| **Interaction History** | 10,000 records |
| **Training Data** | 758 samples |
| **Vocabulary Size** | ~5,000 tokens |
| **LSTM Model Size** | ~2MB |
| **Max Sequence Length** | 20 tokens |
| **Embedding Dimension** | 128 |
| **CF Factors** | 50 dimensions |
| **TF-IDF Features** | 5,000 max |
| **Inference Time** | ~50-100ms per query |
| **API Response Time** | ~200-500ms total |
| **Recommendation Speed** | Real-time (< 1 second) |
| **Concurrent Users** | 100+ (thread-safe) |

---

## 🔧 Configuration

### Customize LSTM Model
In `models/lstm_model.py`:
```python
model = LSTMIntentClassifier(
    vocab_size=5000,           # Vocabulary size
    embedding_dim=128,         # Embedding dimension
    lstm_units=64,             # BiLSTM units
    max_sequence_length=20,    # Max tokens
    num_intents=13             # Number of intents
)
```

### Customize Recommender Weights
In `app.py`:
```python
recommender = HybridRecommender(
    cf_weight=0.6,   # Collaborative filtering weight
    cb_weight=0.4    # Content-based weight
)
```

### Entity Extractor Categories
In `utils/nlp_preprocessing.py` - Update `categories` list and `category_aliases` dict

---

## 🐛 Troubleshooting

### Models Not Loading
```
Error: "WARNING: LSTM model not found"
Solution: Models exist - check paths are correct
         Or retrain: python models/lstm_model.py
```

### Port Already in Use
```
Error: "Address already in use: ('0.0.0.0', 5000)"
Solution:
- Change port in app.py: app.run(port=5001)
- Or kill process: lsof -ti:5000 | xargs kill -9
```

### CORS Issues
```
Error: "Access to XMLHttpRequest blocked"
Solution: Flask-CORS already configured, check CORS header
```

### Slow Performance
- Reduce TF-IDF features: max_features=2000
- Reduce CF factors: n_factors=25
- Use smaller dataset for testing

---

## 📚 Key Workflows

### Workflow 1: User Registration & Session
```
1. User opens website
2. Frontend generates GUEST_ID (random)
3. Session created in SessionManager
4. Cart/wishlist arrays initialized
5. User can browse immediately
```

### Workflow 2: Shopping Search
```
User: "Search for running shoes under $100"
  ↓
LSTM → Intent: search_product
Entity → category: sports, price: 100
  ↓
Content-Based Search on query "running shoes"
Filter by price ≤ 100
  ↓
Return top 12 matching products
Track search interaction
```

### Workflow 3: Personalized Recommendations
```
User: "Show me recommendations"
  ↓
LSTM → Intent: recommendation
  ↓
Get user's interaction history
  ↓
CF: predict scores for unseen items
CB: find similar to user's viewed items
  ↓
Hybrid: 0.6×CF + 0.4×CB
Boost recent categories by +30%
  ↓
Return top 6 recommendations
```

### Workflow 4: Feedback Loop
```
User feedback: "I like this product"
  ↓
SessionManager.record_feedback()
  ↓
Adjust user preferences:
- Like: +2.0 weight to category
- Dislike: -1.0 weight to category
  ↓
Next recommendation uses updated prefs
  ↓
Recommender model improves over time
```

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the API documentation
3. Check server logs for detailed errors
4. Verify all datasets are present and accessible

---

**Happy Shopping! 🛒**

Built with ❤️ using Flask, LSTM, and Machine Learning
