"""
Nova — Engagement Signals
============================
Event-driven KP awarding via domain events.
Listens to events from other bounded contexts and awards KP accordingly.
"""

import logging

from apps.common.event_bus import EventBus, EventTypes

logger = logging.getLogger('nova.engagement')


def _on_book_borrowed(event):
    from apps.engagement.application import KPEngineService
    engine = KPEngineService()
    user_id = event.payload.get('user_id')
    if not user_id:
        return
    engine.award_kp(
        user_id=user_id,
        action='BORROW_BOOK',
        dimension='EXPLORER',
        source_type='borrow',
        source_id=event.payload.get('copy_id', ''),
    )


def _on_book_returned(event):
    from apps.engagement.application import KPEngineService
    engine = KPEngineService()
    user_id = event.payload.get('user_id')
    if not user_id:
        return
    was_overdue = event.payload.get('was_overdue', False)
    if not was_overdue:
        engine.award_kp(
            user_id=user_id,
            action='RETURN_ON_TIME',
            dimension='EXPLORER',
            source_type='return',
        )
    else:
        # Penalty for overdue
        days = event.payload.get('overdue_days', 0)
        if days > 0:
            engine.deduct_kp(
                user_id=user_id,
                points=days * 2,
                reason=f'Overdue return ({days} days)',
                dimension='EXPLORER',
                source_type='overdue_penalty',
            )


def _on_reading_session_ended(event):
    from apps.engagement.application import KPEngineService
    engine = KPEngineService()
    user_id = event.payload.get('user_id')
    if not user_id:
        return

    duration = event.payload.get('duration_seconds', 0)
    progress = event.payload.get('progress', 0)
    session_id = event.metadata.get('aggregate_id', '')

    # Award KP based on session duration
    if duration >= 3600:
        action = 'READING_SESSION_60MIN'
    elif duration >= 1800:
        action = 'READING_SESSION_30MIN'
    elif duration >= 300:
        # Award smaller KP for shorter sessions (5+ minutes)
        action = 'READING_SESSION_SHORT'
    else:
        action = None

    if action:
        engine.award_kp(
            user_id=user_id,
            action=action,
            dimension='SCHOLAR',
            source_type='reading_session',
            source_id=str(session_id),
        )

    # Award bonus if the book was completed (progress >= 100)
    if progress >= 100:
        engine.award_kp(
            user_id=user_id,
            action='COMPLETE_BOOK',
            dimension='SCHOLAR',
            source_type='reading_session',
            source_id=str(session_id),
        )


def _on_book_reviewed(event):
    from apps.engagement.application import KPEngineService
    engine = KPEngineService()
    user_id = event.payload.get('user_id')
    if not user_id:
        return
    engine.award_kp(
        user_id=user_id,
        action='WRITE_REVIEW',
        dimension='CONNECTOR',
        source_type='review',
    )


def _on_user_logged_in(event):
    from apps.engagement.application import KPEngineService
    from apps.engagement.domain.models import UserEngagement

    user_id = event.metadata.get('aggregate_id')
    if not user_id:
        return
    engagement, _ = UserEngagement.objects.get_or_create(user_id=user_id)
    engagement.update_streak()

    engine = KPEngineService()
    engine.award_kp(
        user_id=user_id,
        action='DAILY_LOGIN',
        dimension='DEDICATED',
        source_type='login',
    )

    # Streak bonuses
    if engagement.current_streak == 7:
        engine.award_kp(user_id=user_id, action='STREAK_BONUS_7', dimension='DEDICATED',
                        source_type='streak')
    elif engagement.current_streak == 30:
        engine.award_kp(user_id=user_id, action='STREAK_BONUS_30', dimension='DEDICATED',
                        source_type='streak')

    # Check achievements
    from apps.engagement.application import AchievementService
    AchievementService().check_and_award(user_id)


def _on_achievement_unlocked(event):
    logger.info('Achievement unlocked', extra={
        'user_id': event.metadata.get('aggregate_id', ''),
        'achievement': event.payload.get('achievement_name', ''),
    })


# Register event handlers
EventBus.subscribe(EventTypes.BOOK_BORROWED, _on_book_borrowed)
EventBus.subscribe(EventTypes.BOOK_RETURNED, _on_book_returned)
EventBus.subscribe(EventTypes.READING_SESSION_ENDED, _on_reading_session_ended)
EventBus.subscribe(EventTypes.BOOK_REVIEWED, _on_book_reviewed)
EventBus.subscribe(EventTypes.USER_LOGGED_IN, _on_user_logged_in)
EventBus.subscribe(EventTypes.ACHIEVEMENT_UNLOCKED, _on_achievement_unlocked)
