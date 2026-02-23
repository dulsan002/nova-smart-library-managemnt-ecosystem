"""
Nova — Governance Services
==============================
Application-layer services for audit logging and security events.
"""

import logging
from typing import Optional
from uuid import UUID

from apps.common.utils import get_client_ip, get_user_agent
from apps.governance.domain.models import AuditLog, KPLedger, SecurityEvent

logger = logging.getLogger('nova.governance')


class AuditService:
    """Facade for recording audit log entries."""

    @staticmethod
    def log(
        action: str,
        resource_type: str,
        resource_id: str = '',
        actor_id: Optional[UUID] = None,
        actor_email: str = '',
        actor_role: str = '',
        description: str = '',
        ip_address: Optional[str] = None,
        user_agent: str = '',
        request_id: str = '',
        old_value: dict = None,
        new_value: dict = None,
        metadata: dict = None,
    ) -> AuditLog:
        entry = AuditLog.objects.create(
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            actor_id=actor_id,
            actor_email=actor_email,
            actor_role=actor_role,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            old_value=old_value,
            new_value=new_value,
            metadata=metadata,
        )
        logger.debug('Audit log created', extra={
            'audit_id': str(entry.id),
            'action': action,
            'resource': f'{resource_type}({resource_id})',
        })
        return entry

    @staticmethod
    def log_from_request(request, action, resource_type, resource_id='', **kwargs):
        """Convenience helper that extracts actor info from Django request."""
        user = getattr(request, 'user', None)
        return AuditService.log(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            actor_id=getattr(user, 'id', None) if user and user.is_authenticated else None,
            actor_email=getattr(user, 'email', '') if user and user.is_authenticated else '',
            actor_role=getattr(user, 'role', '') if user and user.is_authenticated else '',
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            request_id=getattr(request, 'request_id', ''),
            **kwargs,
        )


class SecurityEventService:
    """Facade for recording security events."""

    @staticmethod
    def record(
        event_type: str,
        severity: str,
        description: str = '',
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: str = '',
        metadata: dict = None,
    ) -> SecurityEvent:
        event = SecurityEvent.objects.create(
            event_type=event_type,
            severity=severity,
            description=description,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
        )
        if severity in ('HIGH', 'CRITICAL'):
            logger.warning('Security event: %s [%s]', event_type, severity, extra={
                'event_id': str(event.id),
                'user_id': str(user_id) if user_id else None,
                'ip': ip_address,
            })
        return event


class KPLedgerService:
    """Facade for recording Knowledge Point transactions."""

    @staticmethod
    def record(
        user_id: UUID,
        action: str,
        points: int,
        balance_after: int,
        source_type: str = '',
        source_id: str = '',
        dimension: str = '',
        description: str = '',
        metadata: dict = None,
    ) -> KPLedger:
        entry = KPLedger.objects.create(
            user_id=user_id,
            action=action,
            points=points,
            balance_after=balance_after,
            source_type=source_type,
            source_id=str(source_id),
            dimension=dimension,
            description=description,
            metadata=metadata,
        )
        logger.info('KP transaction', extra={
            'user_id': str(user_id),
            'action': action,
            'points': points,
            'balance': balance_after,
        })
        return entry
