from rest_framework import serializers
from .models import OrdemServico, HistoricoManutencao

class OrdemServicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdemServico
        fields = '__all__'
        
        # A magia da segurança Sênior acontece aqui:
        read_only_fields = ['data_abertura', 'data_conclusao']

    def validate(self, data):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.tipo_usuario == 'tecnico':
            responsavel = data.get('responsavel')
            if responsavel and responsavel != request.user:
                raise serializers.ValidationError({
                    'responsavel': 'Técnicos só podem assumir ordens para si mesmos.'
                })
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.tipo_usuario == 'tecnico':
            responsavel = validated_data.get('responsavel')
            if responsavel is None and validated_data.get('status') in ['andamento', 'concluida']:
                validated_data['responsavel'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.tipo_usuario == 'tecnico':
            responsavel = validated_data.get('responsavel', instance.responsavel)
            if instance.responsavel is None and responsavel is None:
                validated_data['responsavel'] = request.user
            if validated_data.get('status') == 'concluida' and validated_data.get('responsavel') is None:
                validated_data['responsavel'] = request.user
        return super().update(instance, validated_data)

class HistoricoManutencaoSerializer(serializers.ModelSerializer):
    custo_total = serializers.ReadOnlyField()

    class Meta:
        model = HistoricoManutencao
        fields = '__all__'