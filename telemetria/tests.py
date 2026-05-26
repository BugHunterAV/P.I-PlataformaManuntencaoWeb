from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Sensor, Telemetria
from ativos.models import Equipamento, Empresa
from alertas.models import Alerta
from manutencao.models import OrdemServico
from accounts.models import Usuario

class TelemetriaAlertTests(APITestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nome="Gamma", cnpj="333", email="g@g.com")
        self.user = Usuario.objects.create_user(
            username="gestor_telemetria", password="123", tipo_usuario="gestor", empresa=self.empresa
        )
        self.client.force_authenticate(user=self.user)
        self.motor = Equipamento.objects.create(
            nome="Motor Telemetria", tipo="Motor Elétrico", numero_serie="TEL-001", empresa=self.empresa
        )
        self.sensor = Sensor.objects.create(
            equipamento=self.motor,
            nome="Sensor Temp",
            tipo="temperatura",
            unidade_medida="°C",
            limite_alerta=100.0
        )
        self.leitura_url = reverse('leituras-list')

    def test_alert_escalation(self):
        """Testa se os alertas e O.S. são gerados e escalados conforme o valor da leitura."""
        # 1. Alerta Baixo (75% de 100 = 75.0)
        data_baixo = {"sensor": self.sensor.id, "valor": 75.0}
        self.client.post(self.leitura_url, data_baixo)
        alerta = Alerta.objects.filter(equipamento=self.motor, status='ativo').first()
        self.assertIsNotNone(alerta)
        self.assertEqual(alerta.nivel, 'baixo')
        
        os = OrdemServico.objects.filter(equipamento=self.motor, status='pendente').first()
        self.assertIsNotNone(os)
        self.assertEqual(os.prioridade, 'baixo')

        # 2. Alerta Médio (90% de 100 = 90.0) -> Escalada
        data_medio = {"sensor": self.sensor.id, "valor": 90.0}
        self.client.post(self.leitura_url, data_medio)
        alerta.refresh_from_db()
        self.assertEqual(alerta.nivel, 'medio')
        
        os.refresh_from_db()
        self.assertEqual(os.prioridade, 'medio')

        # 3. Alerta Crítico (110% de 100 = 110.0) -> Escalada Máxima
        data_critico = {"sensor": self.sensor.id, "valor": 110.0}
        self.client.post(self.leitura_url, data_critico)
        alerta.refresh_from_db()
        self.assertEqual(alerta.nivel, 'critico')
        
        os.refresh_from_db()
        self.assertEqual(os.prioridade, 'critico')

    def test_custom_alert_thresholds(self):
        sensor = Sensor.objects.create(
            equipamento=self.motor,
            nome="Sensor Temp Custom",
            tipo="temperatura",
            unidade_medida="°C",
            limite_alerta=120.0,
            limite_alerta_baixo_pct=60.0,
            limite_alerta_medio_pct=90.0,
            limite_alerta_critico_pct=95.0,
        )

        # Alerta baixo quando atingir 72.0 (60% de 120)
        self.client.post(self.leitura_url, {"sensor": sensor.id, "valor": 72.0})
        alerta = Alerta.objects.filter(equipamento=self.motor, tipo_alerta=f"Alerta de {sensor.get_tipo_display()}", status='ativo').first()
        self.assertIsNotNone(alerta)
        self.assertEqual(alerta.nivel, 'baixo')

        # Escalada para médio aos 108.0 (90% de 120)
        self.client.post(self.leitura_url, {"sensor": sensor.id, "valor": 108.0})
        alerta.refresh_from_db()
        self.assertEqual(alerta.nivel, 'medio')

        # Escalada para crítico aos 114.0 (95% de 120)
        self.client.post(self.leitura_url, {"sensor": sensor.id, "valor": 114.0})
        alerta.refresh_from_db()
        self.assertEqual(alerta.nivel, 'critico')
