"""
Nova — Governance GraphQL Schema
====================================
Queries for audit logs, security events, and KP ledger.
"""

import graphene
from graphene_django import DjangoObjectType

from apps.common.decorators import require_authentication, require_roles
from apps.common.pagination import paginate_queryset, PageInfo
from apps.common.permissions import Role
from apps.governance.domain.models import AuditLog, KPLedger, SecurityEvent


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class AuditLogType(DjangoObjectType):
    # Override action as plain String so values not in ACTION_CHOICES still resolve.
    action = graphene.String()

    class Meta:
        model = AuditLog
        fields = (
            'id', 'actor_id', 'actor_email', 'actor_role',
            'action', 'resource_type', 'resource_id', 'description',
            'ip_address', 'old_value', 'new_value', 'metadata',
            'created_at',
        )


class SecurityEventType(DjangoObjectType):
    class Meta:
        model = SecurityEvent
        fields = (
            'id', 'event_type', 'severity', 'user_id',
            'ip_address', 'description', 'metadata',
            'resolved', 'resolved_by', 'resolved_at', 'created_at',
        )


class KPLedgerType(DjangoObjectType):
    class Meta:
        model = KPLedger
        fields = (
            'id', 'user_id', 'action', 'points', 'balance_after',
            'source_type', 'source_id', 'dimension', 'description',
            'metadata', 'created_at',
        )


class AuditLogEdgeType(graphene.ObjectType):
    """Relay-style edge wrapping an AuditLogType with a cursor."""
    node = graphene.Field(AuditLogType)
    cursor = graphene.String()


class AuditLogConnectionType(graphene.ObjectType):
    edges = graphene.List(AuditLogEdgeType)
    page_info = graphene.Field(lambda: PageInfoType)
    total_count = graphene.Int()


class PageInfoType(graphene.ObjectType):
    has_next_page = graphene.Boolean(required=True)
    has_previous_page = graphene.Boolean(required=True)
    start_cursor = graphene.String()
    end_cursor = graphene.String()


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

class GovernanceQuery(graphene.ObjectType):
    audit_logs = graphene.Field(
        AuditLogConnectionType,
        first=graphene.Int(default_value=50),
        after=graphene.String(),
        action=graphene.String(),
        resource_type=graphene.String(),
        actor_id=graphene.UUID(),
    )

    security_events = graphene.List(
        SecurityEventType,
        severity=graphene.String(),
        event_type=graphene.String(),
        resolved=graphene.Boolean(),
        limit=graphene.Int(default_value=50),
    )

    kp_ledger = graphene.List(
        KPLedgerType,
        user_id=graphene.UUID(),
        action=graphene.String(),
        limit=graphene.Int(default_value=50),
    )

    my_kp_history = graphene.List(
        KPLedgerType,
        limit=graphene.Int(default_value=50),
        description='Current user KP transaction history.',
    )

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    def resolve_audit_logs(self, info, first=50, after=None, action=None,
                           resource_type=None, actor_id=None):
        qs = AuditLog.objects.all()
        if action:
            qs = qs.filter(action=action)
        if resource_type:
            qs = qs.filter(resource_type=resource_type)
        if actor_id:
            qs = qs.filter(actor_id=actor_id)

        page = paginate_queryset(qs, first=first, after=after)
        return AuditLogConnectionType(
            edges=page['edges'],
            page_info=PageInfoType(
                has_next_page=page['has_next_page'],
                has_previous_page=page['has_previous_page'],
                start_cursor=page['start_cursor'],
                end_cursor=page['end_cursor'],
            ),
            total_count=page['total_count'],
        )

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    def resolve_security_events(self, info, severity=None, event_type=None,
                                resolved=None, limit=50):
        qs = SecurityEvent.objects.all()
        if severity:
            qs = qs.filter(severity=severity)
        if event_type:
            qs = qs.filter(event_type=event_type)
        if resolved is not None:
            qs = qs.filter(resolved=resolved)
        return qs[:limit]

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_kp_ledger(self, info, user_id=None, action=None, limit=50):
        qs = KPLedger.objects.all()
        if user_id:
            qs = qs.filter(user_id=user_id)
        if action:
            qs = qs.filter(action=action)
        return qs[:limit]

    @require_authentication
    def resolve_my_kp_history(self, info, limit=50):
        return KPLedger.objects.filter(
            user_id=info.context.user.id,
        )[:limit]
