from rest_framework import viewsets, filters
from .models import Equipamento, EquipamentoLocalizacao
from .serializers import EquipamentoSerializer, EquipamentoLocalizacaoSerializer
from django_filters.rest_framework import DjangoFilterBackend
from accounts.permissions import IsGestorOrReadOnly

class EquipamentoViewSet(viewsets.ModelViewSet):
    queryset = Equipamento.objects.all()
    serializer_class = EquipamentoSerializer
    
    permission_classes = [IsGestorOrReadOnly]
    
    # Já vamos deixar os filtros Sênior prontos!
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['empresa', 'status', 'tipo'] # Filtros exatos
    search_fields = ['nome', 'fabricante', 'modelo', 'numero_serie'] # Busca por texto

class EquipamentoLocalizacaoViewSet(viewsets.ModelViewSet):
    queryset = EquipamentoLocalizacao.objects.all()
    serializer_class = EquipamentoLocalizacaoSerializer
    permission_classes = [IsGestorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['equipamento', 'setor']