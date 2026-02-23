"""
Nova — Identity Application DTOs
==================================
Data Transfer Objects for identity operations.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class RegisterUserDTO:
    email: str
    password: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    institution_id: Optional[str] = None


@dataclass(frozen=True)
class LoginDTO:
    email: str
    password: str
    device_fingerprint: Optional[str] = None
    ip_address: Optional[str] = None


@dataclass(frozen=True)
class TokenPairDTO:
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = 'Bearer'


@dataclass(frozen=True)
class UserProfileDTO:
    id: UUID
    email: str
    first_name: str
    last_name: str
    full_name: str
    role: str
    is_verified: bool
    verification_status: str
    avatar_url: Optional[str]
    phone_number: Optional[str]
    date_of_birth: Optional[date]
    institution_id: Optional[str]
    last_login_at: Optional[datetime]
    login_count: int
    created_at: datetime


@dataclass(frozen=True)
class UpdateProfileDTO:
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    institution_id: Optional[str] = None
    avatar_url: Optional[str] = None


@dataclass(frozen=True)
class ChangePasswordDTO:
    old_password: str
    new_password: str


@dataclass(frozen=True)
class VerificationSubmitDTO:
    user_id: UUID
    id_document_path: str
    selfie_path: str
    ip_address: Optional[str] = None


@dataclass(frozen=True)
class VerificationResultDTO:
    request_id: UUID
    status: str
    extracted_name: Optional[str] = None
    extracted_id_number: Optional[str] = None
    ocr_confidence: Optional[float] = None
    face_match_score: Optional[float] = None
    rejection_reason: Optional[str] = None


@dataclass(frozen=True)
class PasswordResetRequestDTO:
    email: str


@dataclass(frozen=True)
class PasswordResetConfirmDTO:
    token: str
    new_password: str
