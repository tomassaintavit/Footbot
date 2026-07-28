from database import supabase
from datetime import datetime


def get_next_matches():
    try:
        today_iso = datetime.now().date().isoformat()

        query = supabase.table("matches").select("*").gte("match_date", today_iso).order("match_date").execute()
        next_matches = query.data

        if not next_matches:
            return {"success": True, "data": [], "message": "📅 No hay partidos programados próximamente."}

        message = "🗓️ <b>Próximos Partidos</b>\n<pre>\n"
        for m in next_matches:
            raw = (m.get("match_date") or "")
            try:
                dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                friendly_date = dt.strftime("%d/%m (%A)")
                hour = dt.strftime("%H:%M").rjust(5)
            except:
                friendly_date = raw[:10]
                hour = "".rjust(5)

            opponent = m.get("opponent", "Rival por confirmar")[:22].ljust(22)
            field = (m.get("field") or m.get("location") or "Cancha por confirmar")[:15].ljust(15)

            message += f"{friendly_date}  {hour}  vs {opponent}  {field}\n"
        message += "</pre>"
        return {"success": True, "data": next_matches, "message": message}
    except Exception as e:
        return {"success": False, "message": f"Error al obtener los próximos partidos: {str(e)}"}