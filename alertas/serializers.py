from rest_framework import serializers
from .models import Alerta
from accounts.validation import validate_equipment_resource


class AlertaSerializer(serializers.ModelSerializer):
    ordem_servico_id = serializers.SerializerMethodField()

    class Meta:
        model = Alerta
        fields = [
            'id', 'equipamento', 'sensor', 'tipo_alerta', 'origem',
            'evento_chave', 'dados_analise', 'analise_ia',
            'data_ultima_analise', 'nivel', 'descricao', 'data_alerta',
            'status', 'ordem_servico_id',
        ]
        read_only_fields = ['data_alerta', 'data_ultima_analise', 'ordem_servico_id']

    def get_ordem_servico_id(self, obj):
        try:
            ordem = obj.ordem_servico_preditiva
        except Exception:
            ordem = None
        return ordem.id if ordem else None

    def validate(self, data):
        request = self.context.get('request')
        equipamento = data.get('equipamento', getattr(self.instance, 'equipamento', None))
        validate_equipment_resource(
            request.user if request else None,
            equipamento,
        )
        sensor = data.get('sensor', getattr(self.instance, 'sensor', None))
        if sensor and equipamento and sensor.equipamento_id != equipamento.id:
            raise serializers.ValidationError({
                'sensor': 'O sensor deve pertencer ao equipamento informado.'
            })
        return data
