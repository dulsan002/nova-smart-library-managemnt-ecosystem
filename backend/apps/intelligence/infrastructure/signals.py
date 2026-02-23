"""
Nova — Intelligence Signals
================================
Cross-context event listeners that trigger intelligence operations.
"""

import logging

from apps.common.event_bus import EventBus, EventTypes

logger = logging.getLogger('nova.intelligence.signals')


# ---------------------------------------------------------------------------
# On book returned → recompute user preferences if they've read enough
# ---------------------------------------------------------------------------

def _on_book_returned(event):
    """
    After a book is returned, check if the user's preference vector
    should be recomputed (every 5 borrows).
    """
    user_id = event.data.get('user_id')
    if not user_id:
        return

    from apps.circulation.domain.models import BorrowRecord
    total_borrows = BorrowRecord.objects.filter(
        user_id=user_id, status='RETURNED',
    ).count()

    if total_borrows > 0 and total_borrows % 5 == 0:
        from apps.intelligence.infrastructure.tasks import (
            recompute_user_embeddings,
            generate_recommendations,
        )
        recompute_user_embeddings.apply_async(
            args=[str(user_id)], countdown=10,
        )
        generate_recommendations.apply_async(
            args=[str(user_id)], countdown=30,
        )
        logger.info(
            'Queued preference recomputation for user %s '
            '(total borrows: %d)',
            user_id, total_borrows,
        )


# ---------------------------------------------------------------------------
# On book reviewed → refresh recommendations
# ---------------------------------------------------------------------------

def _on_book_reviewed(event):
    """
    A new review changes the user's taste signal — refresh recs.
    """
    user_id = event.data.get('user_id')
    if not user_id:
        return

    from apps.intelligence.infrastructure.tasks import generate_recommendations
    generate_recommendations.apply_async(
        args=[str(user_id)], countdown=60,
    )


# ---------------------------------------------------------------------------
# Register handlers
# ---------------------------------------------------------------------------

EventBus.subscribe(EventTypes.BOOK_RETURNED, _on_book_returned)
EventBus.subscribe(EventTypes.BOOK_REVIEWED, _on_book_reviewed)
