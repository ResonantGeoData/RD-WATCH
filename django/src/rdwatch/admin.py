from django.contrib import admin

from .models import (
    PredictionConfiguration,
    Saliency,
    SaliencyTile,
    SatelliteImage,
    Site,
    TrackingConfiguration,
)

# general admin settings
admin.site.site_header = "WATCH Admin"
admin.site.site_title = "WATCH Admin"


@admin.register(PredictionConfiguration)
class PredictionConfigurationAdmin(admin.ModelAdmin):
    list_display = ("id", "timestamp")


@admin.register(Saliency)
class SaliencyAdmin(admin.ModelAdmin):
    list_display = ("id", "configuration", "source")


@admin.register(SaliencyTile)
class SaliencyTileAdmin(admin.ModelAdmin):
    list_display = ("id", "raster", "saliency")


@admin.register(SatelliteImage)
class SatelliteImageAdmin(admin.ModelAdmin):
    list_display = ("id", "sensor", "timestamp")


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "configuration",
        "saliency",
        "label",
        "score",
    )


@admin.register(TrackingConfiguration)
class TrackingConfigurationAdmin(admin.ModelAdmin):
    list_display = ("id", "timestamp", "threshold")
