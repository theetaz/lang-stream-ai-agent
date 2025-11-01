"""
CRUD operations package.
Exports all CRUD operations for easy import.
"""
from database.crud.user_crud import (
    create_user,
    get_user_by_id,
    get_user_by_email,
    get_user_by_google_id,
    get_or_create_user_by_google,
    update_user,
    list_users,
    delete_user,
    deactivate_user,
)
from database.crud.session_crud import (
    create_session,
    get_session_by_id,
    get_session_by_refresh_token,
    get_user_sessions,
    deactivate_session,
    deactivate_all_user_sessions,
    update_session_activity,
    delete_session,
)

__all__ = [
    "create_user",
    "get_user_by_id",
    "get_user_by_email",
    "get_user_by_google_id",
    "get_or_create_user_by_google",
    "update_user",
    "list_users",
    "delete_user",
    "deactivate_user",
    "create_session",
    "get_session_by_id",
    "get_session_by_refresh_token",
    "get_user_sessions",
    "deactivate_session",
    "deactivate_all_user_sessions",
    "update_session_activity",
    "delete_session",
]
