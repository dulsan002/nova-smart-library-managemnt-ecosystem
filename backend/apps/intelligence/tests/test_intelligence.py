"""
Tests for the Intelligence bounded context
=============================================
Covers: cosine_similarity, domain models, recommendation engine helpers.
"""

import pytest

np = pytest.importorskip('numpy', reason='numpy not installed')

from uuid import uuid4

from apps.intelligence.infrastructure.recommendation_engine import cosine_similarity
from apps.intelligence.domain.models import (
    Recommendation,
    UserPreference,
    TrendingBook,
    SearchLog,
)


# ─── cosine_similarity (pure function) ──────────────────────────────

class TestCosineSimilarity:

    def test_identical_vectors(self):
        v = np.array([1.0, 2.0, 3.0])
        assert abs(cosine_similarity(v, v) - 1.0) < 1e-6

    def test_orthogonal_vectors(self):
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])
        assert abs(cosine_similarity(a, b)) < 1e-6

    def test_opposite_vectors(self):
        a = np.array([1.0, 0.0])
        b = np.array([-1.0, 0.0])
        assert abs(cosine_similarity(a, b) - (-1.0)) < 1e-6

    def test_zero_vector_returns_zero(self):
        a = np.array([0.0, 0.0])
        b = np.array([1.0, 2.0])
        assert cosine_similarity(a, b) == 0.0

    def test_both_zero_returns_zero(self):
        assert cosine_similarity(np.array([0.0]), np.array([0.0])) == 0.0


# ─── Domain Models ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestRecommendation:

    def test_create_recommendation(self, user, make_book):
        book = make_book(isbn_13="9780000008001")
        rec = Recommendation.objects.create(
            user=user,
            book=book,
            strategy="CONTENT_BASED",
            score=0.85,
            explanation="Based on your reading history.",
        )
        assert rec.score == 0.85
        assert rec.is_dismissed is False
        assert rec.is_clicked is False


@pytest.mark.django_db
class TestUserPreference:

    def test_create_preference(self, user):
        pref = UserPreference.objects.create(
            user=user,
            preferred_categories=["algorithms", "databases"],
            preferred_languages=["en"],
            reading_speed="average",
        )
        assert pref.preferred_categories == ["algorithms", "databases"]


@pytest.mark.django_db
class TestTrendingBook:

    def test_create_trending(self, make_book):
        book = make_book(isbn_13="9780000008002")
        tb = TrendingBook.objects.create(
            book=book,
            period="WEEKLY",
            rank=1,
            borrow_count=25,
            view_count=100,
            score=88.5,
        )
        assert tb.rank == 1
        assert tb.period == "WEEKLY"


@pytest.mark.django_db
class TestSearchLog:

    def test_create_search_log(self, user):
        log = SearchLog.objects.create(
            user=user,
            query_text="clean code",
            results_count=5,
        )
        assert log.query_text == "clean code"
        assert log.results_count == 5
