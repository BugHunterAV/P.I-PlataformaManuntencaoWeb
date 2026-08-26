from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Sensor, Telemetria
from .serializers import SensorSerializer, TelemetriaSerializer
from accounts.permissions import IsAuthenticatedNoDeleteForTecnico


class SensorViewSet(viewsets.ModelViewSet):
    serializer_class = SensorSerializer
    permission_classes = [IsAuthenticatedNoDeleteForTecnico]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['equipamento', 'equipamento__empresa', 'tipo', 'ativo']
    search_fields = ['descricao']

    def get_queryset(self):
        user = self.request.user
        qs = Sensor.objects.select_related('equipamento')
        if user.tipo_usuario != 'admin':
            if user.empresa:
                qs = qs.filter(equipamento__empresa=user.empresa)
            else:
                return qs.none()
        equipamento_ids = self.request.query_params.get('equipamento__in')
        if equipamento_ids:
            try:
                ids = [int(value) for value in equipamento_ids.split(',') if value.strip()]
            except ValueError:
                ids = []
            qs = qs.filter(equipamento_id__in=ids)
        return qs


from django_filters import rest_framework as df_filters

class TelemetriaFilter(df_filters.FilterSet):
    valor_min = df_filters.NumberFilter(field_name="valor", lookup_expr='gte')
    valor_max = df_filters.NumberFilter(field_name="valor", lookup_expr='lte')
    timestamp_de = df_filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    timestamp_ate = df_filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')

    class Meta:
        model = Telemetria
        fields = ['sensor', 'sensor__equipamento', 'valor_min', 'valor_max', 'timestamp_de', 'timestamp_ate']

class TelemetriaViewSet(viewsets.ModelViewSet):
    serializer_class = TelemetriaSerializer
    permission_classes = [IsAuthenticatedNoDeleteForTecnico]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TelemetriaFilter

    def get_queryset(self):
        user = self.request.user
        qs = Telemetria.objects.select_related('sensor', 'sensor__equipamento').order_by('-timestamp')
        if user.tipo_usuario != 'admin':
            if user.empresa:
                qs = qs.filter(sensor__equipamento__empresa=user.empresa)
            else:
                return qs.none()

        equipamento_ids = self.request.query_params.get('sensor__equipamento__in')
        if equipamento_ids:
            try:
                ids = [int(value) for value in equipamento_ids.split(',') if value.strip()]
            except ValueError:
                ids = []
            qs = qs.filter(sensor__equipamento_id__in=ids)
        return qs