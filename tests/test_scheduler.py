"""Tests for message scheduler."""
import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock


class TestMessageScheduler:
    """Tests for message scheduler."""
    
    @pytest.mark.asyncio
    async def test_scheduler_init(self):
        """Test scheduler initialization."""
        from app.scheduler import MessageScheduler
        
        scheduler = MessageScheduler()
        
        assert scheduler._running == False
        assert scheduler._task is None
    
    @pytest.mark.asyncio
    async def test_scheduler_start_stop(self):
        """Test starting and stopping scheduler."""
        from app.scheduler import MessageScheduler
        
        scheduler = MessageScheduler()
        
        # Can't fully test without DB, just ensure methods exist
        assert hasattr(scheduler, 'start')
        assert hasattr(scheduler, 'stop')
        assert hasattr(scheduler, '_run')


class TestSchedulerIntegration:
    """Tests for scheduler integration."""
    
    def test_scheduler_instance(self):
        """Test scheduler instance exists."""
        from app.scheduler import scheduler
        
        assert scheduler is not None
        assert hasattr(scheduler, 'start')
        assert hasattr(scheduler, 'stop')
    
    def test_start_stop_functions(self):
        """Test start/stop functions exist."""
        from app.scheduler import start_scheduler, stop_scheduler
        
        assert start_scheduler is not None
        assert stop_scheduler is not None


class TestMessageStatus:
    """Tests for message status constants."""
    
    def test_status_constants(self):
        """Test status constants are defined."""
        from app.config import (
            MESSAGE_STATUS_PENDING,
            MESSAGE_STATUS_SENT,
            MESSAGE_STATUS_FAILED,
            MESSAGE_STATUS_SCHEDULED
        )
        
        assert MESSAGE_STATUS_PENDING == "pending"
        assert MESSAGE_STATUS_SENT == "sent"
        assert MESSAGE_STATUS_FAILED == "failed"
        assert MESSAGE_STATUS_SCHEDULED == "scheduled"


# Run with: pytest tests/test_scheduler.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])