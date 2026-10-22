"""
Serviço de Análise de Tendência de Sensores.

Calcula regressão linear simples sobre leituras recentes de um sensor
para detectar tendências crescentes/decrescentes e projetar quando o
limite operacional será atingido.
"""
from datetime import timedelta
import math
from django.utils import timezone
from .models import Sensor, Telemetria, TrendConfig


def get_effective_config(sensor):
    """
    Retorna a configuração de tendência efetiva para um sensor.
    Prioridade: config específica do sensor > config global > padrão hardcoded.
    """
    try:
        config = sensor.trend_config
        if config and config.ativo:
            return {
                'periodo_horas': config.periodo_horas,
                'num_leituras': config.num_leituras,
                'sensibilidade': config.sensibilidade,
                'is_custom': True,
            }
    except TrendConfig.DoesNotExist:
        pass

    # Tenta config global (sensor=null)
    global_config = TrendConfig.objects.filter(sensor__isnull=True, ativo=True).first()
    if global_config:
        return {
            'periodo_horas': global_config.periodo_horas,
            'num_leituras': global_config.num_leituras,
            'sensibilidade': global_config.sensibilidade,
            'is_custom': False,
        }

    # Padrão hardcoded
    return {
        'periodo_horas': 24,
        'num_leituras': 50,
        'sensibilidade': 'media',
        'is_custom': False,
    }


def _sensitivity_threshold(sensibilidade):
    """
    Retorna o limiar de slope (variação/hora) que classifica como tendência
    significativa. Quanto menor o valor, mais sensível a detecção.
    """
    return {
        'alta': 0.005,
        'media': 0.02,
        'baixa': 0.05,
    }.get(sensibilidade, 0.02)


def analyze_sensor_trend(sensor_id):
    """
    Analisa a tendência de um sensor específico.

    Retorna dict com:
        - direction: 'increasing' | 'decreasing' | 'stable'
        - slope: variação por hora
        - projected_breach_hours: horas estimadas até atingir o limite (ou None)
        - risk_level: 'baixo' | 'medio' | 'alto' | 'critico'
        - readings_summary: lista de {valor, timestamp}
        - config_used: informações da config utilizada
        - sensor_info: dados básicos do sensor
    """
    try:
        sensor = Sensor.objects.select_related('equipamento').get(pk=sensor_id, ativo=True)
    except Sensor.DoesNotExist:
        return None

    config = get_effective_config(sensor)
    since = timezone.now() - timedelta(hours=config['periodo_horas'])

    # Busca primeiro as mais recentes e só depois reordena para a regressão.
    # O código anterior aplicava o limite após ordenar ascendentemente e podia
    # descartar as leituras novas quando havia mais que o limite configurado.
    raw_limit = max(config['num_leituras'] * 2, config['num_leituras'])
    raw_readings = list(
        Telemetria.objects.filter(sensor=sensor, timestamp__gte=since)
        .order_by('-timestamp', '-id')[:raw_limit]
        .values('valor', 'timestamp')
    )

    # Uma amostra por timestamp: em duplicatas, a primeira é a leitura mais
    # recente devido à ordenação acima. NaN/inf não sustentam uma projeção.
    unique = {}
    for reading in raw_readings:
        value = reading['valor']
        timestamp = reading['timestamp']
        if value is None or not math.isfinite(float(value)) or timestamp is None:
            continue
        unique.setdefault(timestamp, {'valor': float(value), 'timestamp': timestamp})
    leituras = sorted(unique.values(), key=lambda item: item['timestamp'])[-config['num_leituras']:]

    if len(leituras) < 3:
        return {
            'sensor_id': sensor.id,
            'sensor_info': _sensor_info(sensor),
            'direction': 'stable',
            'slope': 0.0,
            'slope_per_hour': 0.0,
            'projected_breach_hours': None,
            'risk_level': 'baixo',
            'readings_summary': leituras,
            'readings_count': len(leituras),
            'config_used': config,
            'insufficient_data': True,
            'data_quality': 'insufficient',
            'analysis_window_hours': config['periodo_horas'],
            'intervention_recommended': False,
            **_operational_context(sensor.id),
        }

    # Regressão linear simples: y = a + b*x
    # x = horas desde a primeira leitura
    t0 = leituras[0]['timestamp']
    xs = []
    ys = []
    for r in leituras:
        hours_elapsed = (r['timestamp'] - t0).total_seconds() / 3600.0
        xs.append(hours_elapsed)
        ys.append(r['valor'])

    n = len(xs)
    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xy = sum(x * y for x, y in zip(xs, ys))
    sum_x2 = sum(x * x for x in xs)

    denominator = n * sum_x2 - sum_x * sum_x
    if abs(denominator) < 1e-12:
        slope = 0.0
        intercept = sum_y / n if n else 0
    else:
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n

    # Normaliza slope por hora
    slope_per_hour = slope  # já está em unidade/hora

    # Determina direção baseado no threshold de sensibilidade
    threshold = _sensitivity_threshold(config['sensibilidade'])
    limite = sensor.limite_alerta

    # Normaliza threshold pelo limite para ser proporcional
    abs_threshold = threshold * limite if limite and limite > 0 else threshold

    if slope_per_hour > abs_threshold:
        direction = 'increasing'
    elif slope_per_hour < -abs_threshold:
        direction = 'decreasing'
    else:
        direction = 'stable'

    # Projeção: o sensor existente modela um limite superior. Uma tendência
    # decrescente, portanto, não é tratada como aproximação desse limite.
    projected_breach_hours = None
    ultimo_valor = ys[-1]
    ultimo_x = xs[-1]

    if limite and limite > 0 and direction == 'increasing' and slope_per_hour > 0:
        remaining = limite - ultimo_valor
        if remaining > 0:
            projected_breach_hours = round(remaining / slope_per_hour, 1)
        elif remaining <= 0:
            projected_breach_hours = 0  # Já ultrapassou

    # Calcula nível de risco
    risk_level = _calculate_risk_level(
        ultimo_valor, limite, direction, projected_breach_hours, config['sensibilidade']
    )

    intervention_recommended = (
        direction == 'increasing' and risk_level in ('alto', 'critico')
    ) or (
        direction == 'increasing' and projected_breach_hours is not None
        and projected_breach_hours <= 24
    )

    return {
        'sensor_id': sensor.id,
        'sensor_info': _sensor_info(sensor),
        'direction': direction,
        'slope': round(slope, 6),
        'slope_per_hour': round(slope_per_hour, 4),
        'projected_breach_hours': projected_breach_hours,
        'risk_level': risk_level,
        'current_value': round(ultimo_valor, 2),
        'limite_operacional': limite,
        'readings_summary': [
            {'valor': round(r['valor'], 2), 'timestamp': r['timestamp'].isoformat()}
            for r in leituras
        ],
        'readings_count': len(leituras),
        'config_used': config,
        'insufficient_data': False,
        'data_quality': 'valid',
        'analysis_window_hours': config['periodo_horas'],
        'intervention_recommended': intervention_recommended,
        'analyzed_at': timezone.now().isoformat(),
        **_operational_context(sensor.id),
    }


def _operational_context(sensor_id):
    """Retorna vínculos operacionais sem tornar o algoritmo dependente deles."""
    from alertas.models import Alerta
    from manutencao.models import OrdemServico

    alerta = Alerta.objects.filter(
        sensor_id=sensor_id, origem='tendencia', status='ativo'
    ).order_by('-data_alerta').first()
    if alerta is None:
        return {'active_alert_id': None, 'predictive_work_order': None}
    ordem = OrdemServico.objects.filter(alerta_origem=alerta).values('id', 'status').first()
    return {
        'active_alert_id': alerta.id,
        'predictive_work_order': ordem,
    }


def _sensor_info(sensor):
    return {
        'id': sensor.id,
        'nome': sensor.nome,
        'tipo': sensor.tipo,
        'tipo_display': sensor.get_tipo_display(),
        'unidade_medida': sensor.unidade_medida,
        'limite_alerta': sensor.limite_alerta,
        'equipamento_id': sensor.equipamento_id,
        'equipamento_nome': sensor.equipamento.nome,
    }


def _calculate_risk_level(valor_atual, limite, direction, breach_hours, sensibilidade):
    """
    Determina o nível de risco baseado na projeção e estado atual.
    """
    if not limite or limite <= 0:
        return 'baixo'

    percentual = (valor_atual / limite) * 100

    # Já acima do limite
    if percentual >= 100:
        return 'critico'

    # Tendência crescente com projeção
    if direction == 'increasing' and breach_hours is not None:
        if breach_hours <= 2:
            return 'critico'
        elif breach_hours <= 8:
            return 'alto'
        elif breach_hours <= 24:
            return 'medio'

    # Baseado no percentual atual
    if percentual >= 85:
        return 'alto'
    elif percentual >= 70:
        return 'medio'

    # Tendência crescente mas longe do limite
    if direction == 'increasing':
        return 'medio' if sensibilidade == 'alta' else 'baixo'

    return 'baixo'


def get_all_sensor_trends(user, only_atypical=False):
    """
    Retorna tendências de todos os sensores visíveis ao usuário.
    Se only_atypical=True, filtra apenas sensores com tendências não-estáveis
    ou com risco >= medio.
    """
    if user.tipo_usuario == 'admin':
        sensors = Sensor.objects.filter(ativo=True).select_related('equipamento')
    elif user.empresa:
        sensors = Sensor.objects.filter(
            ativo=True,
            equipamento__empresa=user.empresa
        ).select_related('equipamento')
    else:
        return []

    results = []
    for sensor in sensors:
        trend = analyze_sensor_trend(sensor.id)
        if trend is None:
            continue
        if only_atypical:
            if trend['direction'] == 'stable' and trend['risk_level'] == 'baixo':
                continue
        results.append(trend)

    # Ordena por risco (critico primeiro)
    risk_order = {'critico': 0, 'alto': 1, 'medio': 2, 'baixo': 3}
    results.sort(key=lambda t: risk_order.get(t['risk_level'], 4))

    return results
