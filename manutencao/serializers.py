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
        user = request.user if request and request.user.is_authenticated else None
        equipamento = data.get('equipamento', getattr(self.instance, 'equipamento', None))
        responsavel = data.get('responsavel', getattr(self.instance, 'responsavel', None))

        if user and user.tipo_usuario != 'admin' and equipamento and equipamento.empresa_id != user.empresa_id:
            raise serializers.ValidationError({'equipamento': 'O equipamento deve pertencer à sua empresa.'})

        if responsavel and equipamento and responsavel.empresa_id != equipamento.empresa_id:
            raise serializers.ValidationError({'responsavel': 'O responsável deve pertencer à empresa do equipamento.'})

        if user and user.tipo_usuario == 'tecnico':
            if responsavel and responsavel != user:
                raise serializers.ValidationError({
                    'responsavel': 'Técnicos só podem assumir ordens para si mesmos.'
                })

            if self.instance and self.instance.responsavel and self.instance.responsavel != user:
                raise serializers.ValidationError('Técnicos não podem editar ordens atribuídas a outro técnico.')

        if self.instance and self.instance.status == 'concluida' and data.get('status') not in (None, 'concluida'):
            raise serializers.ValidationError({'status': 'Uma ordem concluída não pode voltar para outro status.'})

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