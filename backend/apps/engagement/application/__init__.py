"""
Nova — Engagement Application Services
==========================================
KP engine, achievement evaluation, and leaderboard.
"""

import logging
from typing import Optional
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.common.event_bus import DomainEvent, EventBus, EventTypes
from apps.common.exceptions import EngagementError, DailyKPCapReachedError

from apps.engagement.domain.models import (
    Achievement,
    DailyActivity,
    UserAchievement,
    UserEngagement,
)
from apps.governance.services import KPLedgerService

logger = logging.getLogger('nova.engagement')


class KPEngineService:
    """
    Core Knowledge Points engine.
    Applies multipliers, daily caps, and records in the KP ledger.
    """

    KP_WEIGHTS = None

    @classmethod
    def _get_weights(cls):
        if cls.KP_WEIGHTS is None:
            cls.KP_WEIGHTS = getattr(settings, 'ENGAGEMENT_CONFIG', {}).get('kp_weights', {
                'BORROW_BOOK': 10,
                'RETURN_ON_TIME': 15,
                'RETURN_EARLY': 20,
                'READING_SESSION_SHORT': 10,
                'READING_SESSION_30MIN': 25,
                'READING_SESSION_60MIN': 40,
                'COMPLETE_BOOK': 50,
                'WRITE_REVIEW': 20,
                'DAILY_LOGIN': 5,
                'FIRST_BORROW': 30,
                'STREAK_BONUS_7': 50,
                'STREAK_BONUS_30': 150,
            })
        return cls.KP_WEIGHTS

    @transaction.atomic
    def award_kp(
        self,
        user_id: UUID,
        action: str,
        dimension: str = 'EXPLORER',
        source_type: str = '',
        source_id: str = '',
        description: str = '',
        metadata: dict = None,
    ) -> int:
        """
        Award KP to a user for a specific action.
        Returns the actual points awarded (after multiplier & cap).
        """
        weights = self._get_weights()
        base_points = weights.get(action, 0)
        if base_points <= 0:
            return 0

        engagement, created = UserEngagement.objects.get_or_create(user_id=user_id)

        # Apply streak multiplier
        multiplier = engagement.get_streak_multiplier()
        points = int(base_points * multiplier)

        # Check daily cap
        if not engagement.can_earn_kp(points):
            remaining = getattr(settings, 'ENGAGEMENT_CONFIG', {}).get('daily_kp_cap', 200) - engagement.kp_earned_today
            if remaining <= 0:
                logger.info('Daily KP cap reached', extra={'user_id': str(user_id)})
                return 0
            points = remaining

        # Award
        actual = engagement.award_kp(points, dimension)

        # Record in ledger
        KPLedgerService.record(
            user_id=user_id,
            action='AWARD',
            points=actual,
            balance_after=engagement.total_kp,
            source_type=source_type or action,
            source_id=str(source_id),
            dimension=dimension,
            description=description or f'{action}: +{actual} KP (x{multiplier})',
            metadata=metadata or {'base': base_points, 'multiplier': multiplier},
        )

        # Update daily activity
        today = timezone.now().date()
        daily, _ = DailyActivity.objects.get_or_create(
            user_id=user_id, date=today,
        )
        daily.kp_earned += actual
        daily.save(update_fields=['kp_earned', 'updated_at'])

        # Publish event
        EventBus.publish(DomainEvent(
            event_type=EventTypes.KP_AWARDED,
            payload={
                'points': actual,
                'action': action,
                'dimension': dimension,
                'total_kp': engagement.total_kp,
                'level': engagement.level,
            },
            metadata={'aggregate_id': str(user_id)},
        ))

        logger.info('KP awarded', extra={
            'user_id': str(user_id),
            'action': action,
            'points': actual,
            'total': engagement.total_kp,
        })
        return actual

    @transaction.atomic
    def deduct_kp(
        self,
        user_id: UUID,
        points: int,
        reason: str = '',
        dimension: str = '',
        source_type: str = '',
        source_id: str = '',
    ) -> int:
        """Deduct KP (penalty). Returns actual deduction."""
        engagement, _ = UserEngagement.objects.get_or_create(user_id=user_id)
        actual = engagement.deduct_kp(points, dimension)

        KPLedgerService.record(
            user_id=user_id,
            action='DEDUCT',
            points=-actual,
            balance_after=engagement.total_kp,
            source_type=source_type,
            source_id=str(source_id),
            dimension=dimension,
            description=reason,
        )

        EventBus.publish(DomainEvent(
            event_type=EventTypes.KP_DEDUCTED,
            payload={'points': actual, 'reason': reason},
            metadata={'aggregate_id': str(user_id)},
        ))
        return actual


class AchievementService:
    """Evaluates and awards achievements."""

    @transaction.atomic
    def check_and_award(self, user_id: UUID):
        """
        Evaluate all active achievements against user's stats.
        Award any newly earned achievements.
        """
        from apps.identity.domain.models import User
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return []

        engagement, _ = UserEngagement.objects.get_or_create(user_id=user_id)
        earned_codes = set(
            UserAchievement.objects.filter(user=user).values_list('achievement__code', flat=True)
        )

        user_stats = self._gather_stats(user, engagement)
        newly_earned = []

        for achievement in Achievement.objects.filter(is_active=True):
            if achievement.code in earned_codes:
                continue

            if self._evaluate_criteria(achievement.criteria, user_stats):
                ua = UserAchievement.objects.create(
                    user=user,
                    achievement=achievement,
                    kp_awarded=achievement.kp_reward,
                )
                newly_earned.append(ua)

                # Award bonus KP
                if achievement.kp_reward > 0:
                    engine = KPEngineService()
                    engine.award_kp(
                        user_id=user_id,
                        action='ACHIEVEMENT_BONUS',
                        dimension='ACHIEVER',
                        source_type='achievement',
                        source_id=str(achievement.id),
                        description=f'Achievement unlocked: {achievement.name}',
                    )

                EventBus.publish(DomainEvent(
                    event_type=EventTypes.ACHIEVEMENT_UNLOCKED,
                    payload={
                        'achievement_code': achievement.code,
                        'achievement_name': achievement.name,
                        'kp_reward': achievement.kp_reward,
                    },
                    metadata={'aggregate_id': str(user_id)},
                ))

        return newly_earned

    def _gather_stats(self, user, engagement) -> dict:
        """Collect all relevant stats for achievement evaluation."""
        from apps.circulation.domain.models import BorrowRecord
        from apps.digital_content.domain.models import ReadingSession
        from apps.catalog.domain.models import BookReview

        return {
            'total_kp': engagement.total_kp,
            'level': engagement.level,
            'current_streak': engagement.current_streak,
            'longest_streak': engagement.longest_streak,
            'books_borrowed': BorrowRecord.objects.filter(user=user).count(),
            'books_returned': BorrowRecord.objects.filter(user=user, status='RETURNED').count(),
            'books_read': ReadingSession.objects.filter(
                user=user, progress_percent__gte=100,
            ).values('digital_asset__book').distinct().count(),
            'reviews_written': BookReview.objects.filter(user=user).count(),
            'reading_sessions': ReadingSession.objects.filter(
                user=user, status='COMPLETED',
            ).count(),
            'total_reading_minutes': (
                ReadingSession.objects.filter(user=user).aggregate(
                    total=Sum('duration_seconds'),
                )['total'] or 0
            ) // 60,
        }

    def _evaluate_criteria(self, criteria: dict, stats: dict) -> bool:
        """Evaluate a single achievement's criteria against user stats."""
        if not criteria:
            return False

        crit_type = criteria.get('type', '')
        threshold = criteria.get('threshold', 0)

        evaluators = {
            'total_kp': lambda: stats.get('total_kp', 0) >= threshold,
            'level': lambda: stats.get('level', 0) >= threshold,
            'streak': lambda: stats.get('current_streak', 0) >= threshold,
            'longest_streak': lambda: stats.get('longest_streak', 0) >= threshold,
            'books_borrowed': lambda: stats.get('books_borrowed', 0) >= threshold,
            'books_returned': lambda: stats.get('books_returned', 0) >= threshold,
            'books_read': lambda: stats.get('books_read', 0) >= threshold,
            'reviews_written': lambda: stats.get('reviews_written', 0) >= threshold,
            'reading_sessions': lambda: stats.get('reading_sessions', 0) >= threshold,
            'reading_minutes': lambda: stats.get('total_reading_minutes', 0) >= threshold,
        }

        evaluator = evaluators.get(crit_type)
        return evaluator() if evaluator else False


class LeaderboardService:
    """Leaderboard queries and ranking updates."""

    @staticmethod
    def get_top(limit: int = 50):
        """Get top users by KP."""
        return UserEngagement.objects.select_related('user').order_by('-total_kp')[:limit]

    @staticmethod
    def get_user_rank(user_id: UUID) -> dict:
        """Get a specific user's rank and surrounding users."""
        try:
            engagement = UserEngagement.objects.get(user_id=user_id)
        except UserEngagement.DoesNotExist:
            return {'rank': None, 'total_kp': 0, 'percentile': None}

        rank = UserEngagement.objects.filter(total_kp__gt=engagement.total_kp).count() + 1
        total_users = UserEngagement.objects.count()
        percentile = round((1 - rank / max(total_users, 1)) * 100, 2) if total_users > 0 else 0

        return {
            'rank': rank,
            'total_kp': engagement.total_kp,
            'level': engagement.level,
            'level_title': engagement.level_title,
            'percentile': percentile,
        }

    @staticmethod
    def update_all_ranks():
        """Batch update ranks for all users (periodic task)."""
        engagements = UserEngagement.objects.order_by('-total_kp')
        total = engagements.count()

        for idx, eng in enumerate(engagements.iterator(), start=1):
            eng.rank = idx
            eng.rank_percentile = round((1 - idx / max(total, 1)) * 100, 2)
            eng.save(update_fields=['rank', 'rank_percentile', 'updated_at'])
