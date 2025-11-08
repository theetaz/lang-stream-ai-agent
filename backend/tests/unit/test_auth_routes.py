"""
Unit tests for auth routes/endpoints.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from common.errors import ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from main import app


class TestAuthRoutes:
    """Test suite for auth routes."""

    # ============= Register Endpoint Tests =============
    def test_register_success(self, test_client, mock_db, mock_request, sample_register_data):
        """Test successful registration."""
        # Setup
        with patch("api.v1.auth.routes.get_db") as mock_get_db, patch(
            "api.v1.auth.routes.AuthService"
        ) as mock_service_class:
            mock_get_db.return_value = AsyncMock()
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            mock_token_response = {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "token_type": "bearer",
                "user": {"id": str(uuid.uuid4()), "email": sample_register_data["email"]},
                "session_id": str(uuid.uuid4()),
            }
            mock_service.register.return_value = type("obj", (object,), mock_token_response)()

            # Execute
            response = test_client.post("/api/v1/auth/register", json=sample_register_data)

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert "access_token" in data["data"]

    def test_register_duplicate_email(self, test_client, mock_db, sample_register_data):
        """Test registration with duplicate email."""
        # Setup
        with patch("api.v1.auth.routes.get_db") as mock_get_db, patch(
            "api.v1.auth.routes.AuthService"
        ) as mock_service_class:
            mock_get_db.return_value = AsyncMock()
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.register.side_effect = ValidationError("Email already registered")

            # Execute
            response = test_client.post("/api/v1/auth/register", json=sample_register_data)

            # Assert
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert data["success"] is False
            assert "Email already registered" in data["message"]

    def test_register_invalid_email(self, test_client, sample_register_data):
        """Test registration with invalid email format."""
        # Setup
        invalid_data = sample_register_data.copy()
        invalid_data["email"] = "invalid-email"

        # Execute
        response = test_client.post("/api/v1/auth/register", json=invalid_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["success"] is False
        assert "Validation error" in data["message"]

    def test_register_missing_fields(self, test_client):
        """Test registration with missing required fields."""
        # Execute
        response = test_client.post("/api/v1/auth/register", json={"email": "test@example.com"})

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["success"] is False

    # ============= Login Endpoint Tests =============
    def test_login_success(self, test_client, mock_user):
        """Test successful login."""
        # Setup
        login_data = {"email": mock_user.email, "password": "secret"}

        with patch("api.v1.auth.routes.get_db") as mock_get_db, patch(
            "api.v1.auth.routes.AuthService"
        ) as mock_service_class:
            mock_get_db.return_value = AsyncMock()
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            mock_token_response = {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "token_type": "bearer",
                "user": mock_user.to_dict(),
                "session_id": str(uuid.uuid4()),
            }
            mock_service.login.return_value = type("obj", (object,), mock_token_response)()

            # Execute
            response = test_client.post("/api/v1/auth/login", json=login_data)

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "access_token" in data["data"]

    def test_login_invalid_credentials(self, test_client):
        """Test login with invalid credentials."""
        # Setup
        login_data = {"email": "test@example.com", "password": "wrongpassword"}

        with patch("api.v1.auth.routes.get_db") as mock_get_db, patch(
            "api.v1.auth.routes.AuthService"
        ) as mock_service_class:
            mock_get_db.return_value = AsyncMock()
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.login.side_effect = UnauthorizedError("Invalid email or password")

            # Execute
            response = test_client.post("/api/v1/auth/login", json=login_data)

            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            data = response.json()
            assert data["success"] is False
            assert "Invalid email or password" in data["message"]

    def test_login_missing_fields(self, test_client):
        """Test login with missing fields."""
        # Execute
        response = test_client.post("/api/v1/auth/login", json={"email": "test@example.com"})

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # ============= Google OAuth Endpoint Tests =============
    def test_google_auth_success(self, test_client, sample_google_auth_data):
        """Test successful Google OAuth."""
        # Setup
        with patch("api.v1.auth.routes.get_db") as mock_get_db, patch(
            "api.v1.auth.routes.AuthService"
        ) as mock_service_class:
            mock_get_db.return_value = AsyncMock()
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            mock_token_response = {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "token_type": "bearer",
                "user": {"id": str(uuid.uuid4()), "email": sample_google_auth_data["email"]},
                "session_id": str(uuid.uuid4()),
            }
            mock_service.google_auth.return_value = type("obj", (object,), mock_token_response)()

            # Execute
            response = test_client.post("/api/v1/auth/google", json=sample_google_auth_data)

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "access_token" in data["data"]

    # ============= Refresh Token Endpoint Tests =============
    def test_refresh_token_success(self, test_client, valid_refresh_token):
        """Test successful token refresh."""
        # Setup
        refresh_data = {"refresh_token": valid_refresh_token}

        with patch("api.v1.auth.routes.get_db") as mock_get_db, patch(
            "api.v1.auth.routes.AuthService"
        ) as mock_service_class:
            mock_get_db.return_value = AsyncMock()
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            mock_token_response = {
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token",
                "token_type": "bearer",
                "user": {"id": str(uuid.uuid4())},
                "session_id": str(uuid.uuid4()),
            }
            mock_service.refresh_tokens.return_value = type("obj", (object,), mock_token_response)()

            # Execute
            response = test_client.post("/api/v1/auth/refresh", json=refresh_data)

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "access_token" in data["data"]

    def test_refresh_token_invalid(self, test_client):
        """Test refresh with invalid token."""
        # Setup
        refresh_data = {"refresh_token": "invalid_token"}

        with patch("api.v1.auth.routes.get_db") as mock_get_db, patch(
            "api.v1.auth.routes.AuthService"
        ) as mock_service_class:
            mock_get_db.return_value = AsyncMock()
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.refresh_tokens.side_effect = UnauthorizedError("Invalid refresh token")

            # Execute
            response = test_client.post("/api/v1/auth/refresh", json=refresh_data)

            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            data = response.json()
            assert data["success"] is False

    # ============= Logout Endpoint Tests =============
    def test_logout_success(self, test_client, mock_user, valid_access_token):
        """Test successful logout."""
        # Setup
        with patch("api.v1.auth.routes.get_current_user") as mock_get_user, patch(
            "api.v1.auth.routes.get_db"
        ) as mock_get_db, patch("api.v1.auth.routes.AuthService") as mock_service_class:
            mock_get_user.return_value = mock_user
            mock_get_db.return_value = AsyncMock()
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.logout.return_value = {"message": "Logged out successfully"}

            # Execute
            response = test_client.post(
                "/api/v1/auth/logout",
                headers={"Authorization": f"Bearer {valid_access_token}"},
            )

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True

    def test_logout_unauthorized(self, test_client):
        """Test logout without token."""
        # Execute
        response = test_client.post("/api/v1/auth/logout")

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # ============= Get Me Endpoint Tests =============
    def test_get_me_success(self, test_client, mock_user, valid_access_token):
        """Test getting current user info."""
        # Setup
        with patch("api.v1.auth.routes.get_current_user") as mock_get_user_func:
            mock_get_user_func.return_value = mock_user

            # Execute
            response = test_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {valid_access_token}"},
            )

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["email"] == mock_user.email

    def test_get_me_unauthorized(self, test_client):
        """Test get me without token."""
        # Execute
        response = test_client.get("/api/v1/auth/me")

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # ============= Get Sessions Endpoint Tests =============
    def test_get_sessions_all(self, test_client, mock_user, mock_sessions_list, valid_access_token):
        """Test getting all sessions."""
        # Setup
        with patch("api.v1.auth.routes.get_current_user") as mock_get_user_func, patch(
            "api.v1.auth.routes.get_db"
        ) as mock_get_db, patch("api.v1.auth.routes.AuthService") as mock_service_class:
            mock_get_user_func.return_value = mock_user
            mock_get_db.return_value = AsyncMock()
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            from schemas.auth import SessionsListResponse, SessionResponse

            sessions_response = SessionsListResponse(
                sessions=[SessionResponse(**s.to_dict()) for s in mock_sessions_list],
                total=len(mock_sessions_list),
                page=1,
                per_page=50,
                total_pages=1,
            )
            mock_service.get_sessions.return_value = sessions_response

            # Execute
            response = test_client.get(
                "/api/v1/auth/sessions",
                headers={"Authorization": f"Bearer {valid_access_token}"},
            )

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total"] == len(mock_sessions_list)

    def test_get_sessions_active_only(self, test_client, mock_user, mock_sessions_list, valid_access_token):
        """Test getting only active sessions."""
        # Setup
        active_sessions = [s for s in mock_sessions_list if s.is_active]

        with patch("api.v1.auth.routes.get_current_user") as mock_get_user_func, patch(
            "api.v1.auth.routes.get_db"
        ) as mock_get_db, patch("api.v1.auth.routes.AuthService") as mock_service_class:
            mock_get_user_func.return_value = mock_user
            mock_get_db.return_value = AsyncMock()
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            from schemas.auth import SessionsListResponse, SessionResponse

            sessions_response = SessionsListResponse(
                sessions=[SessionResponse(**s.to_dict()) for s in active_sessions],
                total=len(active_sessions),
                page=1,
                per_page=50,
                total_pages=1,
            )
            mock_service.get_sessions.return_value = sessions_response

            # Execute
            response = test_client.get(
                "/api/v1/auth/sessions?is_active=true",
                headers={"Authorization": f"Bearer {valid_access_token}"},
            )

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total"] == len(active_sessions)

    def test_get_sessions_pagination(self, test_client, mock_user, mock_sessions_list, valid_access_token):
        """Test sessions pagination."""
        # Setup
        with patch("api.v1.auth.routes.get_current_user") as mock_get_user_func, patch(
            "api.v1.auth.routes.get_db"
        ) as mock_get_db, patch("api.v1.auth.routes.AuthService") as mock_service_class:
            mock_get_user_func.return_value = mock_user
            mock_get_db.return_value = AsyncMock()
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            from schemas.auth import SessionsListResponse, SessionResponse

            sessions_response = SessionsListResponse(
                sessions=[SessionResponse(**s.to_dict()) for s in mock_sessions_list[:2]],
                total=len(mock_sessions_list),
                page=1,
                per_page=2,
                total_pages=3,
            )
            mock_service.get_sessions.return_value = sessions_response

            # Execute
            response = test_client.get(
                "/api/v1/auth/sessions?page=1&per_page=2",
                headers={"Authorization": f"Bearer {valid_access_token}"},
            )

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["page"] == 1
            assert data["data"]["per_page"] == 2

    def test_get_sessions_unauthorized(self, test_client):
        """Test get sessions without token."""
        # Execute
        response = test_client.get("/api/v1/auth/sessions")

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # ============= Delete Session Endpoint Tests =============
    def test_delete_session_success(self, test_client, mock_user, mock_session, valid_access_token):
        """Test successful session deletion."""
        # Setup
        with patch("api.v1.auth.routes.get_current_user") as mock_get_user_func, patch(
            "api.v1.auth.routes.get_db"
        ) as mock_get_db, patch("api.v1.auth.routes.AuthService") as mock_service_class:
            mock_get_user_func.return_value = mock_user
            mock_get_db.return_value = AsyncMock()
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.delete_session.return_value = {"message": "Session deleted successfully"}

            # Execute
            response = test_client.delete(
                f"/api/v1/auth/sessions/{mock_session.id}",
                headers={"Authorization": f"Bearer {valid_access_token}"},
            )

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True

    def test_delete_session_not_found(self, test_client, mock_user, valid_access_token):
        """Test deleting non-existent session."""
        # Setup
        with patch("api.v1.auth.routes.get_current_user") as mock_get_user_func, patch(
            "api.v1.auth.routes.get_db"
        ) as mock_get_db, patch("api.v1.auth.routes.AuthService") as mock_service_class:
            mock_get_user_func.return_value = mock_user
            mock_get_db.return_value = AsyncMock()
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.delete_session.side_effect = NotFoundError("Session not found")

            # Execute
            response = test_client.delete(
                f"/api/v1/auth/sessions/{uuid.uuid4()}",
                headers={"Authorization": f"Bearer {valid_access_token}"},
            )

            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["success"] is False

    def test_delete_session_forbidden(self, test_client, mock_user, mock_session, valid_access_token):
        """Test deleting another user's session."""
        # Setup
        with patch("api.v1.auth.routes.get_current_user") as mock_get_user_func, patch(
            "api.v1.auth.routes.get_db"
        ) as mock_get_db, patch("api.v1.auth.routes.AuthService") as mock_service_class:
            mock_get_user_func.return_value = mock_user
            mock_get_db.return_value = AsyncMock()
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.delete_session.side_effect = ForbiddenError("Cannot delete other user's session")

            # Execute
            response = test_client.delete(
                f"/api/v1/auth/sessions/{mock_session.id}",
                headers={"Authorization": f"Bearer {valid_access_token}"},
            )

            # Assert
            assert response.status_code == status.HTTP_403_FORBIDDEN
            data = response.json()
            assert data["success"] is False

    # ============= Delete All Sessions Endpoint Tests =============
    def test_delete_all_sessions_success(self, test_client, mock_user, valid_access_token):
        """Test deleting all sessions."""
        # Setup
        with patch("api.v1.auth.routes.get_current_user") as mock_get_user_func, patch(
            "api.v1.auth.routes.get_db"
        ) as mock_get_db, patch("api.v1.auth.routes.AuthService") as mock_service_class:
            mock_get_user_func.return_value = mock_user
            mock_get_db.return_value = AsyncMock()
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.delete_all_sessions.return_value = {"message": "Logged out from 3 session(s)"}

            # Execute
            response = test_client.delete(
                "/api/v1/auth/sessions/all",
                headers={"Authorization": f"Bearer {valid_access_token}"},
            )

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True

