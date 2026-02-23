"""
Nova — Custom User Manager
============================
Manager for the custom User model with email-based authentication.
"""

from django.contrib.auth.models import BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier.
    Filters out soft-deleted users by default.
    """

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def all_with_deleted(self):
        return super().get_queryset()

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user with the given email and password.
        """
        if not email:
            raise ValueError('Email address is required.')

        email = self.normalize_email(email)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', False)  # Requires verification

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser with the given email and password.
        Superusers are automatically active and verified.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('role', 'SUPER_ADMIN')
        extra_fields.setdefault('verification_status', 'APPROVED')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

    def active_users(self):
        """Return only active, non-deleted users."""
        return self.get_queryset().filter(is_active=True)

    def by_role(self, role: str):
        """Filter users by role."""
        return self.get_queryset().filter(role=role, is_active=True)
