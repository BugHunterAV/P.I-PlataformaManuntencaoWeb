from rest_framework import serializers
from .models import Empresa, Usuario

# 1. Serializer para a Empresa
class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = '__all__' # Pega em todos os campos do Model e converte para JSON

# 2. Serializer para o Usuário
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        # Aqui é uma boa prática de segurança não colocar '__all__', 
        # para não expor a password encriptada ou permissões do Django na API.
        fields = ['id', 'username', 'email', 'nome', 'empresa', 'tipo_usuario', 'cargo', 'especialidade', 'telefone']