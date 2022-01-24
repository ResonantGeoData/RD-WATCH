from django.conf import settings
from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.admin.mixins import (
    MODIFIABLE_FILTERS,
    TASK_EVENT_FILTERS,
    TASK_EVENT_READONLY,
    GeoAdminInline,
    _FileGetNameMixin,
    reprocess,
)

from .models import Observation, Region, Site, STACFile
from .tasks.jobs import task_populate_stac_file_outline


class SiteInline(GeoAdminInline):
    model = Site
    fk_name = 'parent_region'
    extra = 0
    readonly_fields = (
        'modified',
        'created',
    )
    modifiable = False  # To still show the footprint and outline


@admin.register(Region)
class RegionAdmin(OSMGeoAdmin):
    list_display = (
        'pk',
        'region_id',
        'start_date',
        'end_date',
        'modified',
        'created',
    )
    readonly_fields = (
        'modified',
        'created',
    )
    inlines = (SiteInline,)
    list_filter = (
        'start_date',
        'end_date',
    ) + MODIFIABLE_FILTERS


class ObservationInline(GeoAdminInline):
    model = Observation
    fk_name = 'parent_site'
    extra = 0
    readonly_fields = (
        'modified',
        'created',
    )
    modifiable = False  # To still show the footprint and outline


def update_site_regions(modeladmin, request, queryset):
    for site in queryset.all():
        if not site.parent_region:
            try:
                site.parent_region = Region.objects.get(region_id=site.properties['region_id'])
                site.save(
                    update_fields=[
                        'parent_region',
                    ]
                )
            except Region.DoesNotExist:
                pass


@admin.register(Site)
class SiteAdmin(OSMGeoAdmin):
    list_display = (
        'pk',
        'site_id',
        'parent_region',
        'start_date',
        'end_date',
        'modified',
        'created',
    )
    readonly_fields = (
        'modified',
        'created',
    )
    inlines = (ObservationInline,)
    list_filter = (
        'start_date',
        'end_date',
        'parent_region__region_id',
    ) + MODIFIABLE_FILTERS
    raw_id_fields = ('parent_region',)
    actions = (update_site_regions,)


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
        ('file__collection', 'file__created_by', 'processed', 'server_modified')
        + MODIFIABLE_FILTERS
        + TASK_EVENT_FILTERS
    )
    raw_id_fields = ('file',)
