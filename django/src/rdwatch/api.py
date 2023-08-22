from ninja import NinjaAPI
from ninja.errors import ValidationError

from .views.model_run import router as model_run_router
from .views.performer import router as performer_router
from .views.region import router as region_router
from .views.site_evaluation import router as site_evaluation_router
from .views.site_image import router as images_router
from .views.site_observation import router as site_observation_router

api = NinjaAPI()

api.add_router('/evaluations/', site_evaluation_router)
api.add_router('/observations/', site_observation_router)
api.add_router('/model-runs/', model_run_router)
api.add_router('/performers/', performer_router)
api.add_router('/evaluations/images/', images_router)
api.add_router('/regions/', region_router)


# useful for getting information back about validation errors
@api.exception_handler(ValidationError)
def custom_validation_errors(request, exc):
    print(exc.errors)  # <--------------------- !!!!
    return api.create_response(request, {'detail': exc.errors}, status=422)
