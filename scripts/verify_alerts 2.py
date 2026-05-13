import os
import django
import sys

# Configuração do ambiente Django
# Absolute path logic
BASE_DIR = r"c:\Code\Aluno\P.I-PlataformaManuntencaoWeb"
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from telemetria.models import Sensor, Telemetria
from alertas.models import Alerta
from telemetria.config_alertas import LIMITES_ALERTA

def test_automated_alert():
    print("="*50)
    print("TESTE DE ALERTA AUTOMATIZADO")
    print("="*50)

    # 1. Pegar um sensor de temperatura
    sensor = Sensor.objects.filter(tipo_sensor='temperatura').first()
    if not sensor:
        print("[ERRO] Nenhum sensor de temperatura encontrado. Popule o banco primeiro.")
        return

    equipamento = sensor.equipamento
    tipo_eq = equipamento.tipo
    
    # Pegar o limite configurado
    from telemetria.config_alertas import obter_limite
    limite = obter_limite(tipo_eq, 'temperatura')
    valor_anomalo = limite + 10.0

    print(f"Equipamento: {equipamento.nome} ({tipo_eq})")
    print(f"Tipo Sensor: {sensor.tipo_sensor}")
    print(f"Limite Configurado: {limite}")
    
    # Contar alertas antes
    qtd_antes = Alerta.objects.filter(equipamento=equipamento).count()

    print(f"Inserindo Valor Anômalo: {valor_anomalo}...")

    # 2. Criar telemetria que deve disparar o signal
    Telemetria.objects.create(sensor=sensor, valor=valor_anomalo)

    # 3. Verificar se um novo alerta foi criado
    qtd_depois = Alerta.objects.filter(equipamento=equipamento).count()

    if qtd_depois > qtd_antes:
        novo_alerta = Alerta.objects.filter(equipamento=equipamento).order_by('-id').first()
        print(f"[SUCESSO] Alerta gerado automaticamente!")
        print(f"Título: {novo_alerta.tipo_alerta}")
        print(f"Nível: {novo_alerta.nivel}")
        print(f"Descrição: {novo_alerta.descricao}")
    else:
        print(f"[FALHA] O alerta não foi gerado. Qtd antes: {qtd_antes}, Qtd depois: {qtd_depois}")

    print("="*50)

if __name__ == "__main__":
    test_automated_alert()
