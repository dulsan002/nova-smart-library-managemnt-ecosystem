"""
Nova — JWT Token Service
============================
Concrete implementation of TokenServiceInterface using PyJWT + Django ORM.
Implements refresh‑token rotation with family‑based revocation.
"""

import hashlib
import logging
import secrets
from datetime import timedelta
from typing import Optional
from uuid import UUID

import jwt
from django.conf import settings
from django.utils import timezone

from apps.common.exceptions import AuthenticationError, TokenError
from apps.identity.application import TokenPairDTO
from apps.identity.application.interfaces import TokenServiceInterface
from apps.identity.domain.models import RefreshToken

logger = logging.getLogger('nova.identity')


class JWTTokenService(TokenServiceInterface):
    """
    JWT access tokens (short-lived) + opaque refresh tokens stored in DB.
    Refresh tokens support rotation and family-based revocation.
    """

    def __init__(self):
        # Use the same secret key as django-graphql-jwt for consistency
        jwt_settings = getattr(settings, 'GRAPHQL_JWT', {})
        self._secret = jwt_settings.get('JWT_SECRET_KEY', settings.SECRET_KEY)
        self._algorithm = jwt_settings.get('JWT_ALGORITHM', 'HS256')
        jwt_conf = getattr(settings, 'GRAPHQL_JWT', {})
        self._access_lifetime = jwt_conf.get(
            'JWT_EXPIRATION_DELTA', timedelta(minutes=15),
        )
        self._refresh_lifetime = jwt_conf.get(
            'JWT_REFRESH_EXPIRATION_DELTA', timedelta(days=7),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_token_pair(
        self, user, device_fingerprint: Optional[str] = None,
    ) -> TokenPairDTO:
        access_token = self._issue_access_token(user)
        raw_refresh, refresh_obj = self._issue_refresh_token(
            user, device_fingerprint=device_fingerprint,
        )
        return TokenPairDTO(
            access_token=access_token,
            refresh_token=raw_refresh,
            expires_in=int(self._access_lifetime.total_seconds()),
        )

    def refresh_access_token(self, raw_refresh_token: str) -> TokenPairDTO:
        token_hash = RefreshToken.hash_token(raw_refresh_token)

        try:
            rt = RefreshToken.objects.select_related('user').get(token_hash=token_hash)
        except RefreshToken.DoesNotExist:
            raise TokenError(message='Invalid refresh token.')

        if rt.is_revoked:
            # Potential token reuse — revoke entire family
            RefreshToken.revoke_token_family(rt)
            logger.warning('Refresh token reuse detected, family revoked',
                           extra={'token_id': str(rt.id), 'user_id': str(rt.user_id)})
            raise TokenError(message='Token has been revoked.')

        if rt.expires_at < timezone.now():
            raise TokenError(message='Refresh token expired.')

        # Rotate: revoke old, issue new
        rt.revoke()

        user = rt.user
        if not user.is_active:
            raise AuthenticationError(message='Account is inactive.', code='ACCOUNT_INACTIVE')

        access_token = self._issue_access_token(user)
        raw_new, new_rt = self._issue_refresh_token(
            user,
            device_fingerprint=rt.device_fingerprint,
            rotated_from=rt,
        )

        return TokenPairDTO(
            access_token=access_token,
            refresh_token=raw_new,
            expires_in=int(self._access_lifetime.total_seconds()),
        )

    def revoke_refresh_token(self, token_hash: str) -> None:
        try:
            rt = RefreshToken.objects.get(token_hash=token_hash)
            rt.revoke()
        except RefreshToken.DoesNotExist:
            pass  # Idempotent

    def revoke_all_user_tokens(self, user_id: UUID) -> None:
        RefreshToken.revoke_all_for_user(user_id)

    def decode_access_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise TokenError(message='Access token expired.')
        except jwt.InvalidTokenError:
            raise TokenError(message='Invalid access token.')

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _issue_access_token(self, user) -> str:
        now = timezone.now()
        payload = {
            'sub': str(user.id),
            'email': user.email,
            'role': user.role,
            'is_verified': user.is_verified,
            'iat': now,
            'exp': now + self._access_lifetime,
            'type': 'access',
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def _issue_refresh_token(
        self,
        user,
        device_fingerprint: Optional[str] = None,
        rotated_from: Optional[RefreshToken] = None,
    ):
        raw_token = secrets.token_urlsafe(64)
        token_hash = RefreshToken.hash_token(raw_token)

        rt = RefreshToken.objects.create(
            user=user,
            token_hash=token_hash,
            device_fingerprint=device_fingerprint or '',
            expires_at=timezone.now() + self._refresh_lifetime,
            rotated_from=rotated_from,
        )
        return raw_token, rt
