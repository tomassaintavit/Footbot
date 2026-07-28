from database import supabase

def delete_debt_by_player_name(player_name: str):
    """
    Busca al jugador por su nombre o apodo y elimina sus registros en la tabla de deudas.
    """
    try:
        # 1. Buscar al jugador en Supabase (por nombre o nickname)
        # Nota: Usamos .ilike para que no importe si es mayúscula o minúscula
        player_query = supabase.table("players")\
            .select("id, name")\
            .or_(f"name.ilike.%{player_name}%,nickname.ilike.%{player_name}%")\
            .execute()
        if not player_query.data:
            return {"success": False, "message": f"No encontré a ningún jugador que se llame '{player_name}'."}
        # Tomamos el primer jugador encontrado
        player = player_query.data[0]
        player_id = player["id"]
        # 2. Eliminar las deudas de ese jugador
        delete_query = supabase.table("debts")\
            .delete()\
            .eq("player_id", player_id)\
            .execute()
        return {
            "success": True, 
            "message": f"¡Listo! Se eliminaron las deudas de {player['name']}."
        }
    except Exception as e:
        return {"success": False, "message": f"Error al borrar la deuda: {str(e)}"}
    
def create_debt_by_player_name(player_name: str, amount: float):
    """
    Busca al jugador y le asigna una nueva deuda en Supabase.
    """
    try:
        # 1. Buscar al jugador
        player_query = supabase.table("players")\
            .select("id, name")\
            .or_(f"name.ilike.%{player_name}%,nickname.ilike.%{player_name}%")\
            .execute()

        if not player_query.data:
            return {"success": False, "message": f"No encontré a '{player_name}' para asignarle la deuda."}

        player = player_query.data[0]
        
        # 2. Insertar la nueva deuda
        supabase.table("debts").insert({
            "player_id": player["id"],
            "amount": amount
        }).execute()

        return {
            "success": True, 
            "message": f"✅ Se cargó una deuda de ${amount} para {player['name']}."
        }

    except Exception as e:
        return {"success": False, "message": f"Error al crear la deuda: {str(e)}"}

def get_debts_list():
    """
    Consulta la tabla de deudas para obtener todos los registros no pagados,
    los agrupa por jugador y devuelve un mensaje formateado.
    """
    try:
        # 1. Consultar deudas pendientes (is_paid = False) con join a players
        query = supabase.table("debts")\
            .select("amount, players(name, nickname)")\
            .eq("is_paid", False)\
            .execute()
        
        debts_data = query.data
        
        if not debts_data:
            return {
                "success": True, 
                "message": "✅ <b>¡Buenas noticias!</b> No hay deudas pendientes en el equipo."
            }
        
        # 2. Agrupar montos por jugador
        # Usamos un diccionario para sumar deudas si un jugador tiene varias
        summary = {}
        for d in debts_data:
            player_info = d.get("players")
            if player_info:
                name = player_info.get("name") or player_info.get("nickname") or "Jugador sin nombre"
                amount = d.get("amount", 0)
                summary[name] = summary.get(name, 0) + amount
        
        message = "💸 <b>Deudas Pendientes</b>\n<pre>\n"
        total_team_debt = 0

        name_width = max(len(n) for n in summary.keys()) if summary else 10
        name_width = max(name_width, 10)

        message += f"{'Jugador'.ljust(name_width)}  {'Deuda':>10}\n"
        message += f"{'─' * name_width}  {'─' * 10}\n"

        for player in sorted(summary.keys()):
            amount = summary[player]
            message += f"{player.ljust(name_width)}  ${amount:>8,.0f}\n"
            total_team_debt += amount

        message += f"{'─' * name_width}  {'─' * 10}\n"
        message += f"{'Total'.ljust(name_width)}  ${total_team_debt:>8,.0f}\n"
        message += "</pre>"
        
        return {"success": True, "message": message}
        
    except Exception as e:
        return {"success": False, "message": f"Error al obtener la lista de deudas: {str(e)}"}

