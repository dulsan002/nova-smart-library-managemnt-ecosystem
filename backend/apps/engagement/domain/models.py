"""
Nova — Engagement Domain Models
===================================
UserEngagement (aggregate root), Achievement, UserAchievement, DailyStreak.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.base_models import UUIDModel


class UserEngagement(UUIDModel):
    """
    Aggregate root: one-per-user engagement profile.
    Stores KP balances, level, streaks, and dimension breakdowns.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='engagement',
    )

    # Total KP
    total_kp = models.PositiveIntegerField(default=0)
    level = models.PositiveSmallIntegerField(default=1)
    level_title = models.CharField(max_length=50, default='Novice Reader')

    # Dimension KP breakdown
    explorer_kp = models.PositiveIntegerField(default=0, help_text='Borrowing/browsing')
    scholar_kp = models.PositiveIntegerField(default=0, help_text='Completion/reviews')
    connector_kp = models.PositiveIntegerField(default=0, help_text='Social/sharing')
    achiever_kp = models.PositiveIntegerField(default=0, help_text='Achievements/milestones')
    dedicated_kp = models.PositiveIntegerField(default=0, help_text='Streaks/consistency')

    # Streaks
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    # Daily cap tracking
    kp_earned_today = models.PositiveIntegerField(default=0)
    kp_today_date = models.DateField(null=True, blank=True)

    # Ranking (updated periodically)
    rank = models.PositiveIntegerField(null=True, blank=True)
    rank_percentile = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
    )

    class Meta:
        db_table = 'engagement_user_engagement'
        ordering = ['-total_kp']
        indexes = [
            models.Index(fields=['-total_kp'], name='idx_eng_total_kp'),
            models.Index(fields=['level'], name='idx_eng_level'),
            models.Index(fields=['rank'], name='idx_eng_rank'),
        ]

    def __str__(self):
        return f'{self.user} — Level {self.level} ({self.total_kp} KP)'

    def _check_daily_cap_reset(self):
        """Reset daily counter if it's a new day."""
        today = timezone.now().date()
        if self.kp_today_date != today:
            self.kp_earned_today = 0
            self.kp_today_date = today

    def can_earn_kp(self, amount: int) -> bool:
        """Check if user can earn more KP today (daily cap)."""
        self._check_daily_cap_reset()
        cap = getattr(settings, 'ENGAGEMENT_CONFIG', {}).get('DAILY_KP_CAP', 200)
        return (self.kp_earned_today + amount) <= cap

    def award_kp(self, points: int, dimension: str = ''):
        """
        Add KP to the user's balance and appropriate dimension.
        Returns the actual points awarded (may be capped).
        """
        self._check_daily_cap_reset()
        cap = getattr(settings, 'ENGAGEMENT_CONFIG', {}).get('DAILY_KP_CAP', 200)
        remaining = cap - self.kp_earned_today
        actual = min(points, max(remaining, 0))

        if actual <= 0:
            return 0

        self.total_kp += actual
        self.kp_earned_today += actual

        # Add to dimension
        dimension_map = {
            'EXPLORER': 'explorer_kp',
            'SCHOLAR': 'scholar_kp',
            'CONNECTOR': 'connector_kp',
            'ACHIEVER': 'achiever_kp',
            'DEDICATED': 'dedicated_kp',
        }
        field_name = dimension_map.get(dimension)
        if field_name:
            setattr(self, field_name, getattr(self, field_name) + actual)

        # Recalculate level
        self._update_level()

        self.save()
        return actual

    def deduct_kp(self, points: int, dimension: str = ''):
        """Deduct KP (penalty). Cannot go below zero."""
        deduction = min(points, self.total_kp)
        self.total_kp -= deduction

        dimension_map = {
            'EXPLORER': 'explorer_kp',
            'SCHOLAR': 'scholar_kp',
            'CONNECTOR': 'connector_kp',
            'ACHIEVER': 'achiever_kp',
            'DEDICATED': 'dedicated_kp',
        }
        field_name = dimension_map.get(dimension)
        if field_name:
            current = getattr(self, field_name)
            setattr(self, field_name, max(current - deduction, 0))

        self._update_level()
        self.save()
        return deduction

    def update_streak(self):
        """Update login/activity streak."""
        today = timezone.now().date()
        if self.last_activity_date == today:
            return  # Already recorded today

        if self.last_activity_date and (today - self.last_activity_date).days == 1:
            self.current_streak += 1
        elif self.last_activity_date and (today - self.last_activity_date).days > 1:
            self.current_streak = 1  # Reset
        else:
            self.current_streak = 1  # First activity

        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak

        self.last_activity_date = today
        self.save(update_fields=[
            'current_streak', 'longest_streak', 'last_activity_date', 'updated_at',
        ])

    def get_streak_multiplier(self) -> float:
        """Calculate streak multiplier based on consecutive days."""
        multipliers = getattr(settings, 'ENGAGEMENT_CONFIG', {}).get(
            'STREAK_MULTIPLIERS', {3: 1.1, 7: 1.25, 14: 1.5, 30: 2.0},
        )
        current_mult = 1.0
        for threshold, mult in sorted(multipliers.items()):
            if self.current_streak >= int(threshold):
                current_mult = mult
        return current_mult

    def _update_level(self):
        """Recalculate level based on total KP."""
        levels = getattr(settings, 'ENGAGEMENT_CONFIG', {}).get('LEVELS', {})
        if not levels:
            levels = {
                1: {'min_kp': 0, 'title': 'Novice Reader'},
                2: {'min_kp': 100, 'title': 'Bookworm'},
                3: {'min_kp': 300, 'title': 'Scholar'},
                4: {'min_kp': 600, 'title': 'Bibliophile'},
                5: {'min_kp': 1000, 'title': 'Knowledge Seeker'},
                6: {'min_kp': 1500, 'title': 'Sage'},
                7: {'min_kp': 2500, 'title': 'Library Champion'},
                8: {'min_kp': 4000, 'title': 'Grand Scholar'},
                9: {'min_kp': 6000, 'title': 'Enlightened Mind'},
                10: {'min_kp': 10000, 'title': 'Nova Master'},
            }
        current_level = 1
        current_title = 'Novice Reader'
        for lvl, info in sorted(levels.items(), key=lambda x: int(x[0])):
            if self.total_kp >= info['min_kp']:
                current_level = int(lvl)
                current_title = info['title']
        self.level = current_level
        self.level_title = current_title


class Achievement(UUIDModel):
    """
    Definition of an achievement / badge that users can earn.
    """

    CATEGORY_CHOICES = [
        ('READING', 'Reading'),
        ('BORROWING', 'Borrowing'),
        ('SOCIAL', 'Social'),
        ('STREAK', 'Streak'),
        ('MILESTONE', 'Milestone'),
        ('SPECIAL', 'Special'),
    ]

    RARITY_CHOICES = [
        ('COMMON', 'Common'),
        ('UNCOMMON', 'Uncommon'),
        ('RARE', 'Rare'),
        ('EPIC', 'Epic'),
        ('LEGENDARY', 'Legendary'),
    ]

    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=100, blank=True, default='')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, db_index=True)
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, default='COMMON')
    kp_reward = models.PositiveIntegerField(default=0)

    # Criteria (JSON for flexible rule engine)
    criteria = models.JSONField(
        default=dict,
        help_text='{"type": "books_read", "threshold": 10}',
    )

    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'engagement_achievement'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f'{self.name} [{self.rarity}]'


class UserAchievement(UUIDModel):
    """Records when a user earns an achievement."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='achievements',
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='earned_by',
    )
    earned_at = models.DateTimeField(default=timezone.now)
    kp_awarded = models.PositiveIntegerField(default=0)
    notified = models.BooleanField(default=False)

    class Meta:
        db_table = 'engagement_user_achievement'
        ordering = ['-earned_at']
        unique_together = [('user', 'achievement')]
        indexes = [
            models.Index(fields=['user', '-earned_at'], name='idx_uachv_user_time'),
        ]

    def __str__(self):
        return f'{self.user} earned {self.achievement.name}'


class DailyActivity(UUIDModel):
    """
    Tracks daily activity for streak calculation and analytics.
    One record per user per day.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='daily_activities',
    )
    date = models.DateField(db_index=True)
    kp_earned = models.PositiveIntegerField(default=0)

    # Activity counts
    books_borrowed = models.PositiveSmallIntegerField(default=0)
    books_returned = models.PositiveSmallIntegerField(default=0)
    reading_minutes = models.PositiveIntegerField(default=0)
    pages_read = models.PositiveIntegerField(default=0)
    reviews_written = models.PositiveSmallIntegerField(default=0)
    sessions_completed = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'engagement_daily_activity'
        ordering = ['-date']
        unique_together = [('user', 'date')]
        indexes = [
            models.Index(fields=['user', '-date'], name='idx_daily_user_date'),
        ]

    def __str__(self):
        return f'{self.user} — {self.date} ({self.kp_earned} KP)'
