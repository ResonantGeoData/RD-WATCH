from django.urls import path

from rdwatch import views
from rdwatch.api import api

urlpatterns = [
    path('', api.urls),
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
]
