from database import supabase

def get_positions_table():
    """
    Consulta la tabla de posiciones en Supabase y devuelve un mensaje formateado.
    """
    try:
        # Consultamos la tabla de posiciones ordenada por el campo 'position'
        query = supabase.table("positions").select("*").order("position").execute()
        positions_data = query.data
        
        if not positions_data:
            return {
                "success": True, 
                "data": [], 
                "message": "📊 La tabla de posiciones aún no tiene datos cargados. ¡Pronto habrá novedades!"
            }
        
        message = "🏆 <b>Tabla de Posiciones - Zona 2</b>\n<pre>\n"
        message += f"{'#'.ljust(3)} {'Equipo'.ljust(15)} {'Pts'.rjust(4)} {'PJ'.rjust(3)} {'DG'.rjust(4)}\n"
        message += f"{'─'*3} {'─'*15} {'─'*4} {'─'*3} {'─'*4}\n"

        for p in positions_data:
            pos = str(p.get("position", "-")).ljust(3)
            name = p.get("team_name", "Equipo")[:15].ljust(15)
            pts = str(p.get("points", 0)).rjust(4)
            pj = str(p.get("played", 0)).rjust(3)
            dg = str(p.get("goal_diff", 0)).rjust(4)

            message += f"{pos} {name} {pts} {pj} {dg}\n"

        message += "</pre>\n<i>Datos actualizados desde Torneo Golden.</i>"
        
        return {"success": True, "data": positions_data, "message": message}

    except Exception as e:
        return {"success": False, "message": f"Error técnico al leer posiciones: {str(e)}"}
