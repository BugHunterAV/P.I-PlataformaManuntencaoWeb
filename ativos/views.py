from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Equipamento, EquipamentoLocalizacao, PlanoManutencao, TipoEquipamento, HistoricoCriticidadeEquipamento
from .serializers import (EquipamentoSerializer, EquipamentoLocalizacaoSerializer, PlanoManutencaoSerializer,
                          TipoEquipamentoSerializer, HistoricoCriticidadeEquipamentoSerializer)
from accounts.permissions import IsGestorOrReadOnly


class EquipamentoViewSet(viewsets.ModelViewSet):
    serializer_class = EquipamentoSerializer
    permission_classes = [IsGestorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['empresa', 'status', 'tipo', 'tipo_equipamento', 'criticidade', 'localizacao__setor']
    search_fields = ['nome', 'fabricante', 'modelo', 'numero_serie']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Equipamento.objects.none()
        user = self.request.user
        if user.tipo_usuario == 'admin':
            return Equipamento.objects.all()
        if user.empresa:
            return Equipamento.objects.filter(empresa=user.empresa)
        return Equipamento.objects.none()


class TipoEquipamentoViewSet(viewsets.ModelViewSet):
    serializer_class = TipoEquipamentoSerializer
    permission_classes = [IsGestorOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.tipo_usuario == 'admin':
            return TipoEquipamento.objects.all()
        return TipoEquipamento.objects.filter(empresa=user.empresa) if user.empresa else TipoEquipamento.objects.none()


class HistoricoCriticidadeEquipamentoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = HistoricoCriticidadeEquipamentoSerializer
    filterset_fields = ['equipamento']

    def get_queryset(self):
        user = self.request.user
        qs = HistoricoCriticidadeEquipamento.objects.select_related('equipamento', 'alterado_por')
        if user.tipo_usuario == 'admin':
            return qs
        return qs.filter(equipamento__empresa=user.empresa) if user.empresa else qs.none()


class EquipamentoLocalizacaoViewSet(viewsets.ModelViewSet):
    serializer_class = EquipamentoLocalizacaoSerializer
    permission_classes = [IsGestorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['equipamento', 'setor']
    search_fields = ['setor']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return EquipamentoLocalizacao.objects.none()
        user = self.request.user
        qs = EquipamentoLocalizacao.objects.select_related('equipamento')
        if user.tipo_usuario == 'admin':
            return qs.all()
        if user.empresa:
            return qs.filter(equipamento__empresa=user.empresa)
        return qs.none()


class PlanoManutencaoViewSet(viewsets.ModelViewSet):
    """
    Gerencia os planos de manutenção preditiva por horímetro.
    Apenas Gestores e Admins podem criar/editar planos.
    Técnicos podem visualizar.
    """
    serializer_class = PlanoManutencaoSerializer
    permission_classes = [IsGestorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['equipamento', 'ativo', 'prioridade']
    search_fields = ['nome_servico', 'descricao']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return PlanoManutencao.objects.none()
        user = self.request.user
        qs = PlanoManutencao.objects.select_related('equipamento')
        if user.tipo_usuario == 'admin':
            return qs.all()
        if user.empresa:
            return qs.filter(equipamento__empresa=user.empresa)
        return qs.none()
