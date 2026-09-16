from django.urls import path
from .views import (
    GeminiChatView,
    GeminiOsAnalysisView,
    GeminiUnassignedOrdersView,
    GeminiFinanceView,
    GeminiTrendAnalysisView,
    PromptConfigListView,
    PromptConfigDetailView,
)

urlpatterns = [
    path('chat/', GeminiChatView.as_view(), name='gemini_chat'),
    path('ordens/analise/', GeminiOsAnalysisView.as_view(), name='gemini_ordens_analise'),
    path('ordens/sem-atribuicao/', GeminiUnassignedOrdersView.as_view(), name='gemini_ordens_sem_atribuicao'),
    path('gestao/financeira/', GeminiFinanceView.as_view(), name='gemini_gestao_financeira'),
    path('tendencia/', GeminiTrendAnalysisView.as_view(), name='gemini_tendencia'),
    path('prompts/', PromptConfigListView.as_view(), name='gemini_prompts_list'),
    path('prompts/<int:pk>/', PromptConfigDetailView.as_view(), name='gemini_prompts_detail'),
    path('prompts/<int:pk>/reset/', PromptConfigDetailView.as_view(), name='gemini_prompts_reset'),
]

