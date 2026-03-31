from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Telemetria
from alertas.models import Alerta
from .config_alertas import obter_limite

@receiver(post_save, sender=Telemetria)
def checar_limites_telemetria(sender, instance, created, **kwargs):
    """
    SISTEMA DE INTELIGÊNCIA PREDITIVA (BPMN)
    Analisa os dados de telemetria e gera alertas se anomalias forem detectadas.
    """
    if created:
        sensor = instance.sensor
        valor = instance.valor
        equipamento = sensor.equipamento

        # Busca o limite configurado em config_alertas.py
        limite = obter_limite(equipamento.tipo, sensor.tipo_sensor)

        if limite is not None and valor > limite:
            # Gerar Alerta de Falha (Nível Crítico por padrão se ultrapassar limite)
            Alerta.objects.create(
                equipamento=equipamento,
                tipo_alerta=f"Alerta de {sensor.get_tipo_sensor_display()}",
                nivel='critico',
                descricao=(
                    f"Anomalia detectada no {equipamento.nome} ({equipamento.tipo}). "
                    f"O sensor de {sensor.get_tipo_sensor_display()} registrou {valor}{sensor.unidade_medida}, "
                    f"excedendo o limite configurado de {limite}{sensor.unidade_medida}."
                )
            )
