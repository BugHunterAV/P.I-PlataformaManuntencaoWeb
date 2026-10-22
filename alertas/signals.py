from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Alerta
from manutencao.services import PrioridadeOSService

@receiver(post_save, sender=Alerta)
def vincular_ordem_servico_ao_alerta(sender, instance, created, **kwargs):
    """
    Sempre que um alerta for criado (manual ou automático), 
    garante que uma Ordem de Serviço seja aberta se o nível for Critico ou Médio.
    """
    # Só processa se o alerta estiver ativo e for novo ou escalado
    if instance.status != 'ativo':
        return

    if instance.origem == 'tendencia':
        PrioridadeOSService.criar_por_tendencia(instance)
    else:
        PrioridadeOSService.criar_por_alerta(instance)
