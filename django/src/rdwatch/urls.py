from django.urls import include, path
from rdwatch import views
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"site", views.SiteViewSet)

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
    path("", include(router.urls)),
]
