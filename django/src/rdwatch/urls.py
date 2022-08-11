from django.urls import path
from rdwatch import views
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.schemas import get_schema_view

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
    path("status", views.RetrieveServerStatus.as_view()),
    path(
        "site/<int:pk>/tiles/<int:z>/<int:x>/<int:y>",
        views.RetrieveSiteTile.as_view(),
    ),
]
