import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = None
if api_key and api_key != "CHAVEAQKUI" and len(api_key.strip()) > 0:
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Erro ao inicializar o cliente do Gemini: {e}")

def get_media_quebras_equipamentos(name):
    if not client:
        return f"IA indisponível. Detalhes de quebra para o equipamento: {name}."
        
    prompt = f"""
    Você é um analista de dados especializado em manutenção industrial.
    Receba os dados de quebra de equipamentos e calcule para o equipamento '{name}':
    1. Tempo médio de quebra
    2. Equipamento que mais quebra
    3. Quais tecnicos mais fazem manutencao
    
    Forneça uma descrição analítica resumida e clara sobre este equipamento.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"Erro ao gerar a descrição do equipamento '{name}': {e}"