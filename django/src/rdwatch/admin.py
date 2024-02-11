import os

import cv2
from segment_anything import SamPredictor, sam_model_registry

from django.contrib import admin, messages
from django.core.files.base import ContentFile
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
            try:
                checkpoint = '/data/SAM/sam_vit_h_4b8939.pth'
                model_type = 'vit_h'
                sam = sam_model_registry[model_type](checkpoint=checkpoint)
                sam.to(device='cpu')
                predictor = SamPredictor(sam)

                image_file = site_image.image.open(mode='rb')
                local_file_path = '/tmp/image.png'
                with open(local_file_path, 'wb') as local_file:
                    local_file.write(image_file.read())

                print('Reading local image file')

                image = cv2.imread(local_file_path)
                print('Setting the predictor for the file')
                predictor.set_image(image)
                print('Creating the embedding')
                image_embedding = predictor.get_image_embedding().cpu().numpy()
                print('Saving the npy')

                # Assuming you want to save the numpy array to the image_embedding field
                site_image.image_embedding.save(
                    'sampleImage.npy', ContentFile(image_embedding.tobytes())
                )

                os.remove(local_file_path)
                counter += 1

            except Exception as e:
                # Handle exceptions (e.g., logging, showing error messages)
                print(f'Error processing image {site_image.id}: {e}')

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
