import requests
import json
import os

OLLAMA_URL = "http://localhost:11434/api/generate"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def extract_intent(user_prompt: str, model: str = "llama3", history: list = []):
    """
    Usa Ollama (local) o Groq (nube) para clasificar el mensaje del usuario.
    Si existe GROQ_API_KEY en el entorno, usará Groq para el despliegue en la web.
    """
    groq_key = os.getenv("GROQ_API_KEY")
    
    # Construimos el historial como texto legible
    history_text = ""
    for msg in history[-10:]:
        role = "Usuario" if msg.get("role") == "user" else "Footbot"
        history_text += f"{role}: {msg.get('text', '')}\n"

    system_prompt = f"""
    Eres el asistente de Footbot. Tu objetivo es clasificar el mensaje del usuario y responder ÚNICAMENTE en formato JSON.
    
    Acciones posibles:
    - chat: Charla normal, preguntas de información.
    - delete_debt: Si se pide perdonar, borrar o cancelar una deuda.
    - get_help: Si el usuario pregunta qué puede hacer el bot, qué comandos hay o pide ayuda.
    - get_debts_list: Si se pide ver quiénes deben, la lista de deudores o cuánto debe el equipo en total.
    - update_debt: Marcamos un pago como realizado o modificamos montos.
    - upload_attendance: Si se pide subir la lista de asistencia.
    - add_debt: Si se pide agregar una deuda.
    - add_player: Si se pide agregar un jugador.
    - delete_player: Si se pide eliminar un jugador.
    - update_player: Si se pide modificar un jugador o agregarle datos.
    - get_player: Si se pide obtener información de un jugador.
    - get_players_list: Si se pide obtener una lista de jugadores.
    - get_next_matches: Si se pide obtener los próximos partidos.
    - get_attendance_list: Si se pide ver quiénes están anotados o confirmados para el partido.
    - get_positions_table: Si se pide ver la tabla de posiciones del torneo.

    {f'Conversación previa:{chr(10)}{history_text}' if history_text else ''}
    Texto del usuario: "{user_prompt}"
    
    Responde un JSON válido con esta estructura:
    {{
        "action": "nombre_accion",
        "response": "texto_amigable",
        "params": {{ "player_name": "...", "amount": 0, ... }}
    }}
    """

    try:
        if groq_key:
            # --- Lógica para GROQ (Producción) ---
            response = requests.post(GROQ_URL, 
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile", 
                    "messages": [
                        {"role": "system", "content": "Eres un asistente que solo responde en JSON."},
                        {"role": "user", "content": system_prompt}
                    ],
                    "response_format": {"type": "json_object"}
                }
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return json.loads(content)


        else:
            # --- Lógica para OLLAMA (Local) ---
            response = requests.post(OLLAMA_URL, 
                json={
                    "model": model, 
                    "prompt": system_prompt, 
                    "stream": False,
                    "format": "json"
                }
            )
            response.raise_for_status()
            return json.loads(response.json()["response"])
            
    except Exception as e:
        return {
            "action": "chat", 
            "response": f"Lo siento, tuve un problema técnico: {str(e)}",
            "params": {}
        }