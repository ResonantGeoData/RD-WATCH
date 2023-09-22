from ninja import NinjaAPI
from ninja.errors import ValidationError

from .views.model_run import router as modelruns
from .views.performer import router as performers
from .views.region import router as regions
from .views.scores import router as scores
from .views.proposal import router as proposal_router

api = NinjaAPI(urls_namespace='scoring')

api.add_router('/scoring/scores/', scores)
api.add_router('/scoring/performers/', performers)
api.add_router('/scoring/regions/', regions)
api.add_router('/scoring/model-runs/', modelruns)
api.add_router('/scoring/evaluations/', proposal_router)

# for getting info about validation errors
@api.exception_handler(ValidationError)
def custom_validation_errors(request, exc):
    print(exc.errors)  # <--------------------- !!!!
    return api.create_response(request, {'detail': exc.errors}, status=422)
