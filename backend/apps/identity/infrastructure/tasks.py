"""
Nova — Identity Celery Tasks
================================
Background tasks for the identity bounded context.
"""

import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.common.event_bus import DomainEvent, EventBus, EventTypes

logger = logging.getLogger('nova.identity')


@shared_task(
    bind=True,
    name='identity.process_identity_verification',
    queue='verification',
    max_retries=3,
    default_retry_delay=60,
)
def process_identity_verification(self, request_id: str):
    """
    Process a single identity verification request:
      1. OCR on ID document image
      2. Face matching between selfie and ID photo
      3. Update request status + user verification_status
    """
    from apps.identity.domain.models import VerificationRequest

    try:
        request = VerificationRequest.objects.select_related('user').get(pk=request_id)
    except VerificationRequest.DoesNotExist:
        logger.error('Verification request not found', extra={'request_id': request_id})
        return

    user = request.user

    try:
        # ---- OCR ----
        from apps.intelligence.infrastructure.ocr_service import OCRService
        ocr = OCRService()
        ocr_result = ocr.extract(request.id_document_path)

        request.extracted_name = ocr_result.extracted_name
        request.extracted_id_number = ocr_result.extracted_id_number
        request.ocr_confidence = ocr_result.confidence

        # ---- Face Matching ----
        from apps.intelligence.infrastructure.face_service import FaceRecognitionService
        face = FaceRecognitionService()
        face_result = face.verify(
            document_image_path=request.id_document_path,
            selfie_image_path=request.selfie_path,
        )
        request.face_match_score = face_result.confidence

        # ---- Decision ----
        ai_config = getattr(settings, 'AI_CONFIG', {})
        ocr_threshold = ai_config.get('ocr_confidence_threshold', 0.75)
        face_threshold = ai_config.get('face_match_threshold', 0.80)

        if (
            request.ocr_confidence >= ocr_threshold
            and request.face_match_score >= face_threshold
        ):
            request.approve()
            user.mark_verified()
            event_type = EventTypes.VERIFICATION_APPROVED
        elif (
            request.ocr_confidence >= ocr_threshold * 0.8
            or request.face_match_score >= face_threshold * 0.8
        ):
            # Borderline — flag for manual review
            request.queue_for_manual_review()
            event_type = EventTypes.VERIFICATION_SUBMITTED  # Will be reviewed manually
        else:
            request.reject(reason='AI confidence below threshold.')
            user.verification_status = 'REJECTED'
            user.save(update_fields=['verification_status', 'updated_at'])
            event_type = EventTypes.VERIFICATION_REJECTED

        EventBus.publish(DomainEvent(
            event_type=event_type,
            aggregate_id=str(user.id),
            data={
                'request_id': str(request.id),
                'ocr_confidence': request.ocr_confidence,
                'face_match_score': request.face_match_score,
            },
        ))
        logger.info('Verification processed', extra={
            'request_id': request_id,
            'status': request.status,
        })

    except Exception as exc:
        logger.exception('Verification processing failed', extra={'request_id': request_id})
        request.status = 'FAILED'
        request.rejection_reason = str(exc)[:500]
        request.save(update_fields=['status', 'rejection_reason', 'updated_at'])

        # Retry
        raise self.retry(exc=exc)


@shared_task(name='identity.cleanup_expired_tokens', queue='maintenance')
def cleanup_expired_tokens():
    """Periodic task to remove expired / revoked refresh tokens."""
    from apps.identity.domain.models import RefreshToken

    cutoff = timezone.now()
    deleted_count, _ = RefreshToken.objects.filter(
        expires_at__lt=cutoff,
    ).delete()
    revoked_count, _ = RefreshToken.objects.filter(
        is_revoked=True,
        updated_at__lt=cutoff - timezone.timedelta(days=1),
    ).delete()
    logger.info('Token cleanup', extra={
        'expired_deleted': deleted_count,
        'revoked_deleted': revoked_count,
    })
