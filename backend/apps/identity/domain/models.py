"""
Nova — Identity Domain Models
================================
Core user model, verification requests, and refresh tokens.
"""

import uuid
import hashlib

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone

from apps.common.base_models import TimeStampedModel, UUIDModel, SoftDeletableModel, SoftDeletableManager
from apps.common.types import UserRole, VerificationStatus
from apps.identity.domain.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin, UUIDModel, SoftDeletableModel):
    """
    Custom user model for the Nova system.
    Uses email as the unique identifier instead of username.
    Supports soft deletion and role-based access control.
    """

    ROLE_CHOICES = [
        (UserRole.SUPER_ADMIN.value, 'Super Administrator'),
        (UserRole.LIBRARIAN.value, 'Librarian'),
        (UserRole.ASSISTANT.value, 'Library Assistant'),
        (UserRole.USER.value, 'User'),
    ]

    email = models.EmailField(
        unique=True,
        max_length=255,
        db_index=True,
        help_text='Primary email address used for authentication.'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True, default='')
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=UserRole.USER.value,
        db_index=True,
    )
    is_active = models.BooleanField(
        default=False,
        help_text='Whether the user can log in. Set to True after verification.'
    )
    is_staff = models.BooleanField(
        default=False,
        help_text='Whether the user can access the Django admin.'
    )
    is_verified = models.BooleanField(
        default=False,
        help_text='Whether the user has passed identity verification.'
    )
    verification_status = models.CharField(
        max_length=20,
        choices=[(s.value, s.value) for s in VerificationStatus],
        default=VerificationStatus.PENDING.value,
    )
    avatar_url = models.URLField(max_length=500, blank=True, default='')
    date_of_birth = models.DateField(null=True, blank=True)
    institution_id = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text='Student/staff ID number.'
    )
    nic_number = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text='National Identity Card number.'
    )
    last_login_at = models.DateTimeField(null=True, blank=True)
    login_count = models.PositiveIntegerField(default=0)

    # Manager
    objects = UserManager()
    all_objects = models.Manager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'identity_users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email'], name='idx_user_email'),
            models.Index(fields=['role', 'is_active'], name='idx_user_role_active'),
            models.Index(
                fields=['deleted_at'],
                name='idx_user_not_deleted',
                condition=models.Q(deleted_at__isnull=True),
            ),
        ]

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.email})'

    @property
    def full_name(self) -> str:
        return f'{self.first_name} {self.last_name}'.strip()

    def record_login(self):
        """Record a successful login."""
        self.last_login_at = timezone.now()
        self.login_count = models.F('login_count') + 1
        self.save(update_fields=['last_login_at', 'login_count', 'updated_at'])

    def activate(self):
        """Activate the user account."""
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])

    def deactivate(self):
        """Deactivate the user account."""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])

    def mark_verified(self):
        """Mark the user as identity-verified."""
        self.is_verified = True
        self.verification_status = VerificationStatus.APPROVED.value
        self.is_active = True
        self.save(update_fields=[
            'is_verified', 'verification_status', 'is_active', 'updated_at'
        ])

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.SUPER_ADMIN.value

    @property
    def is_librarian(self) -> bool:
        return self.role in [UserRole.SUPER_ADMIN.value, UserRole.LIBRARIAN.value]

    @property
    def is_staff_member(self) -> bool:
        return self.role in [
            UserRole.SUPER_ADMIN.value,
            UserRole.LIBRARIAN.value,
            UserRole.ASSISTANT.value,
        ]


class RoleConfig(UUIDModel, TimeStampedModel):
    """
    Dynamic role permission configuration.
    Super admins can create custom roles or override built-in role permissions.
    Permissions are stored as a JSON dict:
      { "module_key": ["create", "read", "update", "delete"], ... }
    """

    MODULE_CHOICES = [
        ('books', 'Books'),
        ('authors', 'Authors'),
        ('digital_content', 'Digital Content'),
        ('users', 'Users'),
        ('employees', 'Employees'),
        ('circulation', 'Circulation'),
        ('assets', 'Assets'),
        ('analytics', 'Analytics'),
        ('ai', 'AI Models & Config'),
        ('audit', 'Audit Log'),
        ('settings', 'Settings'),
        ('roles', 'Roles & Permissions'),
        ('members', 'Members'),
    ]

    VALID_ACTIONS = ('create', 'read', 'update', 'delete')

    role_key = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Unique machine-readable key for this role e.g. LIBRARIAN, CUSTOM_ROLE.',
    )
    display_name = models.CharField(
        max_length=100,
        help_text='Human-readable name e.g. "Librarian", "Senior Assistant".',
    )
    description = models.TextField(blank=True, default='')
    permissions = models.JSONField(
        default=dict,
        help_text='JSON dict mapping module keys to lists of allowed actions.',
    )
    is_system = models.BooleanField(
        default=False,
        help_text='System roles (SUPER_ADMIN, LIBRARIAN, etc.) cannot be deleted.',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'identity_role_configs'
        verbose_name = 'Role Configuration'
        verbose_name_plural = 'Role Configurations'
        ordering = ['display_name']

    def __str__(self):
        return f'{self.display_name} ({self.role_key})'

    @classmethod
    def get_modules(cls):
        """Return list of available module keys."""
        return [key for key, _ in cls.MODULE_CHOICES]

    @classmethod
    def get_module_labels(cls):
        """Return list of {key, label} dicts for all modules."""
        return [{'key': key, 'label': label} for key, label in cls.MODULE_CHOICES]

    def has_module_action(self, module: str, action: str) -> bool:
        """Check whether this role grants a specific action on a module."""
        return action in self.permissions.get(module, [])


class Member(UUIDModel, TimeStampedModel, SoftDeletableModel):
    """
    Library member / reader / patron record.
    Tracks people who use the library — may or may not have a system user account.
    This is the *library card holder* entity, separate from system users and employees.
    """

    MEMBERSHIP_TYPE_CHOICES = [
        ('STUDENT', 'Student'),
        ('FACULTY', 'Faculty'),
        ('STAFF', 'Staff'),
        ('PUBLIC', 'Public'),
        ('SENIOR', 'Senior Citizen'),
        ('CHILD', 'Child'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('EXPIRED', 'Expired'),
        ('REVOKED', 'Revoked'),
    ]

    # Optional link to a system user account
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='member_profile',
        help_text='Linked system user account (optional).',
    )

    # Core identity
    membership_number = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        help_text='Library card / membership number.',
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=255, blank=True, default='')
    phone_number = models.CharField(max_length=20, blank=True, default='')
    date_of_birth = models.DateField(null=True, blank=True)
    nic_number = models.CharField(max_length=20, blank=True, default='')
    address = models.TextField(blank=True, default='')

    # Membership info
    membership_type = models.CharField(
        max_length=20,
        choices=MEMBERSHIP_TYPE_CHOICES,
        default='PUBLIC',
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        db_index=True,
    )
    joined_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)
    max_borrows = models.PositiveSmallIntegerField(
        default=5,
        help_text='Maximum simultaneous borrows allowed.',
    )

    # Emergency / guardian
    emergency_contact_name = models.CharField(max_length=200, blank=True, default='')
    emergency_contact_phone = models.CharField(max_length=20, blank=True, default='')

    notes = models.TextField(blank=True, default='', help_text='Internal admin notes.')

    objects = SoftDeletableManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'identity_members'
        verbose_name = 'Library Member'
        verbose_name_plural = 'Library Members'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['membership_number'], name='idx_member_number'),
            models.Index(fields=['status', 'membership_type'], name='idx_member_status_type'),
        ]

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.membership_number})'

    @property
    def full_name(self) -> str:
        return f'{self.first_name} {self.last_name}'.strip()

    @property
    def is_active_member(self) -> bool:
        return self.status == 'ACTIVE'


class VerificationRequest(UUIDModel):
    """
    Stores identity verification attempts.
    Each attempt captures the ID document, selfie, and AI processing results.
    """

    STATUS_CHOICES = [(s.value, s.value) for s in VerificationStatus]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='verification_requests',
    )
    id_document_path = models.CharField(max_length=500)
    selfie_path = models.CharField(max_length=500)

    # OCR Results
    extracted_name = models.CharField(max_length=200, blank=True, default='')
    extracted_id_number = models.CharField(max_length=100, blank=True, default='')
    ocr_confidence = models.DecimalField(
        max_digits=5, decimal_places=4, null=True, blank=True,
    )

    # Face Match Results
    face_match_score = models.DecimalField(
        max_digits=5, decimal_places=4, null=True, blank=True,
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=VerificationStatus.PENDING.value,
        db_index=True,
    )
    rejection_reason = models.TextField(blank=True, default='')

    # Review
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_verifications',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    attempt_number = models.PositiveSmallIntegerField(default=1)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'identity_verification_requests'
        verbose_name = 'Verification Request'
        verbose_name_plural = 'Verification Requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status'], name='idx_verification_user_status'),
            models.Index(fields=['status', 'created_at'], name='idx_verification_pending'),
        ]

    def __str__(self):
        return f'Verification for {self.user.email} — {self.status}'

    def approve(self, reviewer: User = None):
        """Approve this verification request."""
        self.status = VerificationStatus.APPROVED.value
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save(update_fields=[
            'status', 'reviewed_by', 'reviewed_at', 'updated_at'
        ])
        self.user.mark_verified()

    def reject(self, reason: str, reviewer: User = None):
        """Reject this verification request."""
        self.status = VerificationStatus.REJECTED.value
        self.rejection_reason = reason
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save(update_fields=[
            'status', 'rejection_reason', 'reviewed_by', 'reviewed_at', 'updated_at',
        ])

    def queue_for_manual_review(self):
        """Move to manual review queue."""
        self.status = VerificationStatus.MANUAL_REVIEW.value
        self.save(update_fields=['status', 'updated_at'])


class RefreshToken(UUIDModel):
    """
    Stores hashed refresh tokens for JWT rotation.
    Each token is single-use — rotation creates a new token and revokes the old.
    Token family tracking enables detection of token theft.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='refresh_tokens',
    )
    token_hash = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text='SHA-256 hash of the refresh token value.',
    )
    device_fingerprint = models.CharField(max_length=255, blank=True, default='')
    is_revoked = models.BooleanField(default=False)
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    rotated_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rotated_to',
    )
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'identity_refresh_tokens'
        verbose_name = 'Refresh Token'
        verbose_name_plural = 'Refresh Tokens'
        indexes = [
            models.Index(fields=['token_hash'], name='idx_refresh_token_hash'),
            models.Index(fields=['user', 'is_revoked'], name='idx_refresh_user_active'),
        ]

    def __str__(self):
        status = 'revoked' if self.is_revoked else 'active'
        return f'Token for {self.user.email} ({status})'

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_revoked and not self.is_expired

    def revoke(self):
        """Revoke this refresh token."""
        self.is_revoked = True
        self.revoked_at = timezone.now()
        self.save(update_fields=['is_revoked', 'revoked_at', 'updated_at'])

    @staticmethod
    def hash_token(raw_token: str) -> str:
        """Generate SHA-256 hash of a raw token string."""
        return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

    @classmethod
    def revoke_all_for_user(cls, user: User):
        """Revoke all active refresh tokens for a user (force logout everywhere)."""
        cls.objects.filter(
            user=user,
            is_revoked=False,
        ).update(
            is_revoked=True,
            revoked_at=timezone.now(),
        )

    @classmethod
    def revoke_token_family(cls, token: 'RefreshToken'):
        """
        Revoke entire token family (all tokens derived from the same chain).
        This is triggered when a revoked token is reused (potential theft).
        """
        # Revoke all tokens for this user as a security measure
        cls.revoke_all_for_user(token.user)
