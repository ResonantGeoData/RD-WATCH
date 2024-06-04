from ninja import NinjaAPI
from ninja.errors import ValidationError

from . import views

api = NinjaAPI(urls_namespace='scoring')

api.add_router('/evaluations/', views.site_evaluation.router)
api.add_router('/evaluations/images/', views.site_image.router)
api.add_router('/model-runs/', views.model_run.router)
api.add_router('/observations/', views.site_observation.router)
api.add_router('/performers/', views.performer.router)
api.add_router('/regions/', views.region.router)
api.add_router('/sites/', views.site.router)
api.add_router('/eval-numbers/', views.eval.router)
api.add_router('/satellite-fetching/', views.satellite_fetching.router)


# useful for getting information back about validation errors
@api.exception_handler(ValidationError)
def custom_validation_errors(request, exc):
    print(exc.errors)  # <--------------------- !!!!
    return api.create_response(request, {'detail': exc.errors}, status=422)
