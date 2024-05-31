from ninja import NinjaAPI

from . import views

api = NinjaAPI(urls_namespace='smartflow')

api.add_router('/', views.router)
