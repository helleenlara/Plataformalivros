# services/recomendador.py
import json
import google.generativeai as genai
from app.config import GEMINI_API_KEY

def gerar_perfil(dados_dict):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")
    chat = model.start_chat()

    prompt = f"""
Gere um perfil literário com base nas respostas abaixo:
{json.dumps(dados_dict, indent=2, ensure_ascii=False)}
"""

    response = chat.send_message(prompt.strip())
    return response.text
