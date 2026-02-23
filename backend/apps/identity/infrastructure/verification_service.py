"""
Nova — Identity Verification Service
========================================
Concrete implementation of VerificationServiceInterface.
Orchestrates OCR + face-matching via Celery tasks.
"""

import logging
from uuid import UUID

from apps.common.exceptions import VerificationError
from apps.identity.application import VerificationResultDTO, VerificationSubmitDTO
from apps.identity.application.interfaces import VerificationServiceInterface

logger = logging.getLogger('nova.identity')


class AIVerificationService(VerificationServiceInterface):
    """
    Submits verification requests.
    Actual OCR + face matching happens asynchronously in the
    intelligence context; this service enqueues the Celery task.
    """

    def submit_verification(self, dto: VerificationSubmitDTO) -> VerificationResultDTO:
        """
        Synchronous submission — creates the record (handled by use case)
        and returns a pending result.  Actual AI processing is async.
        """
        return VerificationResultDTO(
            request_id=dto.user_id,  # Placeholder — real id set by use case
            status='PENDING',
        )

    def process_verification_async(self, request_id: UUID) -> None:
        """Queue the background verification task."""
        from apps.identity.infrastructure.tasks import process_identity_verification
        process_identity_verification.delay(str(request_id))
        logger.info('Verification task queued', extra={'request_id': str(request_id)})
