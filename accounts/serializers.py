from rest_framework import serializers
from .models import Empresa, Usuario

class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = '__all__'

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'empresa', 'tipo_usuario', 'cargo', 'telefone', 'foto_perfil']

    def validate(self, data):
        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else None
        if user and user.tipo_usuario != 'admin':
            empresa = data.get('empresa', getattr(self.instance, 'empresa', None))
            tipo_usuario = data.get(
                'tipo_usuario',
                getattr(self.instance, 'tipo_usuario', None),
            )
            if not user.empresa_id or empresa != user.empresa:
                raise serializers.ValidationError({
                    'empresa': 'O usuário deve pertencer à sua empresa.'
                })
            if tipo_usuario == 'admin':
                raise serializers.ValidationError({
                    'tipo_usuario': 'Somente administradores podem criar ou promover administradores.'
                })
        return data