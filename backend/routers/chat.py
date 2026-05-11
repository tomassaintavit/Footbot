from fastapi import APIRouter, HTTPException
from database import supabase
from schemas import ChatRequest
from services import intelligence, debts, players, attendance, matches, positions, logs


router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/")
async def chat(request: ChatRequest):
    # 1. Identificamos quién es el usuario
    user_query = supabase.table("players").select("*").eq("auth_id", request.auth_id).execute()
    if not user_query.data:
        raise HTTPException(status_code=404, detail="No se encontró el jugador que mando mensaje en la base de datos.")
    user = user_query.data[0]

    # 2. Le pedimos al servicio de inteligencia que clasifique el mensaje
    intent = intelligence.extract_intent(request.prompt, request.model, request.history)
    action = intent.get("action")
    params = intent.get("params", {})
    response_text = intent.get("response", "Lo siento, no pude procesar eso.")

    # 3. Seguridad: Acciones críticas solo para administradores
    critical_actions = ["delete_debt", "update_debt", "add_debt", "add_player", "delete_player", "update_player"]
    if action in critical_actions and not user.get("is_admin"):
        return {"chat": "⛔ No tienes permisos de administrador para realizar esta acción."}

    # 4. Router de Ejecución (El cerebro del bot)
    if action == "delete_debt":
        result = debts.delete_debt_by_player_name(params.get("player_name"))
        if result.get("success"):
            logs.create_log(user["id"], "delete_debt", f"Eliminó deudas de {params.get('player_name')}")
        return {"chat": result["message"]}

    elif action == "get_help":
        help_message = """🤖 **¡Soy Footbot! Aquí tienes lo que puedo hacer por el equipo:**

⚽ **Partidos**
- *¿Cuándo jugamos?*: Te digo el próximo partido.
- *Tabla de posiciones*: Muestro cómo vamos en el torneo.

📝 **Asistencia**
- *¿Quiénes van?*: Lista de confirmados para el próximo partido.
- *Subir lista*: Pega la lista de WhatsApp y yo la proceso.

💸 **Deudas**
- *¿Quién debe plata?*: Lista de deudores y montos totales.

👤 **Jugadores**
- *Ver lista de jugadores*: Todos los registrados.
- *Información de [Nombre]*: Goles, tarjetas y estado de suspensión.

¡Pregúntame lo que necesites!"""
        return {"chat": help_message}

    elif action == "get_debts_list":

        result = debts.get_debts_list()
        return {"chat": result["message"]}

    elif action in ["add_debt", "update_debt"]:

        amount = params.get("amount", 0)
        result = debts.create_debt_by_player_name(params.get("player_name"), amount)
        if result.get("success"):
            logs.create_log(user["id"], action, f"Añadió/Actualizó deuda de ${amount} a {params.get('player_name')}")
        return {"chat": result["message"]}
    elif action in ["add_player"]:
        name = params.get("player_name")
        result = players.create_player(name)
        if result.get("success"):
            logs.create_log(user["id"], "add_player", f"Creó al jugador {name}")
        return {"chat": result["message"]}
    elif action in ["delete_player"]:
        name = params.get("player_name")
        result = players.delete_player(name)
        if result.get("success"):
            logs.create_log(user["id"], "delete_player", f"Eliminó al jugador {name}")
        return {"chat": result["message"]}
    elif action == "update_player":
        name = params.get("player_name")
        result = players.update_player(
            name=name,
            nickname=params.get("nickname"),
            dni=params.get("dni"),
            email=params.get("email"),
            goals=params.get("goals"),
            yellow_cards=params.get("yellow_cards"),
            red_cards=params.get("red_cards"),
            is_suspended=params.get("is_suspended")
        )
        if result.get("success"):
            logs.create_log(user["id"], "update_player", f"Actualizó datos de {name}")
        return {"chat": result["message"]}
    elif action in ["get_player"]:
        name = params.get("player_name")
        result = players.get_player(name)
        return {"chat": result["message"]}
    elif action == "upload_attendance":
        result = attendance.process_attendance_list(request.prompt, request.model)
        return {"chat": result["message"]}
    elif action == "get_players_list":
        result = players.get_players_list()
        return {"chat": result["message"]}
    elif action == "get_next_matches":
        result = matches.get_next_matches()
        return {"chat": result["message"]}
    elif action == "get_attendance_list":
        result = attendance.get_match_attendance()
        return {"chat": result["message"]}
    elif action == "get_positions_table":
        result = positions.get_positions_table()
        return {"chat": result["message"]}



    # Si es una charla normal o no detectamos nada especial, devolvemos lo que dijo Ollama
    return {"chat": response_text}


