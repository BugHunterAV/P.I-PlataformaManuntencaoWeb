from rest_framework import serializers
from .models import Alerta
from accounts.validation import validate_equipment_resource


class AlertaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerta
        fields = '__all__'

    def validate(self, data):
        request = self.context.get('request')
        equipamento = data.get('equipamento', getattr(self.instance, 'equipamento', None))
        validate_equipment_resource(
            request.user if request else None,
            equipamento,
        )
        return data
