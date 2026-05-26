from rest_framework import serializers
from .models import Sensor, Telemetria

class SensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sensor
        fields = '__all__'

    def validate(self, data):
        low = data.get('limite_alerta_baixo_pct', getattr(self.instance, 'limite_alerta_baixo_pct', None))
        medium = data.get('limite_alerta_medio_pct', getattr(self.instance, 'limite_alerta_medio_pct', None))
        critical = data.get('limite_alerta_critico_pct', getattr(self.instance, 'limite_alerta_critico_pct', None))

        low = 70.0 if low is None else low
        medium = 85.0 if medium is None else medium
        critical = 100.0 if critical is None else critical

        for name, value in [
            ('limite_alerta_baixo_pct', low),
            ('limite_alerta_medio_pct', medium),
            ('limite_alerta_critico_pct', critical),
        ]:
            if value is not None and not (0 <= value <= 100):
                raise serializers.ValidationError({name: 'Deve ser um percentual entre 0 e 100.'})

        if not (0 <= low < medium < critical <= 100):
            raise serializers.ValidationError(
                'Os valores de alerta devem obedecer: baixo < médio < crítico e estar entre 0 e 100.'
            )

        return data

class TelemetriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Telemetria
        fields = '__all__'
