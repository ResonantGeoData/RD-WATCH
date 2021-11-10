from django.urls import path
from rest_framework.routers import SimpleRouter

from . import rest

router = SimpleRouter(trailing_slash=False)
router.register(r'api/watch/stac_item', rest.stac_item.STACItemViewSet)
router.register(r'api/watch/region', rest.viewsets.RegionViewset)
router.register(r'api/watch/gc_record', rest.viewsets.GoogleCloudRecordViewset)


urlpatterns = [
    # path(
    #     'api/watch/gc_record/search_post',
    #     rest.post.SearchCreateGoogleCloudRecord.as_view(),
    #     name='gc-record-search-create',
    # ),
] + router.urls
