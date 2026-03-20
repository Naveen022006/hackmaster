"""
Dataset Generator for Personal Shopping Agent.
Generates realistic users, products, and interaction data.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import random
from typing import List, Dict, Tuple
import sys
sys.path.append(str(__file__).rsplit('/', 2)[0])

from utils.config import (
    DATASET_CONFIG, CATEGORIES, LOCATIONS,
    ACTION_WEIGHTS, DATA_DIR
)


class DatasetGenerator:
    """Generates synthetic but realistic e-commerce datasets."""

    def __init__(self, seed: int = None):
        self.seed = seed or DATASET_CONFIG["random_seed"]
        np.random.seed(self.seed)
        random.seed(self.seed)

        # Product templates for realistic names
        self.product_templates = self._create_product_templates()

    def _create_product_templates(self) -> Dict[str, List[str]]:
        """Create product name templates for each category."""
        return {
            "Electronics": [
                "{brand} Smartphone {adj} {num}GB",
                "{brand} Laptop {adj} Series {num}\"",
                "{brand} Wireless Earbuds {adj}",
                "{brand} Smart TV {num}\" {adj}",
                "{brand} Tablet {adj} {num}GB",
                "{brand} Smartwatch {adj} Edition",
                "{brand} Bluetooth Speaker {adj}",
                "{brand} Power Bank {num}mAh",
                "{brand} Gaming Console {adj}",
                "{brand} Camera {adj} {num}MP"
            ],
            "Clothing": [
                "{brand} {adj} T-Shirt",
                "{brand} {adj} Jeans",
                "{brand} {adj} Sneakers",
                "{brand} {adj} Jacket",
                "{brand} {adj} Dress",
                "{brand} {adj} Shorts",
                "{brand} {adj} Hoodie",
                "{brand} {adj} Polo Shirt",
                "{brand} {adj} Formal Shirt",
                "{brand} {adj} Track Pants"
            ],
            "Home & Kitchen": [
                "{brand} {adj} Mixer Grinder",
                "{brand} {adj} Air Fryer",
                "{brand} {adj} Microwave Oven",
                "{brand} {adj} Refrigerator {num}L",
                "{brand} {adj} Washing Machine {num}kg",
                "{brand} {adj} Vacuum Cleaner",
                "{brand} {adj} Water Purifier",
                "{brand} {adj} Induction Cooktop",
                "{brand} {adj} Pressure Cooker {num}L",
                "{brand} {adj} Electric Kettle"
            ],
            "Books": [
                "The {adj} Journey by {brand}",
                "{adj} Programming Guide",
                "Learn {adj} in 30 Days",
                "The Art of {adj} Living",
                "{adj} Science Fiction Novel",
                "History of {adj} Civilizations",
                "{adj} Mystery Thriller",
                "Complete {adj} Reference",
                "{adj} Self Help Guide",
                "Stories of {adj} Adventures"
            ],
            "Beauty": [
                "{brand} {adj} Face Cream",
                "{brand} {adj} Lipstick Set",
                "{brand} {adj} Shampoo {num}ml",
                "{brand} {adj} Perfume {num}ml",
                "{brand} {adj} Sunscreen SPF{num}",
                "{brand} {adj} Hair Oil {num}ml",
                "{brand} {adj} Face Wash",
                "{brand} {adj} Body Lotion",
                "{brand} {adj} Makeup Kit",
                "{brand} {adj} Serum"
            ],
            "Sports": [
                "{brand} {adj} Running Shoes",
                "{brand} {adj} Football",
                "{brand} {adj} Cricket Bat",
                "{brand} {adj} Yoga Mat",
                "{brand} {adj} Dumbbell Set {num}kg",
                "{brand} {adj} Badminton Racket",
                "{brand} {adj} Tennis Racket",
                "{brand} {adj} Fitness Band",
                "{brand} {adj} Swimming Goggles",
                "{brand} {adj} Cycling Helmet"
            ],
            "Toys": [
                "{brand} {adj} Building Blocks Set",
                "{brand} {adj} Remote Control Car",
                "{brand} {adj} Board Game",
                "{brand} {adj} Puzzle {num} Pieces",
                "{brand} {adj} Action Figure",
                "{brand} {adj} Doll House",
                "{brand} {adj} Educational Kit",
                "{brand} {adj} Art Set",
                "{brand} {adj} Musical Toy",
                "{brand} {adj} Outdoor Play Set"
            ],
            "Grocery": [
                "{brand} {adj} Tea {num}g",
                "{brand} {adj} Coffee {num}g",
                "{brand} {adj} Biscuits Pack",
                "{brand} {adj} Cooking Oil {num}L",
                "{brand} {adj} Rice {num}kg",
                "{brand} {adj} Flour {num}kg",
                "{brand} {adj} Spices Combo",
                "{brand} {adj} Honey {num}g",
                "{brand} {adj} Cereal {num}g",
                "{brand} {adj} Chocolate Pack"
            ]
        }

    def _get_adjectives(self) -> List[str]:
        """Get list of product adjectives."""
        return [
            "Premium", "Pro", "Elite", "Classic", "Ultra", "Max",
            "Lite", "Plus", "Essential", "Advanced", "Smart", "Neo",
            "Eco", "Royal", "Gold", "Silver", "Deluxe", "Basic"
        ]

    def _generate_description(self, name: str, category: str, brand: str, price: float) -> str:
        """Generate realistic product description."""
        descriptions = {
            "Electronics": [
                f"Experience cutting-edge technology with {name}. Features latest innovations from {brand}.",
                f"{name} - Perfect blend of style and performance. High-quality build with premium features.",
                f"Upgrade your tech life with {name} by {brand}. Engineered for excellence.",
            ],
            "Clothing": [
                f"Step out in style with {name}. Made with premium quality fabric by {brand}.",
                f"{name} - Comfort meets fashion. Perfect for any occasion.",
                f"Express yourself with {name} from {brand}. Trendy design, lasting comfort.",
            ],
            "Home & Kitchen": [
                f"Transform your kitchen with {name}. Reliable performance by {brand}.",
                f"{name} - Making your daily chores effortless. Energy efficient and durable.",
                f"Bring home {name} by {brand}. Built for modern households.",
            ],
            "Books": [
                f"Dive into {name}. An enriching read published by {brand}.",
                f"{name} - A must-read for every book lover. Thought-provoking content.",
                f"Expand your horizons with {name}. Available from {brand} publications.",
            ],
            "Beauty": [
                f"Enhance your beauty routine with {name} by {brand}. Dermatologically tested.",
                f"{name} - Your secret to radiant skin. Premium formulation by {brand}.",
                f"Discover the magic of {name}. Trusted skincare from {brand}.",
            ],
            "Sports": [
                f"Elevate your game with {name} by {brand}. Professional grade quality.",
                f"{name} - Engineered for athletes. Durable and high-performance.",
                f"Train like a pro with {name}. Premium sports gear from {brand}.",
            ],
            "Toys": [
                f"Spark imagination with {name} from {brand}. Safe and educational.",
                f"{name} - Fun for all ages. Quality entertainment by {brand}.",
                f"Create happy memories with {name}. Trusted toy from {brand}.",
            ],
            "Grocery": [
                f"Pure and natural {name} by {brand}. Quality you can trust.",
                f"{name} - Goodness in every bite. Premium selection from {brand}.",
                f"Healthy living starts with {name}. Fresh quality from {brand}.",
            ]
        }

        base_desc = random.choice(descriptions.get(category, descriptions["Electronics"]))
        price_tier = "budget-friendly" if price < 1000 else "mid-range" if price < 5000 else "premium"
        return f"{base_desc} This {price_tier} product offers great value for money."

    def generate_users(self, num_users: int = None) -> pd.DataFrame:
        """Generate user dataset with realistic demographics."""
        num_users = num_users or DATASET_CONFIG["num_users"]

        users = []
        for i in range(1, num_users + 1):
            # Age distribution - skewed towards 20-40 (typical e-commerce users)
            age = int(np.random.beta(2, 5) * 60 + 18)
            age = min(max(age, 18), 70)

            # Gender with slight variation
            gender = np.random.choice(["Male", "Female", "Other"], p=[0.48, 0.48, 0.04])

            # Location weighted by population
            location = random.choice(LOCATIONS)

            # User preferences
            num_pref_categories = np.random.randint(1, 4)
            pref_categories = random.sample(list(CATEGORIES.keys()), num_pref_categories)

            # Preferred brands from selected categories
            pref_brands = []
            for cat in pref_categories:
                pref_brands.extend(random.sample(CATEGORIES[cat], min(2, len(CATEGORIES[cat]))))

            # Price range based on age/spending power
            base_price = 500 + (age - 18) * 100
            price_min = max(100, base_price + np.random.randint(-500, 500))
            price_max = price_min + np.random.randint(5000, 50000)

            preferences = {
                "categories": pref_categories,
                "brands": pref_brands[:5],
                "price_range": {"min": int(price_min), "max": int(price_max)}
            }

            users.append({
                "user_id": f"U{i:05d}",
                "age": age,
                "gender": gender,
                "location": location,
                "preferences": json.dumps(preferences)
            })

        df = pd.DataFrame(users)

        # Add some missing values for realism (about 2%)
        missing_mask = np.random.random(len(df)) < 0.02
        df.loc[missing_mask, "age"] = np.nan

        return df

    def generate_products(self, num_products: int = None) -> pd.DataFrame:
        """Generate product dataset with realistic attributes."""
        num_products = num_products or DATASET_CONFIG["num_products"]

        adjectives = self._get_adjectives()
        products = []

        for i in range(1, num_products + 1):
            category = random.choice(list(CATEGORIES.keys()))
            brand = random.choice(CATEGORIES[category])

            # Generate product name
            template = random.choice(self.product_templates[category])
            name = template.format(
                brand=brand,
                adj=random.choice(adjectives),
                num=random.choice([8, 16, 32, 64, 128, 256, 500, 750, 1000, 50, 55, 65])
            )

            # Price varies by category
            price_ranges = {
                "Electronics": (999, 150000),
                "Clothing": (299, 15000),
                "Home & Kitchen": (499, 75000),
                "Books": (99, 2500),
                "Beauty": (149, 5000),
                "Sports": (199, 25000),
                "Toys": (149, 10000),
                "Grocery": (29, 2000)
            }

            price_min, price_max = price_ranges[category]
            # Log-normal distribution for more realistic prices
            price = np.exp(np.random.uniform(np.log(price_min), np.log(price_max)))
            price = round(price, -1)  # Round to nearest 10

            # Rating with realistic distribution (skewed towards 3.5-4.5)
            rating = min(5.0, max(1.0, np.random.normal(3.8, 0.7)))
            rating = round(rating, 1)

            description = self._generate_description(name, category, brand, price)

            products.append({
                "product_id": f"P{i:05d}",
                "name": name,
                "category": category,
                "brand": brand,
                "price": price,
                "rating": rating,
                "description": description
            })

        df = pd.DataFrame(products)

        # Add some missing ratings (about 5% - new products without reviews)
        missing_mask = np.random.random(len(df)) < 0.05
        df.loc[missing_mask, "rating"] = np.nan

        return df

    def generate_interactions(
        self,
        users_df: pd.DataFrame,
        products_df: pd.DataFrame,
        num_interactions: int = None
    ) -> pd.DataFrame:
        """Generate realistic user-product interaction data."""
        num_interactions = num_interactions or DATASET_CONFIG["num_interactions"]

        user_ids = users_df["user_id"].tolist()
        product_ids = products_df["product_id"].tolist()

        # Create product lookup for category matching
        product_lookup = products_df.set_index("product_id")[["category", "brand", "price"]].to_dict("index")

        # Parse user preferences
        user_prefs = {}
        for _, row in users_df.iterrows():
            try:
                prefs = json.loads(row["preferences"])
                user_prefs[row["user_id"]] = prefs
            except:
                user_prefs[row["user_id"]] = {"categories": [], "brands": [], "price_range": {"min": 0, "max": 100000}}

        interactions = []
        action_types = list(ACTION_WEIGHTS.keys())
        action_probs = list(ACTION_WEIGHTS.values())

        # Generate time range for interactions (last 6 months)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)

        for _ in range(num_interactions):
            user_id = random.choice(user_ids)
            user_pref = user_prefs.get(user_id, {})

            # Bias product selection towards user preferences (70% match, 30% random)
            if random.random() < 0.7 and user_pref.get("categories"):
                # Filter products matching user preferences
                pref_categories = user_pref.get("categories", [])
                pref_brands = user_pref.get("brands", [])
                price_range = user_pref.get("price_range", {"min": 0, "max": 100000})

                matching_products = [
                    pid for pid in product_ids
                    if product_lookup[pid]["category"] in pref_categories
                    or product_lookup[pid]["brand"] in pref_brands
                ]

                if matching_products:
                    product_id = random.choice(matching_products)
                else:
                    product_id = random.choice(product_ids)
            else:
                product_id = random.choice(product_ids)

            # Action type
            action = np.random.choice(action_types, p=action_probs)

            # Rating only for purchases and some add_to_cart (post-purchase review)
            rating = None
            if action == "purchase" and random.random() < 0.6:
                rating = round(min(5.0, max(1.0, np.random.normal(4.0, 0.8))), 1)

            # Random timestamp with recency bias (more recent interactions more likely)
            days_ago = int(np.random.exponential(30))
            days_ago = min(days_ago, 180)
            timestamp = end_date - timedelta(
                days=days_ago,
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )

            interactions.append({
                "user_id": user_id,
                "product_id": product_id,
                "action": action,
                "rating": rating,
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S")
            })

        df = pd.DataFrame(interactions)

        # Sort by timestamp
        df = df.sort_values("timestamp").reset_index(drop=True)

        return df

    def generate_all_datasets(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Generate all datasets and save to files."""
        print("Generating users dataset...")
        users_df = self.generate_users()

        print("Generating products dataset...")
        products_df = self.generate_products()

        print("Generating interactions dataset...")
        interactions_df = self.generate_interactions(users_df, products_df)

        # Save to CSV
        users_df.to_csv(DATA_DIR / "users.csv", index=False)
        products_df.to_csv(DATA_DIR / "products.csv", index=False)
        interactions_df.to_csv(DATA_DIR / "interactions.csv", index=False)

        print(f"\nDatasets saved to {DATA_DIR}")
        print(f"Users: {len(users_df)} rows")
        print(f"Products: {len(products_df)} rows")
        print(f"Interactions: {len(interactions_df)} rows")

        return users_df, products_df, interactions_df


if __name__ == "__main__":
    generator = DatasetGenerator()
    users, products, interactions = generator.generate_all_datasets()

    print("\n--- Sample Users ---")
    print(users.head())

    print("\n--- Sample Products ---")
    print(products.head())

    print("\n--- Sample Interactions ---")
    print(interactions.head())

    print("\n--- Dataset Statistics ---")
    print(f"Unique users with interactions: {interactions['user_id'].nunique()}")
    print(f"Unique products with interactions: {interactions['product_id'].nunique()}")
    print(f"Action distribution:\n{interactions['action'].value_counts()}")
