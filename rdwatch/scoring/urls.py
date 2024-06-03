from django.urls import path

from rdwatch_scoring.api import api

api_urls = api.urls

urlpatterns = [
    path('', api_urls),
]
