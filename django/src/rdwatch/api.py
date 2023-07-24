from ninja import NinjaAPI

from .views.model_run import router as model_run_router
from .views.performer import router as performer_router
from .views.region import router as region_router
from .views.site_image import router as images_router

api = NinjaAPI()

api.add_router('/performers/', performer_router)
api.add_router('/evaluations/images/', images_router)
api.add_router('/regions/', region_router)
api.add_router('/model-runs/', model_run_router)
