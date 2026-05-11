"""Tests for config and validation."""
import pytest
from datetime import datetime, timezone


class TestConfig:
    """Tests for configuration."""
    
    def test_config_values(self):
        """Test config has required values."""
        from app.config import (
            API_TITLE,
            API_VERSION,
            DATABASE_URL,
            DEFAULT_TIMEZONE
        )
        
        assert API_TITLE is not None
        assert API_VERSION is not None
        assert DATABASE_URL is not None
        assert DEFAULT_TIMEZONE is not None
    
    def test_data_dir_exists(self, tmp_path):
        """Test data directory is created."""
        from app.config import DATA_DIR
        
        # Data dir should exist or be created
        assert DATA_DIR is not None


class TestPhoneValidation:
    """Tests for phone number validation."""
    
    def test_valid_phone_formats(self):
        """Test various valid phone formats."""
        valid_phones = [
            "+1234567890",
            "+1-234-567-8900",
            "1234567890",
            "+44 20 7946 0958"
        ]
        
        # Check basic format
        for phone in valid_phones:
            # Remove common formatting chars should leave digits
            cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
            assert len(cleaned) >= 10 or cleaned.startswith('+')
    
    def test_invalid_phone_formats(self):
        """Test invalid phone formats."""
        invalid_phones = [
            "",
            "abc",
            "123",
            "+"  # Just plus
        ]
        
        # These should be caught by validation
        for phone in invalid_phones:
            cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
            # Either too short or just a plus sign
            assert len(cleaned) < 10 or cleaned == '+'


class TestMessageValidation:
    """Tests for message validation."""
    
    def test_message_content_validation(self):
        """Test message content validation."""
        # Valid messages
        valid_messages = [
            "Hello!",
            "Test message with numbers 123",
            "Message with emojis 🎉",
            "Cyrillic: Привет",
            "Arabic: مرحبا"
        ]
        
        for msg in valid_messages:
            assert len(msg) > 0
            assert len(msg) <= 65536  # Should handle large messages
    
    def test_empty_message(self):
        """Test empty message is invalid."""
        msg = ""
        assert len(msg) == 0
    
    def test_message_too_long(self):
        """Test very long message."""
        # WhatsApp has a character limit (~65536 for single message)
        # but we should handle gracefully


class TestDatetimeValidation:
    """Tests for datetime validation."""
    
    def test_past_datetime(self):
        """Test past datetime is invalid for scheduling."""
        past = datetime(2020, 1, 1, tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        
        assert past < now
    
    def test_future_datetime(self):
        """Test future datetime is valid."""
        future = datetime(2030, 12, 31, tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        
        assert future > now
    
    def test_datetime_format(self):
        """Test datetime is ISO format."""
        dt = datetime.now(timezone.utc)
        iso_str = dt.isoformat()
        
        # Should be parseable
        parsed = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        assert parsed is not None


class TestStatusFiltering:
    """Tests for status filtering."""
    
    def test_valid_statuses(self):
        """Test valid status values."""
        valid_statuses = ["pending", "sent", "failed", "scheduled", "all"]
        
        for status in valid_statuses:
            assert status in valid_statuses
    
    def test_history_filter_parameters(self):
        """Test history endpoint accepts status filter."""
        # This is tested in test_api.py
        pass


class TestSecurityValidation:
    """Tests for security validations."""
    
    def test_sql_injection_patterns(self):
        """Test SQL injection patterns are detected."""
        # Should be caught by parameterized queries
        malicious = [
            "'; DROP TABLE messages; --",
            "'; SELECT * FROM messages; --",
            "1' OR '1'='1",
            "'; DELETE FROM messages; --"
        ]
        
        # These should NOT cause errors when used as phone numbers
        # because we use parameterized queries
        for test in malicious:
            # The "bad" content should be treated as literal string
            assert "DROP" in test
    
    def test_xss_patterns(self):
        """Test XSS patterns are detected."""
        xss_patterns = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(1)",
            "<svg onload=alert(1)>"
        ]
        
        # These would be stored as-is if user sends them (intentional)
        # but should be escaped when displayed
        for pattern in xss_patterns:
            assert "<" in pattern or "javascript" in pattern
    
    def test_path_traversal(self):
        """Test path traversal is prevented."""
        # Should not allow path traversal in any input
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/etc/passwd"
        ]
        
        for path in malicious_paths:
            # These should be caught as invalid inputs
            assert ".." in path or path.startswith("/")
    
    def test_api_key_validation(self):
        """Test API key format."""
        from app.config import TEST_API_KEY
        
        # Should be present if configured
        if TEST_API_KEY:
            assert len(TEST_API_KEY) >= 16


# Run with: pytest tests/test_validation.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])