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
