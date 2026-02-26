"""
Nova — Identity GraphQL Queries
===================================
All read operations for the identity bounded context.
"""

import graphene
from graphene.types.generic import GenericScalar

from apps.common.decorators import require_authentication, require_roles
from apps.common.pagination import paginate_queryset, PageInfo
from apps.common.permissions import Role
from apps.identity.domain.models import User, VerificationRequest, RoleConfig, Member
from apps.identity.presentation.types import (
    UserConnectionType,
    UserType,
    VerificationRequestType,
    RoleConfigType,
    ModuleInfoType,
    MemberType,
    MemberConnectionType,
)


class IdentityQuery(graphene.ObjectType):
    # ---- Self ----
    me = graphene.Field(UserType, description='Currently authenticated user.')

    # ---- Admin: single user ----
    user = graphene.Field(
        UserType,
        id=graphene.UUID(required=True),
        description='Get a user by ID (admin only).',
    )

    # ---- Admin: user list ----
    users = graphene.Field(
        UserConnectionType,
        first=graphene.Int(default_value=25),
        after=graphene.String(),
        role=graphene.String(),
        is_active=graphene.Boolean(),
        search=graphene.String(),
        description='Paginated user list (admin/librarian).',
    )

    # ---- Verification requests ----
    my_verification_requests = graphene.List(
        VerificationRequestType,
        description='Verification history for the current user.',
    )

    pending_verifications = graphene.List(
        VerificationRequestType,
        description='All pending verification requests (admin/librarian).',
    )

    # ---- RBAC ----
    role_configs = graphene.List(
        RoleConfigType,
        description='All role configurations (super admin only).',
    )

    role_config = graphene.Field(
        RoleConfigType,
        id=graphene.UUID(required=True),
        description='A single role configuration by ID.',
    )

    available_modules = graphene.List(
        ModuleInfoType,
        description='Available permission modules and their labels.',
    )

    my_permissions = graphene.Field(
        GenericScalar,
        description="Current user's role permissions (module to actions map).",
    )

    # ---- Members ----
    members = graphene.Field(
        MemberConnectionType,
        first=graphene.Int(default_value=25),
        after=graphene.String(),
        status=graphene.String(),
        membership_type=graphene.String(),
        search=graphene.String(),
        description='Paginated member list.',
    )

    member = graphene.Field(
        MemberType,
        id=graphene.UUID(required=True),
        description='A single member by ID.',
    )

    # ------------------------------------------------------------------
    # Resolvers
    # ------------------------------------------------------------------

    @require_authentication
    def resolve_me(self, info):
        return info.context.user

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_user(self, info, id):
        try:
            return User.objects.get(pk=id)
        except User.DoesNotExist:
            return None

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_users(self, info, first=25, after=None, role=None, is_active=None, search=None):
        qs = User.objects.all().order_by('-created_at')

        if role:
            qs = qs.filter(role=role)
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        page = paginate_queryset(qs, first=first, after=after)

        return UserConnectionType(
            edges=page['edges'],
            page_info=PageInfo(
                has_next_page=page['has_next_page'],
                has_previous_page=page['has_previous_page'],
                start_cursor=page['start_cursor'],
                end_cursor=page['end_cursor'],
            ),
            total_count=page['total_count'],
        )

    @require_authentication
    def resolve_my_verification_requests(self, info):
        return VerificationRequest.objects.filter(
            user=info.context.user,
        ).order_by('-created_at')

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_pending_verifications(self, info):
        return VerificationRequest.objects.filter(
            status__in=['PENDING', 'MANUAL_REVIEW'],
        ).order_by('created_at')

    # ---- RBAC Resolvers ----

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    def resolve_role_configs(self, info):
        return RoleConfig.objects.all()

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    def resolve_role_config(self, info, id):
        try:
            return RoleConfig.objects.get(pk=id)
        except RoleConfig.DoesNotExist:
            return None

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    def resolve_available_modules(self, info):
        return [
            ModuleInfoType(key=k, label=l)
            for k, l in RoleConfig.MODULE_CHOICES
        ]

    @require_authentication
    def resolve_my_permissions(self, info):
        """Return the permission map for the current user's role."""
        user = info.context.user
        try:
            config = RoleConfig.objects.get(role_key=user.role, is_active=True)
            return config.permissions
        except RoleConfig.DoesNotExist:
            # Fallback: return empty permissions (deny all)
            return {}

    # ---- Member Resolvers ----

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_members(self, info, first=25, after=None, status=None, membership_type=None, search=None):
        qs = Member.objects.all().order_by('-created_at')

        if status:
            qs = qs.filter(status=status)
        if membership_type:
            qs = qs.filter(membership_type=membership_type)
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(membership_number__icontains=search) |
                Q(nic_number__icontains=search) |
                Q(phone_number__icontains=search)
            )

        page = paginate_queryset(qs, first=first, after=after)

        return MemberConnectionType(
            edges=page['edges'],
            page_info=PageInfo(
                has_next_page=page['has_next_page'],
                has_previous_page=page['has_previous_page'],
                start_cursor=page['start_cursor'],
                end_cursor=page['end_cursor'],
            ),
            total_count=page['total_count'],
        )

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_member(self, info, id):
        try:
            return Member.objects.get(pk=id)
        except Member.DoesNotExist:
            return None
