"""
Nova — Identity GraphQL Types
=================================
GraphQL object types for the identity bounded context.
"""

import graphene
from graphene_django import DjangoObjectType
from graphene.types.generic import GenericScalar

from apps.identity.domain.models import User, VerificationRequest, RoleConfig, Member


class UserType(DjangoObjectType):
    """Public-facing user type."""

    full_name = graphene.String()
    is_admin = graphene.Boolean()
    is_librarian = graphene.Boolean()
    is_staff_member = graphene.Boolean()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'phone_number',
            'role', 'is_active', 'is_verified', 'verification_status',
            'avatar_url', 'date_of_birth', 'institution_id', 'nic_number',
            'last_login_at', 'login_count', 'created_at', 'updated_at',
        )

    def resolve_full_name(self, info):
        return self.full_name

    def resolve_is_admin(self, info):
        return self.is_admin

    def resolve_is_librarian(self, info):
        return self.is_librarian

    def resolve_is_staff_member(self, info):
        return self.is_staff_member


class VerificationRequestType(DjangoObjectType):
    class Meta:
        model = VerificationRequest
        fields = (
            'id', 'user', 'status', 'extracted_name',
            'extracted_id_number', 'ocr_confidence', 'face_match_score',
            'rejection_reason', 'reviewed_by', 'reviewed_at',
            'attempt_number', 'created_at',
        )


class TokenPairType(graphene.ObjectType):
    access_token = graphene.String(required=True)
    refresh_token = graphene.String(required=True)
    expires_in = graphene.Int(required=True)
    token_type = graphene.String(required=True)


class AuthPayloadType(graphene.ObjectType):
    """Wrapper returned by login / register mutations."""
    user = graphene.Field(UserType)
    tokens = graphene.Field(TokenPairType)


class PageInfoType(graphene.ObjectType):
    has_next_page = graphene.Boolean(required=True)
    has_previous_page = graphene.Boolean(required=True)
    start_cursor = graphene.String()
    end_cursor = graphene.String()


class UserEdgeType(graphene.ObjectType):
    """Relay-style edge wrapping a UserType with a cursor."""
    node = graphene.Field(UserType)
    cursor = graphene.String()


class UserConnectionType(graphene.ObjectType):
    edges = graphene.List(UserEdgeType)
    page_info = graphene.Field(PageInfoType)
    total_count = graphene.Int()


# ---------------------------------------------------------------------------
# Role Config types
# ---------------------------------------------------------------------------

class ModuleInfoType(graphene.ObjectType):
    """Describes a permission module (e.g. 'books')."""
    key = graphene.String(required=True)
    label = graphene.String(required=True)


class RoleConfigType(DjangoObjectType):
    """Dynamic role configuration with permissions matrix."""

    permissions = GenericScalar(description='JSON dict: module_key → [action, …]')

    class Meta:
        model = RoleConfig
        fields = (
            'id', 'role_key', 'display_name', 'description',
            'permissions', 'is_system', 'is_active',
            'created_at', 'updated_at',
        )


# ---------------------------------------------------------------------------
# Member types
# ---------------------------------------------------------------------------

class MemberType(DjangoObjectType):
    """Library member / patron type."""

    full_name = graphene.String()
    is_active_member = graphene.Boolean()

    class Meta:
        model = Member
        fields = (
            'id', 'user', 'membership_number', 'first_name', 'last_name',
            'email', 'phone_number', 'date_of_birth', 'nic_number', 'address',
            'membership_type', 'status', 'joined_date', 'expiry_date',
            'max_borrows', 'emergency_contact_name', 'emergency_contact_phone',
            'notes', 'created_at', 'updated_at',
        )

    def resolve_full_name(self, info):
        return self.full_name

    def resolve_is_active_member(self, info):
        return self.is_active_member


class MemberEdgeType(graphene.ObjectType):
    node = graphene.Field(MemberType)
    cursor = graphene.String()


class MemberConnectionType(graphene.ObjectType):
    edges = graphene.List(MemberEdgeType)
    page_info = graphene.Field(PageInfoType)
    total_count = graphene.Int()
