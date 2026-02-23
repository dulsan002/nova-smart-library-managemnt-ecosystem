"""
Nova — Engagement Celery Tasks
==================================
"""

import logging

from celery import shared_task

logger = logging.getLogger('nova.engagement')


@shared_task(name='engagement.update_leaderboard_ranks', queue='engagement')
def update_leaderboard_ranks():
    """Periodic task to recalculate all user ranks."""
    from apps.engagement.application import LeaderboardService
    LeaderboardService.update_all_ranks()
    logger.info('Leaderboard ranks updated')


@shared_task(name='engagement.check_achievements', queue='engagement')
def check_achievements_for_user(user_id: str):
    """Check and award achievements for a specific user."""
    from apps.engagement.application import AchievementService
    service = AchievementService()
    newly_earned = service.check_and_award(user_id)
    if newly_earned:
        logger.info('Achievements awarded', extra={
            'user_id': user_id,
            'count': len(newly_earned),
        })
