"""
Nova — Identity Signals
==========================
Django signal handlers for the identity bounded context.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.identity.domain.models import User

logger = logging.getLogger('nova.identity')


@receiver(post_save, sender=User)
def on_user_saved(sender, instance, created, **kwargs):
    """
    Post-save hook for User model.
    - On creation: could trigger welcome email, etc.
    """
    if created:
        logger.info('New user created via signal', extra={
            'user_id': str(instance.id),
            'email': instance.email,
        })
