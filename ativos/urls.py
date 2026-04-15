from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EquipamentoViewSet, EquipamentoLocalizacaoViewSet


router = DefaultRouter()

router.register(r'equipamentos', EquipamentoViewSet, basename='equipamentos')
router.register(r'localizacao', EquipamentoLocalizacaoViewSet, basename='localizacao')

urlpatterns = [
    path('', include(router.urls)),
]