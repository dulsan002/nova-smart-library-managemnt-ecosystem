"""
Nova — Intelligence Application Layer
==========================================
Use-cases / services for recommendations, preferences, search, trending.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import logging
import uuid

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('nova.intelligence')


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------

@dataclass
class RecommendationDTO:
    book_id: uuid.UUID
    strategy: str
    score: float
    explanation: str = ''
    seed_book_id: Optional[uuid.UUID] = None


@dataclass
class UserPreferenceDTO:
    preferred_categories: List[str] = field(default_factory=list)
    preferred_authors: List[str] = field(default_factory=list)
    preferred_languages: List[str] = field(default_factory=list)
    disliked_categories: List[str] = field(default_factory=list)


@dataclass
class SearchDTO:
    query_text: str
    filters: dict = field(default_factory=dict)
    user_id: Optional[uuid.UUID] = None
    ip_address: Optional[str] = None
    session_id: Optional[uuid.UUID] = None


# ---------------------------------------------------------------------------
# Recommendation Service
# ---------------------------------------------------------------------------

class RecommendationService:
    """Orchestrates recommendation generation and retrieval."""

    @staticmethod
    def get_for_user(user_id, limit=20, strategy=None):
        from apps.intelligence.domain.models import Recommendation

        qs = Recommendation.objects.filter(
            user_id=user_id,
            is_dismissed=False,
        ).select_related('book', 'seed_book')

        if strategy:
            qs = qs.filter(strategy=strategy)

        return qs[:limit]

    @staticmethod
    def generate_for_user(user_id):
        """
        Generate recommendations for a user.
        Tries Celery async first; falls back to synchronous if Redis/Celery
        is unavailable.
        Returns the task ID (async) or 'sync' (synchronous).
        """
        from apps.intelligence.infrastructure.tasks import generate_recommendations
        try:
            result = generate_recommendations.delay(str(user_id))
            # In eager mode, result is an EagerResult — task already ran
            return getattr(result, 'id', 'sync')
        except Exception as exc:
            # Celery/Redis unavailable — run synchronously
            logger.info(
                'Celery unavailable (%s), generating recommendations synchronously for user %s',
                exc, user_id,
            )
            try:
                generate_recommendations(str(user_id))
            except Exception as inner_exc:
                logger.error(
                    'Synchronous recommendation generation failed for user %s: %s',
                    user_id, inner_exc,
                )
                raise
            return 'sync'

    @staticmethod
    def record_click(recommendation_id, user_id):
        from apps.intelligence.domain.models import Recommendation
        try:
            rec = Recommendation.objects.get(
                id=recommendation_id, user_id=user_id,
            )
            rec.mark_clicked()
            return True
        except Recommendation.DoesNotExist:
            return False

    @staticmethod
    def dismiss(recommendation_id, user_id):
        from apps.intelligence.domain.models import Recommendation
        try:
            rec = Recommendation.objects.get(
                id=recommendation_id, user_id=user_id,
            )
            rec.dismiss()
            return True
        except Recommendation.DoesNotExist:
            return False


# ---------------------------------------------------------------------------
# User Preference Service
# ---------------------------------------------------------------------------

class UserPreferenceService:
    """Manages explicit and inferred reading preferences."""

    @staticmethod
    def get_or_create(user_id):
        from apps.intelligence.domain.models import UserPreference
        pref, _ = UserPreference.objects.get_or_create(user_id=user_id)
        return pref

    @staticmethod
    def update_explicit(user_id, dto: UserPreferenceDTO):
        from apps.intelligence.domain.models import UserPreference

        pref, _ = UserPreference.objects.get_or_create(user_id=user_id)
        if dto.preferred_categories is not None:
            pref.preferred_categories = dto.preferred_categories
        if dto.preferred_authors is not None:
            pref.preferred_authors = dto.preferred_authors
        if dto.preferred_languages is not None:
            pref.preferred_languages = dto.preferred_languages
        if dto.disliked_categories is not None:
            pref.disliked_categories = dto.disliked_categories
        pref.save()
        return pref

    @staticmethod
    def recompute_preference_vector(user_id):
        """
        Recompute the preference embedding vector from the user's
        reading history. Delegates heavy lifting to the recommendation engine.
        """
        from apps.intelligence.infrastructure.tasks import recompute_user_embeddings
        result = recompute_user_embeddings.delay(str(user_id))
        return result.id


# ---------------------------------------------------------------------------
# Search Analytics Service
# ---------------------------------------------------------------------------

class SearchAnalyticsService:
    """Records and analyses search behaviour."""

    @staticmethod
    def log_search(dto: SearchDTO, results_count: int):
        from apps.intelligence.domain.models import SearchLog

        return SearchLog.objects.create(
            user_id=dto.user_id,
            query_text=dto.query_text,
            filters_applied=dto.filters,
            results_count=results_count,
            ip_address=dto.ip_address,
            session_id=dto.session_id or uuid.uuid4(),
        )

    @staticmethod
    def record_click(search_log_id, clicked_book_id):
        from apps.intelligence.domain.models import SearchLog
        try:
            log = SearchLog.objects.get(id=search_log_id)
            log.clicked_result_id = clicked_book_id
            log.save(update_fields=['clicked_result_id'])
            return True
        except SearchLog.DoesNotExist:
            return False

    @staticmethod
    def trending_searches(limit=10, days=7):
        from apps.intelligence.domain.models import SearchLog
        from django.db.models import Count
        from datetime import timedelta

        cutoff = timezone.now() - timedelta(days=days)
        return (
            SearchLog.objects
            .filter(timestamp__gte=cutoff)
            .values('query_text')
            .annotate(count=Count('id'))
            .order_by('-count')[:limit]
        )


# ---------------------------------------------------------------------------
# Trending Service
# ---------------------------------------------------------------------------

class TrendingService:
    """Retrieves pre-computed trending books."""

    @staticmethod
    def get_trending(period='WEEKLY', limit=20):
        from apps.intelligence.domain.models import TrendingBook

        return (
            TrendingBook.objects
            .filter(period=period)
            .select_related('book')
            .order_by('rank')[:limit]
        )

    @staticmethod
    def refresh():
        """Kick off async trending recomputation."""
        from apps.intelligence.infrastructure.tasks import compute_trending_books
        return compute_trending_books.delay()
