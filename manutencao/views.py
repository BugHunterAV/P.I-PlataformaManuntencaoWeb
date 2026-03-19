from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import OrdemServico
from .serializers import OrdemServicoSerializer

class OrdemServicoViewSet(viewsets.ModelViewSet):
    queryset = OrdemServico.objects.all()
    serializer_class = OrdemServicoSerializer
    
    # Adicionando os filtros de nível Sênior
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    
    # Filtros exatos: Perfeito para botões de filtro na tela
    filterset_fields = ['status', 'prioridade', 'equipamento', 'responsavel']
    
    # Busca por texto: Perfeito para a barra de pesquisa
    search_fields = ['titulo', 'descricao']