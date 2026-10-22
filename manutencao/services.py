"""Regras determinísticas para priorização de ordens de serviço."""

from .models import OrdemServico


PESO = {'baixa': 1, 'media': 2, 'alta': 3, 'critica': 4}


class PrioridadeOSService:
    """Único ponto de cálculo; sinais e serializers delegam a esta classe."""

    MATRIZ = {
        'A': {'baixa': 'media', 'moderada': 'alta', 'alta': 'alta'},
        'B': {'baixa': 'media', 'moderada': 'media', 'alta': 'alta'},
        'C': {'baixa': 'baixa', 'moderada': 'media', 'alta': 'alta'},
        'D': {'baixa': 'baixa', 'moderada': 'baixa', 'alta': 'media'},
    }

    @classmethod
    def calcular(cls, equipamento, tipo_os, gravidade='ausente', risco_seguranca=False, prioridade_plano=None):
        criticidade = equipamento.criticidade
        if risco_seguranca or gravidade == 'critica':
            return 'critica', 'Condição crítica ou risco de segurança informado; intervenção imediata.', criticidade

        if tipo_os in ('preditiva', 'preventiva') and gravidade == 'ausente':
            prioridade = prioridade_plano or 'media'
            return prioridade, (
                f'Prioridade {prioridade}: manutenção programada; a criticidade {criticidade or "não avaliada"} '
                'não transforma sozinha uma atividade preventiva em emergência.'
            ), criticidade

        if gravidade == 'ausente':
            return 'media', (
                'Prioridade média: gravidade da condição não informada; requer triagem. '
                'Nenhuma criticidade foi presumida para reduzir o atendimento.'
            ), criticidade

        if not criticidade:
            return 'alta', (
                f'Prioridade alta: condição de gravidade {gravidade} com equipamento sem criticidade avaliada; '
                'a classificação deve ser concluída sem reduzir a resposta.'
            ), None

        prioridade = cls.MATRIZ[criticidade][gravidade]
        return prioridade, (
            f'Prioridade {prioridade}: equipamento de criticidade {criticidade} e condição de gravidade {gravidade}.'
        ), criticidade

    @classmethod
    def preencher(cls, dados, equipamento, prioridade_plano=None):
        prioridade, justificativa, criticidade = cls.calcular(
            equipamento, dados.get('tipo_os', 'preventiva'), dados.get('gravidade_condicao', 'ausente'),
            dados.get('risco_seguranca', False), prioridade_plano,
        )
        dados.update({
            'prioridade': prioridade, 'prioridade_automatica': prioridade,
            'justificativa_prioridade': justificativa,
            'criticidade_na_abertura': criticidade,
            'justificativa_criticidade_na_abertura': equipamento.justificativa_criticidade or '',
            'prioridade_manual': False,
        })
        return dados

    @classmethod
    def criar_por_alerta(cls, alerta):
        gravidade = {'baixo': 'baixa', 'medio': 'moderada', 'critico': 'critica'}[alerta.nivel]
        titulo = f'MANUTENÇÃO: {alerta.tipo_alerta}'
        ordem = OrdemServico.objects.filter(equipamento=alerta.equipamento, status__in=['pendente', 'andamento'], titulo=titulo).first()
        dados = cls.preencher({
            'tipo_os': 'corretiva', 'gravidade_condicao': gravidade, 'risco_seguranca': False,
        }, alerta.equipamento)
        descricao = f'O.S. vinculada ao alerta: {alerta.tipo_alerta}.\n{alerta.descricao}'
        if ordem is None:
            return OrdemServico.objects.create(equipamento=alerta.equipamento, titulo=titulo, descricao=descricao, status='pendente', **dados)
        if not ordem.prioridade_manual and PESO[dados['prioridade']] > PESO[ordem.prioridade]:
            for campo, valor in dados.items():
                setattr(ordem, campo, valor)
            ordem.descricao += f'\n\n[ATUALIZAÇÃO DE ALERTA] {alerta.descricao}'
            ordem.save()
        return ordem
