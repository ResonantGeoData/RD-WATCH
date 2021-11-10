from django.urls import path
from rest_framework.routers import SimpleRouter

from . import rest

router = SimpleRouter(trailing_slash=False)
router.register(r'api/watch/stac_item', rest.stac_item.STACItemViewSet)


urlpatterns = [
    path(
        'api/watch/region/<int:pk>',
        rest.get.GetRegion.as_view(),
        name='region',
    ),
    path(
        'api/watch/gc_record/<int:pk>',
        rest.get.GetGoogleCloudRecord.as_view(),
        name='gc-record',
    ),
    path(
        'api/watch/gc_record/search',
        rest.get.SearchGoogleCloudRecord.as_view(),
        name='gc-record-search',
    ),
    path(
        'api/watch/region',
        rest.post.CreateRegion.as_view(),
        name='region-create',
    ),
    path(
        'api/watch/gc_record/search_post',
        rest.post.SearchCreateGoogleCloudRecord.as_view(),
        name='gc-record-search-create',
    ),
] + router.urls
