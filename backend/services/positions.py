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
        
        # Construimos el mensaje con un formato de tabla simple en Markdown
        message = "🏆 **Tabla de Posiciones - Zona 2**\n"
        message += "\n`Pos | Equipo          | Pts | PJ | DG`"
        message += "\n`--------------------------------------`"
        
        for p in positions_data:
            pos = str(p.get("position", "-")).ljust(3)
            # Acortamos el nombre si es muy largo para que no rompa la "tabla" visual
            name = p.get("team_name", "Equipo")[:15].ljust(15)
            pts = str(p.get("points", 0)).ljust(3)
            pj = str(p.get("played", 0)).ljust(2)
            dg = str(p.get("goal_diff", 0))
            
            message += f"\n`{pos} | {name} | {pts} | {pj} | {dg}`"
            
        message += "\n\n_Datos actualizados desde Torneo Golden._"
        
        return {"success": True, "data": positions_data, "message": message}

    except Exception as e:
        return {"success": False, "message": f"Error técnico al leer posiciones: {str(e)}"}
