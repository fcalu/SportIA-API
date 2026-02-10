def build_prompt(event, market, prob, ev):
    return f'''
Actúa como analista cuantitativo deportivo (WSPM Model).
No inventes datos.

EVENTO: {event}
MERCADO: {market}
PROBABILIDAD: {prob}
EV: {ev}

Devuelve:
- Riesgos
- Argumentos cuantitativos
- Conclusión clara
'''
