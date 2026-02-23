"""
Asset Management — Domain Models
=================================
Manages library physical assets: furniture, equipment, computers, printers,
HVAC systems, etc. Tracks condition, location, maintenance schedules, and
depreciation for enterprise-level library operations.

Models:
    AssetCategory — hierarchical classification (e.g., Furniture > Tables)
    Asset         — individual tracked asset (aggregate root)
    MaintenanceLog — maintenance / repair records
    AssetDisposal — disposal / write-off records
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.common.base_models import TimeStampedModel


class AssetCategory(TimeStampedModel):
    """Hierarchical asset classification."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='children',
    )
    description = models.TextField(blank=True, default='')
    icon = models.CharField(max_length=50, blank=True, default='')

    class Meta:
        db_table = 'asset_category'
        ordering = ['name']
        verbose_name_plural = 'Asset Categories'

    def __str__(self):
        return self.name


class Asset(TimeStampedModel):
    """
    Individual tracked library asset (aggregate root).
    Examples: desks, chairs, computers, projectors, printers, shelving units.
    """

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active & In Use'
        IN_STORAGE = 'IN_STORAGE', 'In Storage'
        UNDER_MAINTENANCE = 'UNDER_MAINTENANCE', 'Under Maintenance'
        DISPOSED = 'DISPOSED', 'Disposed / Written Off'
        ON_ORDER = 'ON_ORDER', 'On Order'

    class Condition(models.TextChoices):
        EXCELLENT = 'EXCELLENT', 'Excellent'
        GOOD = 'GOOD', 'Good'
        FAIR = 'FAIR', 'Fair'
        POOR = 'POOR', 'Poor'
        DAMAGED = 'DAMAGED', 'Damaged'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset_tag = models.CharField(max_length=50, unique=True, help_text='Unique tag e.g. NOVA-ASSET-0001')
    name = models.CharField(max_length=200)
    category = models.ForeignKey(AssetCategory, on_delete=models.PROTECT, related_name='assets')
    description = models.TextField(blank=True, default='')

    # Status & condition
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    condition = models.CharField(max_length=20, choices=Condition.choices, default=Condition.GOOD)

    # Location
    floor_number = models.PositiveSmallIntegerField(null=True, blank=True)
    room = models.CharField(max_length=100, blank=True, default='')
    location_notes = models.TextField(blank=True, default='')

    # Financial
    purchase_date = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    supplier = models.CharField(max_length=200, blank=True, default='')
    warranty_expiry = models.DateField(null=True, blank=True)

    # Depreciation
    useful_life_years = models.PositiveSmallIntegerField(default=5, help_text='Expected useful life in years')
    salvage_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    # Specs
    serial_number = models.CharField(max_length=100, blank=True, default='')
    manufacturer = models.CharField(max_length=200, blank=True, default='')
    model_number = models.CharField(max_length=100, blank=True, default='')

    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='assigned_assets',
    )

    # Maintenance
    next_maintenance_date = models.DateField(null=True, blank=True)
    maintenance_interval_days = models.PositiveIntegerField(null=True, blank=True, help_text='Days between scheduled maintenance')

    # Image
    image_url = models.URLField(blank=True, default='')

    class Meta:
        db_table = 'asset_asset'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['category']),
            models.Index(fields=['asset_tag']),
        ]

    def __str__(self):
        return f'{self.asset_tag} — {self.name}'

    @property
    def is_under_warranty(self) -> bool:
        if not self.warranty_expiry:
            return False
        return self.warranty_expiry >= date.today()

    @property
    def current_value(self) -> Decimal:
        """Straight-line depreciation."""
        if not self.purchase_price or not self.purchase_date:
            return Decimal('0.00')
        years_owned = (date.today() - self.purchase_date).days / 365.25
        annual_depreciation = (self.purchase_price - self.salvage_value) / self.useful_life_years
        depreciated = annual_depreciation * Decimal(str(years_owned))
        value = self.purchase_price - depreciated
        return max(value, self.salvage_value)

    @property
    def maintenance_overdue(self) -> bool:
        if not self.next_maintenance_date:
            return False
        return self.next_maintenance_date < date.today()


class MaintenanceLog(TimeStampedModel):
    """Record of maintenance or repair performed on an asset."""

    class Type(models.TextChoices):
        PREVENTIVE = 'PREVENTIVE', 'Scheduled / Preventive'
        CORRECTIVE = 'CORRECTIVE', 'Corrective / Repair'
        INSPECTION = 'INSPECTION', 'Inspection'
        UPGRADE = 'UPGRADE', 'Upgrade / Enhancement'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='maintenance_logs')
    maintenance_type = models.CharField(max_length=20, choices=Type.choices)
    description = models.TextField()
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='maintenance_performed',
    )
    performed_date = models.DateField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    vendor = models.CharField(max_length=200, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    condition_after = models.CharField(max_length=20, choices=Asset.Condition.choices, blank=True, default='')

    class Meta:
        db_table = 'asset_maintenance_log'
        ordering = ['-performed_date']

    def __str__(self):
        return f'{self.asset.asset_tag} — {self.maintenance_type} on {self.performed_date}'


class AssetDisposal(TimeStampedModel):
    """Disposal / write-off record for an asset."""

    class Method(models.TextChoices):
        SOLD = 'SOLD', 'Sold'
        DONATED = 'DONATED', 'Donated'
        RECYCLED = 'RECYCLED', 'Recycled'
        SCRAPPED = 'SCRAPPED', 'Scrapped'
        TRANSFERRED = 'TRANSFERRED', 'Transferred'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name='disposal')
    method = models.CharField(max_length=20, choices=Method.choices)
    disposed_date = models.DateField()
    disposal_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    reason = models.TextField()
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='disposals_approved',
    )
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'asset_disposal'
        ordering = ['-disposed_date']

    def __str__(self):
        return f'{self.asset.asset_tag} — {self.method} on {self.disposed_date}'
