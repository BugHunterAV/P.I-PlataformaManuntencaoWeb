"""Regras determinísticas para priorização de ordens de serviço."""

from django.db import transaction
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

    @classmethod
    def criar_por_tendencia(cls, alerta):
        """Cria ou atualiza a única OS aberta do episódio de tendência.

        A relação OneToOne com o alerta é a chave de idempotência operacional:
        análises repetidas atualizam a mesma ordem e um episódio resolvido pode
        gerar uma nova ordem no futuro por estar associado a outro alerta.
        """
        if alerta.status != 'ativo':
            return None

        dados = alerta.dados_analise or {}
        if not dados.get('intervention_recommended'):
            return None

        gravidade = {
            'baixo': 'baixa', 'medio': 'moderada',
            'alto': 'alta', 'critico': 'critica',
        }.get(dados.get('risk_level'), 'moderada')
        prioridade, justificativa, criticidade = cls.calcular(
            alerta.equipamento, 'preditiva', gravidade,
        )
        titulo = f'MANUTENÇÃO PREDITIVA: {alerta.tipo_alerta}'
        descricao = (
            f'Intervenção preditiva vinculada ao alerta #{alerta.id}.\n'
            f'{alerta.descricao}\n'
            f'Indicadores: inclinação {dados.get("slope_per_hour")} por hora; '
            f'leituras analisadas: {dados.get("readings_count")}; '
            f'projeção até o limite: {dados.get("projected_breach_hours")} horas.'
        )
        with transaction.atomic():
            ordem = (
                OrdemServico.objects.select_for_update()
                .filter(alerta_origem=alerta)
                .first()
            )
            if ordem is None:
                ordem = OrdemServico.objects.create(
                    equipamento=alerta.equipamento,
                    sensor_origem=alerta.sensor,
                    alerta_origem=alerta,
                    tipo_os='preditiva',
                    titulo=titulo,
                    descricao=descricao,
                    status='pendente',
                    prioridade=prioridade,
                    gravidade_condicao=gravidade,
                    prioridade_automatica=prioridade,
                    justificativa_prioridade=justificativa,
                    criticidade_na_abertura=criticidade,
                    justificativa_criticidade_na_abertura=(
                        alerta.equipamento.justificativa_criticidade or ''
                    ),
                )
            elif ordem.status in ('pendente', 'andamento') and not ordem.prioridade_manual:
                ordem.prioridade = prioridade
                ordem.prioridade_automatica = prioridade
                ordem.gravidade_condicao = gravidade
                ordem.justificativa_prioridade = justificativa
                ordem.descricao = descricao
                ordem.save(update_fields=[
                    'prioridade', 'prioridade_automatica', 'gravidade_condicao',
                    'justificativa_prioridade', 'descricao',
                ])
        return ordem
