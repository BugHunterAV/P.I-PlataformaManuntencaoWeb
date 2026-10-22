from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from .models import Equipamento, EquipamentoLocalizacao, PlanoManutencao
from accounts.validation import validate_equipment_resource

class EquipamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipamento
        fields = '__all__'

    def validate(self, data):
        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else None
        empresa = data.get('empresa', getattr(self.instance, 'empresa', None))
        if user and user.tipo_usuario != 'admin':
            if empresa is None or empresa != user.empresa:
                raise serializers.ValidationError({
                    'empresa': 'O equipamento deve pertencer à sua empresa.'
                })
        return data

class EquipamentoLocalizacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipamentoLocalizacao
        fields = '__all__'

    def validate(self, data):
        request = self.context.get('request')
        equipamento = data.get('equipamento', getattr(self.instance, 'equipamento', None))
        validate_equipment_resource(
            request.user if request else None,
            equipamento,
        )
        return data


class PlanoManutencaoSerializer(serializers.ModelSerializer):
    proximo_disparo_horas = serializers.SerializerMethodField()

    class Meta:
        model = PlanoManutencao
        fields = '__all__'
        read_only_fields = ['horimetro_ultima_os']

    @extend_schema_field(OpenApiTypes.FLOAT)
    def get_proximo_disparo_horas(self, obj):
        """Calcula e exibe quando a próxima O.S. será gerada."""
        return obj.horimetro_ultima_os + obj.intervalo_horas


    def validate(self, data):
        request = self.context.get('request')
        equipamento = data.get('equipamento', getattr(self.instance, 'equipamento', None))
        validate_equipment_resource(
            request.user if request else None,
            equipamento,
        )
        return data