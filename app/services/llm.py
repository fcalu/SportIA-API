from openai import OpenAI
from app.core.config import settings


def run_llm(user_prompt: str, system_prompt: str = None):

    if not settings.OPENAI_API_KEY:
        return "LLM deshabilitado (sin API key)"

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    else:
        messages.append({
            "role": "system",
            "content": "Eres un analista profesional de apuestas deportivas, claro, técnico y preciso."
        })

    messages.append({"role": "user", "content": user_prompt})

    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.35
    )

    return r.choices[0].message.content
