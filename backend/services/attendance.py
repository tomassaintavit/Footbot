import json
import requests
from datetime import datetime
from database import supabase

def process_attendance_list(text: str, model: str = "llama3"):
    """
    Toma un bloque de texto, identifica el partido, mapea los jugadores y los registra.
    """
    try:
        # 1. Obtener contexto de partidos próximos
        matches_query = supabase.table("matches")\
            .select("*")\
            .gte("match_date", datetime.now().isoformat())\
            .order("match_date")\
            .limit(3).execute()
        
        matches_context = ""
        for m in matches_query.data:
            matches_context += f"- ID: {m['id']} | Fecha: {m['match_date']} | Rival: {m['opponent']}\n"

        # 2. Obtener lista de jugadores para mapeo
        players_query = supabase.table("players").select("id, name, nickname").execute()
        players_context = [{"id": p["id"], "name": p["name"], "nickname": p["nickname"]} for p in players_query.data]

        # 3. Prompt para el LLM
        prompt = f"""
        Eres el asistente de "Buen Palo". Extrae los jugadores que confirman y el partido.
        
        Jugadores: {json.dumps(players_context)}
        Partidos: {matches_context}
        Texto: "{text}"
        
        RESPONDE SOLO JSON:
        {{
            "match_id": "ID",
            "players": [{"id": "id-o-null", "name_detected": "nombre"}]
        }}
        """
        
        response = requests.post("http://localhost:11434/api/generate", 
            json={"model": model, "prompt": prompt, "stream": False, "format": "json"})
        response.raise_for_status()
        
        data = json.loads(response.json()["response"])
        match_id = data.get("match_id")
        detected_players = data.get("players", [])

        if not match_id or match_id == "null":
            if matches_query.data:
                match_id = matches_query.data[0]["id"]
            else:
                return {"success": False, "message": "No hay partidos programados."}

        added_count = 0
        for p in detected_players:
            p_id = p.get("id")
            if p_id and p_id != "null":
                existing = supabase.table("attendance").select("*")\
                    .eq("match_id", match_id).eq("player_id", p_id).execute()
                
                if not existing.data:
                    supabase.table("attendance").insert({
                        "match_id": match_id,
                        "player_id": p_id,
                        "status": "confirmado"
                    }).execute()
                    added_count += 1

        return {
            "success": True, 
            "message": f"✅ Se anotaron {added_count} jugadores para el partido.",
            "match_id": match_id
        }

    except Exception as e:
        return {"success": False, "message": f"Error en el servicio de asistencia: {str(e)}"}
