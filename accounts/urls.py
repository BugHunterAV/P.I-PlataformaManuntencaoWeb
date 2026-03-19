from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmpresaViewSet, UsuarioViewSet

# 1. Instanciamos o roteador
router = DefaultRouter()

# 2. Registamos as nossas "entidades" no roteador
router.register(r'empresas', EmpresaViewSet)
router.register(r'usuarios', UsuarioViewSet)

# 3. Disponibilizamos as rotas geradas
urlpatterns = [
    path('', include(router.urls)),
]