from django.urls import path
from .views import (
    GeminiChatView,
    GeminiOsAnalysisView,
    GeminiUnassignedOrdersView,
    GeminiFinanceView,
)

urlpatterns = [
    path('chat/', GeminiChatView.as_view(), name='gemini_chat'),
    path('ordens/analise/', GeminiOsAnalysisView.as_view(), name='gemini_ordens_analise'),
    path('ordens/sem-atribuicao/', GeminiUnassignedOrdersView.as_view(), name='gemini_ordens_sem_atribuicao'),
    path('gestao/financeira/', GeminiFinanceView.as_view(), name='gemini_gestao_financeira'),
]
