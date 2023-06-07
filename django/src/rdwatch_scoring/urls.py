from django.urls import path
from rest_framework import routers

from rdwatch_scoring.api import api

router = routers.SimpleRouter(trailing_slash=False)

urlpatterns = [
    path('/api/scoring', api.urls),
]

urlpatterns += router.urls
