"""
Nova — Digital Content Domain Models
========================================
DigitalAsset, ReadingSession, Bookmark, Highlight, UserLibrary.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.base_models import UUIDModel, SoftDeletableModel


class DigitalAsset(UUIDModel, SoftDeletableModel):
    """
    A digital file associated with a book — eBook (EPUB/PDF) or Audiobook (MP3).
    A single Book can have multiple digital assets (one per format).
    """

    ASSET_TYPE_CHOICES = [
        ('EBOOK_EPUB', 'eBook (EPUB)'),
        ('EBOOK_PDF', 'eBook (PDF)'),
        ('AUDIOBOOK', 'Audiobook'),
    ]

    book = models.ForeignKey(
        'catalog.Book',
        on_delete=models.CASCADE,
        related_name='digital_assets',
    )
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPE_CHOICES, db_index=True)

    # File storage
    file_path = models.CharField(max_length=500, help_text='Relative path in object storage.')
    file_size_bytes = models.BigIntegerField(default=0)
    file_hash = models.CharField(max_length=128, blank=True, default='',
                                 help_text='SHA-256 hash for integrity.')
    mime_type = models.CharField(max_length=100, blank=True, default='')

    # Audiobook-specific
    duration_seconds = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Total duration for audiobooks.',
    )
    narrator = models.CharField(max_length=200, blank=True, default='')

    # eBook-specific
    total_pages = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Total page count for eBooks.',
    )

    # Metadata
    is_drm_protected = models.BooleanField(default=False)
    upload_completed = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='uploaded_assets',
    )

    class Meta:
        db_table = 'digital_content_asset'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['book', 'asset_type'], name='idx_asset_book_type'),
            models.Index(fields=['asset_type'], name='idx_asset_type'),
        ]
        # One asset per type per book
        unique_together = [('book', 'asset_type')]

    def __str__(self):
        return f'{self.book.title} — {self.get_asset_type_display()}'

    @property
    def is_ebook(self) -> bool:
        return self.asset_type.startswith('EBOOK')

    @property
    def is_audiobook(self) -> bool:
        return self.asset_type == 'AUDIOBOOK'


class ReadingSession(UUIDModel):
    """
    Tracks a user's reading or listening session in the digital library.
    Used for KP calculation and analytics.
    """

    SESSION_TYPE_CHOICES = [
        ('READING', 'Reading'),
        ('LISTENING', 'Listening'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('PAUSED', 'Paused'),
        ('COMPLETED', 'Completed'),
        ('ABANDONED', 'Abandoned'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reading_sessions',
    )
    digital_asset = models.ForeignKey(
        DigitalAsset,
        on_delete=models.CASCADE,
        related_name='sessions',
    )
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)

    # Progress
    progress_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text='0.00 to 100.00',
    )
    last_position = models.JSONField(
        null=True, blank=True,
        help_text='Bookmark position: {"page": N} or {"seconds": N}.',
    )

    # KP awarded for this session
    kp_awarded = models.PositiveIntegerField(default=0)

    # Device info
    device_type = models.CharField(max_length=50, blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'digital_content_reading_session'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', '-started_at'], name='idx_session_user_time'),
            models.Index(fields=['digital_asset', 'user'], name='idx_session_asset_user'),
            models.Index(fields=['status'], name='idx_session_status'),
            models.Index(fields=['session_type'], name='idx_session_type'),
        ]

    def __str__(self):
        return f'{self.user} — {self.session_type} ({self.status})'

    def end_session(self):
        self.status = 'COMPLETED'
        self.ended_at = timezone.now()
        if self.started_at:
            delta = (self.ended_at - self.started_at).total_seconds()
            self.duration_seconds = int(delta)
        self.save(update_fields=[
            'status', 'ended_at', 'duration_seconds', 'updated_at',
        ])

    def pause_session(self):
        self.status = 'PAUSED'
        self.save(update_fields=['status', 'updated_at'])

    def resume_session(self):
        self.status = 'ACTIVE'
        self.save(update_fields=['status', 'updated_at'])

    def update_progress(self, percent: float, position: dict = None):
        from decimal import Decimal
        self.progress_percent = Decimal(str(min(percent, 100.0)))
        if position:
            self.last_position = position
        self.save(update_fields=['progress_percent', 'last_position', 'updated_at'])


class Bookmark(UUIDModel):
    """User bookmark in a digital asset."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookmarks',
    )
    digital_asset = models.ForeignKey(
        DigitalAsset,
        on_delete=models.CASCADE,
        related_name='bookmarks',
    )
    title = models.CharField(max_length=200, blank=True, default='')
    position = models.JSONField(
        help_text='{"page": N, "offset": N} or {"seconds": N}',
    )
    note = models.TextField(blank=True, default='')
    color = models.CharField(max_length=20, blank=True, default='yellow')

    class Meta:
        db_table = 'digital_content_bookmark'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'digital_asset'], name='idx_bookmark_user_asset'),
        ]

    def __str__(self):
        return f'Bookmark: {self.title or "untitled"} ({self.user})'


class Highlight(UUIDModel):
    """User text highlight in an eBook."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='highlights',
    )
    digital_asset = models.ForeignKey(
        DigitalAsset,
        on_delete=models.CASCADE,
        related_name='highlights',
    )
    text = models.TextField()
    position_start = models.JSONField(help_text='{"page": N, "offset": N}')
    position_end = models.JSONField(help_text='{"page": N, "offset": N}')
    color = models.CharField(max_length=20, default='yellow')
    note = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'digital_content_highlight'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'digital_asset'], name='idx_highlight_user_asset'),
        ]

    def __str__(self):
        return f'Highlight: {self.text[:40]}... ({self.user})'


class UserLibrary(UUIDModel):
    """
    Tracks which digital assets a user has added to their personal library.
    Stores overall progress and reading stats.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='digital_library',
    )
    digital_asset = models.ForeignKey(
        DigitalAsset,
        on_delete=models.CASCADE,
        related_name='library_entries',
    )
    added_at = models.DateTimeField(default=timezone.now)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    overall_progress = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
    )
    total_time_seconds = models.PositiveIntegerField(default=0)
    is_finished = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    last_position = models.JSONField(
        null=True, blank=True,
        help_text='Last reading/listening position: {"page": N} or {"time": N}.',
    )

    class Meta:
        db_table = 'digital_content_user_library'
        ordering = ['-last_accessed_at']
        unique_together = [('user', 'digital_asset')]
        indexes = [
            models.Index(fields=['user', '-last_accessed_at'], name='idx_ulib_user_access'),
            models.Index(fields=['user', 'is_favorite'], name='idx_ulib_user_fav'),
        ]

    def __str__(self):
        return f'{self.user} — {self.digital_asset}'

    def record_access(self):
        self.last_accessed_at = timezone.now()
        self.save(update_fields=['last_accessed_at', 'updated_at'])

    def update_progress(self, progress: float, time_spent: int, position: dict = None):
        from decimal import Decimal
        self.overall_progress = Decimal(str(min(progress, 100.0)))
        self.total_time_seconds += time_spent
        self.last_accessed_at = timezone.now()
        if position:
            self.last_position = position
        if progress >= 100.0:
            self.is_finished = True
        update_fields = [
            'overall_progress', 'total_time_seconds', 'is_finished',
            'last_accessed_at', 'updated_at',
        ]
        if position:
            update_fields.append('last_position')
        self.save(update_fields=update_fields)
