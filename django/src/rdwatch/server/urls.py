from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('api/', include('rdwatch.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
]

# Conditionally add the scoring URLs if the scoring app is installed
if 'rdwatch_scoring' in apps.app_configs.keys():
    urlpatterns.append(path('api/scoring/', include('rdwatch_scoring.urls')))
if 'rdwatch_smartflow' in apps.app_configs.keys():
    urlpatterns.append(path('api/smartflow/', include('rdwatch_smartflow.urls')))

if settings.DEBUG:
    try:
        import debug_toolbar

        urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
    except ModuleNotFoundError:
        # If DEBUG mode is enabled in production, django-debug-toolbar is
        # likely not installed. If this happens, just ignore the error.
        pass
