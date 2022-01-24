from rest_framework.routers import SimpleRouter

from . import rest

router = SimpleRouter(trailing_slash=False)
router.register(r'api/watch/stac_file', rest.viewsets.STACFileViewSet)
router.register(r'api/watch/region', rest.viewsets.RegionViewSet)


urlpatterns = [] + router.urls
