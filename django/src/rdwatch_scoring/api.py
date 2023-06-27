from ninja import NinjaAPI

from .views import router as scores

api = NinjaAPI()

api.add_router('/scores/', scores)
