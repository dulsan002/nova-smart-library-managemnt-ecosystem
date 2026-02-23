"""
System Settings — GraphQL Schema
==================================
Admin-friendly settings management via GraphQL.
"""

import graphene
from graphene_django import DjangoObjectType

from apps.common.decorators import require_authentication, require_roles, audit_action
from apps.common.permissions import Role
from apps.common.domain.settings_model import SystemSetting


class SystemSettingType(DjangoObjectType):
    typed_value = graphene.String()

    class Meta:
        model = SystemSetting
        fields = (
            'id', 'key', 'value', 'value_type', 'category',
            'label', 'description', 'is_sensitive', 'updated_by',
            'created_at', 'updated_at',
        )

    def resolve_typed_value(self, info):
        if self.is_sensitive:
            return '********'
        return str(self.typed_value)

    def resolve_value(self, info):
        if self.is_sensitive:
            return '********'
        return self.value


class UpdateSystemSetting(graphene.Mutation):
    class Arguments:
        key = graphene.String(required=True)
        value = graphene.String(required=True)

    Output = SystemSettingType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    @audit_action(action='UPDATE', resource_type='SystemSetting')
    def mutate(self, info, key, value):
        setting = SystemSetting.objects.get(key=key)
        # Validate type
        if setting.value_type == 'INTEGER':
            int(value)  # Raises ValueError if invalid
        elif setting.value_type == 'FLOAT':
            float(value)
        elif setting.value_type == 'BOOLEAN':
            if value.lower() not in ('true', 'false', '1', '0', 'yes', 'no'):
                raise ValueError(f'Invalid boolean value: {value}')
        elif setting.value_type == 'JSON':
            import json
            json.loads(value)  # Raises JSONDecodeError if invalid

        setting.value = value
        setting.updated_by = info.context.user
        setting.save()
        return setting


class SyncDefaultSettings(graphene.Mutation):
    """Ensures all default settings exist in the database."""

    created_count = graphene.Int()

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    def mutate(self, info):
        count = SystemSetting.sync_defaults()
        return SyncDefaultSettings(created_count=count)


class SettingsQuery(graphene.ObjectType):
    system_settings = graphene.List(
        SystemSettingType,
        category=graphene.String(),
    )
    system_setting = graphene.Field(
        SystemSettingType,
        key=graphene.String(required=True),
    )

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    def resolve_system_settings(self, info, category=None):
        qs = SystemSetting.objects.all()
        if category:
            qs = qs.filter(category=category)
        return qs

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    def resolve_system_setting(self, info, key):
        return SystemSetting.objects.get(key=key)


class SettingsMutation(graphene.ObjectType):
    update_system_setting = UpdateSystemSetting.Field()
    sync_default_settings = SyncDefaultSettings.Field()
