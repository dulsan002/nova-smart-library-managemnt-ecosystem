"""
Tests for the Digital Content bounded context
================================================
Covers: DigitalAsset properties, ReadingSession lifecycle, UserLibrary methods.
"""

import pytest
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from apps.digital_content.domain.models import (
    DigitalAsset,
    ReadingSession,
    Bookmark,
    Highlight,
    UserLibrary,
)


# ─── Helpers ─────────────────────────────────────────────────────────

@pytest.fixture
def digital_asset(db, make_book, librarian):
    book = make_book(isbn_13="9780000009001")
    return DigitalAsset.objects.create(
        book=book,
        asset_type="EBOOK_PDF",
        file_path="digital/test/content.pdf",
        file_size_bytes=5_000_000,
        file_hash="sha256:abc123",
        mime_type="application/pdf",
        total_pages=300,
        uploaded_by=librarian,
    )


@pytest.fixture
def audiobook(db, make_book, librarian):
    book = make_book(isbn_13="9780000009002")
    return DigitalAsset.objects.create(
        book=book,
        asset_type="AUDIOBOOK",
        file_path="digital/test/audio.mp3",
        file_size_bytes=50_000_000,
        file_hash="sha256:def456",
        mime_type="audio/mpeg",
        duration_seconds=18000,
        uploaded_by=librarian,
    )


# ─── DigitalAsset Properties ────────────────────────────────────────

@pytest.mark.django_db
class TestDigitalAsset:

    def test_is_ebook(self, digital_asset):
        assert digital_asset.is_ebook is True
        assert digital_asset.is_audiobook is False

    def test_is_audiobook(self, audiobook):
        assert audiobook.is_audiobook is True
        assert audiobook.is_ebook is False


# ─── ReadingSession ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestReadingSession:

    def test_create_session(self, user, digital_asset):
        session = ReadingSession.objects.create(
            user=user,
            digital_asset=digital_asset,
            status="ACTIVE",
        )
        assert session.status == "ACTIVE"

    def test_end_session(self, user, digital_asset):
        start = timezone.now() - timedelta(minutes=30)
        session = ReadingSession.objects.create(
            user=user,
            digital_asset=digital_asset,
            status="ACTIVE",
            started_at=start,
        )
        session.end_session()
        session.refresh_from_db()
        assert session.status == "COMPLETED"
        assert session.ended_at is not None
        assert session.duration_seconds >= 0

    def test_pause_session(self, user, digital_asset):
        session = ReadingSession.objects.create(
            user=user, digital_asset=digital_asset, status="ACTIVE",
        )
        session.pause_session()
        session.refresh_from_db()
        assert session.status == "PAUSED"

    def test_resume_session(self, user, digital_asset):
        session = ReadingSession.objects.create(
            user=user, digital_asset=digital_asset, status="PAUSED",
        )
        session.resume_session()
        session.refresh_from_db()
        assert session.status == "ACTIVE"

    def test_update_progress(self, user, digital_asset):
        session = ReadingSession.objects.create(
            user=user, digital_asset=digital_asset, status="ACTIVE",
        )
        session.update_progress(45.5)
        session.refresh_from_db()
        assert session.progress_percent == 45.5

    def test_update_progress_caps_at_100(self, user, digital_asset):
        session = ReadingSession.objects.create(
            user=user, digital_asset=digital_asset, status="ACTIVE",
        )
        session.update_progress(150.0)
        session.refresh_from_db()
        assert session.progress_percent == 100.0


# ─── Bookmark ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBookmark:

    def test_create_bookmark(self, user, digital_asset):
        bm = Bookmark.objects.create(
            user=user,
            digital_asset=digital_asset,
            title="Chapter 3",
            position={"page": 42},
        )
        assert bm.title == "Chapter 3"
        assert bm.position["page"] == 42


# ─── Highlight ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestHighlight:

    def test_create_highlight(self, user, digital_asset):
        hl = Highlight.objects.create(
            user=user,
            digital_asset=digital_asset,
            text="Important passage",
            position_start={"page": 10, "offset": 50},
            position_end={"page": 10, "offset": 120},
            color="yellow",
        )
        assert hl.text == "Important passage"
        assert hl.color == "yellow"


# ─── UserLibrary ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserLibrary:

    def test_create_library_entry(self, user, digital_asset):
        entry = UserLibrary.objects.create(
            user=user,
            digital_asset=digital_asset,
        )
        assert entry.overall_progress == 0
        assert entry.is_finished is False
        assert entry.is_favorite is False

    def test_update_progress(self, user, digital_asset):
        entry = UserLibrary.objects.create(
            user=user, digital_asset=digital_asset,
        )
        entry.update_progress(progress=50.0, time_spent=600)
        entry.refresh_from_db()
        assert entry.overall_progress == 50.0
        assert entry.total_time_seconds == 600
        assert entry.is_finished is False

    def test_update_progress_marks_finished(self, user, digital_asset):
        entry = UserLibrary.objects.create(
            user=user, digital_asset=digital_asset,
        )
        entry.update_progress(progress=100.0, time_spent=3600)
        entry.refresh_from_db()
        assert entry.is_finished is True

    def test_record_access(self, user, digital_asset):
        entry = UserLibrary.objects.create(
            user=user, digital_asset=digital_asset,
        )
        old_access = entry.last_accessed_at
        entry.record_access()
        entry.refresh_from_db()
        assert entry.last_accessed_at is not None
        if old_access:
            assert entry.last_accessed_at >= old_access
