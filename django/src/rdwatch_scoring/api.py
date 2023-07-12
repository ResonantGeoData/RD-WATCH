from ninja import NinjaAPI

from .views import router as scores

api = NinjaAPI(urls_namespace='scoring')

api.add_router('/scores/', scores)
