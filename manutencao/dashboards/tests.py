from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from manutencao.models import OrdemServico
from ativos.models import Equipamento, Empresa
from accounts.models import Usuario
from alertas.models import Alerta


class DashboardSummaryTests(APITestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nome="Delta", cnpj="444", email="d@d.com")
        self.tecnico = Usuario.objects.create_user(
            username="tecnico_dash", password="123", tipo_usuario="tecnico", empresa=self.empresa
        )
        self.tecnico_outro = Usuario.objects.create_user(
            username="tecnico_outro", password="123", tipo_usuario="tecnico", empresa=self.empresa
        )
        self.gestor = Usuario.objects.create_user(
            username="gestor_dash", password="123", tipo_usuario="gestor", empresa=self.empresa
        )
        self.equip1 = Equipamento.objects.create(
            nome="Bomba 1", tipo="Bomba", numero_serie="B-001", empresa=self.empresa
        )
        self.equip2 = Equipamento.objects.create(
            nome="Motor 2", tipo="Motor", numero_serie="M-002", empresa=self.empresa
        )
        self.ordem_livre = OrdemServico.objects.create(
            equipamento=self.equip1, titulo="OS Livre", descricao="Sem técnico", status="pendente"
        )
        self.ordem_minha = OrdemServico.objects.create(
            equipamento=self.equip1, titulo="OS Minha", descricao="Minha ordem", status="andamento", responsavel=self.tecnico
        )
        self.ordem_outra = OrdemServico.objects.create(
            equipamento=self.equip2, titulo="OS Outra", descricao="Outra ordem", status="andamento", responsavel=self.tecnico_outro
        )
        self.alerta = Alerta.objects.create(
            equipamento=self.equip1, tipo_alerta="Exemplo", nivel="critico", status="ativo"
        )
        self.url = reverse('dashboard-summary')

    def test_dashboard_summary_tecnico_returns_only_assigned_scope(self):
        self.client.force_authenticate(user=self.tecnico)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('ordens_abertas', response.data)
        self.assertIn('minhas_ordens', response.data)
        self.assertIn('ordens_sem_tecnico', response.data)
        self.assertEqual(response.data['ordens_abertas'], 3)
        self.assertEqual(response.data['minhas_ordens'], 1)
        self.assertEqual(response.data['ordens_sem_tecnico'], 2)
        self.assertEqual(response.data['total_equipamentos'], 1)
        self.assertEqual(response.data['alertas_ativos']['critico'], 1)
        self.assertEqual(len(response.data['equipamentos']), 1)

    def test_dashboard_summary_gestor_keeps_company_view(self):
        self.client.force_authenticate(user=self.gestor)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('resumo_status', response.data)
        self.assertIn('kpis_globais', response.data)
        self.assertIn('detalhes_equipamentos', response.data)
        self.assertEqual(response.data['resumo_status']['total'], 2)

    def test_kpi_dashboard_returns_valid_kpi_list(self):
        self.client.force_authenticate(user=self.gestor)
        OrdemServico.objects.create(
            equipamento=self.equip1,
            titulo="OS Concluída",
            descricao="Teste kpi",
            status="concluida",
            data_abertura=timezone.now() - timedelta(hours=3),
            data_conclusao=timezone.now(),
        )
        response = self.client.get(reverse('kpi-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)
        item = response.data[0]
        self.assertIn('mttr_hours', item)
        self.assertIn('mtbf_hours', item)
        self.assertIn('disponibilidade_porcentagem', item)
        self.assertIn('total_manutencoes', item)
