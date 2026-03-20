"""
Data Migration Service - Migrate CSV data to MongoDB.
"""
import pandas as pd
from datetime import datetime
from typing import Dict
import sys
sys.path.append(str(__file__).rsplit('/', 2)[0])

from utils.config import DATA_DIR
from services.database import get_database
from services.auth import get_auth_service


def migrate_csv_to_mongodb() -> Dict:
    """Migrate data from CSV files to MongoDB."""
    db = get_database()
    auth = get_auth_service()
    results = {
        "products_migrated": 0,
        "users_migrated": 0,
        "interactions_migrated": 0,
        "errors": []
    }

    # Check if CSV files exist
    products_file = DATA_DIR / "products.csv"
    users_file = DATA_DIR / "users.csv"
    interactions_file = DATA_DIR / "interactions.csv"

    # Migrate Products
    if products_file.exists():
        try:
            print("Migrating products...")
            products_df = pd.read_csv(products_file)

            # Clear existing products
            db.clear_collection("products")

            # Convert to list of dicts
            products = products_df.to_dict("records")

            # Clean data
            for product in products:
                # Handle NaN values
                if pd.isna(product.get("rating")):
                    product["rating"] = None
                if pd.isna(product.get("description")):
                    product["description"] = ""

            count = db.insert_products(products)
            results["products_migrated"] = count
            print(f"  Migrated {count} products")
        except Exception as e:
            results["errors"].append(f"Products: {str(e)}")
            print(f"  Error migrating products: {e}")

    # Migrate Users (create as auth users)
    if users_file.exists():
        try:
            print("Migrating users...")
            users_df = pd.read_csv(users_file)

            # We'll create user accounts with default passwords
            migrated = 0
            for _, row in users_df.iterrows():
                try:
                    # Check if user already exists
                    existing = db.get_user_by_id(row["user_id"])
                    if existing:
                        continue

                    user_doc = {
                        "user_id": row["user_id"],
                        "email": f"{row['user_id'].lower()}@shopai.com",
                        "name": f"User {row['user_id']}",
                        "password_hash": auth.hash_password("password123"),
                        "age": int(row["age"]) if pd.notna(row.get("age")) else None,
                        "gender": row.get("gender"),
                        "location": row.get("location"),
                        "preferences": row.get("preferences") if pd.notna(row.get("preferences")) else "{}",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "is_active": True,
                        "is_migrated": True
                    }
                    db.users.insert_one(user_doc)
                    migrated += 1
                except Exception as e:
                    pass  # Skip duplicates

            results["users_migrated"] = migrated
            print(f"  Migrated {migrated} users")
        except Exception as e:
            results["errors"].append(f"Users: {str(e)}")
            print(f"  Error migrating users: {e}")

    # Migrate Interactions
    if interactions_file.exists():
        try:
            print("Migrating interactions...")
            interactions_df = pd.read_csv(interactions_file)

            # Clear existing interactions
            db.clear_collection("interactions")

            # Convert to list of dicts
            interactions = []
            for _, row in interactions_df.iterrows():
                interaction = {
                    "user_id": row["user_id"],
                    "product_id": row["product_id"],
                    "action": row["action"],
                    "rating": float(row["rating"]) if pd.notna(row.get("rating")) else None,
                    "timestamp": pd.to_datetime(row["timestamp"]) if pd.notna(row.get("timestamp")) else datetime.utcnow()
                }
                interactions.append(interaction)

            count = db.insert_interactions(interactions)
            results["interactions_migrated"] = count
            print(f"  Migrated {count} interactions")
        except Exception as e:
            results["errors"].append(f"Interactions: {str(e)}")
            print(f"  Error migrating interactions: {e}")

    # Create default admin if not exists
    auth.create_default_admin()

    print("\nMigration complete!")
    print(f"  Products: {results['products_migrated']}")
    print(f"  Users: {results['users_migrated']}")
    print(f"  Interactions: {results['interactions_migrated']}")
    if results["errors"]:
        print(f"  Errors: {results['errors']}")

    return results


if __name__ == "__main__":
    results = migrate_csv_to_mongodb()
    print(f"\nResults: {results}")
