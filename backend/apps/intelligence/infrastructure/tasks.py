"""
Nova — Intelligence Celery Tasks
====================================
Async tasks for recommendation generation, embedding computation,
trending book calculation, and book embedding batch jobs.
"""

import logging

from celery import shared_task
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger('nova.intelligence.tasks')


# ---------------------------------------------------------------------------
# Recommendation generation
# ---------------------------------------------------------------------------

@shared_task(
    name='intelligence.generate_recommendations',
    queue='intelligence',
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def generate_recommendations(self, user_id: str):
    """
    Generate a fresh set of recommendations for a user using the
    hybrid engine, then persist them to the database.
    """
    from apps.intelligence.infrastructure.recommendation_engine import (
        generate_hybrid_recommendations,
    )
    from apps.intelligence.domain.models import Recommendation

    try:
        logger.info('Generating recommendations for user %s', user_id)

        recs = generate_hybrid_recommendations(user_id, limit=50)

        if not recs:
            logger.info('No recommendations produced for user %s', user_id)
            return {'user_id': user_id, 'count': 0}

        # Clear old non-clicked, non-dismissed recommendations
        Recommendation.objects.filter(
            user_id=user_id,
            is_clicked=False,
            is_dismissed=False,
        ).delete()

        # Bulk-create new ones
        objects = []
        for book_id, score, explanation, strategy, seed_id in recs:
            objects.append(Recommendation(
                user_id=user_id,
                book_id=book_id,
                strategy=strategy,
                score=score,
                explanation=explanation,
                seed_book_id=seed_id,
            ))

        Recommendation.objects.bulk_create(objects, ignore_conflicts=True)

        logger.info(
            'Generated %d recommendations for user %s',
            len(objects), user_id,
        )
        return {'user_id': user_id, 'count': len(objects)}

    except Exception as exc:
        logger.error(
            'Recommendation generation failed for user %s: %s',
            user_id, exc,
        )
        # In eager mode, retry raises immediately — guard against it
        from django.conf import settings as _settings
        if getattr(_settings, 'CELERY_TASK_ALWAYS_EAGER', False):
            raise
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# User preference vector recomputation
# ---------------------------------------------------------------------------

@shared_task(
    name='intelligence.recompute_user_embeddings',
    queue='intelligence',
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def recompute_user_embeddings(self, user_id: str):
    """
    Recompute the user's preference vector from their reading history,
    then update the UserPreference record.
    """
    from apps.intelligence.infrastructure.recommendation_engine import (
        compute_user_preference_vector,
    )
    from apps.intelligence.domain.models import UserPreference

    try:
        vector = compute_user_preference_vector(user_id)
        if vector:
            pref, _ = UserPreference.objects.get_or_create(user_id=user_id)
            pref.preference_vector = vector
            pref.last_computed_at = timezone.now()
            pref.save(update_fields=[
                'preference_vector', 'last_computed_at', 'updated_at',
            ])
            logger.info(
                'Recomputed preference vector for user %s (dim=%d)',
                user_id, len(vector),
            )
        else:
            logger.info(
                'No reading history to compute vector for user %s', user_id,
            )
        return {'user_id': user_id, 'vector_dim': len(vector) if vector else 0}

    except Exception as exc:
        logger.error(
            'Preference vector computation failed for user %s: %s',
            user_id, exc,
        )
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# Batch book embedding computation
# ---------------------------------------------------------------------------

@shared_task(
    name='intelligence.compute_book_embeddings_batch',
    queue='intelligence',
)
def compute_book_embeddings_batch(batch_size: int = 100):
    """
    Compute embeddings for books that don't have one yet.
    Runs as a scheduled Celery beat task.
    """
    from apps.catalog.domain.models import Book
    from apps.intelligence.infrastructure.recommendation_engine import (
        compute_book_embedding,
    )

    books = Book.objects.filter(
        embedding_vector__isnull=True,
    )[:batch_size]

    computed = 0
    for book in books:
        try:
            vec = compute_book_embedding(book)
            book.embedding_vector = vec
            book.save(update_fields=['embedding_vector', 'updated_at'])
            computed += 1
        except Exception as exc:
            logger.warning(
                'Failed to embed book %s: %s', book.id, exc,
            )

    logger.info('Computed embeddings for %d / %d books.', computed, len(books))
    return {'computed': computed, 'attempted': len(books)}


# ---------------------------------------------------------------------------
# Trending books computation
# ---------------------------------------------------------------------------

@shared_task(
    name='intelligence.compute_trending_books',
    queue='intelligence',
)
def compute_trending_books():
    """
    Recompute trending books for all periods based on borrow counts,
    review counts, and view patterns.
    """
    from datetime import timedelta

    from django.db.models import Count, Avg, Q

    from apps.catalog.domain.models import Book
    from apps.circulation.domain.models import BorrowRecord
    from apps.intelligence.domain.models import TrendingBook

    now = timezone.now()
    periods = {
        'DAILY': timedelta(days=1),
        'WEEKLY': timedelta(days=7),
        'MONTHLY': timedelta(days=30),
        'ALL_TIME': timedelta(days=3650),
    }

    for period_name, delta in periods.items():
        cutoff = now - delta

        # Aggregate borrow counts per book in the period
        book_stats = (
            BorrowRecord.objects
            .filter(created_at__gte=cutoff)
            .values('book_copy__book_id')
            .annotate(
                borrow_count=Count('id'),
            )
            .order_by('-borrow_count')[:100]
        )

        # Clear existing entries for this period
        TrendingBook.objects.filter(period=period_name).delete()

        rank = 1
        for stat in book_stats:
            book_id = stat['book_copy__book_id']
            borrow_count = stat['borrow_count']

            try:
                book = Book.objects.get(id=book_id)
            except Book.DoesNotExist:
                continue

            # Composite score: borrows * 3 + rating * 10 + reviews * 2
            score = (
                borrow_count * 3.0
                + (book.average_rating or 0) * 10.0
                + (book.rating_count or 0) * 2.0
            )

            TrendingBook.objects.create(
                book_id=book_id,
                period=period_name,
                rank=rank,
                borrow_count=borrow_count,
                review_count=book.rating_count or 0,
                score=score,
            )
            rank += 1

    logger.info('Trending books recomputed for all periods.')
    return {'status': 'completed'}


# ---------------------------------------------------------------------------
# Periodic: batch recommendation refresh for active users
# ---------------------------------------------------------------------------

@shared_task(
    name='intelligence.refresh_active_user_recommendations',
    queue='intelligence',
)
def refresh_active_user_recommendations():
    """
    Refresh recommendations for users who have been active in the
    last 7 days. Runs daily via Celery beat.
    """
    from datetime import timedelta
    from apps.engagement.domain.models import UserEngagement

    cutoff = timezone.now().date() - timedelta(days=7)
    active_user_ids = (
        UserEngagement.objects
        .filter(last_activity_date__gte=cutoff)
        .values_list('user_id', flat=True)[:200]
    )

    for user_id in active_user_ids:
        generate_recommendations.apply_async(
            args=[str(user_id)],
            countdown=5,
        )

    logger.info(
        'Queued recommendation refresh for %d active users.',
        len(active_user_ids),
    )
    return {'queued': len(active_user_ids)}


# ---------------------------------------------------------------------------
# Overdue risk prediction (periodic)
# ---------------------------------------------------------------------------

@shared_task(
    name='intelligence.predict_overdue_risks',
    queue='intelligence',
)
def predict_overdue_risks():
    """
    Run overdue probability predictions for all active borrows.
    Creates notifications for high-risk items.
    """
    from apps.circulation.domain.models import BorrowRecord
    from apps.intelligence.infrastructure.predictive_analytics import (
        OverduePredictor,
    )
    from apps.intelligence.infrastructure.notification_engine import (
        NotificationEngine,
    )

    active = BorrowRecord.objects.filter(
        status='ACTIVE',
    ).select_related('user', 'book_copy__book')

    high_risk = 0
    for record in active.iterator(chunk_size=200):
        try:
            prediction = OverduePredictor.predict(record)
            if prediction.probability >= 0.7:
                high_risk += 1
                NotificationEngine.create(
                    user=record.user,
                    notification_type='OVERDUE_WARNING',
                    data={
                        'book_title': record.book_copy.book.title,
                        'probability': prediction.probability,
                        'risk_level': prediction.risk_level,
                        'due_date': str(record.due_date),
                    },
                )
        except Exception as exc:
            logger.warning('Overdue prediction error for %s: %s', record.id, exc)

    logger.info('Overdue predictions: %d high-risk borrows notified.', high_risk)
    return {'high_risk': high_risk, 'total_checked': active.count()}


# ---------------------------------------------------------------------------
# Churn analysis (periodic)
# ---------------------------------------------------------------------------

@shared_task(
    name='intelligence.analyze_churn_risks',
    queue='intelligence',
)
def analyze_churn_risks():
    """Weekly churn risk analysis for all active members."""
    from apps.identity.domain.models import User
    from apps.intelligence.infrastructure.predictive_analytics import (
        ChurnPredictor,
    )
    from apps.intelligence.infrastructure.notification_engine import (
        NotificationEngine,
    )

    users = User.objects.filter(is_active=True, role__in=['MEMBER', 'STUDENT'])
    at_risk = 0

    for user in users.iterator(chunk_size=200):
        try:
            prediction = ChurnPredictor.predict(user, weeks=8)
            if prediction.churn_probability >= 0.7:
                at_risk += 1
                NotificationEngine.create(
                    user=user,
                    notification_type='RE_ENGAGEMENT',
                    data={
                        'weeks_inactive': prediction.weeks_since_last_activity,
                        'recommendations': prediction.recommendations[:2],
                    },
                )
        except Exception as exc:
            logger.warning('Churn prediction error for %s: %s', user.id, exc)

    logger.info('Churn analysis: %d at-risk users flagged.', at_risk)
    return {'at_risk': at_risk}


# ---------------------------------------------------------------------------
# Auto-tag new books (periodic)
# ---------------------------------------------------------------------------

@shared_task(
    name='intelligence.auto_tag_new_books',
    queue='intelligence',
)
def auto_tag_new_books():
    """Auto-tag books that don't have tags yet."""
    from apps.catalog.domain.models import Book
    from apps.intelligence.infrastructure.content_analysis import AutoTagger

    books = Book.objects.filter(tags=[], deleted_at__isnull=True)[:100]
    tagged = 0

    for book in books:
        try:
            AutoTagger.auto_tag_book(book, top_n=5)
            tagged += 1
        except Exception as exc:
            logger.warning('Auto-tag failed for %s: %s', book.id, exc)

    logger.info('Auto-tagged %d books.', tagged)
    return {'tagged': tagged}


# ---------------------------------------------------------------------------
# Send pending notifications
# ---------------------------------------------------------------------------

@shared_task(
    name='intelligence.deliver_notifications',
    queue='default',
)
def deliver_notifications():
    """Deliver pending in-app notifications (mark as sent)."""
    from apps.intelligence.infrastructure.notification_engine import (
        UserNotification,
    )

    pending = UserNotification.objects.filter(
        is_sent=False,
        channel='IN_APP',
    ).select_related('user')[:500]

    sent = 0
    for notif in pending:
        notif.is_sent = True
        notif.sent_at = timezone.now()
        notif.save(update_fields=['is_sent', 'sent_at'])
        sent += 1

    if sent:
        logger.info('Delivered %d in-app notifications.', sent)
    return {'sent': sent}


# ---------------------------------------------------------------------------
# Model training (scheduled)
# ---------------------------------------------------------------------------

@shared_task(
    name='intelligence.run_model_training',
    queue='intelligence',
    time_limit=7200,
)
def run_model_training(pipeline: str = 'all'):
    """
    Run ML model training pipelines.

    Args:
        pipeline: 'embedding', 'collaborative', 'overdue', or 'all'.
    """
    from apps.intelligence.infrastructure.training_pipeline import (
        CollaborativeFilterPipeline,
        EmbeddingPipeline,
        OverdueClassifierPipeline,
    )

    results = {}

    if pipeline in ('embedding', 'all'):
        result = EmbeddingPipeline.run_full()
        results['embedding'] = {
            'status': result.status,
            'metrics': result.metrics,
        }

    if pipeline in ('collaborative', 'all'):
        result = CollaborativeFilterPipeline.run_full()
        results['collaborative'] = {
            'status': result.status,
            'metrics': result.metrics,
        }

    if pipeline in ('overdue', 'all'):
        result = OverdueClassifierPipeline.run_full()
        results['overdue'] = {
            'status': result.status,
            'metrics': result.metrics,
        }

    logger.info('Model training complete: %s', results)
    return results
