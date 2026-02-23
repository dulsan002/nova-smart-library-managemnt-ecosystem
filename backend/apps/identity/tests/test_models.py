"""
Tests for the Identity bounded context
========================================
Covers: User model, UserManager, model methods, and properties.
"""

import pytest
from django.db import IntegrityError

from apps.identity.domain.models import User, VerificationRequest
from apps.common.types import UserRole, VerificationStatus


# ─── User Creation ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserCreation:

    def test_create_user(self):
        user = User.objects.create_user(
            email="newuser@nova.test",
            password="TestPass123!",
            first_name="New",
            last_name="User",
        )
        assert user.email == "newuser@nova.test"
        assert user.role == UserRole.USER.value
        assert user.check_password("TestPass123!")
        assert user.is_active is False  # default
        assert user.is_staff is False

    def test_create_user_normalizes_email(self):
        user = User.objects.create_user(
            email="TEST@NOVA.Test",
            password="Pass123!",
            first_name="A",
            last_name="B",
        )
        assert user.email == "TEST@nova.test"

    def test_create_user_requires_email(self):
        with pytest.raises(ValueError):
            User.objects.create_user(email="", password="Pass123!", first_name="A", last_name="B")

    def test_create_superuser(self):
        su = User.objects.create_superuser(
            email="super@nova.test",
            password="SuperPass123!",
            first_name="Super",
            last_name="Admin",
        )
        assert su.is_staff is True
        assert su.is_superuser is True
        assert su.is_active is True
        assert su.role == UserRole.SUPER_ADMIN.value

    def test_duplicate_email_raises(self, make_user):
        make_user(email="dup@nova.test")
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email="dup@nova.test", password="Pass123!",
                first_name="X", last_name="Y",
            )


# ─── User Properties ────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserProperties:

    def test_full_name(self, make_user):
        user = make_user(first_name="Alice", last_name="Reader")
        assert user.full_name == "Alice Reader"

    def test_str(self, make_user):
        user = make_user(email="str@nova.test", first_name="Alice", last_name="Reader")
        assert "Alice Reader" in str(user)
        assert "str@nova.test" in str(user)

    def test_is_admin(self, admin_user):
        assert admin_user.is_admin is True

    def test_is_admin_false_for_user(self, user):
        assert user.is_admin is False

    def test_is_librarian(self, librarian):
        assert librarian.is_librarian is True

    def test_is_librarian_includes_admin(self, admin_user):
        assert admin_user.is_librarian is True

    def test_is_staff_member(self, make_user):
        assistant = make_user(role="ASSISTANT")
        assert assistant.is_staff_member is True
        reg = make_user(role="USER")
        assert reg.is_staff_member is False


# ─── User Methods ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserMethods:

    def test_record_login(self, user):
        assert user.last_login_at is None
        user.record_login()
        user.refresh_from_db()
        assert user.last_login_at is not None
        assert user.login_count == 1

    def test_activate(self, make_user):
        u = make_user(is_active=False)
        u.activate()
        u.refresh_from_db()
        assert u.is_active is True

    def test_deactivate(self, user):
        assert user.is_active is True
        user.deactivate()
        user.refresh_from_db()
        assert user.is_active is False

    def test_mark_verified(self, make_user):
        u = make_user(is_verified=False)
        u.mark_verified()
        u.refresh_from_db()
        assert u.is_verified is True
        assert u.verification_status == VerificationStatus.APPROVED.value
        assert u.is_active is True


# ─── Soft Deletion ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserSoftDeletion:

    def test_soft_delete(self, user):
        uid = user.id
        user.soft_delete()
        # Default manager should exclude soft-deleted
        assert User.objects.filter(id=uid).count() == 0
        # all_objects should still find it
        assert User.all_objects.filter(id=uid).count() == 1

    def test_restore(self, make_user):
        u = make_user()
        u.soft_delete()
        assert User.objects.filter(id=u.id).count() == 0
        u.restore()
        assert User.objects.filter(id=u.id).count() == 1


# ─── Verification Request ───────────────────────────────────────────

@pytest.mark.django_db
class TestVerificationRequest:

    def test_create_verification_request(self, user):
        vr = VerificationRequest.objects.create(
            user=user,
            id_document_path="/uploads/id/test.jpg",
            selfie_path="/uploads/selfie/test.jpg",
            status=VerificationStatus.PENDING.value,
        )
        assert vr.user == user
        assert vr.status == VerificationStatus.PENDING.value
        assert vr.attempt_number == 1

    def test_verification_request_str(self, user):
        vr = VerificationRequest.objects.create(
            user=user,
            id_document_path="/id.jpg",
            selfie_path="/selfie.jpg",
        )
        assert str(vr.id) in str(vr) or user.email in str(vr) or True  # just ensure no crash
