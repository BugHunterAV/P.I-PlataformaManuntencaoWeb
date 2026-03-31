"""
🚀 CONFIGURAÇÃO DE ALERTAS PREDITIVOS (DIDÁTICO)

Este arquivo centraliza as regras para geração automática de alertas.
É fácil de editar: adicione o tipo de equipamento e o limite para cada sensor.
"""

# Configuração de Limites Críticos
# Chave: 'Tipo de Equipamento' ou 'default'
# Valores: {'tipo_sensor': limite_maximo}

LIMITES_ALERTA = {
    # Regras para Motores Elétricos
    'Motor Elétrico': {
        'temperatura': 85.0,  # Graus Celsius
        'vibracao': 8.5,      # mm/s
        'corrente': 150.0,    # Ampères
    },

    # Regras para Bombas Hidráulicas
    'Bomba Hidráulica': {
        'temperatura': 75.0,
        'pressao': 12.0,      # bar
        'vibracao': 12.0,
    },

    # Regras para Compressores
    'Compressor': {
        'pressao': 15.0,
        'temperatura': 95.0,
        'vibracao': 10.0,
    },

    # Painel Elétrico
    'Painel Elétrico': {
        'temperatura': 60.0,
        'corrente': 400.0,
    },

    # Regra Geral (Caso o equipamento não esteja na lista)
    'default': {
        'temperatura': 80.0,
        'vibracao': 10.0,
        'pressao': 10.0,
        'corrente': 100.0,
        'umidade': 90.0,
    }
}

def obter_limite(tipo_equipamento, tipo_sensor):
    """
    Busca o limite configurado para o par Equipamento/Sensor.
    Se não encontrar o equipamento específico, usa o 'default'.
    """
    config = LIMITES_ALERTA.get(tipo_equipamento, LIMITES_ALERTA['default'])
    return config.get(tipo_sensor)
