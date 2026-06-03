from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Telemetria
from alertas.models import Alerta


@receiver(post_save, sender=Telemetria)
def checar_limites_telemetria(sender, instance, created, **kwargs):
    """
    Sistema Preditivo de Alertas — dispara automaticamente a cada nova leitura de sensor.
    As Ordens de Serviço agora são geradas pelo sinal de post_save do modelo Alerta,
    garantindo que alertas manuais também gerem O.S.
    """
    if not created:
        return

    sensor = instance.sensor
    if not sensor.ativo:
        return

    valor = instance.valor
    equipamento = sensor.equipamento
    limite = sensor.limite_alerta

    if limite is None or limite <= 0:
        return

    percentual = (valor / limite) * 100

    # Usa percentuais configuráveis do sensor, com fallback para os valores padrão.
    limite_baixo = sensor.limite_alerta_baixo_pct if sensor.limite_alerta_baixo_pct is not None else 70.0
    limite_medio = sensor.limite_alerta_medio_pct if sensor.limite_alerta_medio_pct is not None else 85.0
    limite_critico = sensor.limite_alerta_critico_pct if sensor.limite_alerta_critico_pct is not None else 100.0

    # Determina o nível pelo percentual do limite atingido
    if percentual >= limite_critico:
        nivel = 'critico'
    elif percentual >= limite_medio:
        nivel = 'medio'
    elif percentual >= limite_baixo:
        nivel = 'baixo'
    else:
        return  # Valor normal — nenhum alerta necessário

    tipo_alerta = f"Alerta de {sensor.get_tipo_display()}"

    # Deduplicação: busca alerta ativo do mesmo tipo no mesmo equipamento
    alerta_existente = Alerta.objects.filter(
        equipamento=equipamento,
        tipo_alerta=tipo_alerta,
        status='ativo'
    ).first()

    if alerta_existente:
        # Só atualiza se o nível piorou
        ordem_nivel = {'baixo': 1, 'medio': 2, 'critico': 3}
        if ordem_nivel[nivel] > ordem_nivel[alerta_existente.nivel]:
            alerta_existente.nivel = nivel
            alerta_existente.descricao = (
                f"Situação agravada em {equipamento.nome}. "
                f"Sensor de {sensor.get_tipo_display()} registrou "
                f"{valor}{sensor.unidade_medida} "
                f"({round(percentual, 1)}% do limite de {limite}{sensor.unidade_medida})."
            )
            alerta_existente.save() # Gatilho para o sinal de Alerta criar/atualizar O.S.
        return

    # Cria novo alerta
    alerta_descricao = (
        f"Anomalia detectada em {equipamento.nome}. "
        f"Sensor de {sensor.get_tipo_display()} registrou "
        f"{valor}{sensor.unidade_medida} "
        f"({round(percentual, 1)}% do limite de {limite}{sensor.unidade_medida})."
    )

    Alerta.objects.create(
        equipamento=equipamento,
        tipo_alerta=tipo_alerta,
        nivel=nivel,
        descricao=alerta_descricao
    ) # Gatilho para o sinal de Alerta criar O.S.
