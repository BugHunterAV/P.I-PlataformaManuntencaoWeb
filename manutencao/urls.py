from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrdemServicoViewSet

router = DefaultRouter()
# A rota vai se chamar 'ordens-servico'
router.register(r'ordens-servico', OrdemServicoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]