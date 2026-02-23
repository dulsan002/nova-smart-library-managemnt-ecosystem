"""
Asset Management — GraphQL Schema
===================================
Full CRUD for library physical assets with filtering, stats, and maintenance tracking.
"""

import graphene
from graphene_django import DjangoObjectType

from apps.common.decorators import require_authentication, require_roles, audit_action
from apps.common.permissions import Role
from apps.asset_management.domain.models import AssetCategory, Asset, MaintenanceLog, AssetDisposal


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class AssetCategoryType(DjangoObjectType):
    asset_count = graphene.Int()

    class Meta:
        model = AssetCategory
        fields = ('id', 'name', 'slug', 'parent', 'children', 'description', 'icon', 'created_at')

    def resolve_asset_count(self, info):
        return self.assets.count()


class AssetType(DjangoObjectType):
    current_value = graphene.Float()
    is_under_warranty = graphene.Boolean()
    maintenance_overdue = graphene.Boolean()

    class Meta:
        model = Asset
        fields = (
            'id', 'asset_tag', 'name', 'category', 'description',
            'status', 'condition', 'floor_number', 'room', 'location_notes',
            'purchase_date', 'purchase_price', 'supplier', 'warranty_expiry',
            'useful_life_years', 'salvage_value', 'serial_number',
            'manufacturer', 'model_number', 'assigned_to',
            'next_maintenance_date', 'maintenance_interval_days',
            'image_url', 'maintenance_logs', 'created_at', 'updated_at',
        )

    def resolve_current_value(self, info):
        return float(self.current_value)

    def resolve_is_under_warranty(self, info):
        return self.is_under_warranty

    def resolve_maintenance_overdue(self, info):
        return self.maintenance_overdue


class MaintenanceLogType(DjangoObjectType):
    class Meta:
        model = MaintenanceLog
        fields = (
            'id', 'asset', 'maintenance_type', 'description',
            'performed_by', 'performed_date', 'cost', 'vendor',
            'notes', 'condition_after', 'created_at',
        )


class AssetDisposalType(DjangoObjectType):
    class Meta:
        model = AssetDisposal
        fields = (
            'id', 'asset', 'method', 'disposed_date', 'disposal_value',
            'reason', 'approved_by', 'notes', 'created_at',
        )


class AssetStatsType(graphene.ObjectType):
    total_assets = graphene.Int()
    active_count = graphene.Int()
    under_maintenance_count = graphene.Int()
    disposed_count = graphene.Int()
    total_value = graphene.Float()
    maintenance_overdue_count = graphene.Int()
    warranty_expiring_soon = graphene.Int()


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------

class CreateAssetCategory(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        slug = graphene.String(required=True)
        parent_id = graphene.UUID()
        description = graphene.String()
        icon = graphene.String()

    Output = AssetCategoryType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    @audit_action(action='CREATE', resource_type='AssetCategory')
    def mutate(self, info, name, slug, parent_id=None, description='', icon=''):
        parent = None
        if parent_id:
            parent = AssetCategory.objects.get(pk=parent_id)
        return AssetCategory.objects.create(
            name=name, slug=slug, parent=parent,
            description=description, icon=icon,
        )


class CreateAsset(graphene.Mutation):
    class Arguments:
        asset_tag = graphene.String(required=True)
        name = graphene.String(required=True)
        category_id = graphene.UUID(required=True)
        description = graphene.String()
        status = graphene.String()
        condition = graphene.String()
        floor_number = graphene.Int()
        room = graphene.String()
        purchase_date = graphene.Date()
        purchase_price = graphene.Float()
        supplier = graphene.String()
        warranty_expiry = graphene.Date()
        useful_life_years = graphene.Int()
        serial_number = graphene.String()
        manufacturer = graphene.String()
        model_number = graphene.String()
        assigned_to_id = graphene.UUID()
        next_maintenance_date = graphene.Date()
        maintenance_interval_days = graphene.Int()
        image_url = graphene.String()

    Output = AssetType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    @audit_action(action='CREATE', resource_type='Asset')
    def mutate(self, info, asset_tag, name, category_id, **kwargs):
        from apps.identity.domain.models import User
        category = AssetCategory.objects.get(pk=category_id)
        data = {'asset_tag': asset_tag, 'name': name, 'category': category}
        simple_fields = [
            'description', 'status', 'condition', 'floor_number', 'room',
            'purchase_date', 'purchase_price', 'supplier', 'warranty_expiry',
            'useful_life_years', 'serial_number', 'manufacturer', 'model_number',
            'next_maintenance_date', 'maintenance_interval_days', 'image_url',
        ]
        for field in simple_fields:
            if field in kwargs and kwargs[field] is not None:
                data[field] = kwargs[field]
        if kwargs.get('assigned_to_id'):
            data['assigned_to'] = User.objects.get(pk=kwargs['assigned_to_id'])
        return Asset.objects.create(**data)


class UpdateAsset(graphene.Mutation):
    class Arguments:
        id = graphene.UUID(required=True)
        name = graphene.String()
        status = graphene.String()
        condition = graphene.String()
        floor_number = graphene.Int()
        room = graphene.String()
        description = graphene.String()
        assigned_to_id = graphene.UUID()
        next_maintenance_date = graphene.Date()
        maintenance_interval_days = graphene.Int()

    Output = AssetType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    @audit_action(action='UPDATE', resource_type='Asset')
    def mutate(self, info, id, **kwargs):
        asset = Asset.objects.get(pk=id)
        update_fields = [
            'name', 'status', 'condition', 'floor_number', 'room',
            'description', 'next_maintenance_date', 'maintenance_interval_days',
        ]
        for field in update_fields:
            if field in kwargs and kwargs[field] is not None:
                setattr(asset, field, kwargs[field])
        if 'assigned_to_id' in kwargs:
            if kwargs['assigned_to_id']:
                from apps.identity.domain.models import User
                asset.assigned_to = User.objects.get(pk=kwargs['assigned_to_id'])
            else:
                asset.assigned_to = None
        asset.save()
        return asset


class DeleteAsset(graphene.Mutation):
    class Arguments:
        id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    @audit_action(action='DELETE', resource_type='Asset')
    def mutate(self, info, id):
        Asset.objects.filter(pk=id).delete()
        return DeleteAsset(ok=True)


class LogMaintenance(graphene.Mutation):
    class Arguments:
        asset_id = graphene.UUID(required=True)
        maintenance_type = graphene.String(required=True)
        description = graphene.String(required=True)
        performed_date = graphene.Date(required=True)
        cost = graphene.Float()
        vendor = graphene.String()
        notes = graphene.String()
        condition_after = graphene.String()

    Output = MaintenanceLogType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    @audit_action(action='CREATE', resource_type='MaintenanceLog')
    def mutate(self, info, asset_id, maintenance_type, description, performed_date, **kwargs):
        from datetime import timedelta
        asset = Asset.objects.get(pk=asset_id)
        log = MaintenanceLog.objects.create(
            asset=asset, maintenance_type=maintenance_type,
            description=description, performed_by=info.context.user,
            performed_date=performed_date,
            cost=kwargs.get('cost', 0),
            vendor=kwargs.get('vendor', ''),
            notes=kwargs.get('notes', ''),
            condition_after=kwargs.get('condition_after', ''),
        )
        if kwargs.get('condition_after'):
            asset.condition = kwargs['condition_after']
        if asset.maintenance_interval_days:
            asset.next_maintenance_date = performed_date + timedelta(days=asset.maintenance_interval_days)
        asset.status = 'ACTIVE'
        asset.save()
        return log


class DisposeAsset(graphene.Mutation):
    class Arguments:
        asset_id = graphene.UUID(required=True)
        method = graphene.String(required=True)
        disposed_date = graphene.Date(required=True)
        disposal_value = graphene.Float()
        reason = graphene.String(required=True)
        notes = graphene.String()

    Output = AssetDisposalType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    @audit_action(action='CREATE', resource_type='AssetDisposal')
    def mutate(self, info, asset_id, method, disposed_date, reason, **kwargs):
        asset = Asset.objects.get(pk=asset_id)
        disposal = AssetDisposal.objects.create(
            asset=asset, method=method, disposed_date=disposed_date,
            disposal_value=kwargs.get('disposal_value', 0),
            reason=reason, approved_by=info.context.user,
            notes=kwargs.get('notes', ''),
        )
        asset.status = 'DISPOSED'
        asset.save()
        return disposal


# ---------------------------------------------------------------------------
# Query & Mutation roots
# ---------------------------------------------------------------------------

class AssetManagementQuery(graphene.ObjectType):
    asset_categories = graphene.List(AssetCategoryType)
    assets = graphene.List(
        AssetType,
        status=graphene.String(),
        category_id=graphene.UUID(),
        search=graphene.String(),
        limit=graphene.Int(default_value=50),
    )
    asset = graphene.Field(AssetType, id=graphene.UUID(required=True))
    asset_stats = graphene.Field(AssetStatsType)
    maintenance_logs = graphene.List(
        MaintenanceLogType,
        asset_id=graphene.UUID(),
        limit=graphene.Int(default_value=20),
    )

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN, Role.ASSISTANT])
    def resolve_asset_categories(self, info):
        return AssetCategory.objects.select_related('parent').all()

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN, Role.ASSISTANT])
    def resolve_assets(self, info, status=None, category_id=None, search=None, limit=50):
        qs = Asset.objects.select_related('category', 'assigned_to').all()
        if status:
            qs = qs.filter(status=status)
        if category_id:
            qs = qs.filter(category_id=category_id)
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(asset_tag__icontains=search) |
                Q(serial_number__icontains=search)
            )
        return qs[:limit]

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN, Role.ASSISTANT])
    def resolve_asset(self, info, id):
        return Asset.objects.select_related('category', 'assigned_to').get(pk=id)

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_asset_stats(self, info):
        from django.db.models import Sum, Count, Q
        from datetime import date, timedelta

        qs = Asset.objects.all()
        agg = qs.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status='ACTIVE')),
            maint=Count('id', filter=Q(status='UNDER_MAINTENANCE')),
            disposed=Count('id', filter=Q(status='DISPOSED')),
            total_val=Sum('purchase_price'),
        )
        today = date.today()
        maint_overdue = qs.filter(
            next_maintenance_date__lt=today,
        ).exclude(status='DISPOSED').count()
        warranty_soon = qs.filter(
            warranty_expiry__gte=today,
            warranty_expiry__lte=today + timedelta(days=30),
        ).count()

        return AssetStatsType(
            total_assets=agg['total'],
            active_count=agg['active'],
            under_maintenance_count=agg['maint'],
            disposed_count=agg['disposed'],
            total_value=float(agg['total_val'] or 0),
            maintenance_overdue_count=maint_overdue,
            warranty_expiring_soon=warranty_soon,
        )

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_maintenance_logs(self, info, asset_id=None, limit=20):
        qs = MaintenanceLog.objects.select_related('asset', 'performed_by').all()
        if asset_id:
            qs = qs.filter(asset_id=asset_id)
        return qs[:limit]


class AssetManagementMutation(graphene.ObjectType):
    create_asset_category = CreateAssetCategory.Field()
    create_asset = CreateAsset.Field()
    update_asset = UpdateAsset.Field()
    delete_asset = DeleteAsset.Field()
    log_maintenance = LogMaintenance.Field()
    dispose_asset = DisposeAsset.Field()
