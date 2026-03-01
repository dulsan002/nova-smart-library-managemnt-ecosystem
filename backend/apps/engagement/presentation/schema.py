"""
Nova — Engagement GraphQL Schema
====================================
KP profile, achievements, leaderboard, and daily activity.
"""

import graphene
from graphene_django import DjangoObjectType

from apps.common.decorators import require_authentication, require_roles
from apps.common.permissions import Role

from apps.engagement.application import KPEngineService, LeaderboardService
from apps.engagement.domain.models import (
    Achievement,
    DailyActivity,
    UserAchievement,
    UserEngagement,
)


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class UserEngagementType(DjangoObjectType):
    streak_multiplier = graphene.Float()

    class Meta:
        model = UserEngagement
        fields = (
            'id', 'user', 'total_kp', 'level', 'level_title',
            'explorer_kp', 'scholar_kp', 'connector_kp',
            'achiever_kp', 'dedicated_kp',
            'current_streak', 'longest_streak', 'last_activity_date',
            'kp_earned_today', 'rank', 'rank_percentile',
            'created_at', 'updated_at',
        )

    def resolve_streak_multiplier(self, info):
        return self.get_streak_multiplier()


class AchievementType(DjangoObjectType):
    class Meta:
        model = Achievement
        fields = (
            'id', 'code', 'name', 'description', 'icon',
            'category', 'rarity', 'kp_reward', 'criteria',
            'is_active', 'sort_order',
        )


class UserAchievementType(DjangoObjectType):
    class Meta:
        model = UserAchievement
        fields = (
            'id', 'user', 'achievement', 'earned_at',
            'kp_awarded', 'notified',
        )


class DailyActivityType(DjangoObjectType):
    class Meta:
        model = DailyActivity
        fields = (
            'id', 'user', 'date', 'kp_earned',
            'books_borrowed', 'books_returned', 'reading_minutes',
            'pages_read', 'reviews_written', 'sessions_completed',
        )


class LeaderboardEntryType(graphene.ObjectType):
    rank = graphene.Int()
    user_id = graphene.UUID()
    email = graphene.String()
    full_name = graphene.String()
    total_kp = graphene.Int()
    level = graphene.Int()
    level_title = graphene.String()
    avatar_url = graphene.String()


class UserRankType(graphene.ObjectType):
    rank = graphene.Int()
    total_kp = graphene.Int()
    level = graphene.Int()
    level_title = graphene.String()
    percentile = graphene.Float()


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

class EngagementQuery(graphene.ObjectType):
    my_engagement = graphene.Field(UserEngagementType)
    my_achievements = graphene.List(UserAchievementType)
    my_daily_activity = graphene.List(
        DailyActivityType,
        days=graphene.Int(default_value=30),
    )
    my_rank = graphene.Field(UserRankType)

    all_achievements = graphene.List(AchievementType, category=graphene.String())

    leaderboard = graphene.List(
        LeaderboardEntryType,
        limit=graphene.Int(default_value=50),
    )

    # Admin: user engagement by ID
    user_engagement = graphene.Field(
        UserEngagementType,
        user_id=graphene.UUID(required=True),
    )

    # Admin: user achievements by ID
    user_achievements = graphene.List(
        UserAchievementType,
        user_id=graphene.UUID(required=True),
    )

    @require_authentication
    def resolve_my_engagement(self, info):
        engagement, _ = UserEngagement.objects.get_or_create(
            user=info.context.user,
        )
        return engagement

    @require_authentication
    def resolve_my_achievements(self, info):
        return UserAchievement.objects.filter(
            user=info.context.user,
        ).select_related('achievement')

    @require_authentication
    def resolve_my_daily_activity(self, info, days=30):
        from django.utils import timezone
        from datetime import timedelta
        cutoff = timezone.now().date() - timedelta(days=days)
        return DailyActivity.objects.filter(
            user=info.context.user,
            date__gte=cutoff,
        )

    @require_authentication
    def resolve_my_rank(self, info):
        data = LeaderboardService.get_user_rank(info.context.user.id)
        return UserRankType(**data)

    def resolve_all_achievements(self, info, category=None):
        qs = Achievement.objects.filter(is_active=True)
        if category:
            qs = qs.filter(category=category)
        return qs

    def resolve_leaderboard(self, info, limit=50):
        entries = LeaderboardService.get_top(limit)
        result = []
        for idx, eng in enumerate(entries, start=1):
            result.append(LeaderboardEntryType(
                rank=idx,
                user_id=eng.user_id,
                email=eng.user.email,
                full_name=eng.user.full_name,
                total_kp=eng.total_kp,
                level=eng.level,
                level_title=eng.level_title,
                avatar_url=eng.user.avatar_url,
            ))
        return result

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_user_engagement(self, info, user_id):
        try:
            return UserEngagement.objects.get(user_id=user_id)
        except UserEngagement.DoesNotExist:
            return None

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_user_achievements(self, info, user_id):
        return UserAchievement.objects.filter(
            user_id=user_id,
        ).select_related('achievement').order_by('-earned_at')


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------

class AdminAwardKP(graphene.Mutation):
    """Admin manual KP adjustment."""

    class Arguments:
        user_id = graphene.UUID(required=True)
        points = graphene.Int(required=True)
        reason = graphene.String(required=True)
        dimension = graphene.String(default_value='ACHIEVER')

    success = graphene.Boolean()
    actual_points = graphene.Int()

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    def mutate(self, info, user_id, points, reason, dimension='ACHIEVER'):
        engine = KPEngineService()
        if points > 0:
            # For admin adjustments, directly award the specified points
            # instead of looking up from KP_WEIGHTS
            engagement, created = UserEngagement.objects.get_or_create(user_id=user_id)
            actual = engagement.award_kp(points, dimension, bypass_cap=True)

            # Record in ledger
            from apps.governance.services import KPLedgerService
            KPLedgerService.record(
                user_id=user_id,
                action='AWARD',
                points=actual,
                balance_after=engagement.total_kp,
                source_type='admin_adjustment',
                source_id='',
                dimension=dimension,
                description=reason or f'Admin adjustment: +{actual} KP',
            )
        else:
            actual = engine.deduct_kp(
                user_id=user_id,
                points=abs(points),
                reason=reason,
                dimension=dimension,
                source_type='admin_adjustment',
            )
        return AdminAwardKP(success=True, actual_points=actual)


class EngagementMutation(graphene.ObjectType):
    admin_award_kp = AdminAwardKP.Field()
