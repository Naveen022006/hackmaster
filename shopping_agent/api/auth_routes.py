"""
Authentication API Routes for Personal Shopping Agent.
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth import (
    get_auth_service, AuthService,
    UserCreate, UserLogin, AdminCreate, Token
)
from services.database import get_database


# Router
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Security
security = HTTPBearer(auto_error=False)


# Request/Response Models
class RegisterRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)
    phone: Optional[str] = None
    location: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminRegisterRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    role: str = Field(default="admin")


class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
    phone: Optional[str] = None
    location: Optional[str] = None
    role: str = "user"
    is_admin: bool = False


class MessageResponse(BaseModel):
    message: str
    success: bool = True


# Dependency to get current user from token
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[Dict]:
    """Extract and validate user from JWT token."""
    if not credentials:
        return None

    user = auth_service.get_current_user(credentials.credentials)
    return user


async def require_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict:
    """Require authenticated user."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = auth_service.get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user


async def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict:
    """Require authenticated admin."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = auth_service.get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    return user


# User Registration
@router.post("/register", response_model=Token)
async def register_user(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user account.

    Returns an access token upon successful registration.
    """
    try:
        user_data = UserCreate(
            email=request.email,
            name=request.name,
            password=request.password,
            phone=request.phone,
            location=request.location
        )
        auth_service.register_user(user_data)

        # Auto-login after registration
        login_data = UserLogin(email=request.email, password=request.password)
        token = auth_service.login_user(login_data)

        return token

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


# User Login
@router.post("/login", response_model=Token)
async def login_user(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user and return access token.
    """
    try:
        login_data = UserLogin(email=request.email, password=request.password)
        token = auth_service.login_user(login_data)
        return token

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


# Admin Login
@router.post("/admin/login", response_model=Token)
async def login_admin(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate admin and return access token.
    """
    try:
        login_data = UserLogin(email=request.email, password=request.password)
        token = auth_service.login_admin(login_data)
        return token

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Admin login failed: {str(e)}")


# Admin Registration (requires existing admin)
@router.post("/admin/register", response_model=MessageResponse)
async def register_admin(
    request: AdminRegisterRequest,
    current_admin: Dict = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new admin account.

    Requires authentication as an existing admin.
    """
    # Only superadmin can create other admins
    if current_admin.get("role") != "superadmin":
        raise HTTPException(
            status_code=403,
            detail="Only superadmin can create new admins"
        )

    try:
        admin_data = AdminCreate(
            email=request.email,
            name=request.name,
            password=request.password,
            role=request.role
        )
        auth_service.register_admin(admin_data, created_by=current_admin.get("email"))

        return MessageResponse(message=f"Admin {request.email} created successfully")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Admin registration failed: {str(e)}")


# Get Current User
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Dict = Depends(require_user)):
    """
    Get current authenticated user's profile.
    """
    return UserResponse(
        user_id=current_user.get("user_id", ""),
        email=current_user["email"],
        name=current_user["name"],
        role=current_user.get("role", "user"),
        is_admin=current_user.get("is_admin", False)
    )


# Validate Token
@router.get("/validate")
async def validate_token(current_user: Dict = Depends(get_current_user)):
    """
    Validate current token and return user info.
    """
    if not current_user:
        return {"valid": False, "user": None}

    return {
        "valid": True,
        "user": {
            "user_id": current_user.get("user_id"),
            "email": current_user.get("email"),
            "name": current_user.get("name"),
            "role": current_user.get("role"),
            "is_admin": current_user.get("is_admin", False)
        }
    }


# Logout (client-side token removal, but we can log it)
@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: Dict = Depends(require_user)):
    """
    Logout current user.

    Note: Since JWT is stateless, the client should remove the token.
    This endpoint is for logging/auditing purposes.
    """
    return MessageResponse(message="Logged out successfully")
