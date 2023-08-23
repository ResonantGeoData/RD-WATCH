from ninja import NinjaAPI

from .views.model_run import router as modelruns
from .views.performer import router as performers
from .views.region import router as regions
from .views.scores import router as scores
from .views.scoring import router as scoring

api = NinjaAPI(urls_namespace='scoring')

api.add_router('/scoring/scores/', scores)
api.add_router('/scoring/performers/', performers)
api.add_router('/scoring/regions/', regions)
api.add_router('/scoring/model-runs/', modelruns)
api.add_router('/scoring/scoring/', scoring)
