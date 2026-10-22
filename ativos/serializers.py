from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from .models import Equipamento, EquipamentoLocalizacao, PlanoManutencao, TipoEquipamento, HistoricoCriticidadeEquipamento
from .services import aplicar_criticidade
from accounts.validation import validate_equipment_resource

class EquipamentoSerializer(serializers.ModelSerializer):
    criticidade_sugerida = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Equipamento
        fields = '__all__'
        read_only_fields = ['criticidade_origem']

    def get_criticidade_sugerida(self, obj):
        return obj.tipo_equipamento.criticidade_padrao if obj.tipo_equipamento else None

    def validate(self, data):
        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else None
        empresa = data.get('empresa', getattr(self.instance, 'empresa', None))
        if user and user.tipo_usuario != 'admin':
            if empresa is None or empresa != user.empresa:
                raise serializers.ValidationError({
                    'empresa': 'O equipamento deve pertencer à sua empresa.'
                })
        tipo = data.get('tipo_equipamento', getattr(self.instance, 'tipo_equipamento', None))
        if tipo and empresa and tipo.empresa_id != empresa.id:
            raise serializers.ValidationError({'tipo_equipamento': 'O tipo deve pertencer à empresa do equipamento.'})
        if 'criticidade' in data and data.get('criticidade') and not data.get('justificativa_criticidade', getattr(self.instance, 'justificativa_criticidade', '')):
            raise serializers.ValidationError({'justificativa_criticidade': 'Informe a justificativa da classificação.'})
        return data

    def create(self, validated_data):
        criticidade = validated_data.pop('criticidade', None)
        justificativa = validated_data.get('justificativa_criticidade', '')
        equipamento = super().create(validated_data)
        if criticidade:
            return aplicar_criticidade(equipamento, criticidade, justificativa, self.context.get('request').user, 'individual')
        if equipamento.tipo_equipamento and equipamento.tipo_equipamento.criticidade_padrao:
            return aplicar_criticidade(equipamento, equipamento.tipo_equipamento.criticidade_padrao,
                                       equipamento.tipo_equipamento.descricao_criterios,
                                       self.context.get('request').user, 'tipo')
        return equipamento

    def update(self, instance, validated_data):
        nova = validated_data.pop('criticidade', instance.criticidade)
        alterou = nova != instance.criticidade
        equipamento = super().update(instance, validated_data)
        if alterou:
            return aplicar_criticidade(equipamento, nova, equipamento.justificativa_criticidade,
                                       self.context.get('request').user, 'individual')
        return equipamento


class TipoEquipamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEquipamento
        fields = '__all__'

    def validate_empresa(self, empresa):
        request = self.context.get('request')
        if request and request.user.tipo_usuario != 'admin' and empresa != request.user.empresa:
            raise serializers.ValidationError('O tipo deve pertencer à sua empresa.')
        return empresa


class HistoricoCriticidadeEquipamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricoCriticidadeEquipamento
        fields = '__all__'
        read_only_fields = [
            'equipamento', 'criticidade_anterior', 'criticidade_nova',
            'justificativa', 'alterado_por', 'criado_em',
        ]

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
