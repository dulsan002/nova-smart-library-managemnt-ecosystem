"""
Nova — Smart Notification Engine
====================================
AI-driven notification system that selects the right message,
channel, and timing for each user based on their behaviour profile.

Notification types:
  - OVERDUE_WARNING: Predicted overdue (from OverduePredictor)
  - RECOMMENDATION: New personalised pick
  - ACHIEVEMENT: Unlocked badge / milestone
  - STREAK_REMINDER: About to lose streak
  - NEW_ARRIVAL: Book in preferred category added
  - RESERVATION_READY: Reserved book available
  - RE_ENGAGEMENT: Churn-risk re-engagement
  - KP_MILESTONE: Reached KP level threshold
  - DUE_DATE_REMINDER: Approaching due date
"""

import logging
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Dict, List, Optional

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.base_models import TimeStampedModel, UUIDModel

logger = logging.getLogger('nova.intelligence.notifications')


# ---------------------------------------------------------------------------
# Domain Model
# ---------------------------------------------------------------------------

class NotificationType(models.TextChoices):
    OVERDUE_WARNING = 'OVERDUE_WARNING', 'Predicted Overdue Warning'
    RECOMMENDATION = 'RECOMMENDATION', 'New Recommendation'
    ACHIEVEMENT = 'ACHIEVEMENT', 'Achievement Unlocked'
    STREAK_REMINDER = 'STREAK_REMINDER', 'Streak At Risk'
    NEW_ARRIVAL = 'NEW_ARRIVAL', 'New Book Arrival'
    RESERVATION_READY = 'RESERVATION_READY', 'Reservation Ready'
    RE_ENGAGEMENT = 'RE_ENGAGEMENT', 'Re-engagement Nudge'
    KP_MILESTONE = 'KP_MILESTONE', 'KP Level Milestone'
    DUE_DATE_REMINDER = 'DUE_DATE_REMINDER', 'Due Date Reminder'


class NotificationChannel(models.TextChoices):
    IN_APP = 'IN_APP', 'In-App'
    EMAIL = 'EMAIL', 'Email'
    PUSH = 'PUSH', 'Push Notification'


class NotificationPriority(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'
    URGENT = 'URGENT', 'Urgent'


class UserNotification(UUIDModel, TimeStampedModel):
    """Persisted notification record for a user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(
        max_length=30, choices=NotificationType.choices,
    )
    channel = models.CharField(
        max_length=10, choices=NotificationChannel.choices,
        default=NotificationChannel.IN_APP,
    )
    priority = models.CharField(
        max_length=10, choices=NotificationPriority.choices,
        default=NotificationPriority.MEDIUM,
    )
    title = models.CharField(max_length=300)
    body = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    scheduled_for = models.DateTimeField(
        null=True, blank=True,
        help_text='If set, delivery is deferred until this time.',
    )

    class Meta:
        db_table = 'intelligence_notification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['scheduled_for']),
        ]

    def __str__(self):
        return f'{self.notification_type} → {self.user}'

    def mark_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at', 'updated_at'])

    def mark_sent(self):
        self.is_sent = True
        self.sent_at = timezone.now()
        self.save(update_fields=['is_sent', 'sent_at', 'updated_at'])


# ---------------------------------------------------------------------------
# Notification Templates
# ---------------------------------------------------------------------------

TEMPLATES = {
    NotificationType.OVERDUE_WARNING: {
        'title': 'Return reminder for "{book_title}"',
        'body': (
            'Our system predicts you might miss the due date '
            '({due_date}). Return early to keep your streak and '
            'avoid fines!'
        ),
        'priority': NotificationPriority.HIGH,
    },
    NotificationType.RECOMMENDATION: {
        'title': 'We think you\'ll love "{book_title}"',
        'body': '{explanation}',
        'priority': NotificationPriority.LOW,
    },
    NotificationType.ACHIEVEMENT: {
        'title': 'Achievement unlocked: {achievement_name}!',
        'body': (
            'Congratulations! You earned the "{achievement_name}" '
            'badge and {kp_reward} Knowledge Points.'
        ),
        'priority': NotificationPriority.MEDIUM,
    },
    NotificationType.STREAK_REMINDER: {
        'title': 'Don\'t lose your {streak_days}-day streak!',
        'body': (
            'You\'re on a {streak_days}-day reading streak. '
            'Read for just 15 minutes today to keep it going!'
        ),
        'priority': NotificationPriority.MEDIUM,
    },
    NotificationType.NEW_ARRIVAL: {
        'title': 'New in {category}: "{book_title}"',
        'body': (
            'A new book matching your interests just arrived: '
            '"{book_title}" by {author}.'
        ),
        'priority': NotificationPriority.LOW,
    },
    NotificationType.RESERVATION_READY: {
        'title': 'Your reserved book is ready!',
        'body': (
            '"{book_title}" is now available for pickup. '
            'Please collect it within 48 hours.'
        ),
        'priority': NotificationPriority.HIGH,
    },
    NotificationType.RE_ENGAGEMENT: {
        'title': 'We miss you, {first_name}!',
        'body': (
            'It\'s been {days_away} days since your last visit. '
            'Here\'s a personalised reading list to welcome you back.'
        ),
        'priority': NotificationPriority.MEDIUM,
    },
    NotificationType.KP_MILESTONE: {
        'title': 'Level up! You\'re now a {level_title}',
        'body': (
            'You\'ve reached Level {level} with {total_kp} '
            'Knowledge Points. Keep exploring!'
        ),
        'priority': NotificationPriority.MEDIUM,
    },
    NotificationType.DUE_DATE_REMINDER: {
        'title': '"{book_title}" is due {due_label}',
        'body': (
            'Please return "{book_title}" by {due_date} to avoid '
            'overdue fines. You can also renew online if eligible.'
        ),
        'priority': NotificationPriority.HIGH,
    },
}


# ---------------------------------------------------------------------------
# Notification Engine
# ---------------------------------------------------------------------------

class NotificationEngine:
    """
    Orchestrates notification creation, personalisation, and
    delivery scheduling.
    """

    # Throttle: max notifications per user per day
    DAILY_LIMIT = 8

    @classmethod
    def create(
        cls,
        user,
        notification_type: str,
        context: Dict,
        channel: str = 'IN_APP',
        scheduled_for=None,
    ) -> Optional[UserNotification]:
        """
        Create a notification from a template, personalised with
        the given context dictionary.
        """
        # Throttle check
        if cls._is_throttled(user):
            logger.info(
                'Notification throttled for user %s (daily limit)',
                user.id,
            )
            return None

        # Deduplicate: don't send the same type twice in 2 hours
        recent = UserNotification.objects.filter(
            user=user,
            notification_type=notification_type,
            created_at__gte=timezone.now() - timedelta(hours=2),
        ).exists()
        if recent:
            return None

        template = TEMPLATES.get(notification_type, {})
        if not template:
            logger.warning('No template for notification type %s', notification_type)
            return None

        try:
            title = template['title'].format(**context)
            body = template['body'].format(**context)
        except KeyError as e:
            logger.error(
                'Template variable missing for %s: %s',
                notification_type, e,
            )
            return None

        notification = UserNotification.objects.create(
            user=user,
            notification_type=notification_type,
            channel=channel,
            priority=template.get('priority', NotificationPriority.MEDIUM),
            title=title,
            body=body,
            data=context,
            scheduled_for=scheduled_for,
        )

        logger.info(
            'Created notification %s (%s) for user %s',
            notification.id, notification_type, user.id,
        )
        return notification

    @classmethod
    def _is_throttled(cls, user) -> bool:
        """Check if the user has exceeded the daily notification limit."""
        today_start = timezone.now().replace(
            hour=0, minute=0, second=0, microsecond=0,
        )
        count = UserNotification.objects.filter(
            user=user, created_at__gte=today_start,
        ).count()
        return count >= cls.DAILY_LIMIT

    @classmethod
    def get_unread(cls, user_id, limit=50):
        """Retrieve unread notifications for a user."""
        return UserNotification.objects.filter(
            user_id=user_id, is_read=False,
        )[:limit]

    @classmethod
    def get_all(cls, user_id, limit=100):
        return UserNotification.objects.filter(
            user_id=user_id,
        )[:limit]

    @classmethod
    def mark_all_read(cls, user_id):
        """Mark all unread notifications as read."""
        now = timezone.now()
        return UserNotification.objects.filter(
            user_id=user_id, is_read=False,
        ).update(is_read=True, read_at=now)

    @classmethod
    def schedule_optimal_time(cls, user) -> Optional[timezone.datetime]:
        """
        Determine the optimal delivery time for a user based on
        their historical activity patterns.
        """
        from apps.engagement.domain.models import DailyActivity
        from django.db.models import Avg

        # Find the hour when the user is most active (from reading sessions)
        from apps.digital_content.domain.models import ReadingSession

        sessions = (
            ReadingSession.objects
            .filter(user=user)
            .extra({'hour': "EXTRACT(hour FROM started_at)"})
            .values('hour')
            .annotate(count=models.Count('id'))
            .order_by('-count')[:1]
        )

        if sessions:
            peak_hour = int(sessions[0]['hour'])
        else:
            peak_hour = 9  # Default: 9 AM

        # Schedule for the next occurrence of that hour
        now = timezone.now()
        target = now.replace(
            hour=peak_hour, minute=0, second=0, microsecond=0,
        )
        if target <= now:
            target += timedelta(days=1)

        return target
