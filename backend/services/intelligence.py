import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"

def extract_intent(user_prompt: str, model: str = "llama3"):
    """
    Usa Ollama para clasificar el mensaje del usuario y devolver un JSON con la intención.
    """
    prompt_instructions = f"""
    Eres el asistente de Footbot. Tu objetivo es clasificar el mensaje del usuario.
    RESPONDE ÚNICAMENTE EN FORMATO JSON.
    Acciones posibles:
    - chat: Charla normal, preguntas de información.
    - delete_debt: Si se pide perdonar, borrar o cancelar una deuda.
    - update_debt: Marcamos un pago como realizado o modificamos montos.
    - upload_attendance: Si se pide subir la lista de asistencia.
    - add_debt: Si se pide agregar una deuda.
    - add_player: Si se pide agregar un jugador.
    - delete_player: Si se pide eliminar un jugador.
    - update_player: Si se pide modificar un jugador o agregarle datos.
    - get_player: Si se pide obtener información de un jugador.
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