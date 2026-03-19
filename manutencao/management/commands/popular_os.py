from django.core.management.base import BaseCommand
from manutencao.models import OrdemServico
from ativos.models import Equipamento
from accounts.models import Usuario
from faker import Faker
import random
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Popula a base de dados com Ordens de Serviço aleatórias'

    def handle(self, *args, **kwargs):
        self.stdout.write("A iniciar a criação de Ordens de Serviço...")

        fake = Faker('pt_PT')
        
        equipamentos = list(Equipamento.objects.all())
        usuarios = list(Usuario.objects.filter(tipo_usuario__in=['gestor', 'tecnico']))
        
        if not equipamentos or not usuarios:
            self.stdout.write(self.style.ERROR("Aviso: Precisa de ter equipamentos e utilizadores criados primeiro!"))
            return

        problemas = ['Fuga de óleo', 'Vibração excessiva', 'Sobreaquecimento', 'Falha no sensor', 'Ruído anómalo', 'Substituição de correia']
        status_opcoes = ['pendente', 'andamento']
        prioridades = ['baixa', 'media', 'alta', 'urgente']

        for _ in range(50):
            equipamento = random.choice(equipamentos)
            responsavel = random.choice(usuarios)
            status = random.choice(status_opcoes)
            
            # Vamos criar OS apenas pendentes ou em andamento para podermos finalizar depois!
            OrdemServico.objects.create(
                equipamento=equipamento,
                responsavel=responsavel,
                titulo=f"{random.choice(problemas)} - {equipamento.nome}",
                descricao=fake.text(max_nb_chars=200),
                status=status,
                prioridade=random.choice(prioridades)
            )

        self.stdout.write(self.style.SUCCESS("Base de dados populada com 50 Ordens de Serviço!"))