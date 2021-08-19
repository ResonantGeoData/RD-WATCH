from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.admin.mixins import (
    MODIFIABLE_FILTERS,
    SPATIAL_ENTRY_FILTERS,
    TASK_EVENT_FILTERS,
    TASK_EVENT_READONLY,
    _FileGetNameMixin,
    reprocess,
)

from .models import Feature, Region


# TODO: use inline patch from https://github.com/ResonantGeoData/ResonantGeoData/pull/489
class FeatureInline(admin.StackedInline):
    model = Feature
    fk_name = 'parent_region'
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
