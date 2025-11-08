"""
Pytest configuration and shared fixtures for auth module tests.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from auth.jwt import create_access_token
from faker import Faker
from fastapi import Request
from fastapi.testclient import TestClient
from main import app
from models.session import Session
from models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

fake = Faker()


# ============= Database Fixtures =============
@pytest.fixture
def mock_db():
    """Mock AsyncSession for database operations."""
    db = AsyncMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    db.add = Mock()
    return db


@pytest.fixture
def mock_db_result(mock_user, mock_session):
    """Mock database query result."""
    result = MagicMock()
    result.scalars = Mock()
    result.scalar = Mock()
    return result


# ============= Model Fixtures =============
@pytest.fixture
def mock_user():
    """Create a mock User object."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=fake.email(),
        password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        name=fake.name(),
        avatar_url=fake.image_url(),
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    return user


@pytest.fixture
def mock_inactive_user(mock_user):
    """Create a mock inactive User object."""
    mock_user.is_active = False
    return mock_user


@pytest.fixture
def mock_session(mock_user):
    """Create a mock Session object."""
    session_id = uuid.uuid4()
    session = Session(
        id=session_id,
        user_id=mock_user.id,
        refresh_token_hash=fake.sha256(),
        device_info="iPhone, iOS 15.0, Safari 15.0",
        ip_address=fake.ipv4(),
        user_agent=fake.user_agent(),
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    return session


@pytest.fixture
def mock_inactive_session(mock_session):
    """Create a mock inactive Session object."""
    mock_session.is_active = False
    return mock_session


@pytest.fixture
def mock_sessions_list(mock_user):
    """Create a list of mock Session objects."""
    sessions = []
    for i in range(5):
        session = Session(
            id=uuid.uuid4(),
            user_id=mock_user.id,
            refresh_token_hash=fake.sha256(),
            device_info=f"Device {i+1}",
            ip_address=fake.ipv4(),
            user_agent=fake.user_agent(),
            is_active=i < 3,  # First 3 are active
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        sessions.append(session)
    return sessions


# ============= Request Fixtures =============
@pytest.fixture
def mock_request():
    """Mock FastAPI Request object."""
    request = Mock(spec=Request)
    request.headers = {
        "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)",
        "authorization": "Bearer test_token",
    }
    request.client = Mock()
    request.client.host = "127.0.0.1"
    return request


# ============= Test Data Fixtures =============
@pytest.fixture
def sample_register_data():
    """Sample registration request data."""
    return {
        "email": fake.email(),
        "password": "TestPassword123!",
        "name": fake.name(),
    }


@pytest.fixture
def sample_login_data(mock_user):
    """Sample login request data."""
    return {
        "email": mock_user.email,
        "password": "secret",  # Matches mock_user password_hash
    }


@pytest.fixture
def sample_google_auth_data():
    """Sample Google OAuth request data."""
    return {
        "google_id": fake.uuid4(),
        "email": fake.email(),
        "name": fake.name(),
        "avatar_url": fake.image_url(),
    }


@pytest.fixture
def sample_refresh_data(mock_user, mock_session):
    """Sample refresh token request data."""
    refresh_token = create_access_token(
        {"user_id": str(mock_user.id), "session_id": str(mock_session.id)}
    )
    return {"refresh_token": refresh_token}


# ============= Token Fixtures =============
@pytest.fixture
def valid_access_token(mock_user, mock_session):
    """Create a valid access token."""
    return create_access_token(
        {
            "user_id": str(mock_user.id),
            "email": mock_user.email,
            "name": mock_user.name,
            "session_id": str(mock_session.id),
        }
    )


@pytest.fixture
def valid_refresh_token(mock_user, mock_session):
    """Create a valid refresh token."""
    from auth.jwt import create_refresh_token

    return create_refresh_token(
        {
            "user_id": str(mock_user.id),
            "session_id": str(mock_session.id),
        }
    )


# ============= Service Fixtures =============
@pytest.fixture
def mock_auth_service(mock_db):
    """Mock AuthService instance."""
    from api.v1.auth.service import AuthService

    return AuthService(mock_db)


# ============= Dependency Override Fixtures =============
@pytest.fixture
def override_get_db(mock_db):
    """Override get_db dependency."""
    from database.db_client import get_db

    async def _get_db():
        yield mock_db

    return _get_db


@pytest.fixture
def override_get_current_user(mock_user):
    """Override get_current_user dependency."""
    from auth.utils import get_current_user

    async def _get_current_user():
        return mock_user

    return _get_current_user


@pytest.fixture
def override_get_auth_service(mock_auth_service):
    """Override get_auth_service dependency."""
    from api.v1.auth.routes import get_auth_service

    def _get_auth_service():
        return mock_auth_service

    return _get_auth_service


# ============= Test Client Fixture =============
@pytest.fixture
def test_client():
    """Create a test client for FastAPI app."""
    client = TestClient(app)
    yield client
    # Clean up dependency overrides after each test
    app.dependency_overrides.clear()


@pytest.fixture
def override_dependencies(mock_user, mock_db):
    """Helper fixture to override FastAPI dependencies for authenticated routes."""
    from auth.utils import get_current_user
    from api.v1.auth.routes import get_auth_service
    from api.v1.auth.service import AuthService
    
    async def override_get_current_user():
        return mock_user
    
    def override_get_auth_service():
        return AuthService(mock_db)
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_auth_service] = override_get_auth_service
    
    yield
    
    # Cleanup is handled by test_client fixture


# ============= Helper Functions =============
def setup_db_execute_mock(mock_db, return_value=None, call_count=1):
    """Helper to setup db.execute mock.

    Args:
        mock_db: Mock database session
        return_value: Value(s) to return. Can be a single value, list, or None
        call_count: Number of times execute will be called (for multiple queries)
    """
    if call_count == 1:
        mock_result = MagicMock()
        if return_value is not None:
            if isinstance(return_value, list):
                mock_result.scalars.return_value.all.return_value = return_value
                mock_result.scalars.return_value.first.return_value = (
                    return_value[0] if return_value else None
                )
            else:
                mock_result.scalars.return_value.first.return_value = return_value
                mock_result.scalar.return_value = return_value
        else:
            mock_result.scalars.return_value.first.return_value = None
            mock_result.scalar.return_value = 0

        mock_db.execute.return_value = mock_result
        return mock_result
    else:
        # Multiple calls - return different values for each call
        mock_results = []
        for i in range(call_count):
            mock_result = MagicMock()
            if i == 0:  # First call is usually count query
                mock_result.scalar.return_value = (
                    return_value
                    if isinstance(return_value, int)
                    else len(return_value) if isinstance(return_value, list) else 0
                )
            else:  # Subsequent calls return the list
                if isinstance(return_value, list):
                    mock_result.scalars.return_value.all.return_value = return_value
                    mock_result.scalars.return_value.first.return_value = (
                        return_value[0] if return_value else None
                    )
                else:
                    mock_result.scalars.return_value.first.return_value = return_value
            mock_results.append(mock_result)

        mock_db.execute.side_effect = mock_results
        return mock_results


def setup_db_count_mock(mock_db, count: int):
    """Helper to setup db.execute mock for count queries."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = count
    mock_db.execute.return_value = mock_result
    return mock_result


def setup_db_multiple_execute_mock(mock_db, count_value: int, list_value: list):
    """Helper to setup db.execute mock for queries that make multiple calls (count + list)."""
    count_result = MagicMock()
    count_result.scalar.return_value = count_value

    list_result = MagicMock()
    list_result.scalars.return_value.all.return_value = list_value
    list_result.scalars.return_value.first.return_value = (
        list_value[0] if list_value else None
    )

    mock_db.execute.side_effect = [count_result, list_result]
    return [count_result, list_result]
