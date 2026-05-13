from django.urls import path
from .views import KpiDashboardView

urlpatterns = [
    path('kpis/', KpiDashboardView.as_view(), name='kpi-dashboard'),
]
