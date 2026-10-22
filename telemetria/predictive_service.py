"""Orquestração determinística de alertas e OS para tendências.

O serviço não chama o Gemini: a decisão operacional é sempre calculada pelo
backend. A IA é opcional e pode explicar um alerta depois, sem bloquear este
fluxo.
"""

from django.db import IntegrityError, transaction
from django.utils import timezone

from alertas.models import Alerta
from .models import Sensor
from .trend_analysis import analyze_sensor_trend


RISK_TO_ALERT = {'baixo': 'baixo', 'medio': 'medio', 'alto': 'critico', 'critico': 'critico'}


def sync_sensor_trend(sensor_id):
    """Atualiza o episódio de tendência do sensor de forma idempotente."""
    trend = analyze_sensor_trend(sensor_id)
    if not trend or trend.get('insufficient_data'):
        return trend

    sensor = Sensor.objects.select_related('equipamento').filter(pk=sensor_id, ativo=True).first()
    if sensor is None:
        return trend

    is_relevant = trend['direction'] == 'increasing' and trend['risk_level'] in ('medio', 'alto', 'critico')
    event_key = f'tendencia:{sensor.id}:{trend["direction"]}'

    try:
        with transaction.atomic():
            active = Alerta.objects.select_for_update().filter(
                sensor=sensor, origem='tendencia', status='ativo'
            )
            if not is_relevant:
                active.update(status='resolvido', data_ultima_analise=timezone.now())
                return trend

            # Um novo sentido é um novo episódio; o anterior fica auditável.
            active.exclude(evento_chave=event_key).update(
                status='resolvido', data_ultima_analise=timezone.now()
            )
            alerta = active.filter(evento_chave=event_key).first()
            descricao = _trend_description(sensor, trend)
            values = {
                'sensor': sensor,
                'tipo_alerta': f'Tendência de {sensor.get_tipo_display()} ({trend["direction"]})',
                'origem': 'tendencia',
                'evento_chave': event_key,
                'nivel': RISK_TO_ALERT[trend['risk_level']],
                'descricao': descricao,
                'dados_analise': trend,
                'data_ultima_analise': timezone.now(),
                'status': 'ativo',
            }
            if alerta is None:
                alerta = Alerta.objects.create(equipamento=sensor.equipamento, **values)
            else:
                for field, value in values.items():
                    setattr(alerta, field, value)
                alerta.save()
    except IntegrityError:
        # Outra execução ganhou a criação do mesmo episódio. A restrição
        # parcial no banco é a última barreira contra duplicidade concorrente.
        alerta = Alerta.objects.filter(evento_chave=event_key, status='ativo').first()
        if alerta is None:
            raise
    return trend


def _trend_description(sensor, trend):
    projection = trend.get('projected_breach_hours')
    projection_text = (
        'não foi possível estimar o tempo até o limite'
        if projection is None else f'estimativa de {projection} hora(s) até o limite'
    )
    return (
        f'O equipamento {sensor.equipamento.nome} apresenta aumento persistente de '
        f'{sensor.get_tipo_display().lower()} ({trend["readings_count"]} leituras). '
        f'Inclinação observada: {trend["slope_per_hour"]} {sensor.unidade_medida}/hora; '
        f'valor atual: {trend.get("current_value")} {sensor.unidade_medida}; '
        f'limite superior: {sensor.limite_alerta} {sensor.unidade_medida}; '
        f'{projection_text}. Trata-se de uma indicação de risco, não de garantia de falha.'
    )
