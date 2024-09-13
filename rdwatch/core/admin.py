from django.contrib import admin

from rdwatch.core.models import (
    AnimationModelRunExport,
    AnimationSiteExport,
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
    raw_id_fields = ('site',)


@admin.register(SiteEvaluation)
class SiteEvaluationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'configuration',
        'number',
        'timestamp',
        'geom',
        'point',
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
    raw_id_fields = ('site', 'observation')


@admin.register(SiteObservation)
class SiteObservationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'siteeval',
        'label',
        'score',
        'geom',
        'point',
        'constellation',
        'spectrum',
        'timestamp',
    )
    list_filter = ('timestamp',)
    raw_id_fields = ('siteeval', 'label', 'constellation', 'spectrum')


@admin.register(AnimationSiteExport)
class AnimationSiteExportAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'user',
        'site_evaluation',
        'export_file',
        'created',
        'celery_id',
        'arguments',
    )


@admin.register(AnimationModelRunExport)
class AnimationModelRunExportAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'user',
        'export_file',
        'created',
        'celery_id',
        'arguments',
    )
