from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest

from rdwatch.models import (
    ModelRun,
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


@admin.register(ModelRun)
class ModelRunAdmin(admin.ModelAdmin):
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
        'timestamp',
        'image',
        'image_embedding',
        'cloudcover',
        'percent_black',
        'source',
    )
    list_filter = ('timestamp',)
    actions = ['compute_embedding']

    @admin.action(description='Compute Embedding')
    def compute_embedding(self, request: HttpRequest, queryset: QuerySet):
        counter = 0
        for site_image in queryset:
            if not site_image.image_embedding:
                # generate_image_embedding.delay(site_image.pk)
                if site_image:
                    import numpy as np
                    import cv2
                    import os
                    from segment_anything import sam_model_registry, SamPredictor

                    checkpoint = "/data/SAM/sam_vit_    h_4b8939.pth"
                    model_type = "vit_h"
                    sam = sam_model_registry[model_type](checkpoint=checkpoint)

                    sam.to(device='cpu')
                    predictor = SamPredictor(sam)
                    image = cv2.imread(site_image.image)
                    predictor.set_image(image)
                    image_embedding = predictor.get_image_embedding().cpu().numpy()
                    np.save("sampleImage.npy", image_embedding)
                    site_image.image_bbox = "sampleImage.npy"
                    os.remove('sampleImage.npy')
                    counter += 1
        self.message_user(request, f'{counter} images queued', messages.SUCCESS)


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
