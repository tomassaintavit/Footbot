from fastapi import APIRouter, HTTPException
import requests
from schemas import AttendanceRequest
from datetime import datetime
import json
from database import supabase

router = APIRouter(prefix="/attendance", tags=["attendance"])

# ==========================================
# FASE 5: Carga de Asistencia Mejorada
# ==========================================

@router.post("/upload")
async def upload_attendance(request: AttendanceRequest):
    # TODO (Fase 8): Identificar al jugador que envía la lista
    # 1. Buscar en Supabase el jugador con auth_id == request.auth_id
    user_query = supabase.table("players").select("*").eq("auth_id", request.auth_id).execute()
    if len(user_query.data) == 0:
        raise HTTPException(status_code=404, detail="No se encontró el jugador.")
    user = user_query.data[0]
    # 2. (Opcional) Registrar quién subió la lista para auditoría.
    # Nota: Aquí no bloqueamos si no es admin, ¡cualquiera puede confirmar asistencia!
    try:
        # 1. Obtener contexto de partidos para que el LLM elija el correcto
        matches_query = supabase.table("matches")\
            .select("*")\
            .gte("match_date", datetime.now().isoformat())\
            .order("match_date")\
            .limit(3)\
            .execute()
        
        available_matches = matches_query.data
        matches_context = ""
        for m in available_matches:
            matches_context += f"- ID: {m['id']} | Fecha: {m['match_date']} | Rival: {m['opponent']}\n"

        # 2. Obtener lista de jugadores para mapeo por nombre o apodo
        players_query = supabase.table("players").select("id, name, nickname").execute()
        available_players = players_query.data
        players_context = [{"id": p["id"], "name": p["name"], "nickname": p["nickname"]} for p in available_players]

        prompt = f"""
        Eres un asistente del equipo de fútbol "Buen Palo". 
        Tu objetivo es extraer la lista de jugadores que confirman asistencia y determinar a qué partido se refieren.
        
        Jugadores de referencia (pueden usar nombre o nickname):
        {json.dumps(players_context)}

        Partidos disponibles:
        {matches_context}
        
        Texto del usuario: "{request.text}"
        
        Instrucciones:
        1. Limpia los nombres de los jugadores (quita números, puntos, etc).
        2. Los jugadores suelen anotarse con su apodo (nickname). Compáralos con la lista de referencia. Puede que los apodos esten mal escritos si son parecidos a los de un jugador sugiere ese jugador.
        3. Identifica cuál de los partidos disponibles coincide mejor (por rival o fecha).
        4. Si el jugador no está en la lista de referencia, devuélvelo con "id": null.
        5. Devuelve un JSON estrictamente con esta estructura:
           {{
             "match_id": "ID_DEL_PARTIDO_ELEGIDO",
             "opponent_detected": "nombre del rival",
             "players": [
                {{"id": "id-o-null", "name_detected": "nombre escrito"}}
             ]
           }}
        """
      
        # Llamada a Ollama
        response = requests.post("http://localhost:11434/api/generate", 
            json={"model": request.model, "prompt": prompt, "stream": False, "format": "json" })
        response.raise_for_status()
        
        parsed_data = json.loads(response.json()["response"])
        players_data = parsed_data.get("players", [])
        match_id = parsed_data.get("match_id")
        
        processed_players = []

        # 3. Procesar jugadores y asegurar que existan en DB
        # Extraemos solo los IDs válidos actuales para verificar
        valid_player_ids = [p["id"] for p in available_players]

        for p_info in players_data:
            p_id = p_info.get("id")
            name_detected = p_info.get("name_detected")

            # VALIDACIÓN: Si el ID no está en nuestra lista de disponibles, lo tratamos como null
            # Esto evita que la IA invente IDs (hallucinaciones)
            if p_id not in valid_player_ids:
                p_id = None

            if not p_id or p_id == "null":
                # Si el LLM no encontró el ID o es inválido, buscamos por nombre o apodo en nuestra lista local primero
                # Esto es más rápido que consultar la DB por cada uno
                match_local = next((p for p in available_players if p["name"].lower() == name_detected.lower() or (p["nickname"] and p["nickname"].lower() == name_detected.lower())), None)
                
                if match_local:
                    p_id = match_local["id"]
                else:
                    # Si no está en la lista local tampoco, intentamos buscar en la DB (por si se creó recién)
                    existing = supabase.table("players").select("*").eq("name", name_detected).execute()
                    if len(existing.data) == 0:
                        new_player = supabase.table("players").insert({"name": name_detected}).execute()
                        p_id = new_player.data[0]["id"]
                    else:
                        p_id = existing.data[0]["id"]
            
            processed_players.append({"id": p_id, "name": name_detected})

        # 4. Validar el partido seleccionado
        if not match_id or match_id == "null":
            # Si no se detectó partido, usamos el más próximo como fallback
            if len(available_matches) > 0:
                match_id = available_matches[0]["id"]
                match_info = available_matches[0]
            else:
                raise HTTPException(status_code=404, detail="No hay partidos programados en la base de datos.")
        else:
            match_info = next((m for m in available_matches if str(m["id"]) == str(match_id)), 
                              available_matches[0] if available_matches else None)

        if not match_info:
            raise HTTPException(status_code=404, detail="No se pudo encontrar el partido especificado.")

        # 5. Registrar la asistencia en Supabase
        for p in processed_players:
            # Evitar duplicados por partido
            existing_att = supabase.table("attendance").select("*")\
                .eq("match_id", match_id).eq("player_id", p["id"]).execute()
            
            if len(existing_att.data) == 0:
                supabase.table("attendance").insert({
                    "match_id": match_id,
                    "player_id": p["id"],
                    "status": "confirmado"
                }).execute()

        return {
            "status": "success",
            "match": match_info,
            "players_added": len(processed_players)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar asistencia: {str(e)}")