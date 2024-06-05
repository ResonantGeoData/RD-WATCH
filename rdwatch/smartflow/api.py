from ninja import NinjaAPI
from ninja.security import django_auth

from . import views

api = NinjaAPI(urls_namespace='smartflow', auth=django_auth, csrf=True)

api.add_router('/', views.router)
