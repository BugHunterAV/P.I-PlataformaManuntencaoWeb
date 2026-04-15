from rest_framework import serializers
from .models import Equipamento, EquipamentoLocalizacao

class EquipamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipamento
        fields = '__all__' 

class EquipamentoLocalizacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipamentoLocalizacao
        fields = '__all__'