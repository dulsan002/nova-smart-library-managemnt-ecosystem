"""
Tests for apps.common.permissions
===================================
"""

import pytest
from apps.common.permissions import (
    Role,
    Permission,
    has_permission,
    get_permissions_for_role,
    has_any_role,
    ROLE_PERMISSIONS,
)


class TestRoleEnum:

    def test_all_roles_exist(self):
        assert Role.SUPER_ADMIN == "SUPER_ADMIN"
        assert Role.LIBRARIAN == "LIBRARIAN"
        assert Role.ASSISTANT == "ASSISTANT"
        assert Role.USER == "USER"


class TestHasPermission:

    def test_super_admin_has_all_permissions(self):
        for perm in Permission:
            assert has_permission("SUPER_ADMIN", perm) is True

    def test_user_can_view_catalog(self):
        assert has_permission("USER", Permission.VIEW_CATALOG) is True

    def test_user_cannot_manage_books(self):
        assert has_permission("USER", Permission.MANAGE_BOOKS) is False

    def test_librarian_can_waive_fines(self):
        assert has_permission("LIBRARIAN", Permission.WAIVE_FINES) is True

    def test_assistant_cannot_waive_fines(self):
        assert has_permission("ASSISTANT", Permission.WAIVE_FINES) is False

    def test_invalid_role_returns_false(self):
        assert has_permission("INVALID_ROLE", Permission.VIEW_CATALOG) is False

    def test_empty_role_returns_false(self):
        assert has_permission("", Permission.VIEW_CATALOG) is False


class TestGetPermissionsForRole:

    def test_user_permissions(self):
        perms = get_permissions_for_role("USER")
        assert Permission.VIEW_CATALOG in perms
        assert Permission.BORROW_BOOKS in perms
        assert Permission.MANAGE_BOOKS not in perms

    def test_librarian_has_more_than_user(self):
        user_perms = get_permissions_for_role("USER")
        lib_perms = get_permissions_for_role("LIBRARIAN")
        assert len(lib_perms) > len(user_perms)

    def test_invalid_role_returns_empty(self):
        assert get_permissions_for_role("INVALID") == []


class TestHasAnyRole:

    def test_matching_role(self):
        assert has_any_role("USER", ["USER", "LIBRARIAN"]) is True

    def test_no_matching_role(self):
        assert has_any_role("USER", ["LIBRARIAN", "SUPER_ADMIN"]) is False

    def test_empty_allowed_list(self):
        assert has_any_role("USER", []) is False


class TestRolePermissionMatrix:

    def test_role_hierarchy_size(self):
        """Each higher role should have >= permissions of lower roles."""
        user_n = len(ROLE_PERMISSIONS[Role.USER])
        asst_n = len(ROLE_PERMISSIONS[Role.ASSISTANT])
        lib_n = len(ROLE_PERMISSIONS[Role.LIBRARIAN])
        admin_n = len(ROLE_PERMISSIONS[Role.SUPER_ADMIN])

        assert user_n < asst_n < lib_n < admin_n

    def test_user_permissions_subset_of_assistant(self):
        user_set = set(ROLE_PERMISSIONS[Role.USER])
        asst_set = set(ROLE_PERMISSIONS[Role.ASSISTANT])
        assert user_set.issubset(asst_set)
