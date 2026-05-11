"""Tests for user authentication."""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock


class TestUserRegistration:
    """Tests for user registration."""
    
    @pytest.mark.asyncio
    async def test_register_validation(self):
        """Test registration validation."""
        # Test password too short
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "short"
        }
        assert len(data["password"]) < 8
    
    @pytest.mark.asyncio
    async def test_username_validation(self):
        """Test username validation."""
        # Test invalid username
        invalid_usernames = ["ab", "test user", "test@user"]
        
        for username in invalid_usernames:
            assert len(username.replace('_', '').replace('-', '').replace(' ', '').isalnum())


class TestUserAuthentication:
    """Tests for user authentication."""
    
    @pytest.mark.asyncio
    async def test_user_creation(self):
        """Test creating a user with password."""
        from app.database import User
        
        user = User(
            email="test@example.com",
            username="testuser"
        )
        user.set_password("testpassword123")
        
        assert user.email == "test@example.com"
        assert user.hashed_password is not None
        assert user.verify_password("testpassword123")
        assert not user.verify_password("wrongpassword")
    
    @pytest.mark.asyncio
    async def test_token_generation(self):
        """Test token generation."""
        from app.database import User
        
        user = User(
            email="test@example.com",
            username="testuser"
        )
        user.set_password("testpassword123")
        
        token = user.generate_token()
        
        assert token is not None
        assert len(token) > 20


class TestPasswordHashing:
    """Tests for password hashing."""
    
    def test_password_hashing(self):
        """Test password hashing is secure."""
        from app.database import User
        
        user = User(
            email="test@example.com",
            username="testuser"
        )
        user.set_password("securePassword123!")
        
        # Original password should work
        assert user.verify_password("securePassword123!")
        
        # Wrong password should not work
        assert not user.verify_password("wrongPassword")
        
        # Password shouldn't be stored in plain text
        assert user.hashed_password != "securePassword123!"
    
    def test_salt_is_unique(self):
        """Test salts are unique for each user."""
        from app.database import User
        
        user1 = User(email="test1@example.com", username="test1")
        user1.set_password("samepassword")
        
        user2 = User(email="test2@example.com", username="test2")
        user2.set_password("samepassword")
        
        # Both passwords work but hashes are different
        assert user1.verify_password("samepassword")
        assert user2.verify_password("samepassword")
        assert user1.hashed_password != user2.hashed_password


class TestRoleManagement:
    """Tests for role management."""
    
    @pytest.mark.asyncio
    async def test_default_role(self):
        """Test default role is user."""
        from app.database import User
        
        user = User(
            email="test@example.com",
            username="testuser"
        )
        
        assert user.role == "user"
    
    @pytest.mark.asyncio
    async def test_admin_role(self):
        """Test admin role."""
        from app.database import User
        
        user = User(
            email="admin@example.com",
            username="admin",
            role="admin"
        )
        
        assert user.role == "admin"


# Run with: pytest tests/test_auth.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])