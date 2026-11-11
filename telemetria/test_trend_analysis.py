from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from ativos.models import Empresa, Equipamento
from .models import Sensor, Telemetria, TrendConfig
from .trend_analysis import analyze_sensor_trend
from .predictive_service import sync_sensor_trend
from alertas.models import Alerta
from manutencao.models import OrdemServico


class TrendAnalysisRulesTests(TestCase):
    def setUp(self):
        empresa = Empresa.objects.create(nome='Trend Co', cnpj='TREND-TEST', email='trend@test.local')
        equipamento = Equipamento.objects.create(
            empresa=empresa, nome='Motor Trend', numero_serie='TREND-001'
        )
        self.sensor = Sensor.objects.create(
            equipamento=equipamento, nome='Temperatura', tipo='temperatura',
            unidade_medida='C', limite_alerta=100,
        )

    def _readings(self, values, start=None, step_minutes=30):
        start = start or (timezone.now() - timedelta(hours=2))
        readings = Telemetria.objects.bulk_create([
            Telemetria(sensor=self.sensor, valor=value,
                       timestamp=start + timedelta(minutes=index * step_minutes))
            for index, value in enumerate(values)
        ])
        # auto_now_add sobrescreve timestamps em bulk_create; ajustamos a
        # amostra sem disparar os sinais, pois estes não fazem parte do teste
        # matemático da regressão.
        for index, reading in enumerate(readings):
            Telemetria.objects.filter(pk=reading.pk).update(
                timestamp=start + timedelta(minutes=index * step_minutes)
            )

    def test_uses_the_most_recent_readings(self):
        TrendConfig.objects.create(sensor=self.sensor, num_leituras=3, periodo_horas=24)
        self._readings([10, 11, 12, 20, 30])
        result = analyze_sensor_trend(self.sensor.id)
        self.assertEqual(result['readings_count'], 3)
        self.assertEqual([item['valor'] for item in result['readings_summary']], [12, 20, 30])
        self.assertEqual(result['direction'], 'increasing')

    def test_insufficient_data_has_no_projection(self):
        self._readings([40, 41])
        result = analyze_sensor_trend(self.sensor.id)
        self.assertTrue(result['insufficient_data'])
        self.assertIsNone(result['projected_breach_hours'])
        self.assertFalse(result['intervention_recommended'])

    def test_decreasing_series_is_not_upper_limit_breach(self):
        self._readings([90, 80, 70, 60])
        result = analyze_sensor_trend(self.sensor.id)
        self.assertEqual(result['direction'], 'decreasing')
        self.assertIsNone(result['projected_breach_hours'])

    def test_irregular_intervals_are_measured_in_hours(self):
        start = timezone.now() - timedelta(hours=4)
        self._readings([50, 60, 70], start=start, step_minutes=90)
        result = analyze_sensor_trend(self.sensor.id)
        self.assertGreater(result['slope_per_hour'], 0)
        self.assertEqual(result['data_quality'], 'valid')

    def test_relevant_trend_creates_one_predictive_alert_and_work_order(self):
        TrendConfig.objects.create(sensor=self.sensor, num_leituras=3, periodo_horas=24)
        self._readings([80, 90, 98])
        sync_sensor_trend(self.sensor.id)
        sync_sensor_trend(self.sensor.id)
        self.assertEqual(Alerta.objects.filter(sensor=self.sensor, origem='tendencia', status='ativo').count(), 1)
        self.assertEqual(OrdemServico.objects.filter(tipo_os='preditiva', alerta_origem__sensor=self.sensor).count(), 1)

    def test_stable_follow_up_resolves_active_trend(self):
        TrendConfig.objects.create(sensor=self.sensor, num_leituras=3, periodo_horas=24)
        start = timezone.now() - timedelta(hours=2)
        self._readings([80, 90, 98], start=start)
        sync_sensor_trend(self.sensor.id)
        self._readings([50, 50, 50], start=timezone.now() - timedelta(minutes=20), step_minutes=5)
        sync_sensor_trend(self.sensor.id)
        self.assertFalse(Alerta.objects.filter(sensor=self.sensor, origem='tendencia', status='ativo').exists())
        self.assertTrue(Alerta.objects.filter(sensor=self.sensor, origem='tendencia', status='resolvido').exists())

    def test_insufficient_data_resolves_only_after_configured_timeout(self):
        TrendConfig.objects.create(
            sensor=self.sensor, num_leituras=3, periodo_horas=1, max_horas_sem_dados=2
        )
        alerta = Alerta.objects.create(
            equipamento=self.sensor.equipamento, sensor=self.sensor, origem='tendencia',
            evento_chave=f'tendencia:{self.sensor.id}:increasing', tipo_alerta='Tendência',
            nivel='medio', descricao='Ativo para teste', dados_analise={'intervention_recommended': False},
        )
        Telemetria.objects.create(sensor=self.sensor, valor=50)
        result = sync_sensor_trend(self.sensor.id)
        self.assertFalse(result['resolved_alert'])
        alerta.refresh_from_db()
        self.assertEqual(alerta.status, 'ativo')

        Telemetria.objects.filter(sensor=self.sensor).update(
            timestamp=timezone.now() - timedelta(hours=3)
        )
        result = sync_sensor_trend(self.sensor.id)
        self.assertTrue(result['resolved_alert'])
        alerta.refresh_from_db()
        self.assertEqual(alerta.status, 'resolvido')

    def test_sync_does_not_fetch_operational_context(self):
        self._readings([70, 80, 90])
        with patch('telemetria.trend_analysis._operational_context') as context:
            sync_sensor_trend(self.sensor.id)
        context.assert_not_called()
