from openai import OpenAI
from app.core.config import settings

# Creamos el cliente una sola vez fuera de la función para mayor eficiencia
client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

def run_llm(user_prompt: str, system_prompt: str = None):

    if not client:
        return "LLM deshabilitado (sin API key)"

    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    else:
        # Un prompt de sistema más corto ahorra tokens de entrada (dinero)
        messages.append({
            "role": "system",
            "content": "Eres un analista de apuestas técnico y breve. Ve al grano."
        })

    messages.append({"role": "user", "content": user_prompt})

    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.35,
            max_tokens=250, # 🛡️ Límite para que no gaste de más en respuestas largas
            timeout=15      # Evita que el bot se quede "colgado" si OpenAI tarda
        )
        return r.choices[0].message.content
    except Exception as e:
        # Si falla la cuota o el saldo, devolvemos un mensaje amigable en lugar de romper el código
        print(f"❌ Error en OpenAI: {str(e)}")
        return "Análisis no disponible (límite de cuota o saldo). Revisa los datos numéricos arriba."