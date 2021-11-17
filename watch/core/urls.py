from django.urls import path
from rest_framework.routers import SimpleRouter

from . import rest

router = SimpleRouter(trailing_slash=False)
router.register(r'api/watch/stac_file', rest.stac_file.STACFileViewSet)


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
] + router.urls
