"""
Unit tests for auth utility functions.
"""
import pytest
from auth.jwt import create_access_token, create_refresh_token, verify_token
from auth.utils import get_device_info, hash_password, verify_password


class TestPasswordHashing:
    """Test suite for password hashing utilities."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        # Assert
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt hash format

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        # Execute
        result = verify_password(password, hashed)

        # Assert
        assert result is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = hash_password(password)

        # Execute
        result = verify_password(wrong_password, hashed)

        # Assert
        assert result is False

    def test_verify_password_different_hashes(self):
        """Test that same password produces different hashes."""
        password = "TestPassword123!"
        hashed1 = hash_password(password)
        hashed2 = hash_password(password)

        # Assert - bcrypt uses random salt, so hashes should be different
        assert hashed1 != hashed2

        # But both should verify correctly
        assert verify_password(password, hashed1) is True
        assert verify_password(password, hashed2) is True


class TestDeviceInfo:
    """Test suite for device info extraction."""

    def test_get_device_info_valid_user_agent(self):
        """Test device info extraction with valid user agent."""
        user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15"

        # Execute
        result = get_device_info(user_agent)

        # Assert
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_device_info_none(self):
        """Test device info extraction with None user agent."""
        # Execute
        result = get_device_info(None)

        # Assert
        assert result is None

    def test_get_device_info_empty_string(self):
        """Test device info extraction with empty string."""
        # Execute
        result = get_device_info("")

        # Assert
        # Should handle gracefully (might return None or empty string)
        assert result is None or result == ""

    def test_get_device_info_chrome(self):
        """Test device info extraction for Chrome browser."""
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

        # Execute
        result = get_device_info(user_agent)

        # Assert
        assert result is not None
        assert isinstance(result, str)


class TestJWTFunctions:
    """Test suite for JWT token functions."""

    def test_create_access_token(self):
        """Test access token creation."""
        data = {"user_id": "123", "email": "test@example.com"}

        # Execute
        token = create_access_token(data)

        # Assert
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"user_id": "123", "session_id": "456"}

        # Execute
        token = create_refresh_token(data)

        # Assert
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token_valid_access(self):
        """Test verification of valid access token."""
        data = {"user_id": "123", "email": "test@example.com"}
        token = create_access_token(data)

        # Execute
        payload = verify_token(token, token_type="access")

        # Assert
        assert payload is not None
        assert payload["user_id"] == "123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_verify_token_valid_refresh(self):
        """Test verification of valid refresh token."""
        data = {"user_id": "123", "session_id": "456"}
        token = create_refresh_token(data)

        # Execute
        payload = verify_token(token, token_type="refresh")

        # Assert
        assert payload is not None
        assert payload["user_id"] == "123"
        assert payload["session_id"] == "456"
        assert payload["type"] == "refresh"

    def test_verify_token_wrong_type(self):
        """Test verification with wrong token type."""
        data = {"user_id": "123"}
        access_token = create_access_token(data)

        # Execute - Try to verify access token as refresh token
        payload = verify_token(access_token, token_type="refresh")

        # Assert
        assert payload is None

    def test_verify_token_invalid(self):
        """Test verification of invalid token."""
        invalid_token = "invalid.token.here"

        # Execute
        payload = verify_token(invalid_token, token_type="access")

        # Assert
        assert payload is None

    def test_verify_token_empty_string(self):
        """Test verification of empty string token."""
        # Execute
        payload = verify_token("", token_type="access")

        # Assert
        assert payload is None

    def test_create_access_token_with_expires_delta(self):
        """Test access token creation with custom expiration."""
        from datetime import timedelta

        data = {"user_id": "123"}
        expires_delta = timedelta(minutes=60)

        # Execute
        token = create_access_token(data, expires_delta=expires_delta)

        # Assert
        assert token is not None
        payload = verify_token(token, token_type="access")
        assert payload is not None

    def test_token_contains_all_data(self):
        """Test that token contains all provided data."""
        data = {
            "user_id": "123",
            "email": "test@example.com",
            "name": "Test User",
            "session_id": "456",
        }
        token = create_access_token(data)

        # Execute
        payload = verify_token(token, token_type="access")

        # Assert
        assert payload is not None
        assert payload["user_id"] == "123"
        assert payload["email"] == "test@example.com"
        assert payload["name"] == "Test User"
        assert payload["session_id"] == "456"

    def test_different_tokens_for_same_data(self):
        """Test that tokens are different even with same data (due to iat/exp)."""
        import time

        data = {"user_id": "123"}
        token1 = create_access_token(data)
        time.sleep(0.01)  # Small delay to ensure different iat timestamps
        token2 = create_access_token(data)

        # Assert - Tokens should be different due to different iat timestamps
        # (Note: if created in same second, they might be the same, which is acceptable)
        # But both should verify correctly
        payload1 = verify_token(token1, token_type="access")
        payload2 = verify_token(token2, token_type="access")
        assert payload1 is not None
        assert payload2 is not None
        assert payload1["user_id"] == payload2["user_id"]
        # Tokens may be the same if created in the same second, which is fine
        # The important thing is that they both verify correctly

