"""
Simulador de Telemetria Industrial em Tempo Real.

Este script detecta dinamicamente sensores ativos e equipamentos com status 'ativo'
no banco de dados, preserva o histórico de valor para transições suaves e grava
leituras de telemetria na mesma cadência do ambiente real.

O objetivo é simular um fluxo confiável de dados para a aplicação, ajudando a
identificar alertas, relatórios e dashboards sem gerar leituras fora de contexto.
"""

import argparse
import logging
import os
import random
import sys
import time

import django
from django.db import DatabaseError, transaction

# Configuração do ambiente Django
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from telemetria.models import Sensor, Telemetria

logger = logging.getLogger('simulador_realtime')


def parse_args():
    parser = argparse.ArgumentParser(
        description='Simulador de Telemetria Industrial em Tempo Real',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--interval-min', type=float, default=7.0,
                        help='Tempo mínimo em segundos entre ciclos')
    parser.add_argument('--interval-max', type=float, default=10.0,
                        help='Tempo máximo em segundos entre ciclos')
    parser.add_argument('--cycles', type=int, default=0,
                        help='Número máximo de ciclos de geração. 0 = execução contínua')
    parser.add_argument('--seed', type=int,
                        help='Semente para tornar a geração de valores determinística')
    parser.add_argument('--sensor', type=int, nargs='+',
                        help='IDs de sensores específicos para simular')
    parser.add_argument('--equipamento', type=int, nargs='+',
                        help='IDs de equipamentos para limitar a simulação')
    parser.add_argument('--dry-run', action='store_true',
                        help='Executa o simulador sem gravar leituras no banco')
    parser.add_argument('--debug', action='store_true',
                        help='Ativa logs de depuração')
    return parser.parse_args()


def configurar_logging(debug=False):
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    if not logger.handlers:
        logger.addHandler(handler)
    else:
        for h in logger.handlers:
            if isinstance(h, logging.StreamHandler):
                h.setFormatter(formatter)


def obter_sensores_ativos(sensor_ids=None, equipamento_ids=None):
    filtro = {'ativo': True, 'equipamento__status': 'ativo'}
    queryset = Sensor.objects.filter(**filtro).select_related('equipamento')

    if sensor_ids:
        queryset = queryset.filter(id__in=sensor_ids)
    if equipamento_ids:
        queryset = queryset.filter(equipamento_id__in=equipamento_ids)

    return queryset.order_by('equipamento__nome', 'nome')


def carregar_ultimo_valor_por_sensor(sensores):
    sensor_ids = [sensor.id for sensor in sensores]
    ultima_leitura = {}

    if not sensor_ids:
        return ultima_leitura

    leituras = (Telemetria.objects
                .filter(sensor_id__in=sensor_ids)
                .order_by('sensor_id', '-timestamp'))

    for leitura in leituras:
        if leitura.sensor_id not in ultima_leitura:
            ultima_leitura[leitura.sensor_id] = float(leitura.valor)
            if len(ultima_leitura) == len(sensor_ids):
                break

    return ultima_leitura


def inicializar_memoria_sensores(sensores, memoria_atual):
    memoria = {}
    ultima_leitura_por_sensor = carregar_ultimo_valor_por_sensor(sensores)

    for sensor in sensores:
        if sensor.id in memoria_atual:
            memoria[sensor.id] = memoria_atual[sensor.id]
            continue

        if sensor.id in ultima_leitura_por_sensor:
            memoria[sensor.id] = ultima_leitura_por_sensor[sensor.id]
            continue

        limite = sensor.limite_alerta if sensor.limite_alerta and sensor.limite_alerta > 0 else 100.0
        memoria[sensor.id] = round(limite * 0.65, 2)
        logger.debug('Inicializando sensor %s (%s) em %.2f', sensor.nome, sensor.get_tipo_display(), memoria[sensor.id])

    return memoria


def gerar_valor_sensor(sensor, valor_anterior):
    limite = sensor.limite_alerta if sensor.limite_alerta and sensor.limite_alerta > 0 else 100.0
    alvo_minimo = limite * 0.62
    alvo_maximo = limite * 0.68

    flutuacao = random.uniform(-0.4, 0.4)
    novo_valor = valor_anterior + flutuacao

    if novo_valor > alvo_maximo:
        novo_valor -= random.uniform(0.2, 0.5)
    elif novo_valor < alvo_minimo:
        novo_valor += random.uniform(0.2, 0.5)

    novo_valor = round(max(0.1, novo_valor), 2)
    return novo_valor, limite, alvo_minimo, alvo_maximo


def imprimir_resumo_ciclo(ciclo, sensores, novos, removidos):
    logger.info('Ciclo %s: %s sensores ativos (%s novos, %s removidos)',
                ciclo, len(sensores), len(novos), len(removidos))
    if novos:
        logger.debug('Sensores adicionados: %s', ', '.join(str(s) for s in novos))
    if removidos:
        logger.debug('Sensores removidos: %s', ', '.join(str(s) for s in removidos))


def rodar_ciclo(sensores, memoria_valores, dry_run=False):
    leituras_criadas = 0

    for sensor in sensores:
        valor_anterior = memoria_valores[sensor.id]
        novo_valor, limite, alvo_minimo, alvo_maximo = gerar_valor_sensor(sensor, valor_anterior)
        memoria_valores[sensor.id] = novo_valor

        descricao = (
            f"[{sensor.equipamento.nome}] {sensor.get_tipo_display()} - {sensor.nome}: "
            f"{novo_valor} {sensor.unidade_medida or ''} "
            f"(alvo {alvo_minimo:.1f}-{alvo_maximo:.1f}, crítico {limite:.1f})"
        )
        logger.info(descricao)

        if not dry_run:
            try:
                Telemetria.objects.create(sensor=sensor, valor=novo_valor)
                leituras_criadas += 1
            except DatabaseError as exc:
                logger.exception('Falha ao gravar leitura para sensor %s: %s', sensor.id, exc)

    return leituras_criadas


def run_simulator(args):
    configurar_logging(args.debug)

    if args.interval_min <= 0 or args.interval_max <= 0:
        raise ValueError('Os intervalos devem ser maiores que zero.')
    if args.interval_min > args.interval_max:
        args.interval_min, args.interval_max = args.interval_max, args.interval_min

    if args.seed is not None:
        random.seed(args.seed)
        logger.debug('Semente de aleatoriedade definida: %s', args.seed)

    logger.info('Iniciando simulador de telemetria. dry_run=%s, sensor=%s, equipamento=%s',
                args.dry_run, args.sensor, args.equipamento)
    logger.info('Intervalo entre ciclos: %.1f-%.1f segundos', args.interval_min, args.interval_max)

    memoria_valores = {}
    ciclo = 1
    ciclos_totais = args.cycles if args.cycles > 0 else float('inf')

    try:
        while ciclo <= ciclos_totais:
            sensores_ativos = obter_sensores_ativos(sensor_ids=args.sensor, equipamento_ids=args.equipamento)
            ids_ativos = {sensor.id for sensor in sensores_ativos}
            ids_memoria = set(memoria_valores)

            novos = ids_ativos - ids_memoria
            removidos = ids_memoria - ids_ativos

            for sensor_id in removidos:
                memoria_valores.pop(sensor_id, None)

            memoria_valores = inicializar_memoria_sensores(sensores_ativos, memoria_valores)
            imprimir_resumo_ciclo(ciclo, sensores_ativos, novos, removidos)

            if not sensores_ativos:
                logger.warning('Nenhum sensor ativo encontrado. Aguarde ou ative sensores/equipamentos no Admin.')
            else:
                with transaction.atomic():
                    leituras = rodar_ciclo(sensores_ativos, memoria_valores, dry_run=args.dry_run)
                    logger.info('Leituras geradas no ciclo %s: %s', ciclo, leituras)

            intervalo = random.uniform(args.interval_min, args.interval_max)
            logger.debug('Durma por %.1f segundos antes do próximo ciclo.', intervalo)
            time.sleep(intervalo)
            ciclo += 1

    except KeyboardInterrupt:
        logger.info('Simulação interrompida pelo operador.')
    except Exception as exc:
        logger.exception('Erro inesperado no simulador: %s', exc)
    finally:
        logger.info('Simulador finalizado após %s ciclos.', ciclo - 1)


if __name__ == '__main__':
    run_simulator(parse_args())
