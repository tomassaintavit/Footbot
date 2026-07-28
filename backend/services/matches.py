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
        
        message = "🗓️ <b>Próximos Partidos</b>\n<pre>\n"
        for m in next_matches:
            raw_date = (m.get("match_date") or "")[:10]
            try:
                date_obj = datetime.strptime(raw_date, "%Y-%m-%d")
                friendly_date = date_obj.strftime("%d/%m (%A)")
            except:
                friendly_date = raw_date

            opponent = m.get("opponent", "Rival por confirmar")[:22].ljust(22)
            field = (m.get("field") or m.get("location") or "Cancha por confirmar")[:15].ljust(15)
            hour = (m.get("match_time") or "").rjust(5)

            message += f"{friendly_date}  {hour}  vs {opponent}  {field}\n"
        message += "</pre>"
        return {"success": True, "data": next_matches, "message": message}
    except Exception as e:
        return {"success": False, "message": f"Error al obtener los próximos partidos: {str(e)}"}