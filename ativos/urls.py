from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EquipamentoViewSet

# 1. Instancia o roteador
router = DefaultRouter()

# 2. Registra o ViewSet no roteador
router.register(r'equipamentos', EquipamentoViewSet)

# 3. Disponibiliza a rota
urlpatterns = [
    path('', include(router.urls)),
]