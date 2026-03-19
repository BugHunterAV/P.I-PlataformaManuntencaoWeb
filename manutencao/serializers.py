from rest_framework import serializers
from .models import OrdemServico

class OrdemServicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdemServico
        fields = '__all__'
        
        # A magia da segurança Sênior acontece aqui:
        read_only_fields = ['data_abertura', 'data_conclusao']