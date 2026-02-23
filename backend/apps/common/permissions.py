"""
Nova — Permission Constants & Utilities
==========================================
Centralized permission definitions for the RBAC system.
"""

from enum import Enum
from typing import List


class Role(str, Enum):
    """User roles in the system."""
    SUPER_ADMIN = 'SUPER_ADMIN'
    LIBRARIAN = 'LIBRARIAN'
    ASSISTANT = 'ASSISTANT'
    USER = 'USER'


class Permission(str, Enum):
    """Fine-grained permissions for the system."""

    # User Management
    MANAGE_USERS = 'manage_users'
    MANAGE_ROLES = 'manage_roles'
    VIEW_ALL_USERS = 'view_all_users'

    # Catalog
    MANAGE_BOOKS = 'manage_books'
    MANAGE_STOCK = 'manage_stock'
    VIEW_CATALOG = 'view_catalog'

    # Circulation
    PROCESS_BORROWS = 'process_borrows'
    PROCESS_RETURNS = 'process_returns'
    WAIVE_FINES = 'waive_fines'
    VIEW_ALL_BORROWS = 'view_all_borrows'
    BORROW_BOOKS = 'borrow_books'
    VIEW_OWN_BORROWS = 'view_own_borrows'

    # Digital Content
    UPLOAD_DIGITAL_CONTENT = 'upload_digital_content'
    ACCESS_DIGITAL_CONTENT = 'access_digital_content'
    MANAGE_DIGITAL_CONTENT = 'manage_digital_content'

    # Engagement
    VIEW_OWN_ENGAGEMENT = 'view_own_engagement'
    VIEW_ALL_ENGAGEMENT = 'view_all_engagement'
    VIEW_LEADERBOARD = 'view_leaderboard'

    # Recommendations
    VIEW_RECOMMENDATIONS = 'view_recommendations'

    # Analytics
    VIEW_ANALYTICS = 'view_analytics'
    VIEW_LIBRARY_HEALTH = 'view_library_health'
    VIEW_PREDICTIONS = 'view_predictions'

    # Governance
    VIEW_AUDIT_LOGS = 'view_audit_logs'
    VIEW_SECURITY_EVENTS = 'view_security_events'
    REVIEW_VERIFICATIONS = 'review_verifications'

    # Notes
    CREATE_NOTES = 'create_notes'
    CREATE_BOOKMARKS = 'create_bookmarks'


# =============================================================================
# ROLE → PERMISSION MATRIX
# =============================================================================

ROLE_PERMISSIONS: dict[Role, List[Permission]] = {
    Role.SUPER_ADMIN: list(Permission),  # Super admin has ALL permissions

    Role.LIBRARIAN: [
        Permission.VIEW_ALL_USERS,
        Permission.MANAGE_BOOKS,
        Permission.MANAGE_STOCK,
        Permission.VIEW_CATALOG,
        Permission.PROCESS_BORROWS,
        Permission.PROCESS_RETURNS,
        Permission.WAIVE_FINES,
        Permission.VIEW_ALL_BORROWS,
        Permission.BORROW_BOOKS,
        Permission.VIEW_OWN_BORROWS,
        Permission.UPLOAD_DIGITAL_CONTENT,
        Permission.ACCESS_DIGITAL_CONTENT,
        Permission.MANAGE_DIGITAL_CONTENT,
        Permission.VIEW_OWN_ENGAGEMENT,
        Permission.VIEW_ALL_ENGAGEMENT,
        Permission.VIEW_LEADERBOARD,
        Permission.VIEW_RECOMMENDATIONS,
        Permission.VIEW_ANALYTICS,
        Permission.VIEW_LIBRARY_HEALTH,
        Permission.VIEW_AUDIT_LOGS,
        Permission.REVIEW_VERIFICATIONS,
        Permission.CREATE_NOTES,
        Permission.CREATE_BOOKMARKS,
    ],

    Role.ASSISTANT: [
        Permission.MANAGE_STOCK,
        Permission.VIEW_CATALOG,
        Permission.PROCESS_BORROWS,
        Permission.PROCESS_RETURNS,
        Permission.VIEW_ALL_BORROWS,
        Permission.BORROW_BOOKS,
        Permission.VIEW_OWN_BORROWS,
        Permission.ACCESS_DIGITAL_CONTENT,
        Permission.VIEW_OWN_ENGAGEMENT,
        Permission.VIEW_LEADERBOARD,
        Permission.VIEW_RECOMMENDATIONS,
        Permission.VIEW_ANALYTICS,
        Permission.CREATE_NOTES,
        Permission.CREATE_BOOKMARKS,
    ],

    Role.USER: [
        Permission.VIEW_CATALOG,
        Permission.BORROW_BOOKS,
        Permission.VIEW_OWN_BORROWS,
        Permission.ACCESS_DIGITAL_CONTENT,
        Permission.VIEW_OWN_ENGAGEMENT,
        Permission.VIEW_LEADERBOARD,
        Permission.VIEW_RECOMMENDATIONS,
        Permission.CREATE_NOTES,
        Permission.CREATE_BOOKMARKS,
    ],
}


def has_permission(role: str, permission: Permission) -> bool:
    """
    Check if a role has a specific permission.

    Args:
        role: The user's role string.
        permission: The permission to check.

    Returns:
        True if the role has the permission.
    """
    try:
        role_enum = Role(role)
    except ValueError:
        return False

    return permission in ROLE_PERMISSIONS.get(role_enum, [])


def get_permissions_for_role(role: str) -> List[Permission]:
    """
    Get all permissions for a given role.

    Args:
        role: The role string.

    Returns:
        List of Permission enums for the role.
    """
    try:
        role_enum = Role(role)
    except ValueError:
        return []

    return ROLE_PERMISSIONS.get(role_enum, [])


def has_any_role(user_role: str, allowed_roles: List[str]) -> bool:
    """
    Check if a user's role is in the list of allowed roles.

    Args:
        user_role: The user's role string.
        allowed_roles: List of role strings that are allowed.

    Returns:
        True if the user's role is allowed.
    """
    return user_role in allowed_roles
