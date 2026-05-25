from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from accounts.models import Empresa, Usuario
from ativos.models import Equipamento
from manutencao.models import OrdemServico, HistoricoManutencao
from alertas.models import Alerta
from telemetria.models import Sensor, Telemetria


class GeminiApiTests(APITestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nome="Gamma", cnpj="99999999999999", email="gamma@example.com")
        self.gestor = Usuario.objects.create_user(
            username="gestor_gemini",
            password="123456",
            tipo_usuario="gestor",
            empresa=self.empresa,
        )
        self.tecnico = Usuario.objects.create_user(
            username="tecnico_gemini",
            password="123456",
            tipo_usuario="tecnico",
            empresa=self.empresa,
        )
        self.equipamento = Equipamento.objects.create(
            empresa=self.empresa,
            nome="Bomba Teste",
            tipo="bomba_hidraulica",
            numero_serie="BPT-001",
        )

        self.os_aberta = OrdemServico.objects.create(
            equipamento=self.equipamento,
            titulo="Troca de vedação",
            descricao="Verificar vazamento",
            status="pendente",
            prioridade="medio",
        )
        self.os_atribuida = OrdemServico.objects.create(
            equipamento=self.equipamento,
            titulo="Inspeção elétrica",
            descricao="Verificar painel",
            responsavel=self.tecnico,
            status="andamento",
            prioridade="critico",
        )
        self.os_concluida = OrdemServico.objects.create(
            equipamento=self.equipamento,
            titulo="Revisão geral",
            descricao="Revisão finalizada",
            status="concluida",
            prioridade="medio",
        )
        HistoricoManutencao.objects.create(
            ordem_servico=self.os_concluida,
            descricao_servico="Troca de rolamentos",
            data_execucao="2026-05-20",
            custo_pecas=120.00,
            custo_mao_de_obra=80.00,
        )
        Alerta.objects.create(
            equipamento=self.equipamento,
            tipo_alerta="Vazamento",
            nivel="medio",
            descricao="Vazamento detectado no acoplamento",
            status="ativo",
        )
        sensor = Sensor.objects.create(
            equipamento=self.equipamento,
            nome="Sensor de Pressão",
            tipo="pressao",
            unidade_medida="bar",
            limite_alerta=10.0,
            ativo=True,
        )
        Telemetria.objects.create(sensor=sensor, valor=8.5)

    @patch.dict('os.environ', {'GEMINI_API_KEY': ''})
    def test_chat_endpoint_returns_missing_key_message(self):
        self.client.force_authenticate(user=self.gestor)
        url = reverse('gemini_chat')
        response = self.client.post(url, {'message': 'Qual é a situação atual?'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('GEMINI_API_KEY', response.data['response'])
        self.assertIn('habilitar o chat', response.data['response'])

    @patch.dict('os.environ', {'GEMINI_API_KEY': ''})
    def test_os_analysis_endpoint_returns_missing_key_message(self):
        self.client.force_authenticate(user=self.gestor)
        url = reverse('gemini_ordens_analise')
        response = self.client.post(url, {'message': 'Preciso de prioridade nas ordens.'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('GEMINI_API_KEY', response.data['response'])
        self.assertIn('habilitar este endpoint', response.data['response'])

    @patch.dict('os.environ', {'GEMINI_API_KEY': ''})
    def test_unassigned_orders_endpoint_returns_missing_key_message(self):
        self.client.force_authenticate(user=self.gestor)
        url = reverse('gemini_ordens_sem_atribuicao')
        response = self.client.post(url, {'message': 'Como devo alocar as ordens?'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('GEMINI_API_KEY', response.data['response'])
        self.assertIn('habilitar este endpoint', response.data['response'])

    def test_finance_endpoint_for_tecnico_is_forbidden(self):
        self.client.force_authenticate(user=self.tecnico)
        url = reverse('gemini_gestao_financeira')
        response = self.client.post(url, {'message': 'Como reduzir custos?'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('técnico', response.data['response'].lower())

    @patch.dict('os.environ', {'GEMINI_API_KEY': ''})
    def test_finance_endpoint_for_gestor_returns_missing_key_message(self):
        self.client.force_authenticate(user=self.gestor)
        url = reverse('gemini_gestao_financeira')
        response = self.client.post(url, {'message': 'Preciso de um plano financeiro.'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('GEMINI_API_KEY', response.data['response'])
        self.assertIn('habilitar este endpoint', response.data['response'])

    def test_missing_message_returns_bad_request(self):
        self.client.force_authenticate(user=self.gestor)
        url = reverse('gemini_chat')
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)
        self.assertGreater(len(response.data['message']), 0)
