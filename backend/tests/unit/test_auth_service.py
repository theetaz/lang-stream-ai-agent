"""
Unit tests for AuthService class.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from common.errors import ForbiddenError, NotFoundError, UnauthorizedError, ValidationError

from api.v1.auth.service import AuthService
from models.session import Session
from models.user import User
from tests.conftest import setup_db_count_mock, setup_db_execute_mock


class TestAuthService:
    """Test suite for AuthService."""

    # ============= Registration Tests =============
    @pytest.mark.asyncio
    async def test_register_success(self, mock_db, mock_request, sample_register_data):
        """Test successful user registration."""
        # Setup
        service = AuthService(mock_db)
        setup_db_execute_mock(mock_db, None)  # User doesn't exist

        # Execute
        result = await service.register(
            type("obj", (object,), sample_register_data)(), mock_request
        )

        # Assert
        assert result is not None
        assert hasattr(result, "access_token")
        assert hasattr(result, "refresh_token")
        assert hasattr(result, "user")
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_register_duplicate_email(
        self, mock_db, mock_request, sample_register_data, mock_user
    ):
        """Test registration with duplicate email."""
        # Setup
        service = AuthService(mock_db)
        setup_db_execute_mock(mock_db, mock_user)  # User already exists

        # Execute & Assert
        with pytest.raises(ValidationError) as exc_info:
            await service.register(
                type("obj", (object,), sample_register_data)(), mock_request
            )
        assert "Email already registered" in str(exc_info.value.detail)

    # ============= Login Tests =============
    @pytest.mark.asyncio
    async def test_login_success(self, mock_db, mock_request, mock_user):
        """Test successful login."""
        # Setup
        service = AuthService(mock_db)
        setup_db_execute_mock(mock_db, mock_user)

        login_data = type("obj", (object,), {"email": mock_user.email, "password": "secret"})()

        # Execute
        result = await service.login(login_data, mock_request)

        # Assert
        assert result is not None
        assert hasattr(result, "access_token")
        assert hasattr(result, "refresh_token")
        assert result.user["email"] == mock_user.email

    @pytest.mark.asyncio
    async def test_login_invalid_email(self, mock_db, mock_request):
        """Test login with non-existent email."""
        # Setup
        service = AuthService(mock_db)
        setup_db_execute_mock(mock_db, None)  # User doesn't exist

        login_data = type("obj", (object,), {"email": "nonexistent@example.com", "password": "password"})()

        # Execute & Assert
        with pytest.raises(UnauthorizedError) as exc_info:
            await service.login(login_data, mock_request)
        assert "Invalid email or password" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, mock_db, mock_request, mock_user):
        """Test login with wrong password."""
        # Setup
        service = AuthService(mock_db)
        setup_db_execute_mock(mock_db, mock_user)

        login_data = type("obj", (object,), {"email": mock_user.email, "password": "wrongpassword"})()

        # Execute & Assert
        with pytest.raises(UnauthorizedError) as exc_info:
            await service.login(login_data, mock_request)
        assert "Invalid email or password" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, mock_db, mock_request, mock_inactive_user):
        """Test login with inactive user."""
        # Setup
        service = AuthService(mock_db)
        setup_db_execute_mock(mock_db, mock_inactive_user)

        login_data = type("obj", (object,), {"email": mock_inactive_user.email, "password": "secret"})()

        # Execute & Assert
        with pytest.raises(UnauthorizedError) as exc_info:
            await service.login(login_data, mock_request)
        assert "Account is inactive" in str(exc_info.value.detail)

    # ============= Google OAuth Tests =============
    @pytest.mark.asyncio
    async def test_google_auth_new_user(self, mock_db, mock_request, sample_google_auth_data):
        """Test Google OAuth with new user."""
        # Setup
        service = AuthService(mock_db)
        setup_db_execute_mock(mock_db, None)  # User doesn't exist

        google_data = type("obj", (object,), sample_google_auth_data)()

        # Execute
        result = await service.google_auth(google_data, mock_request)

        # Assert
        assert result is not None
        assert hasattr(result, "access_token")
        assert hasattr(result, "refresh_token")
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_google_auth_existing_user(
        self, mock_db, mock_request, sample_google_auth_data, mock_user
    ):
        """Test Google OAuth with existing user."""
        # Setup
        service = AuthService(mock_db)
        mock_user.google_id = sample_google_auth_data["google_id"]
        setup_db_execute_mock(mock_db, mock_user)

        google_data = type("obj", (object,), sample_google_auth_data)()

        # Execute
        result = await service.google_auth(google_data, mock_request)

        # Assert
        assert result is not None
        assert hasattr(result, "access_token")
        assert hasattr(result, "refresh_token")

    # ============= Refresh Token Tests =============
    @pytest.mark.asyncio
    async def test_refresh_tokens_success(
        self, mock_db, mock_request, mock_user, mock_session, valid_refresh_token
    ):
        """Test successful token refresh."""
        # Setup
        service = AuthService(mock_db)
        setup_db_execute_mock(mock_db, mock_session)

        refresh_data = type("obj", (object,), {"refresh_token": valid_refresh_token})()

        # Mock verify_token to return payload
        from unittest.mock import patch

        with patch("api.v1.auth.service.verify_token") as mock_verify:
            mock_verify.return_value = {
                "user_id": str(mock_user.id),
                "session_id": str(mock_session.id),
            }
            setup_db_execute_mock(mock_db, mock_user)

            # Execute
            result = await service.refresh_tokens(refresh_data, mock_request)

            # Assert
            assert result is not None
            assert hasattr(result, "access_token")
            assert hasattr(result, "refresh_token")

    @pytest.mark.asyncio
    async def test_refresh_tokens_invalid_token(self, mock_db, mock_request):
        """Test refresh with invalid token."""
        # Setup
        service = AuthService(mock_db)

        refresh_data = type("obj", (object,), {"refresh_token": "invalid_token"})()

        # Mock verify_token to return None
        from unittest.mock import patch

        with patch("api.v1.auth.service.verify_token") as mock_verify:
            mock_verify.return_value = None

            # Execute & Assert
            with pytest.raises(UnauthorizedError) as exc_info:
                await service.refresh_tokens(refresh_data, mock_request)
            assert "Invalid refresh token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_refresh_tokens_inactive_session(
        self, mock_db, mock_request, mock_user, mock_inactive_session, valid_refresh_token
    ):
        """Test refresh with inactive session."""
        # Setup
        service = AuthService(mock_db)
        setup_db_execute_mock(mock_db, mock_inactive_session)

        refresh_data = type("obj", (object,), {"refresh_token": valid_refresh_token})()

        # Mock verify_token
        from unittest.mock import patch

        with patch("api.v1.auth.service.verify_token") as mock_verify:
            mock_verify.return_value = {
                "user_id": str(mock_user.id),
                "session_id": str(mock_inactive_session.id),
            }

            # Execute & Assert
            with pytest.raises(UnauthorizedError) as exc_info:
                await service.refresh_tokens(refresh_data, mock_request)
            assert "Session expired or invalid" in str(exc_info.value.detail)

    # ============= Logout Tests =============
    @pytest.mark.asyncio
    async def test_logout_success(self, mock_db, mock_request, mock_user, mock_session, valid_access_token):
        """Test successful logout."""
        # Setup
        service = AuthService(mock_db)
        setup_db_execute_mock(mock_db, mock_session)

        # Mock verify_token
        from unittest.mock import patch

        with patch("api.v1.auth.service.verify_token") as mock_verify:
            mock_verify.return_value = {
                "user_id": str(mock_user.id),
                "session_id": str(mock_session.id),
            }

            # Execute
            result = await service.logout(mock_request, str(mock_user.id))

            # Assert
            assert result is not None
            assert "message" in result
            assert mock_db.commit.called

    # ============= Get Sessions Tests =============
    @pytest.mark.asyncio
    async def test_get_sessions_all(self, mock_db, mock_user, mock_sessions_list):
        """Test getting all sessions."""
        # Setup
        service = AuthService(mock_db)
        # get_sessions calls _get_user_sessions which makes 2 execute calls: count + list
        from tests.conftest import setup_db_multiple_execute_mock
        setup_db_multiple_execute_mock(mock_db, len(mock_sessions_list), mock_sessions_list)

        # Execute
        result = await service.get_sessions(
            user_id=mock_user.id, is_active=None, page=1, per_page=50
        )

        # Assert
        assert result is not None
        assert result.total == len(mock_sessions_list)
        assert len(result.sessions) == len(mock_sessions_list)

    @pytest.mark.asyncio
    async def test_get_sessions_active_only(self, mock_db, mock_user, mock_sessions_list):
        """Test getting only active sessions."""
        # Setup
        service = AuthService(mock_db)
        active_sessions = [s for s in mock_sessions_list if s.is_active]
        setup_db_execute_mock(mock_db, active_sessions)
        setup_db_count_mock(mock_db, len(active_sessions))

        # Execute
        result = await service.get_sessions(
            user_id=mock_user.id, is_active=True, page=1, per_page=50
        )

        # Assert
        assert result is not None
        assert result.total == len(active_sessions)
        assert all(session.is_active for session in result.sessions)

    @pytest.mark.asyncio
    async def test_get_sessions_inactive_only(self, mock_db, mock_user, mock_sessions_list):
        """Test getting only inactive sessions."""
        # Setup
        service = AuthService(mock_db)
        inactive_sessions = [s for s in mock_sessions_list if not s.is_active]
        setup_db_execute_mock(mock_db, inactive_sessions)
        setup_db_count_mock(mock_db, len(inactive_sessions))

        # Execute
        result = await service.get_sessions(
            user_id=mock_user.id, is_active=False, page=1, per_page=50
        )

        # Assert
        assert result is not None
        assert result.total == len(inactive_sessions)
        assert all(not session.is_active for session in result.sessions)

    @pytest.mark.asyncio
    async def test_get_sessions_pagination(self, mock_db, mock_user, mock_sessions_list):
        """Test sessions pagination."""
        # Setup
        service = AuthService(mock_db)
        # get_sessions calls _get_user_sessions which makes 2 execute calls: count + list
        from tests.conftest import setup_db_multiple_execute_mock
        paginated_sessions = mock_sessions_list[:2]  # Return first 2
        setup_db_multiple_execute_mock(mock_db, len(mock_sessions_list), paginated_sessions)

        # Execute
        result = await service.get_sessions(
            user_id=mock_user.id, is_active=None, page=1, per_page=2
        )

        # Assert
        assert result is not None
        assert result.page == 1
        assert result.per_page == 2
        assert result.total == len(mock_sessions_list)
        assert len(result.sessions) == 2

    # ============= Delete Session Tests =============
    @pytest.mark.asyncio
    async def test_delete_session_success(self, mock_db, mock_user, mock_session):
        """Test successful session deletion."""
        # Setup
        service = AuthService(mock_db)
        setup_db_execute_mock(mock_db, mock_session)

        # Execute
        result = await service.delete_session(str(mock_session.id), mock_user.id)

        # Assert
        assert result is not None
        assert "message" in result
        assert mock_db.delete.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, mock_db, mock_user):
        """Test deleting non-existent session."""
        # Setup
        service = AuthService(mock_db)
        setup_db_execute_mock(mock_db, None)

        # Execute & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.delete_session(str(uuid.uuid4()), mock_user.id)
        assert "Session not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_delete_session_other_user(self, mock_db, mock_user, mock_session):
        """Test deleting another user's session."""
        # Setup
        service = AuthService(mock_db)
        setup_db_execute_mock(mock_db, mock_session)
        other_user_id = uuid.uuid4()

        # Execute & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            await service.delete_session(str(mock_session.id), other_user_id)
        assert "Cannot delete other user's session" in str(exc_info.value.detail)

    # ============= Delete All Sessions Tests =============
    @pytest.mark.asyncio
    async def test_delete_all_sessions_success(self, mock_db, mock_user, mock_sessions_list):
        """Test deleting all user sessions."""
        # Setup
        service = AuthService(mock_db)
        active_sessions = [s for s in mock_sessions_list if s.is_active]
        setup_db_execute_mock(mock_db, active_sessions)

        # Execute
        result = await service.delete_all_sessions(mock_user.id)

        # Assert
        assert result is not None
        assert "message" in result
        assert str(len(active_sessions)) in result["message"]
        assert mock_db.commit.called

