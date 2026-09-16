from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SensorViewSet, TelemetriaViewSet, TrendConfigViewSet, TrendDashboardView

router = DefaultRouter()
router.register(r'sensores', SensorViewSet, basename='sensores')
router.register(r'leituras', TelemetriaViewSet, basename='leituras')
router.register(r'trend-config', TrendConfigViewSet, basename='trend-config')

urlpatterns = [
    path('', include(router.urls)),
    path('tendencias/', TrendDashboardView.as_view(), name='trend-dashboard'),
]
