"""
Nova — Circulation Signals
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.circulation.domain.models import BorrowRecord

logger = logging.getLogger('nova.circulation')


@receiver(post_save, sender=BorrowRecord)
def on_borrow_record_saved(sender, instance, created, **kwargs):
    if created:
        logger.info('Borrow record created', extra={
            'borrow_id': str(instance.id),
            'user_id': str(instance.user_id),
        })
