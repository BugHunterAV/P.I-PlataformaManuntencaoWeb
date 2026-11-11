import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from telemetria.models import Sensor, TrendAnalysisRun
from telemetria.predictive_service import sync_sensor_trend


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Analisa sensores ativos e sincroniza alertas/OS de tendência.'

    def handle(self, *args, **options):
        run = TrendAnalysisRun.objects.create(status='running')
        try:
            for sensor_id in Sensor.objects.filter(ativo=True).values_list('id', flat=True).iterator():
                try:
                    result = sync_sensor_trend(sensor_id)
                    run.processed_count += 1
                    trend = result.get('trend') or {}
                    run.insufficient_data_count += int(bool(trend.get('insufficient_data')))
                    run.created_alert_count += int(result.get('created_alert', False))
                    run.resolved_alert_count += int(result.get('resolved_alert', False))
                    run.created_work_order_count += int(result.get('created_work_order', False))
                except Exception as exc:
                    run.failure_count += 1
                    run.details += f'Sensor {sensor_id}: {exc}\n'
                    logger.exception('Falha ao analisar tendência do sensor %s', sensor_id)
            run.status = 'partial_failure' if run.failure_count else 'success'
        except Exception as exc:
            run.status = 'failed'
            run.failure_count += 1
            run.details += f'Falha da rotina: {exc}\n'
            raise
        finally:
            run.finished_at = timezone.now()
            run.save()

        message = (
            f'Tendências processadas: {run.processed_count}; sem dados suficientes: '
            f'{run.insufficient_data_count}; alertas criados: {run.created_alert_count}; '
            f'alertas resolvidos: {run.resolved_alert_count}; OS criadas: '
            f'{run.created_work_order_count}; falhas: {run.failure_count}.'
        )
        if run.failure_count:
            self.stdout.write(self.style.ERROR(message))
            raise RuntimeError('A rotina terminou com falhas; consulte TrendAnalysisRun.')
        self.stdout.write(self.style.SUCCESS(message))
