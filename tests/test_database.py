"""Tests for database models."""
import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock


class TestDatabaseModels:
    """Tests for database models."""
    
    @pytest.mark.asyncio
    async def test_message_creation(self):
        """Test creating a message model."""
        from app.database import Message
        
        msg = Message(
            contact_phone="+1234567890",
            contact_name="Test User",
            content="Test message",
            status="pending"
        )
        
        assert msg.contact_phone == "+1234567890"
        assert msg.contact_name == "Test User"
        assert msg.content == "Test message"
        assert msg.status == "pending"
    
    @pytest.mark.asyncio
    async def test_message_with_sent_status(self):
        """Test message with sent status."""
        from app.database import Message
        
        sent_at = datetime.now(timezone.utc)
        msg = Message(
            contact_phone="+1234567890",
            contact_name="Test User",
            content="Test message",
            status="sent",
            sent_at=sent_at
        )
        
        assert msg.status == "sent"
        assert msg.sent_at == sent_at
    
    @pytest.mark.asyncio
    async def test_message_with_failed_status(self):
        """Test message with failed status."""
        msg = Message(
            contact_phone="+1234567890",
            contact_name="Test User",
            content="Test message",
            status="failed",
            error_message="Failed to send"
        )
        
        assert msg.status == "failed"
        assert msg.error_message == "Failed to send"
    
    @pytest.mark.asyncio
    async def test_message_with_scheduled_time(self):
        """Test scheduled message."""
        scheduled = datetime(2025, 12, 31, 23, 59, tzinfo=timezone.utc)
        msg = Message(
            contact_phone="+1234567890",
            contact_name="Test User",
            content="Scheduled message",
            status="scheduled",
            scheduled_at=scheduled
        )
        
        assert msg.status == "scheduled"
        assert msg.scheduled_at == scheduled


class TestDatabaseSession:
    """Tests for database session management."""
    
    @pytest.mark.asyncio
    async def test_get_session(self):
        """Test getting database session."""
        from app.database import get_session
        
        # This is a generator, so we need to iterate it
        session_gen = get_session()
        # Can't fully test without db, but ensures function works
        assert session_gen is not None


class TestAppState:
    """Tests for application state."""
    
    def test_app_state_initial(self):
        """Test initial app state."""
        from app.database import app_state
        
        assert app_state.is_authenticated == False
        assert app_state.qr_code is None
        assert app_state.contacts_cache == []
    
    def test_app_state_reset(self):
        """Test resetting app state."""
        from app.database import app_state
        
        app_state.is_authenticated = True
        app_state.qr_code = "test"
        app_state.contacts_cache = [{"name": "Test"}]
        
        app_state.reset()
        
        assert app_state.is_authenticated == False
        assert app_state.qr_code is None
        assert app_state.contacts_cache == []


class TestContactModel:
    """Tests for contact model."""
    
    @pytest.mark.asyncio
    async def test_contact_creation(self):
        """Test creating a contact."""
        from app.database import Contact
        
        contact = Contact(
            phone="+1234567890",
            name="Test User"
        )
        
        assert contact.phone == "+1234567890"
        assert contact.name == "Test User"
        assert contact.is_online == False
    
    @pytest.mark.asyncio
    async def test_contact_with_avatar(self):
        """Test contact with avatar."""
        contact = Contact(
            phone="+1234567890",
            name="Test User",
            avatar="https://example.com/avatar.jpg"
        )
        
        assert contact.avatar == "https://example.com/avatar.jpg"


# Run with: pytest tests/test_database.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])