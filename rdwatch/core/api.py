from ninja import NinjaAPI
from ninja.errors import ValidationError
from ninja.security import django_auth

from rdwatch import __version__ as rdwatch_version

from .views import site
from .views.animation import router as animation_router
from .views.iqr import router as iqr_router
from .views.model_run import router as model_run_router
from .views.performer import router as performer_router
from .views.region import router as region_router
from .views.satellite_fetching import router as satellite_fetching_router
from .views.server_status import router as server_status_router
from .views.site_evaluation import router as site_evaluation_router
from .views.site_image import router as images_router
from .views.site_observation import router as site_observation_router

api = NinjaAPI(title='RD-WATCH', version=rdwatch_version, auth=django_auth, csrf=True)

api.add_router('/evaluations/', site_evaluation_router)
api.add_router('/observations/', site_observation_router)
api.add_router('/model-runs/', model_run_router)
api.add_router('/performers/', performer_router)
api.add_router('/evaluations/images/', images_router)
api.add_router('/regions/', region_router)
api.add_router('/status/', server_status_router)
api.add_router('/sites/', site.router)
api.add_router('/satellite-fetching/', satellite_fetching_router)
api.add_router('/animation/', animation_router)
api.add_router('/iqr/', iqr_router)


# useful for getting information back about validation errors
@api.exception_handler(ValidationError)
def custom_validation_errors(request, exc):
    print(exc.errors)  # <--------------------- !!!!
    return api.create_response(request, {'detail': exc.errors}, status=422)
