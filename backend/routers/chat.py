from fastapi import APIRouter, HTTPException
from database import supabase
from schemas import ChatRequest
from services import intelligence, debts

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/")
async def chat(request: ChatRequest):
    # 1. Identificamos quién es el usuario
    user_query = supabase.table("players").select("*").eq("auth_id", request.auth_id).execute()
    if not user_query.data:
        raise HTTPException(status_code=404, detail="No se encontró el jugador en la base de datos.")
    user = user_query.data[0]

    # 2. Le pedimos al servicio de inteligencia que clasifique el mensaje
    intent = intelligence.extract_intent(request.prompt, request.model)
    action = intent.get("action")
    params = intent.get("params", {})
    response_text = intent.get("response", "Lo siento, no pude procesar eso.")

    # 3. Seguridad: Acciones críticas solo para administradores
    critical_actions = ["delete_debt", "update_debt", "manage_player", "add_debt"]
    if action in critical_actions and not user.get("is_admin"):
        return {"chat": "⛔ No tienes permisos de administrador para realizar esta acción."}

    # 4. Router de Ejecución (El cerebro del bot)
    if action == "delete_debt":
        result = debts.delete_debt_by_player_name(params.get("player_name"))
        return {"chat": result["message"]}

    elif action in ["add_debt", "update_debt"]:
        amount = params.get("amount", 0)
        result = debts.create_debt_by_player_name(params.get("player_name"), amount)
        return {"chat": result["message"]}

    # Si es una charla normal o no detectamos nada especial, devolvemos lo que dijo Ollama
    return {"chat": response_text}


