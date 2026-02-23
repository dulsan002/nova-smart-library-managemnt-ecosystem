"""
Nova — Digital Content Application Services
===============================================
Use cases for reading sessions, bookmarks, highlights, and user library.
"""

import logging
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from apps.common.event_bus import DomainEvent, EventBus, EventTypes
from apps.common.exceptions import (
    NotFoundError,
    SessionError,
    ActiveSessionExistsError,
    ValidationError,
)

from apps.digital_content.domain.models import (
    Bookmark,
    DigitalAsset,
    Highlight,
    ReadingSession,
    UserLibrary,
)

logger = logging.getLogger('nova.digital_content')


@dataclass(frozen=True)
class StartSessionDTO:
    digital_asset_id: UUID
    session_type: str  # READING | LISTENING
    device_type: str = ''
    ip_address: str = ''


@dataclass(frozen=True)
class UpdateProgressDTO:
    session_id: UUID
    progress_percent: float
    position: Optional[dict] = None


@dataclass(frozen=True)
class CreateBookmarkDTO:
    digital_asset_id: UUID
    title: str = ''
    position: dict = None
    note: str = ''
    color: str = 'yellow'


@dataclass(frozen=True)
class CreateHighlightDTO:
    digital_asset_id: UUID
    text: str = ''
    position_start: dict = None
    position_end: dict = None
    color: str = 'yellow'
    note: str = ''


class StartReadingSessionUseCase:
    """Start a new reading or listening session."""

    @transaction.atomic
    def execute(self, user, dto: StartSessionDTO) -> ReadingSession:
        try:
            asset = DigitalAsset.objects.get(pk=dto.digital_asset_id)
        except DigitalAsset.DoesNotExist:
            raise NotFoundError(message='Digital asset not found.', code='ASSET_NOT_FOUND')

        # Check for active session on the same asset
        active = ReadingSession.objects.filter(
            user=user,
            digital_asset=asset,
            status__in=['ACTIVE', 'PAUSED'],
        ).first()

        if active:
            # Resume instead of creating duplicate
            active.resume_session()
            return active

        session = ReadingSession.objects.create(
            user=user,
            digital_asset=asset,
            session_type=dto.session_type,
            device_type=dto.device_type,
            ip_address=dto.ip_address or None,
        )

        # Ensure user library entry exists
        UserLibrary.objects.get_or_create(
            user=user,
            digital_asset=asset,
        )

        EventBus.publish(DomainEvent(
            event_type=EventTypes.READING_SESSION_STARTED,
            payload={
                'user_id': str(user.id),
                'asset_id': str(asset.id),
                'session_type': dto.session_type,
            },
            metadata={'aggregate_id': str(session.id)},
        ))
        return session


class EndReadingSessionUseCase:
    """End a reading/listening session and record duration."""

    @transaction.atomic
    def execute(self, session_id: UUID, user) -> ReadingSession:
        try:
            session = ReadingSession.objects.select_related('digital_asset').get(
                pk=session_id, user=user,
            )
        except ReadingSession.DoesNotExist:
            raise NotFoundError(message='Session not found.', code='SESSION_NOT_FOUND')

        if session.status not in ('ACTIVE', 'PAUSED'):
            raise SessionError(message='Session already ended.', code='SESSION_ENDED')

        session.end_session()

        # Update user library progress
        try:
            lib_entry = UserLibrary.objects.get(
                user=user, digital_asset=session.digital_asset,
            )
            lib_entry.update_progress(
                progress=float(session.progress_percent),
                time_spent=session.duration_seconds,
                position=session.last_position,
            )
        except UserLibrary.DoesNotExist:
            pass

        EventBus.publish(DomainEvent(
            event_type=EventTypes.READING_SESSION_ENDED,
            payload={
                'user_id': str(user.id),
                'duration_seconds': session.duration_seconds,
                'progress': float(session.progress_percent),
            },
            metadata={'aggregate_id': str(session.id)},
        ))
        return session


class UpdateProgressUseCase:
    """Update reading/listening progress during an active session."""

    def execute(self, user, dto: UpdateProgressDTO) -> ReadingSession:
        try:
            session = ReadingSession.objects.get(pk=dto.session_id, user=user)
        except ReadingSession.DoesNotExist:
            raise NotFoundError(message='Session not found.', code='SESSION_NOT_FOUND')

        session.update_progress(dto.progress_percent, dto.position)

        # Also update user library with current progress and position
        try:
            lib_entry = UserLibrary.objects.get(
                user=user, digital_asset=session.digital_asset,
            )
            lib_entry.update_progress(
                progress=dto.progress_percent,
                time_spent=0,  # time_spent accumulated on session end
                position=dto.position,
            )
        except UserLibrary.DoesNotExist:
            pass

        return session


class AddBookmarkUseCase:
    @transaction.atomic
    def execute(self, user, dto: CreateBookmarkDTO) -> Bookmark:
        try:
            asset = DigitalAsset.objects.get(pk=dto.digital_asset_id)
        except DigitalAsset.DoesNotExist:
            raise NotFoundError(message='Asset not found.', code='ASSET_NOT_FOUND')

        return Bookmark.objects.create(
            user=user,
            digital_asset=asset,
            title=dto.title,
            position=dto.position or {},
            note=dto.note,
            color=dto.color,
        )


class AddHighlightUseCase:
    @transaction.atomic
    def execute(self, user, dto: CreateHighlightDTO) -> Highlight:
        try:
            asset = DigitalAsset.objects.get(pk=dto.digital_asset_id)
        except DigitalAsset.DoesNotExist:
            raise NotFoundError(message='Asset not found.', code='ASSET_NOT_FOUND')

        return Highlight.objects.create(
            user=user,
            digital_asset=asset,
            text=dto.text,
            position_start=dto.position_start or {},
            position_end=dto.position_end or {},
            color=dto.color,
            note=dto.note,
        )


class ToggleFavoriteUseCase:
    def execute(self, user, asset_id: UUID) -> UserLibrary:
        # Auto-create library entry if user hasn't opened this asset yet
        entry, _created = UserLibrary.objects.get_or_create(
            user=user, digital_asset_id=asset_id,
        )

        entry.is_favorite = not entry.is_favorite
        entry.save(update_fields=['is_favorite', 'updated_at'])
        return entry
