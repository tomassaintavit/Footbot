from database import supabase 
from datetime import datetime 

def get_next_matches():
    try:
        # Obtenemos la fecha actual en formato ISO para comparar con la DB (que suele ser string)
        today_iso = datetime.now().date().isoformat()
        
        # Consultamos los partidos cuya fecha sea hoy o futura, ordenados por fecha
        query = supabase.table("matches").select("*").gte("match_date", today_iso).order("match_date").execute()
        next_matches = query.data
        
        if not next_matches:
            return {"success": True, "data": [], "message": "📅 No hay partidos programados próximamente."}
        
        message = "🗓️ **Próximos Partidos:**\n"
        for m in next_matches:
            # Formateamos la fecha si es posible (asumiendo YYYY-MM-DD)
            try:
                date_obj = datetime.strptime(m["match_date"], "%Y-%m-%d")
                friendly_date = date_obj.strftime("%d/%m (%A)") # Ej: 28/04 (Tuesday)
            except:
                friendly_date = m["match_date"]

            opponent = m.get("opponent", "Rival por confirmar")
            field = m.get("field") or m.get("location") or "Cancha por confirmar"
            hour = m.get("match_time") or ""
            
            message += f"\n⚽ **vs {opponent}**"
            message += f"\n📅 {friendly_date} {hour}"
            message += f"\n📍 {field}\n"
            
        return {"success": True, "data": next_matches, "message": message}
    except Exception as e:
        return {"success": False, "message": f"Error al obtener los próximos partidos: {str(e)}"}