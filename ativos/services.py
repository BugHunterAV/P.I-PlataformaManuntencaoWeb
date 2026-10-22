from .models import HistoricoCriticidadeEquipamento


def aplicar_criticidade(equipamento, criticidade, justificativa, usuario=None, origem='individual'):
    """Altera a classe de forma auditável; não é chamada por mudanças do tipo."""
    anterior = equipamento.criticidade
    equipamento.criticidade = criticidade
    equipamento.criticidade_origem = origem
    equipamento.justificativa_criticidade = justificativa or ''
    equipamento.save(update_fields=['criticidade', 'criticidade_origem', 'justificativa_criticidade'])
    if anterior != criticidade:
        HistoricoCriticidadeEquipamento.objects.create(
            equipamento=equipamento, criticidade_anterior=anterior,
            criticidade_nova=criticidade, justificativa=justificativa or '',
            alterado_por=usuario if getattr(usuario, 'is_authenticated', False) else None,
        )
    return equipamento
