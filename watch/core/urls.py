from django.urls import path

from . import rest

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
        'api/watch/gc_record/search-post',
        rest.post.SearchCreateGoogleCloudRecord.as_view(),
        name='gc-record-search-create',
    ),
]
