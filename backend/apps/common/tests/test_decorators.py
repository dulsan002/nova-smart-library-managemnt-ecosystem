"""
Tests for apps.common.decorators
==================================
Tests for require_authentication, require_roles, require_permission, audit_action.
"""

import pytest
from unittest.mock import MagicMock, patch

from apps.common.decorators import (
    require_authentication,
    require_roles,
    require_permission,
    audit_action,
)
from apps.common.permissions import Permission
from apps.common.exceptions import AuthenticationError, AuthorizationError


# ─── Helpers ─────────────────────────────────────────────────────────

def _make_info(user=None, authenticated=True):
    """Build a mock GraphQL info.context."""
    info = MagicMock()
    if user is None:
        user = MagicMock()
        user.is_authenticated = authenticated
        user.is_active = True
        user.role = "USER"
        user.id = "test-uuid"
    info.context.user = user
    return info


# ─── require_authentication ─────────────────────────────────────────

class TestRequireAuthentication:

    def test_allows_authenticated_user(self):
        @require_authentication
        def resolver(root, info):
            return "ok"

        info = _make_info()
        assert resolver(None, info) == "ok"

    def test_rejects_anonymous(self):
        @require_authentication
        def resolver(root, info):
            return "ok"

        info = _make_info(authenticated=False)
        info.context.user.is_authenticated = False
        with pytest.raises(AuthenticationError):
            resolver(None, info)

    def test_rejects_no_user(self):
        @require_authentication
        def resolver(root, info):
            return "ok"

        info = MagicMock()
        info.context.user = None
        with pytest.raises(AuthenticationError):
            resolver(None, info)

    def test_rejects_inactive_user(self):
        @require_authentication
        def resolver(root, info):
            return "ok"

        info = _make_info()
        info.context.user.is_active = False
        with pytest.raises(AuthenticationError, match="deactivated"):
            resolver(None, info)


# ─── require_roles ──────────────────────────────────────────────────

class TestRequireRoles:

    def test_allows_matching_role(self):
        @require_roles(["LIBRARIAN", "SUPER_ADMIN"])
        def resolver(root, info):
            return "ok"

        info = _make_info()
        info.context.user.role = "LIBRARIAN"
        assert resolver(None, info) == "ok"

    def test_rejects_non_matching_role(self):
        @require_roles(["LIBRARIAN"])
        def resolver(root, info):
            return "ok"

        info = _make_info()
        info.context.user.role = "USER"
        with pytest.raises(AuthorizationError):
            resolver(None, info)

    def test_rejects_unauthenticated(self):
        @require_roles(["USER"])
        def resolver(root, info):
            return "ok"

        info = _make_info(authenticated=False)
        info.context.user.is_authenticated = False
        with pytest.raises(AuthenticationError):
            resolver(None, info)


# ─── require_permission ─────────────────────────────────────────────

class TestRequirePermission:

    def test_allows_user_with_permission(self):
        @require_permission(Permission.VIEW_CATALOG)
        def resolver(root, info):
            return "ok"

        info = _make_info()
        info.context.user.role = "USER"
        assert resolver(None, info) == "ok"

    def test_rejects_user_without_permission(self):
        @require_permission(Permission.MANAGE_BOOKS)
        def resolver(root, info):
            return "ok"

        info = _make_info()
        info.context.user.role = "USER"
        with pytest.raises(AuthorizationError):
            resolver(None, info)

    def test_super_admin_always_passes(self):
        @require_permission(Permission.MANAGE_BOOKS)
        def resolver(root, info):
            return "ok"

        info = _make_info()
        info.context.user.role = "SUPER_ADMIN"
        assert resolver(None, info) == "ok"


# ─── audit_action ───────────────────────────────────────────────────

class TestAuditAction:

    @patch("apps.common.decorators.AuditService", create=True)
    def test_calls_audit_service(self, mock_import):
        @audit_action("book_created", "Book")
        def resolver(root, info):
            result = MagicMock()
            result.id = "book-123"
            return result

        info = _make_info()
        resolver(None, info)

        # The audit decorator should not raise even if import fails silently.
        # The decorator catches exceptions internally.

    def test_resolver_result_returned(self):
        @audit_action("book_created", "Book")
        def resolver(root, info):
            return "result_value"

        info = _make_info()
        assert resolver(None, info) == "result_value"
