from django.conf import settings
from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.admin.mixins import (
    MODIFIABLE_FILTERS,
    SPATIAL_ENTRY_FILTERS,
    TASK_EVENT_FILTERS,
    TASK_EVENT_READONLY,
    GeoAdminInline,
    _FileGetNameMixin,
    reprocess,
)

from .models import Feature, Region, STACFile
from .tasks.jobs import task_populate_stac_file_outline


class FeatureInline(GeoAdminInline):
    model = Feature
    fk_name = 'parent_region'
    extra = 0
    list_display = (
        'pk',
        'modified',
        'created',
    )
    list_filter = MODIFIABLE_FILTERS + SPATIAL_ENTRY_FILTERS
    readonly_fields = (
        'modified',
        'created',
    )
    modifiable = False  # To still show the footprint and outline


@admin.register(Region)
class RegionAdmin(OSMGeoAdmin):
    list_display = (
        'pk',
        'status',
        'modified',
        'created',
    )
    readonly_fields = (
        'modified',
        'created',
    ) + TASK_EVENT_READONLY
    inlines = (FeatureInline,)
    actions = (reprocess,)
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS


def update_outdated(modeladmin, request, queryset):
    """Update any entries whose `server_modified` date is after `processed` date."""
    for item in queryset.all():
        if item.server_modified and (
            item.processed is None or item.server_modified > item.processed
        ):
            item.save()


def populate_outline(modeladmin, request, queryset):
    for item in queryset.all():
        if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', None):
            # HACK: for some reason this is necessary
            task_populate_stac_file_outline(item.pk)
        else:
            task_populate_stac_file_outline.delay(item.pk)


@admin.register(STACFile)
class STACFileAdmin(OSMGeoAdmin, _FileGetNameMixin):
    def get_collection(self, obj):
        return obj.file.collection

    get_collection.short_description = 'Collection'
    get_collection.admin_order_field = 'file__collection'

    list_display = (
        'pk',
        'get_name',
        'get_collection',
        'status',
        'server_modified',
        'processed',
        'modified',
        'created',
    )
    readonly_fields = (
        'modified',
        'created',
    ) + TASK_EVENT_READONLY
    actions = (
        reprocess,
        update_outdated,
        populate_outline,
    )
    list_filter = (
        ('file__collection', 'processed', 'server_modified')
        + MODIFIABLE_FILTERS
        + TASK_EVENT_FILTERS
    )
    raw_id_fields = ('file',)
