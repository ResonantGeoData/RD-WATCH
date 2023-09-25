from django.contrib import admin

from rdwatch.models import (
    HyperParameters,
    Region,
    SatelliteFetching,
    SiteEvaluation,
    SiteImage,
    SiteObservation,
    lookups,
)


@admin.register(lookups.CommonBand)
class CommonBandAdmin(admin.ModelAdmin):
    list_display = ('id', 'slug', 'description', 'spectrum')
    search_fields = ('slug',)


@admin.register(lookups.Constellation)
class ConstellationAdmin(admin.ModelAdmin):
    list_display = ('id', 'slug', 'description')
    search_fields = ('slug',)


@admin.register(lookups.ObservationLabel)
class ObservationLabelAdmin(admin.ModelAdmin):
    list_display = ('id', 'slug', 'description')
    search_fields = ('slug',)


@admin.register(lookups.Performer)
class PerformerAdmin(admin.ModelAdmin):
    list_display = ('id', 'slug', 'description')
    search_fields = ('slug',)


@admin.register(lookups.ProcessingLevel)
class ProcessingLevelAdmin(admin.ModelAdmin):
    list_display = ('id', 'slug', 'description')
    search_fields = ('slug',)


@admin.register(HyperParameters)
class HyperParametersAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'title',
        'performer',
        'parameters',
        'evaluation',
        'evaluation_run',
        'expiration_time',
    )
    list_filter = ('created', 'performer')


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(SatelliteFetching)
class SatelliteFetchingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'siteeval',
        'timestamp',
        'status',
        'celery_id',
        'error',
    )
    list_filter = ('siteeval', 'timestamp')


@admin.register(SiteEvaluation)
class SiteEvaluationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'configuration',
        'region',
        'number',
        'timestamp',
        'geom',
        'label',
        'score',
        'version',
    )
    list_filter = ('timestamp',)
    raw_id_fields = ('configuration', 'region', 'label')


@admin.register(SiteImage)
class SiteImageAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'siteeval',
        'siteobs',
        'timestamp',
        'image',
        'cloudcover',
        'percent_black',
        'source',
    )
    list_filter = ('siteeval', 'siteobs', 'timestamp')


@admin.register(SiteObservation)
class SiteObservationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'siteeval',
        'label',
        'score',
        'geom',
        'constellation',
        'spectrum',
        'timestamp',
    )
    list_filter = ('timestamp',)
    raw_id_fields = ('siteeval', 'label', 'constellation', 'spectrum')
