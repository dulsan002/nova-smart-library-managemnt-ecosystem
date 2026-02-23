"""
Nova — Identity Application Services (Use Cases)
====================================================
Orchestrates identity domain logic behind clean interfaces.
"""

import logging
from typing import Optional
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.common.event_bus import DomainEvent, EventBus, EventTypes
from apps.common.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
    VerificationError,
)
from apps.common.validators import validate_email_format, validate_password_strength

from apps.identity.application import (
    ChangePasswordDTO,
    LoginDTO,
    RegisterUserDTO,
    TokenPairDTO,
    UpdateProfileDTO,
    UserProfileDTO,
    VerificationSubmitDTO,
)
from apps.identity.application.interfaces import (
    TokenServiceInterface,
    UserRepositoryInterface,
    VerificationServiceInterface,
)

logger = logging.getLogger('nova.identity')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user_to_profile(user) -> UserProfileDTO:
    return UserProfileDTO(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        role=user.role,
        is_verified=user.is_verified,
        verification_status=user.verification_status,
        avatar_url=user.avatar_url,
        phone_number=user.phone_number,
        date_of_birth=user.date_of_birth,
        institution_id=user.institution_id,
        last_login_at=user.last_login_at,
        login_count=user.login_count,
        created_at=user.created_at,
    )


# ---------------------------------------------------------------------------
# Use Cases
# ---------------------------------------------------------------------------

class RegisterUserUseCase:
    """
    Handles new user registration.
    - Validates input
    - Creates user (inactive until verified)
    - Publishes USER_REGISTERED event
    """

    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        token_service: TokenServiceInterface,
    ):
        self._user_repo = user_repo
        self._token_service = token_service

    @transaction.atomic
    def execute(self, dto: RegisterUserDTO) -> UserProfileDTO:
        # ---- Validation ----
        if not validate_email_format(dto.email):
            raise ValidationError(message='Invalid email format.', field='email')

        pw_result = validate_password_strength(dto.password)
        if not pw_result['is_valid']:
            raise ValidationError(
                message='; '.join(pw_result['issues']),
                field='password',
                details={'issues': pw_result['issues']},
            )

        if self._user_repo.exists_by_email(dto.email):
            raise ConflictError(
                message='An account with this email already exists.',
                code='EMAIL_EXISTS',
            )

        # ---- Create user ----
        from apps.identity.domain.models import User

        user = User.objects.create_user(
            email=dto.email,
            password=dto.password,
            first_name=dto.first_name,
            last_name=dto.last_name,
            phone_number=dto.phone_number,
            date_of_birth=dto.date_of_birth,
            institution_id=dto.institution_id,
        )

        # ---- Domain event ----
        EventBus.publish(DomainEvent(
            event_type=EventTypes.USER_REGISTERED,
            payload={
                'email': user.email,
                'role': user.role,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            metadata={'aggregate_id': str(user.id)},
        ))

        logger.info('User registered', extra={'user_id': str(user.id), 'email': user.email})
        return _user_to_profile(user)


class AuthenticateUserUseCase:
    """
    Handles email + password login.
    - Validates credentials
    - Records login
    - Issues JWT token pair
    """

    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        token_service: TokenServiceInterface,
    ):
        self._user_repo = user_repo
        self._token_service = token_service

    @transaction.atomic
    def execute(self, dto: LoginDTO) -> TokenPairDTO:
        user = self._user_repo.find_by_email(dto.email)

        if user is None or not user.check_password(dto.password):
            logger.warning('Failed login attempt', extra={'email': dto.email, 'ip': dto.ip_address})
            raise AuthenticationError(
                message='Invalid email or password.',
            )

        if not user.is_active:
            raise AuthenticationError(
                message='This account is deactivated. Please contact support.',
            )

        # ---- Record login ----
        user.record_login()

        # ---- Issue tokens ----
        token_pair = self._token_service.create_token_pair(
            user=user,
            device_fingerprint=dto.device_fingerprint,
        )

        # ---- Domain event ----
        EventBus.publish(DomainEvent(
            event_type=EventTypes.USER_LOGGED_IN,
            payload={
                'ip_address': dto.ip_address,
                'device_fingerprint': dto.device_fingerprint,
            },
            metadata={'aggregate_id': str(user.id)},
        ))

        logger.info('User authenticated', extra={'user_id': str(user.id)})
        return token_pair


class RefreshTokenUseCase:
    """
    Issues a new access+refresh pair from a valid refresh token.
    Implements token rotation (old token is revoked).
    """

    def __init__(self, token_service: TokenServiceInterface):
        self._token_service = token_service

    def execute(self, refresh_token: str) -> TokenPairDTO:
        return self._token_service.refresh_access_token(refresh_token)


class LogoutUseCase:
    """Revokes the user's current refresh token (and optionally all tokens)."""

    def __init__(self, token_service: TokenServiceInterface):
        self._token_service = token_service

    def execute(self, refresh_token_hash: str, revoke_all: bool = False, user_id: UUID = None):
        if revoke_all and user_id:
            self._token_service.revoke_all_user_tokens(user_id)
        else:
            self._token_service.revoke_refresh_token(refresh_token_hash)

        EventBus.publish(DomainEvent(
            event_type=EventTypes.USER_LOGGED_OUT,
            payload={'revoke_all': revoke_all},
            metadata={'aggregate_id': str(user_id) if user_id else 'unknown'},
        ))
        logger.info('User logged out', extra={'user_id': str(user_id) if user_id else 'N/A'})


class GetUserProfileUseCase:
    """Returns the profile of a user by ID."""

    def __init__(self, user_repo: UserRepositoryInterface):
        self._user_repo = user_repo

    def execute(self, user_id: UUID) -> UserProfileDTO:
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            raise NotFoundError(resource_type='User')
        return _user_to_profile(user)


class UpdateUserProfileUseCase:
    """Updates mutable profile fields."""

    def __init__(self, user_repo: UserRepositoryInterface):
        self._user_repo = user_repo

    @transaction.atomic
    def execute(self, user_id: UUID, dto: UpdateProfileDTO) -> UserProfileDTO:
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            raise NotFoundError(resource_type='User')

        # Apply only provided fields
        for field_name in (
            'first_name', 'last_name', 'phone_number',
            'date_of_birth', 'institution_id', 'avatar_url',
        ):
            value = getattr(dto, field_name, None)
            if value is not None:
                setattr(user, field_name, value)

        self._user_repo.save(user)

        EventBus.publish(DomainEvent(
            event_type=EventTypes.USER_PROFILE_UPDATED,
            payload={'updated_fields': [f for f in ('first_name', 'last_name', 'phone_number',
                                                     'date_of_birth', 'institution_id', 'avatar_url')
                                        if getattr(dto, f, None) is not None]},
            metadata={'aggregate_id': str(user.id)},
        ))
        return _user_to_profile(user)


class ChangePasswordUseCase:
    """Changes the user's password after verifying the current one."""

    def __init__(self, user_repo: UserRepositoryInterface):
        self._user_repo = user_repo

    @transaction.atomic
    def execute(self, user_id: UUID, dto: ChangePasswordDTO) -> bool:
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            raise NotFoundError(resource_type='User')

        if not user.check_password(dto.old_password):
            raise AuthenticationError(
                message='Current password is incorrect.',
            )

        validate_password_strength(dto.new_password)
        user.set_password(dto.new_password)
        self._user_repo.save(user)

        # Revoke all tokens when password changes
        from apps.identity.domain.models import RefreshToken
        RefreshToken.revoke_all_for_user(user.id)

        EventBus.publish(DomainEvent(
            event_type=EventTypes.PASSWORD_CHANGED,
            payload={},
            metadata={'aggregate_id': str(user.id)},
        ))
        logger.info('Password changed', extra={'user_id': str(user.id)})
        return True


class SubmitVerificationUseCase:
    """
    Submits a document + selfie for AI-powered identity verification.
    Creates a VerificationRequest and queues async processing.
    """

    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        verification_service: VerificationServiceInterface,
    ):
        self._user_repo = user_repo
        self._verification_service = verification_service

    @transaction.atomic
    def execute(self, dto: VerificationSubmitDTO):
        from apps.identity.domain.models import VerificationRequest

        user = self._user_repo.find_by_id(dto.user_id)
        if user is None:
            raise NotFoundError(resource_type='User')

        if user.verification_status == 'APPROVED':
            raise VerificationError(
                message='User is already verified.',
                code='ALREADY_VERIFIED',
            )

        # Check for pending verification
        pending = VerificationRequest.objects.filter(
            user=user, status='PENDING',
        ).exists()
        if pending:
            raise VerificationError(
                message='A verification request is already pending.',
                code='VERIFICATION_PENDING',
            )

        # Count previous attempts
        attempt_count = VerificationRequest.objects.filter(user=user).count()

        max_attempts = getattr(settings, 'VERIFICATION_MAX_ATTEMPTS', 3)
        if attempt_count >= max_attempts:
            raise VerificationError(
                message=f'Maximum verification attempts ({max_attempts}) exceeded.',
                code='MAX_ATTEMPTS_EXCEEDED',
            )

        request = VerificationRequest.objects.create(
            user=user,
            id_document_path=dto.id_document_path,
            selfie_path=dto.selfie_path,
            attempt_number=attempt_count + 1,
            ip_address=dto.ip_address,
            status='PENDING',
        )

        user.verification_status = 'PENDING'
        self._user_repo.save(user)

        # Queue async processing
        self._verification_service.process_verification_async(request.id)

        EventBus.publish(DomainEvent(
            event_type=EventTypes.VERIFICATION_SUBMITTED,
            payload={'request_id': str(request.id), 'attempt': request.attempt_number},
            metadata={'aggregate_id': str(user.id)},
        ))
        logger.info('Verification submitted', extra={
            'user_id': str(user.id),
            'request_id': str(request.id),
        })
        return request


class AdminManageUserUseCase:
    """Admin operations: activate/deactivate/change role."""

    def __init__(self, user_repo: UserRepositoryInterface):
        self._user_repo = user_repo

    @transaction.atomic
    def activate_user(self, user_id: UUID) -> UserProfileDTO:
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            raise NotFoundError(resource_type='User')
        user.activate()
        return _user_to_profile(user)

    @transaction.atomic
    def deactivate_user(self, user_id: UUID) -> UserProfileDTO:
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            raise NotFoundError(resource_type='User')
        user.deactivate()
        return _user_to_profile(user)

    @transaction.atomic
    def change_role(self, user_id: UUID, new_role: str) -> UserProfileDTO:
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            raise NotFoundError(resource_type='User')

        valid_roles = ['SUPER_ADMIN', 'LIBRARIAN', 'ASSISTANT', 'USER']
        if new_role not in valid_roles:
            raise ValidationError(
                message=f'Invalid role: {new_role}',
                code='INVALID_ROLE',
            )
        user.role = new_role
        self._user_repo.save(user)

        EventBus.publish(DomainEvent(
            event_type=EventTypes.USER_ROLE_CHANGED,
            payload={'new_role': new_role},
            metadata={'aggregate_id': str(user.id)},
        ))
        return _user_to_profile(user)
