"""
Authentication Service for Personal Shopping Agent.
Handles JWT tokens, password hashing, and user authentication.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import bcrypt
from pydantic import BaseModel, EmailStr, Field
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import JWT_CONFIG
from services.database import get_database


# Pydantic Models for Authentication
class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)


class UserCreate(UserBase):
    """User registration model."""
    password: str = Field(..., min_length=6, max_length=100)
    phone: Optional[str] = None
    location: Optional[str] = None


class UserLogin(BaseModel):
    """User login model."""
    email: EmailStr
    password: str


class AdminCreate(UserBase):
    """Admin registration model."""
    password: str = Field(..., min_length=8, max_length=100)
    role: str = Field(default="admin", pattern="^(admin|superadmin)$")


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]


class TokenData(BaseModel):
    """Token payload data."""
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_admin: bool = False


class AuthService:
    """Authentication service for users and admins."""

    def __init__(self):
        self.db = get_database()

    # Password Operations
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False

    # Token Operations
    @staticmethod
    def create_access_token(data: Dict, expires_delta: timedelta = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=JWT_CONFIG["access_token_expire_minutes"])

        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(
            to_encode,
            JWT_CONFIG["secret_key"],
            algorithm=JWT_CONFIG["algorithm"]
        )
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> Optional[TokenData]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(
                token,
                JWT_CONFIG["secret_key"],
                algorithms=[JWT_CONFIG["algorithm"]]
            )
            return TokenData(
                user_id=payload.get("user_id"),
                email=payload.get("email"),
                role=payload.get("role"),
                is_admin=payload.get("is_admin", False)
            )
        except JWTError:
            return None

    # User Registration
    def register_user(self, user_data: UserCreate) -> Dict:
        """Register a new user."""
        # Check if email already exists
        existing = self.db.get_user_by_email(user_data.email)
        if existing:
            raise ValueError("Email already registered")

        # Generate user_id
        user_count = self.db.get_user_count()
        user_id = f"U{user_count + 1:05d}"

        # Create user document
        user_doc = {
            "user_id": user_id,
            "email": user_data.email.lower(),
            "name": user_data.name,
            "phone": user_data.phone,
            "location": user_data.location,
            "password_hash": self.hash_password(user_data.password),
            "preferences": {
                "categories": [],
                "brands": [],
                "price_range": {"min": 0, "max": 100000}
            }
        }

        result = self.db.create_user(user_doc)

        # Return user without password
        return {
            "user_id": result["user_id"],
            "email": result["email"],
            "name": result["name"],
            "phone": result.get("phone"),
            "location": result.get("location"),
            "created_at": result["created_at"].isoformat() if result.get("created_at") else None
        }

    # User Login
    def login_user(self, login_data: UserLogin) -> Token:
        """Authenticate a user and return token."""
        user = self.db.get_user_by_email(login_data.email)

        if not user:
            raise ValueError("Invalid email or password")

        if not self.verify_password(login_data.password, user.get("password_hash", "")):
            raise ValueError("Invalid email or password")

        if not user.get("is_active", True):
            raise ValueError("Account is deactivated")

        # Create token
        token_data = {
            "user_id": user["user_id"],
            "email": user["email"],
            "role": "user",
            "is_admin": False
        }

        access_token = self.create_access_token(token_data)

        # Update last login
        self.db.update_user(user["user_id"], {"last_login": datetime.utcnow()})

        return Token(
            access_token=access_token,
            expires_in=JWT_CONFIG["access_token_expire_minutes"] * 60,
            user={
                "user_id": user["user_id"],
                "email": user["email"],
                "name": user["name"],
                "role": "user"
            }
        )

    # Admin Registration
    def register_admin(self, admin_data: AdminCreate, created_by: str = None) -> Dict:
        """Register a new admin."""
        # Check if email already exists
        existing = self.db.get_admin_by_email(admin_data.email)
        if existing:
            raise ValueError("Admin email already registered")

        # Create admin document
        admin_doc = {
            "email": admin_data.email.lower(),
            "name": admin_data.name,
            "password_hash": self.hash_password(admin_data.password),
            "role": admin_data.role,
            "created_by": created_by
        }

        result = self.db.create_admin(admin_doc)

        return {
            "email": result["email"],
            "name": result["name"],
            "role": result["role"],
            "created_at": result["created_at"].isoformat() if result.get("created_at") else None
        }

    # Admin Login
    def login_admin(self, login_data: UserLogin) -> Token:
        """Authenticate an admin and return token."""
        admin = self.db.get_admin_by_email(login_data.email)

        if not admin:
            raise ValueError("Invalid email or password")

        if not self.verify_password(login_data.password, admin.get("password_hash", "")):
            raise ValueError("Invalid email or password")

        if not admin.get("is_active", True):
            raise ValueError("Admin account is deactivated")

        # Create token
        token_data = {
            "user_id": str(admin["_id"]),
            "email": admin["email"],
            "role": admin.get("role", "admin"),
            "is_admin": True
        }

        access_token = self.create_access_token(token_data)

        # Update last login
        self.db.admins.update_one(
            {"email": admin["email"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )

        return Token(
            access_token=access_token,
            expires_in=JWT_CONFIG["access_token_expire_minutes"] * 60,
            user={
                "email": admin["email"],
                "name": admin["name"],
                "role": admin.get("role", "admin"),
                "is_admin": True
            }
        )

    # Token Validation
    def get_current_user(self, token: str) -> Optional[Dict]:
        """Get current user from token."""
        token_data = self.decode_token(token)
        if not token_data:
            return None

        if token_data.is_admin:
            admin = self.db.get_admin_by_email(token_data.email)
            if admin:
                return {
                    "email": admin["email"],
                    "name": admin["name"],
                    "role": admin.get("role", "admin"),
                    "is_admin": True
                }
        else:
            user = self.db.get_user_by_id(token_data.user_id)
            if user:
                return {
                    "user_id": user["user_id"],
                    "email": user["email"],
                    "name": user["name"],
                    "role": "user",
                    "is_admin": False
                }

        return None

    # Initialize Default Admin
    def create_default_admin(self):
        """Create a default admin if none exists."""
        admins = self.db.get_all_admins()
        if not admins:
            try:
                self.register_admin(AdminCreate(
                    email="admin@shopai.com",
                    name="System Admin",
                    password="admin123456",
                    role="superadmin"
                ))
                print("Default admin created: admin@shopai.com / admin123456")
            except ValueError:
                pass  # Admin already exists


# Singleton instance
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get or create singleton auth service."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


if __name__ == "__main__":
    # Test authentication service
    auth = get_auth_service()

    # Create default admin
    auth.create_default_admin()

    # Test admin login
    try:
        token = auth.login_admin(UserLogin(
            email="admin@shopai.com",
            password="admin123456"
        ))
        print(f"\nAdmin login successful!")
        print(f"Token: {token.access_token[:50]}...")
        print(f"User: {token.user}")
    except ValueError as e:
        print(f"Login failed: {e}")
