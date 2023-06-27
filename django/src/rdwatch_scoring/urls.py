from django.urls import path

from rdwatch_scoring.api import api

urlpatterns = [
    path('/api/scoring', api.urls),
]
