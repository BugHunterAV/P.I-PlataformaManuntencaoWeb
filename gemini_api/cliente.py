import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if len(api_key) > 0:
    client - genai.Client(api_key=api_key)
    
    
def get_media_quebras_equipamentos(name):
    
    prompt = """
    Você é um analista de dados especializado em manutenção industrial.
    Receba os dados de quebra de equipamentos e calcule:
    1. Tempo médio de quebra
    2. Equipamento que mais quebra
    3. Quais tecnicos mais fazem manutencao
"""
    prompt = prompt.format(name)    

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text