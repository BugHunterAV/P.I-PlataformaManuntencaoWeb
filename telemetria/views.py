from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Sensor, Telemetria
from .serializers import SensorSerializer, TelemetriaSerializer
from accounts.permissions import IsAuthenticatedNoDeleteForTecnico


class SensorViewSet(viewsets.ModelViewSet):
    serializer_class = SensorSerializer
    permission_classes = [IsAuthenticatedNoDeleteForTecnico]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['equipamento', 'tipo', 'ativo']
    search_fields = ['descricao']

    def get_queryset(self):
        user = self.request.user
        qs = Sensor.objects.select_related('equipamento')
        if user.tipo_usuario == 'admin':
            return qs.all()
        if user.empresa:
            return qs.filter(equipamento__empresa=user.empresa)
        return qs.none()


from django_filters import rest_framework as df_filters

class TelemetriaFilter(df_filters.FilterSet):
    valor_min = df_filters.NumberFilter(field_name="valor", lookup_expr='gte')
    valor_max = df_filters.NumberFilter(field_name="valor", lookup_expr='lte')

    class Meta:
        model = Telemetria
        fields = ['sensor', 'sensor__equipamento', 'valor_min', 'valor_max']

class TelemetriaViewSet(viewsets.ModelViewSet):
    serializer_class = TelemetriaSerializer
    permission_classes = [IsAuthenticatedNoDeleteForTecnico]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TelemetriaFilter

    def get_queryset(self):
        user = self.request.user
        qs = Telemetria.objects.select_related('sensor', 'sensor__equipamento').order_by('-timestamp')
        if user.tipo_usuario == 'admin':
            return qs.all()
        if user.empresa:
            return qs.filter(sensor__equipamento__empresa=user.empresa)
        return qs.none()