from django.urls import path
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.schemas import get_schema_view

from rdwatch import views
from rdwatch.api import api

urlpatterns = [
    path('', api.urls),
    path(
        'openapi.json',
        get_schema_view(
            title='RD-WATCH',
            description='RD-WATCH API',
            version='0.0.0dev0',
            renderer_classes=[CoreJSONRenderer],
        ),
        name='openapi-schema',
    ),
    path('status', views.RetrieveServerStatus.as_view()),  # type: ignore
    path('evaluations', views.site_evaluations),
    path('evaluations/images/<int:pk>', views.site_images),
    path('evaluations/<int:pk>', views.site_observations),
    path('satellite-image/timestamps', views.satelliteimage_time_list),
    path('satellite-image/all-timestamps', views.all_satellite_timestamps),
    path(
        'satellite-image/tile/<int:z>/<int:x>/<int:y>.webp',
        views.satelliteimage_raster_tile,
        name='satellite-tiles',
    ),
    path(
        'satellite-image/bbox',
        views.satelliteimage_raster_bbox,
        name='satellite-bbox',
    ),
    path('satellite-image/visual-timestamps', views.satelliteimage_visual_time_list),
    path(
        'satellite-image/visual-bbox',
        views.satelliteimage_visual_bbox,
        name='satellite-visual-bbox',
    ),
    path(
        'satellite-image/visual-tile/<int:z>/<int:x>/<int:y>.webp',
        views.satelliteimage_visual_tile,
        name='satellite-visual-tiles',
    ),
    path(
        'observations/<int:pk>/generate-images',
        views.get_site_observation_images,
    ),
    path(
        'observations/<int:pk>/cancel-generate-images',
        views.cancel_site_observation_images,
    ),
]
