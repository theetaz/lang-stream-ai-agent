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
]
