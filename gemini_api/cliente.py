import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(override=True)


def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() == "" or api_key == "CHAVEAQKUI":
        return None

    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def is_gemini_available():
    return get_gemini_client() is not None


def generate_content(system_instruction, user_prompt, history=None, model_candidates=None, temperature=0.4):
    client = get_gemini_client()
    if not client:
        raise RuntimeError("A chave GEMINI_API_KEY não está configurada ou é inválida.")

    if model_candidates is None:
        model_candidates = [
            "gemini-3.5-flash",
            "gemini-2.5-flash",
            "gemini-flash-latest",
        ]

    contents = []
    if history:
        for item in history:
            role = "user" if item.get("role") == "user" else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=item.get("text", ""))]
                )
            )

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_prompt)]
        )
    )

    last_error = None
    for model_name in model_candidates:
        try:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=temperature,
            )
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
            return response.text, model_name
        except Exception as e:
            err_str = str(e)
            recoverable = (
                "503" in err_str or
                "UNAVAILABLE" in err_str or
                "ResourceExhausted" in err_str or
                "429" in err_str or
                "404" in err_str or
                "NOT_FOUND" in err_str or
                "not found" in err_str.lower()
            )
            last_error = e
            if recoverable:
                continue
            raise

    raise RuntimeError(f"Todos os modelos falharam. Erro: {last_error}")


def get_media_quebras_equipamentos(name):
    if not is_gemini_available():
        return f"IA indisponível. Detalhes de quebra para o equipamento: {name}."

    prompt = f"""
Você é um analista de dados especializado em manutenção industrial.
Receba os dados de quebra de equipamentos e calcule para o equipamento '{name}':
1. Tempo médio de quebra
2. Equipamento que mais quebra
3. Quais técnicos mais fazem manutenção

Forneça uma descrição analítica resumida e clara sobre este equipamento.
"""

    try:
        response_text, _ = generate_content(
            system_instruction="Você é um analista de manutenção industrial.",
            user_prompt=prompt,
        )
        return response_text
    except Exception as e:
        return f"Erro ao gerar a descrição do equipamento '{name}': {e}"
