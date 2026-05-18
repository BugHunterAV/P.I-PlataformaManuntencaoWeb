from django.urls import path
from .views import (
    ExportarOrdensServicoView,
    ExportarEquipamentosView,
    ExportarAlertasView,
    ExportarTelemetriaView,
    ExportarHistoricoView,
    ExportarDashboardView,
)

urlpatterns = [
    # Ordens de Serviço
    path('ordens-servico/<str:formato>/',
         ExportarOrdensServicoView.as_view(),
         name='exportar-ordens-servico'),

    # Equipamentos
    path('equipamentos/<str:formato>/',
         ExportarEquipamentosView.as_view(),
         name='exportar-equipamentos'),

    # Alertas
    path('alertas/<str:formato>/',
         ExportarAlertasView.as_view(),
         name='exportar-alertas'),

    # Telemetria
    path('telemetria/<str:formato>/',
         ExportarTelemetriaView.as_view(),
         name='exportar-telemetria'),

    # Histórico de Manutenção
    path('historico/<str:formato>/',
         ExportarHistoricoView.as_view(),
         name='exportar-historico'),

    # Dashboard KPIs
    path('dashboard/<str:formato>/',
         ExportarDashboardView.as_view(),
         name='exportar-dashboard'),
]
