from django.urls import path
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.schemas import get_schema_view

from rdwatch import views

urlpatterns = [
    path(
        "openapi.json",
        get_schema_view(
            title="RD-WATCH",
            description="RD-WATCH API",
            version="0.0.0dev0",
            renderer_classes=[CoreJSONRenderer],
        ),
        name="openapi-schema",
    ),
    path("status", views.RetrieveServerStatus.as_view()),  # type: ignore
    path("evaluations", views.site_evaluations),
    path("evaluations/<int:pk>", views.site_observations),
    path("vector-tile/<int:z>/<int:x>/<int:y>.pbf", views.vector_tile),
    path(
        "satellite-image/<int:z>/<int:x>/<int:y>",
        views.satelliteimage_list,
    ),
    path(
        "satellite-image/tile/<int:z>/<int:x>/<int:y>.webp",
        views.satelliteimage_raster_tile,
        name="satellite-tiles",
    ),
]
