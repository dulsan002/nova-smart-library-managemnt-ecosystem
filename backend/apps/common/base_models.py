"""
Nova — Base Models
===================
Abstract base models providing common fields and behaviors for all domain models.
These enforce consistency across bounded contexts.
"""

import uuid

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Abstract base model providing created_at and updated_at timestamps.
    All domain models should inherit from this.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text='Timestamp when this record was created.'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Timestamp when this record was last updated.'
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']


class UUIDModel(TimeStampedModel):
    """
    Abstract base model using UUID as primary key.
    Combines UUID PK with timestamps.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Unique identifier for this record.'
    )

    class Meta:
        abstract = True


class SoftDeletableModel(models.Model):
    """
    Abstract mixin providing soft deletion capability.
    Records are marked as deleted rather than physically removed.
    """
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text='Timestamp when this record was soft-deleted. NULL means active.'
    )

    class Meta:
        abstract = True

    @property
    def is_deleted(self) -> bool:
        """Check if this record has been soft-deleted."""
        return self.deleted_at is not None

    def soft_delete(self):
        """Mark this record as soft-deleted."""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at', 'updated_at'])

    def restore(self):
        """Restore a soft-deleted record."""
        self.deleted_at = None
        self.save(update_fields=['deleted_at', 'updated_at'])


class SoftDeletableManager(models.Manager):
    """
    Manager that filters out soft-deleted records by default.
    Use .all_with_deleted() to include deleted records.
    """

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def all_with_deleted(self):
        return super().get_queryset()

    def deleted_only(self):
        return super().get_queryset().filter(deleted_at__isnull=False)


class VersionedModel(models.Model):
    """
    Abstract mixin providing optimistic concurrency control via version field.
    Used for resources where concurrent updates must be detected (e.g., book stock).
    """
    version = models.PositiveIntegerField(
        default=1,
        help_text='Version number for optimistic concurrency control.'
    )

    class Meta:
        abstract = True

    def save_with_version_check(self, expected_version: int, **kwargs):
        """
        Save only if the current version matches the expected version.
        Raises ConcurrencyError if versions don't match.

        Args:
            expected_version: The version the caller believes is current.
        """
        from apps.common.exceptions import ConcurrencyError

        updated = type(self).objects.filter(
            pk=self.pk,
            version=expected_version
        ).update(
            version=models.F('version') + 1,
            **{k: v for k, v in kwargs.items() if k != 'version'}
        )

        if updated == 0:
            raise ConcurrencyError(
                f'{type(self).__name__} with pk={self.pk} has been modified '
                f'by another process. Expected version {expected_version}.'
            )

        self.refresh_from_db()
        return self
