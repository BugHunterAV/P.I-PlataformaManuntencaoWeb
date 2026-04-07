from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import EmpresaViewSet, UsuarioViewSet, MeView

# Cria o router para registrar as ViewSets automaticamente
router = DefaultRouter()

# O uso do 'basename' é obrigatório aqui porque sobrescrevemos o get_queryset() nas Views
router.register(r'empresas', EmpresaViewSet, basename='empresas')
router.register(r'usuarios', UsuarioViewSet, basename='usuarios')

urlpatterns = [
    # Rotas geradas pelo router (ex: /api/empresas/, /api/usuarios/)
    path('', include(router.urls)),

    # Rota customizada para obter os dados do usuário logado
    path('auth/me/', MeView.as_view(), name='me'),

    # Rotas do Simple JWT para Login (gerar token) e Refresh (atualizar token)
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]