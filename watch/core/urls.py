from rest_framework.routers import SimpleRouter

from . import rest

router = SimpleRouter(trailing_slash=False)
router.register(r'api/watch/stac_file', rest.viewsets.STACFileViewSet)
router.register(r'api/watch/site', rest.viewsets.SiteViewSet)
router.register(r'api/watch/region', rest.viewsets.RegionViewSet)
router.register(r'api/watch/basic/region', rest.viewsets.RegionViewSetBasic)
router.register(r'api/watch/basic/site', rest.viewsets.SiteViewSetBasic)
router.register(r'api/watch/basic/observation', rest.viewsets.ObservationViewSetBasic)

urlpatterns = [] + router.urls
