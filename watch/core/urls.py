from django.urls import path

from . import rest

urlpatterns = [
    path(
        'api/watch/region/<int:pk>',
        rest.get.GetRegion.as_view(),
        name='region',
    ),
    path(
        'api/watch/region',
        rest.post.CreateRegion.as_view(),
        name='region-create',
    ),
]
