import logging

from django.core.management.base import BaseCommand

from telemetria.models import Sensor
from telemetria.predictive_service import sync_sensor_trend


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Analisa sensores ativos e sincroniza alertas/OS de tendência.'

    def handle(self, *args, **options):
        processados = 0
        insuficientes = 0
        falhas = 0
        for sensor_id in Sensor.objects.filter(ativo=True).values_list('id', flat=True).iterator():
            try:
                trend = sync_sensor_trend(sensor_id)
                processados += 1
                if trend and trend.get('insufficient_data'):
                    insuficientes += 1
            except Exception:
                falhas += 1
                logger.exception('Falha ao analisar tendência do sensor %s', sensor_id)
        self.stdout.write(
            self.style.SUCCESS(
                f'Tendências processadas: {processados}; '
                f'sem dados suficientes: {insuficientes}; falhas: {falhas}.'
            )
        )
