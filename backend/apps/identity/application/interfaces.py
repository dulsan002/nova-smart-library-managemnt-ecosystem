"""
Nova — Identity Application Interfaces
==========================================
Abstract interfaces (ports) for the identity bounded context.
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from apps.identity.application import (
    LoginDTO,
    RegisterUserDTO,
    TokenPairDTO,
    UpdateProfileDTO,
    UserProfileDTO,
    VerificationResultDTO,
    VerificationSubmitDTO,
)


class UserRepositoryInterface(ABC):
    """Port for user persistence."""

    @abstractmethod
    def find_by_id(self, user_id: UUID):
        ...

    @abstractmethod
    def find_by_email(self, email: str):
        ...

    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        ...

    @abstractmethod
    def save(self, user) -> None:
        ...


class TokenServiceInterface(ABC):
    """Port for JWT token operations."""

    @abstractmethod
    def create_token_pair(self, user, device_fingerprint: Optional[str] = None) -> TokenPairDTO:
        ...

    @abstractmethod
    def refresh_access_token(self, refresh_token: str) -> TokenPairDTO:
        ...

    @abstractmethod
    def revoke_refresh_token(self, token_hash: str) -> None:
        ...

    @abstractmethod
    def revoke_all_user_tokens(self, user_id: UUID) -> None:
        ...

    @abstractmethod
    def decode_access_token(self, token: str) -> dict:
        ...


class VerificationServiceInterface(ABC):
    """Port for AI-powered identity verification."""

    @abstractmethod
    def submit_verification(self, dto: VerificationSubmitDTO) -> VerificationResultDTO:
        ...

    @abstractmethod
    def process_verification_async(self, request_id: UUID) -> None:
        ...


class PasswordResetServiceInterface(ABC):
    """Port for password reset operations."""

    @abstractmethod
    def request_reset(self, email: str) -> bool:
        ...

    @abstractmethod
    def confirm_reset(self, token: str, new_password: str) -> bool:
        ...
