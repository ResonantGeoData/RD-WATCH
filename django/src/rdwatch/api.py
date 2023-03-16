from ninja import NinjaAPI

from .views.site_model import router as site_model_router

api = NinjaAPI()

api.add_router('/model-runs/', site_model_router)
