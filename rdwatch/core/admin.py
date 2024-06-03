from django.contrib import admin

from rdwatch.core.models import (
    ModelRun,
    Performer,
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


@admin.register(Performer)
class PerformerAdmin(admin.ModelAdmin):
    list_display = ('id', 'team_name', 'short_code')
    search_fields = ('slug',)


@admin.register(lookups.ProcessingLevel)
class ProcessingLevelAdmin(admin.ModelAdmin):
    list_display = ('id', 'slug', 'description')
    search_fields = ('slug',)


@admin.register(ModelRun)
class ModelRunAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'region',
        'title',
        'performer',
        'parameters',
        'evaluation',
        'evaluation_run',
        'expiration_time',
        'ground_truth',
    )
    list_filter = ('created', 'performer', 'region')


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(SatelliteFetching)
class SatelliteFetchingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'site',
        'timestamp',
        'status',
        'celery_id',
        'error',
    )
    list_filter = ('site', 'timestamp')


@admin.register(SiteEvaluation)
class SiteEvaluationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'configuration',
        'number',
        'timestamp',
        'geom',
        'label',
        'score',
        'version',
    )
    list_filter = ('timestamp',)
    raw_id_fields = ('configuration', 'label')


@admin.register(SiteImage)
class SiteImageAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'timestamp',
        'image',
        'image_embedding',
        'cloudcover',
        'percent_black',
        'source',
    )
    list_filter = ('timestamp',)


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
