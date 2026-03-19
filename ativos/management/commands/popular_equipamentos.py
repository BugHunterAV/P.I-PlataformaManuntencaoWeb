from django.core.management.base import BaseCommand
from ativos.models import Equipamento
from accounts.models import Empresa
from faker import Faker
import random

class Command(BaseCommand):
    help = 'Popula o banco de dados com equipamentos industriais aleatórios'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando a criação de equipamentos...")

        fake = Faker('pt_BR')
        
        # 1. Buscamos todas as empresas para atrelar as máquinas a elas
        empresas = list(Empresa.objects.all())
        
        if not empresas:
            self.stdout.write(self.style.ERROR("Nenhuma empresa encontrada! Rode o script de empresas primeiro."))
            return

        # Dados industriais para dar um tom realista ao seu sistema
        tipos = ['Motor Elétrico', 'Bomba Hidráulica', 'Compressor de Ar', 'Esteira Transportadora', 'Torno CNC', 'Ponte Rolante']
        fabricantes = ['WEG', 'Siemens', 'Bosch', 'Schneider', 'ABB', 'Atlas Copco']
        status_opcoes = ['ativo', 'manutencao', 'inativo']

        # Vamos criar 100 máquinas espalhadas pelas empresas
        for i in range(100):
            empresa_escolhida = random.choice(empresas)
            tipo_escolhido = random.choice(tipos)
            fabricante_escolhido = random.choice(fabricantes)
            
            # Gera um modelo fictício (Ex: TX-450)
            modelo_ficticio = f"{fake.lexify(text='??').upper()}-{random.randint(100, 999)}"
            
            # Gera um número de série único (Ex: SN-8472-ABCD)
            num_serie = f"SN-{random.randint(1000, 9999)}-{fake.lexify(text='????').upper()}"
            
            # Nome do equipamento juntando o tipo e o modelo
            nome_equipamento = f"{tipo_escolhido} {modelo_ficticio}"

            # O get_or_create evita duplicar o número de série caso você rode o script duas vezes
            equipamento, criado = Equipamento.objects.get_or_create(
                numero_serie=num_serie,
                defaults={
                    'empresa': empresa_escolhida,
                    'nome': nome_equipamento,
                    'tipo': tipo_escolhido,
                    'fabricante': fabricante_escolhido,
                    'modelo': modelo_ficticio,
                    'data_instalacao': fake.date_between(start_date='-5y', end_date='today'),
                    'status': random.choice(status_opcoes)
                }
            )

            if criado:
                self.stdout.write(self.style.SUCCESS(f'Equipamento "{nome_equipamento}" criado com sucesso!'))

        self.stdout.write(self.style.SUCCESS("Banco de dados populado com 100 novos equipamentos!"))