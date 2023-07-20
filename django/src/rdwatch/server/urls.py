from django.apps import apps
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('api/', include('rdwatch.urls')),
    path('admin/', admin.site.urls),
]
# Conditionally add the scoring URLs if the scoring app is installed
if 'rdwatch_scoring' in apps.app_configs.keys():
    urlpatterns.append(path('api/', include('rdwatch_scoring.urls')))
