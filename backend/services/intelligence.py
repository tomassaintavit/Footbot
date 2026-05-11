import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"

def extract_intent(user_prompt: str, model: str = "llama3", history: list = []):
    """
    Usa Ollama para clasificar el mensaje del usuario y devolver un JSON con la intención.
    Recibe el historial de mensajes anteriores para dar contexto al LLM.
    """
    # Construimos el historial como texto legible para el LLM
    # Limitamos a los últimos 10 mensajes para no sobrecargar el contexto
    history_text = ""
    for msg in history[-10:]:
        role = "Usuario" if msg.get("role") == "user" else "Footbot"
        history_text += f"{role}: {msg.get('text', '')}\n"

    prompt_instructions = f"""
    Eres el asistente de Footbot. Tu objetivo es clasificar el mensaje del usuario.
    RESPONDE ÚNICAMENTE EN FORMATO JSON.
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
    - get_positions_table: Si se pide ver la tabla de posiciones del torneo o cómo va el equipo.

    {f'Conversación previa (para contexto):{chr(10)}{history_text}' if history_text else ''}
    Texto del usuario: "{user_prompt}"
    Formato de respuesta (JSON):
    {{
        "action": "nombre_de_la_accion",
        "response": "Respuesta de texto amigable para el jugador",
        "params": {{ 
            "player_name": "nombre si aplica", 
            "amount": 0, 
            "nickname": "apodo si aplica", 
            "dni": "DNI si aplica", 
            "email": "email si aplica"
        }}
    }}
    """
    
    try:
        response = requests.post(OLLAMA_URL, 
            json={
                "model": model, 
                "prompt": prompt_instructions, 
                "stream": False,
                "format": "json"
            }
        )
        response.raise_for_status()
        
        # Convertimos el texto que devuelve Ollama en un diccionario de Python
        return json.loads(response.json()["response"])
        
    except Exception as e:
        # Si algo falla, devolvemos una respuesta de chat básica con el error
        return {
            "action": "chat", 
            "response": f"Lo siento, tuve un problema técnico: {str(e)}",
            "params": {}
        }