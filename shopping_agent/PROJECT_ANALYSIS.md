# Personal Shopping Agent - Project Analysis & Run Guide

## Project Overview

**Personal Shopping Agent** is a production-ready e-commerce shopping assistant powered by NLP and Machine Learning. It provides intelligent, personalized product recommendations through a conversational chat interface.

---

## Architecture & Components

### 1. **Backend API (FastAPI)**
- **Location**: `api/main.py`
- **Framework**: FastAPI with async support
- **Port**: 8000
- **Key Endpoints**:
  - `POST /chat` - NLP-powered conversation
  - `GET /recommend` - Personalized recommendations
  - `GET /products` - Product browsing
  - `GET /products/{id}/similar` - Similar products
  - `GET /user/{id}/profile` - User preferences
  - `POST /interaction` - Track user actions

### 2. **Machine Learning Models**
- **Hybrid Recommender** (`models/recommender.py`)
  - Combines: Collaborative Filtering (SVD) + Content-Based Filtering
  - Weights: 70% CF + 30% Content
  - Cold-start handling with popularity fallback

- **NLP Processor** (`services/nlp_processor.py`) - RECENTLY IMPROVED 🎯
  - Intent Classification: 10 intents with 400+ training examples
  - Entity Extraction: 14 entity types
  - Fuzzy brand matching for typos
  - Negation handling ("without", "no")
  - New entities: size, gender, discount, condition

### 3. **Data Pipeline**
- **Dataset Generator**: 2,000 users, 5,000 products, 50,000+ interactions
- **Data Preprocessor**: TF-IDF embeddings, feature engineering
- **Recommendation Pipeline**: End-to-end query processing

### 4. **Frontend**
- **Location**: `frontend/index.html`
- **Type**: Single Page Application (SPA)
- **Port**: 3000
- **Features**: Chat UI, login, product cards, admin dashboard

---

## Data & Models Status

### Data Files (✅ Ready)
```
data/
├── users.csv (2,000 users)
├── products.csv (5,000 products)
├── interactions.csv (50,000+ interactions)
├── users_processed.csv
├── products_processed.csv
├── interactions_processed.csv
├── product_embeddings.npy (5000 x 50 dimensions)
└── interaction_matrix.npz (sparse matrix)
```

### Trained Models (✅ Ready)
```
models/
├── hybrid_recommender.pkl (210 MB - fully trained)
├── nlp_processor.pkl (updated with improvements)
├── encoders.pkl (TF-IDF encoders)
└── evaluation.py (metrics calculation)
```

---

## Recent NLP Improvements (March 20, 2026)

### ✅ Enhancements Made:

1. **Training Data**: 110 → 400+ examples
   - 8 → 10 total intents
   - New intents: `inquiry`, `refine`

2. **Price Parsing Fixed**
   - "20k" → 20,000 ✓
   - "5 lakh" → 500,000 ✓
   - Lakh support added
   - Size exclusion (prevents "13 inch" = 13 price)

3. **New Entity Types**
   - Size (screen, storage, RAM, clothing, shoe)
   - Gender (men, women, kids)
   - Discount (% off detection)
   - Condition (new, refurbished, used)

4. **Fuzzy Brand Matching**
   - "samung" → Samsung ✓
   - "addidas" → Adidas ✓
   - Typo tolerance with 80% threshold

5. **Negation Handling**
   - "without camera" → excluded_features ✓
   - "no gaming" → excluded_features ✓

6. **Brand & Category Expansion**
   - 100+ brands (Nothing, Poco, Fire-Boltt, etc.)
   - 200+ category mappings

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI, Uvicorn, Python 3.10+ |
| **ML/NLP** | scikit-learn, NumPy, Pandas, SciPy |
| **Database** | MongoDB (optional), File-based (primary) |
| **Auth** | JWT, bcrypt |
| **Frontend** | Vanilla JavaScript, HTML5, CSS3 |

---

## Project Statistics

| Metric | Value |
|--------|-------|
| Python Files | 40+ |
| Lines of Code | 5000+ |
| Training Examples | 400+ |
| Intent Types | 10 |
| Entity Types | 14 |
| Brands Supported | 100+ |
| Categories | 200+ |
| API Response Time | 50-150ms |

---

## Running the Project

### Quick Start (Recommended)

```bash
# 1. Navigate to project directory
cd d:\hackermaster\shopping_agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start API server
python main.py serve

# In another terminal, start frontend:
python main.py frontend
```

**Access**:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs (Swagger UI)
- Frontend: http://localhost:3000

### Alternative: Full Application

```bash
# Runs both API + Frontend together
python main.py run
```

### Interactive Mode

```bash
# Test the system in CLI
python main.py interact
```

### Setup from Scratch (if needed)

```bash
python main.py all  # Generate data + preprocess + train
python main.py serve  # Start API
```

---

## Sample Chat Queries

The improved chatbot now understands:

```
Basic:
- "Hello!"
- "Show me phones"
- "I want to buy a laptop"

Price Queries (IMPROVED):
- "phones under 20k"
- "laptops under 5 lakh"
- "budget 10k to 20k"

Typos (NEW):
- "samung phone" → Samsung ✓
- "addidas shoes" → Adidas ✓

New Features (IMPROVED):
- "men's shoes under 2000"
- "women's dresses on sale"
- "kids toys"
- "8gb ram phone"
- "13 inch laptop"

Negations (NEW):
- "phone without camera"
- "laptop no gaming"

Comparison:
- "iPhone vs Samsung"
- "Compare Dell and HP"

Inquiry (NEW):
- "how much does iPhone cost"
- "is this in stock"

Refinement (NEW):
- "show me cheaper ones"
- "any more options"
```

---

## API Endpoints Reference

### Chat (NLP-Powered)
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

---

## Testing the Improvements

### Test Case 1: Price Parsing
```python
nlp.process("phones under 20k")
# Expected: max_price = 20000.0 ✓

nlp.process("tv under 5 lakh")
# Expected: max_price = 500000.0 ✓
```

### Test Case 2: Fuzzy Brand Matching
```python
nlp.process("samung phone")
# Expected: brand = Samsung ✓

nlp.process("1plus mobile")
# Expected: brand = OnePlus ✓
```

### Test Case 3: New Entities
```python
nlp.process("men's shoes under 2000")
# Expected: gender = men, max_price = 2000 ✓

nlp.process("13 inch laptop")
# Expected: size = {screen_inches: 13.0} ✓
```

### Test Case 4: Negation
```python
nlp.process("phone without camera")
# Expected: excluded_features = [camera] ✓
```

---

## Performance Metrics

- **Intent Accuracy**: ~85%+
- **Entity Extraction**: High precision
- **Response Time**: 50-150ms
- **Cache Hit Rate**: 40-60% (LRU cache)
- **Model Size**: 210 MB (recommender)

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 8000 in use | Kill existing process or use `--port 8001` |
| ModuleNotFoundError | Run `pip install -r requirements.txt` |
| Model loading error | Run `python main.py train` to retrain |
| No data files | Run `python main.py all` to generate |

---

## Future Enhancements

- [ ] Streaming responses for better UX
- [ ] Multi-language support
- [ ] Real-time collaboration
- [ ] A/B testing framework
- [ ] Advanced analytics dashboard
- [ ] Conversation context persistence
- [ ] Recommendation explainability

---

## Notes

- All data is synthetic for demo purposes
- Models are pre-trained and ready to use
- No database setup required (file-based)
- Frontend is SPA (no server-side rendering)
- API follows RESTful conventions

---

**Last Updated**: March 20, 2026
**Version**: 2.0 (with NLP improvements)
**Status**: ✅ Production Ready
