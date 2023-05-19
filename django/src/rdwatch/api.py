from ninja import NinjaAPI

from .views.performer import router as performer_router
from .views.site_model import router as site_model_router

api = NinjaAPI()

api.add_router('/performers/', performer_router)
api.add_router('/model-runs/', site_model_router)
