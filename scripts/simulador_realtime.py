"""
Simulador de Telemetria Industrial em Tempo Real (BugHunter)
Varre dinamicamente o banco de dados a cada ciclo, mantendo os sensores ativos
em regime de trabalho severo (aquecidos), mas logo abaixo do limite de alerta.

Dinamismo: Se você ativar/inativar um equipamento no Admin, o script detectará no próximo ciclo.
Banco de Dados: Compatível nativamente com SQLite e PostgreSQL.
"""

import os
import sys
import django
import time
import random
import argparse

# 1. Configuração do Ambiente Django
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

# Importações dos Models do Django após o django.setup()
from ativos.models import Equipamento
from telemetria.models import Sensor, Telemetria


def obter_sensores_ativos():
    """
    Varre o banco de dados procurando sensores vinculados a equipamentos ativos.
    Garante que mudanças no Admin do Django reflitam no próximo ciclo.
    """
    return Sensor.objects.filter(ativo=True, equipamento__status='ativo').select_related('equipamento')


def inicializar_memoria_sensores(sensores, memoria_atual):
    """
    Mantém o histórico do último valor gerado para que a flutuação seja suave
    (Random Walk), em vez de saltos bruscos e irreais.
    """
    nova_memoria = {}
    for sensor in sensores:
        # Se o sensor já estava na memória, mantém o histórico dele
        if sensor.id in memoria_atual:
            nova_memoria[sensor.id] = memoria_atual[sensor.id]
            continue
            
        # Se for um sensor novo detectado na varredura, busca a última leitura real do banco
        ultima_leitura = Telemetria.objects.filter(sensor=sensor).order_by('-timestamp').first()
        
        if ultima_leitura:
            nova_memoria[sensor.id] = float(ultima_leitura.valor)
        else:
            # Se nunca teve leitura, inicializa em 65% do limite de alerta (Regime Severo / Quente)
            limite = sensor.limite_alerta if sensor.limite_alerta else 100.0
            nova_memoria[sensor.id] = round(limite * 0.65, 2)
            
    return nova_memoria


def run_simulator():
    print("\n" + "="*60)
    print("      SIMULADOR DE TELEMETRIA INDUSTRIAL EM TEMPO REAL      ")
    print("="*60)
    print("-> Monitorando alterações em Equipamentos e Sensores no Banco...")
    print("-> Mantendo métricas em regime severo (Próximas ao Alerta, < 70%).")
    print("-> Pressione CTRL+C para encerrar a simulação a qualquer momento.\n")

    memoria_valores = {}
    ciclo = 1

    try:
        while True:
            # Define uma pausa randômica e dinâmica para o ciclo atual entre 7 e 10 segundos
            intervalo = random.randint(7, 10)
            
            # VARREDURA DINÂMICA: Busca quem está ativo EXATAMENTE agora no banco
            sensores_ativos = obter_sensores_ativos()
            total_sensores = sensores_ativos.count()

            print(f"[Ciclo #{ciclo}] Varredura concluída. {total_sensores} sensores operando de forma ativa.")

            if total_sensores == 0:
                print("   [AVISO] Nenhum equipamento/sensor ativo encontrado. Ative-os via Admin ou execute o seed_db.py.")
            else:
                # Sincroniza a memória caso novos ativos tenham entrado no fluxo
                memoria_valores = inicializar_memoria_sensores(sensores_ativos, memoria_valores)

                # Gera os dados para cada um dos sensores detectados
                for sensor in sensores_ativos:
                    limite = sensor.limite_alerta
                    valor_anterior = memoria_valores[sensor.id]

                    # Alvos de segurança baseados no seu signals.py (abaixo de 70% não gera alerta)
                    alvo_minimo = limite * 0.62
                    alvo_maximo = limite * 0.68

                    # Simula ruído operacional suave (Random Walk)
                    flutuacao = random.uniform(-0.4, 0.4)
                    novo_valor = valor_anterior + flutuacao

                    # Travas matemáticas para garantir o regime quente, sem estourar o limite por erro randômico
                    if novo_valor > alvo_maximo:
                        novo_valor -= random.uniform(0.2, 0.5)  # Força descer se passar de 68%
                    elif novo_valor < alvo_minimo:
                        novo_valor += random.uniform(0.2, 0.5)  # Força subir se cair de 62%

                    novo_valor = round(max(0.1, novo_valor), 2)
                    memoria_valores[sensor.id] = novo_valor

                    # Gravação no Banco de Dados via Django ORM (Engatilha os Signals automaticamente!)
                    Telemetria.objects.create(sensor=sensor, valor=novo_valor)

                    print(f"   + [{sensor.equipamento.nome}] {sensor.get_tipo_display()}: {novo_valor} {sensor.unidade_medida} (Alvo < {round(limite * 0.7, 1)})")

            print(f"-> Aguardando {intervalo} segundos para a próxima pulsação...\n")
            time.sleep(intervalo)
            ciclo += 1

    except KeyboardInterrupt:
        print("\n[DESCONECTADO] Simulação finalizada com sucesso pelo operador.")


if __name__ == '__main__':
    run_simulator()