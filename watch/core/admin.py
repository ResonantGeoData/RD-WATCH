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

from .models import Feature, GoogleCloudRecord, Region, STACFile
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
class RegionAdmin(OSMGeoAdmin, _FileGetNameMixin):
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
class STACFileAdmin(OSMGeoAdmin):
    list_display = (
        'pk',
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
    list_filter = ('file__collection',) + MODIFIABLE_FILTERS + TASK_EVENT_FILTERS


@admin.register(GoogleCloudRecord)
class GoogleCloudRecordAdmin(OSMGeoAdmin):
    list_display = (
        'pk',
        'catalog',
        'status',
        'modified',
        'created',
    )
    readonly_fields = (
        'modified',
        'created',
    ) + TASK_EVENT_READONLY
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS
    actions = (reprocess,)
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS
