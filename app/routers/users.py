"""User authentication and admin router."""
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import select
from app.database import User, get_session
import secrets


router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# In-memory token storage (in production, use Redis or database)
active_tokens = {}


# Request/Response Models
class RegisterRequest(BaseModel):
    """Registration request."""
    email: EmailStr
    username: str
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, - and _')
        return v


class LoginRequest(BaseModel):
    """Login request."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not v:
            raise ValueError('Password is required')
        return v


class LoginResponse(BaseModel):
    """Login response."""
    success: bool
    token: Optional[str] = None
    user: Optional[dict] = None
    message: str


class UserResponse(BaseModel):
    """User response."""
    id: int
    email: str
    username: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class TokenPayload(BaseModel):
    """JWT-like token payload."""
    user_id: int
    email: str
    username: str
    role: str
    exp: datetime


def verify_token(authorization: Optional[str] = Header(None)) -> User:
    """Verify bearer token and return user."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    if not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    # Look up token
    user_data = active_tokens.get(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user_data


def require_admin(user: User = Depends(verify_token)) -> User:
    """Require admin role."""
    if user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# Routes
@router.post("/register", response_model=LoginResponse)
async def register(request: RegisterRequest):
    """Register a new user."""
    async for session in get_session():
        # Check if email exists
        stmt = select(User).where(User.email == request.email)
        result = await session.execute(stmt)
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Check if username exists
        stmt = select(User).where(User.username == request.username)
        result = await session.execute(stmt)
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Username already taken")
        
        # Create user
        user = User(
            email=request.email,
            username=request.username,
            role="user",
            is_active=True
        )
        user.set_password(request.password)
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        # Generate token
        token = user.generate_token()
        active_tokens[token] = user
        
        return LoginResponse(
            success=True,
            token=token,
            user={
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role
            },
            message="Registration successful"
        )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login and get token."""
    async for session in get_session():
        # Find user by email or username
        if request.email:
            stmt = select(User).where(User.email == request.email)
        elif request.username:
            stmt = select(User).where(User.username == request.username)
        else:
            raise HTTPException(status_code=400, detail="Email or username required")
        
        result = await session.execute(stmt)
        user = result.scalars().first()
        
        if not user or not user.verify_password(request.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is disabled")
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        await session.commit()
        
        # Generate token
        token = user.generate_token()
        active_tokens[token] = user
        
        return LoginResponse(
            success=True,
            token=token,
            user={
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role
            },
            message="Login successful"
        )


@router.post("/logout")
async def logout(user: User = Depends(verify_token)):
    """Logout and invalidate token."""
    # Remove token from active tokens
    for token, u in list(active_tokens.items()):
        if u.id == user.id:
            del active_tokens[token]
    
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(user: User = Depends(verify_token)):
    """Get current user info."""
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login
    )


# Admin routes
@router.get("/admin/users", response_model=List[UserResponse])
async def list_users(
    admin: User = Depends(require_admin),
    limit: int = 50,
    offset: int = 0
):
    """List all users (admin only)."""
    async for session in get_session():
        stmt = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        return [
            UserResponse(
                id=u.id,
                email=u.email,
                username=u.username,
                role=u.role,
                is_active=u.is_active,
                created_at=u.created_at,
                last_login=u.last_login
            )
            for u in users
        ]


@router.post("/admin/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role: str,
    admin: User = Depends(require_admin)
):
    """Update user role (admin only)."""
    if role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    async for session in get_session():
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.role = role
        await session.commit()
        
        return {"success": True, "message": f"User role updated to {role}"}


@router.post("/admin/users/{user_id}/activate")
async def toggle_user_active(
    user_id: int,
    admin: User = Depends(require_admin)
):
    """Activate/deactivate user (admin only)."""
    async for session in get_session():
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.is_active = not user.is_active
        await session.commit()
        
        return {
            "success": True,
            "message": f"User {'activated' if user.is_active else 'deactivated'}"
        }


@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(require_admin)
):
    """Delete user (admin only)."""
    async for session in get_session():
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Can't delete yourself
        if user.id == admin.id:
            raise HTTPException(status_code=400, detail="Cannot delete yourself")
        
        await session.delete(user)
        await session.commit()
        
        return {"success": True, "message": "User deleted"}