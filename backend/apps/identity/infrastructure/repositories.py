"""
Nova — Identity Repositories
================================
Concrete (Django ORM) implementations of repository interfaces.
"""

from typing import Optional
from uuid import UUID

from apps.identity.application.interfaces import UserRepositoryInterface
from apps.identity.domain.models import User


class DjangoUserRepository(UserRepositoryInterface):
    """User repository backed by Django ORM."""

    def find_by_id(self, user_id: UUID) -> Optional[User]:
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def find_by_email(self, email: str) -> Optional[User]:
        try:
            return User.objects.get(email=email.lower())
        except User.DoesNotExist:
            return None

    def exists_by_email(self, email: str) -> bool:
        return User.objects.filter(email=email.lower()).exists()

    def save(self, user: User) -> None:
        user.save()
