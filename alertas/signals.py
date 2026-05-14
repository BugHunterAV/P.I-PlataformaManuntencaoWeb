from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Alerta
from manutencao.models import OrdemServico

@receiver(post_save, sender=Alerta)
def vincular_ordem_servico_ao_alerta(sender, instance, created, **kwargs):
    """
    Sempre que um alerta for criado (manual ou automático), 
    garante que uma Ordem de Serviço seja aberta se o nível for Critico ou Médio.
    """
    # Só processa se o alerta estiver ativo e for novo ou escalado
    if instance.status != 'ativo':
        return

    # Mapeamento de severidade do Alerta -> Prioridade da O.S.
    prioridade_map = {
        'critico': 'critico',
        'medio': 'medio',
        'baixo': 'baixo'
    }
    
    prioridade_alvo = prioridade_map.get(instance.nivel, 'baixo')
    
    # Decidimos se alertas "Baixos" geram O.S. automática. 
    # Geralmente sim, mas se quiser restringir, pode adicionar um check aqui.
    
    titulo_os = f"MANUTENÇÃO: {instance.tipo_alerta}"
    
    # Verifica se já existe uma O.S. ativa para este equipamento E este problema específico
    os_ativa = OrdemServico.objects.filter(
        equipamento=instance.equipamento,
        status__in=['pendente', 'andamento'],
        titulo=titulo_os
    ).first()

    if not os_ativa:
        # Cria a O.S. se não houver nenhuma ativa para este tipo de problema
        OrdemServico.objects.create(
            equipamento=instance.equipamento,
            titulo=titulo_os,
            descricao=f"O.S. vinculada ao alerta: {instance.tipo_alerta}.\n{instance.descricao}",
            prioridade=prioridade_alvo,
            tipo_os='corretiva',
            status='pendente'
        )
    else:
        # Se a O.S. já existe, verifica se o nível de prioridade precisa subir
        ordem_peso = {'baixo': 1, 'medio': 2, 'critico': 3}
        if ordem_peso[prioridade_alvo] > ordem_peso[os_ativa.prioridade]:
            os_ativa.prioridade = prioridade_alvo
            os_ativa.descricao += f"\n\n[ATUALIZAÇÃO DE ALERTA]: Nível escalado para {instance.nivel.upper()}. {instance.descricao}"
            os_ativa.save()
