from ninja import NinjaAPI

from .views.performer import router as performer_router
from .views.region import router as region_router
from .views.site_model import router as site_model_router
from .views.vector_tile import router as vector_tile_router

api = NinjaAPI()

api.add_router('/performers/', performer_router)
api.add_router('/regions/', region_router)
api.add_router('/model-runs/', site_model_router)
api.add_router('/vector-tile/', vector_tile_router)
