"""
Tests for Identity Application Services (Use Cases)
=====================================================
Tests use mocked repository & token service interfaces.
"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

pytestmark = pytest.mark.django_db

from apps.common.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
)
from apps.identity.application import (
    LoginDTO,
    RegisterUserDTO,
    UpdateProfileDTO,
)
from apps.identity.application.services import (
    RegisterUserUseCase,
    AuthenticateUserUseCase,
    RefreshTokenUseCase,
    LogoutUseCase,
    GetUserProfileUseCase,
    UpdateUserProfileUseCase,
)


# ─── Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def mock_user_repo():
    return MagicMock()


@pytest.fixture
def mock_token_service():
    return MagicMock()


def _fake_user(**overrides):
    """Return a mock user with sensible defaults."""
    u = MagicMock()
    defaults = {
        "id": uuid4(),
        "email": "test@nova.test",
        "first_name": "Test",
        "last_name": "User",
        "full_name": "Test User",
        "role": "USER",
        "is_verified": True,
        "verification_status": "APPROVED",
        "avatar_url": "",
        "phone_number": "",
        "date_of_birth": None,
        "institution_id": "",
        "last_login_at": None,
        "login_count": 0,
        "created_at": None,
        "is_active": True,
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(u, k, v)
    u.check_password = MagicMock(return_value=True)
    u.record_login = MagicMock()
    return u


# ─── RegisterUserUseCase ────────────────────────────────────────────

class TestRegisterUserUseCase:

    def test_successful_registration(self, mock_user_repo, mock_token_service):
        mock_user_repo.exists_by_email.return_value = False

        uc = RegisterUserUseCase(mock_user_repo, mock_token_service)
        dto = RegisterUserDTO(
            email="new@nova.test",
            password="StrongP@ss123",
            first_name="New",
            last_name="User",
            phone_number="",
            date_of_birth=None,
            institution_id="",
        )

        with patch("apps.identity.domain.models.User") as MockUser:
            fake = _fake_user(email="new@nova.test")
            MockUser.objects.create_user.return_value = fake

            profile = uc.execute(dto)

        assert profile.email == "new@nova.test"

    def test_duplicate_email_raises_conflict(self, mock_user_repo, mock_token_service):
        mock_user_repo.exists_by_email.return_value = True

        uc = RegisterUserUseCase(mock_user_repo, mock_token_service)
        dto = RegisterUserDTO(
            email="dup@nova.test",
            password="StrongP@ss123",
            first_name="A",
            last_name="B",
            phone_number="",
            date_of_birth=None,
            institution_id="",
        )

        with pytest.raises(ConflictError, match="already exists"):
            uc.execute(dto)


# ─── AuthenticateUserUseCase ────────────────────────────────────────

class TestAuthenticateUserUseCase:

    def test_successful_login(self, mock_user_repo, mock_token_service):
        user = _fake_user()
        mock_user_repo.find_by_email.return_value = user
        mock_token_service.create_token_pair.return_value = MagicMock(
            access_token="acc", refresh_token="ref"
        )

        uc = AuthenticateUserUseCase(mock_user_repo, mock_token_service)
        dto = LoginDTO(email="test@nova.test", password="Pass", ip_address="127.0.0.1", device_fingerprint="")

        result = uc.execute(dto)
        assert result.access_token == "acc"
        user.record_login.assert_called_once()

    def test_wrong_password_raises(self, mock_user_repo, mock_token_service):
        user = _fake_user()
        user.check_password.return_value = False
        mock_user_repo.find_by_email.return_value = user

        uc = AuthenticateUserUseCase(mock_user_repo, mock_token_service)
        dto = LoginDTO(email="test@nova.test", password="wrong", ip_address="127.0.0.1", device_fingerprint="")

        with pytest.raises(AuthenticationError, match="Invalid"):
            uc.execute(dto)

    def test_nonexistent_user_raises(self, mock_user_repo, mock_token_service):
        mock_user_repo.find_by_email.return_value = None

        uc = AuthenticateUserUseCase(mock_user_repo, mock_token_service)
        dto = LoginDTO(email="noone@nova.test", password="Pass", ip_address="127.0.0.1", device_fingerprint="")

        with pytest.raises(AuthenticationError):
            uc.execute(dto)

    def test_inactive_account_raises(self, mock_user_repo, mock_token_service):
        user = _fake_user(is_active=False)
        mock_user_repo.find_by_email.return_value = user

        uc = AuthenticateUserUseCase(mock_user_repo, mock_token_service)
        dto = LoginDTO(email="test@nova.test", password="Pass", ip_address="127.0.0.1", device_fingerprint="")

        with pytest.raises(AuthenticationError, match="deactivated"):
            uc.execute(dto)


# ─── RefreshTokenUseCase ────────────────────────────────────────────

class TestRefreshTokenUseCase:

    def test_delegates_to_token_service(self, mock_token_service):
        mock_token_service.refresh_access_token.return_value = MagicMock()

        uc = RefreshTokenUseCase(mock_token_service)
        uc.execute("some-refresh-token")

        mock_token_service.refresh_access_token.assert_called_once_with("some-refresh-token")


# ─── LogoutUseCase ──────────────────────────────────────────────────

class TestLogoutUseCase:

    def test_revoke_single_token(self, mock_token_service):
        uc = LogoutUseCase(mock_token_service)
        uc.execute("token-hash")
        mock_token_service.revoke_refresh_token.assert_called_once_with("token-hash")

    def test_revoke_all_tokens(self, mock_token_service):
        uid = uuid4()
        uc = LogoutUseCase(mock_token_service)
        uc.execute("token-hash", revoke_all=True, user_id=uid)
        mock_token_service.revoke_all_user_tokens.assert_called_once_with(uid)


# ─── GetUserProfileUseCase ──────────────────────────────────────────

class TestGetUserProfileUseCase:

    def test_returns_profile(self, mock_user_repo):
        user = _fake_user()
        mock_user_repo.find_by_id.return_value = user

        uc = GetUserProfileUseCase(mock_user_repo)
        profile = uc.execute(user.id)
        assert profile.email == user.email

    def test_not_found_raises(self, mock_user_repo):
        mock_user_repo.find_by_id.return_value = None

        uc = GetUserProfileUseCase(mock_user_repo)
        with pytest.raises(NotFoundError):
            uc.execute(uuid4())


# ─── UpdateUserProfileUseCase ───────────────────────────────────────

class TestUpdateUserProfileUseCase:

    def test_updates_fields(self, mock_user_repo):
        user = _fake_user()
        mock_user_repo.find_by_id.return_value = user

        uc = UpdateUserProfileUseCase(mock_user_repo)
        dto = UpdateProfileDTO(
            first_name="Updated",
            last_name=None,
            phone_number="+1234567890",
            date_of_birth=None,
            institution_id=None,
            avatar_url=None,
        )
        uc.execute(user.id, dto)

        assert user.first_name == "Updated"
        assert user.phone_number == "+1234567890"
