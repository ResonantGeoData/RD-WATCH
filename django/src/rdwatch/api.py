from ninja import NinjaAPI

from .views.model_run import router as model_run_router
from .views.performer import router as performer_router
from .views.region import router as region_router
from .views.vector_tile import router as vector_tile_router

api = NinjaAPI()

api.add_router('/performers/', performer_router)
api.add_router('/regions/', region_router)
api.add_router('/model-runs/', model_run_router)
api.add_router('/vector-tile/', vector_tile_router)
