from database import supabase

def create_player(name: str):
    
    try:
        supabase.table("players").insert({
            "name": name,
            "nickname": None,
            "dni": None,
            "email": None,
            "goals": 0,
            "yellow_cards": 0,
            "red_cards": 0,
            "is_suspended": False,
            "suspension_reason": None,
            "is_admin": False,
            "auth_id": None
        }).execute()
        return {"success": True, "message": f"Jugador {name} creado exitosamente."}
    except Exception as e:
        return {"success": False, "message": f"Error al crear el jugador: {str(e)}"}
    

def delete_player(name: str):
    try:
        supabase.table("players").delete().eq("name", name).execute()
        return {"success": True, "message": f"Jugador {name} eliminado exitosamente."}
    except Exception as e:
        return {"success": False, "message": f"Error al eliminar el jugador: {str(e)}"}
    
def update_player(name: str, **kwargs):
    """
    Actualiza de forma inteligente cualquier campo de un jugador.
    **kwargs permite pasarle nickname, dni, email, goals, yellow_cards, etc.
    """
    try:
        # 1. Filtramos solo los campos que no son None
        update_data = {k: v for k, v in kwargs.items() if v is not None}

        if not update_data:
            return {"success": False, "message": "No se proporcionaron datos para actualizar."}

        # 2. Buscamos al jugador por nombre (insensible a mayúsculas)
        check_player = supabase.table("players").select("id").ilike("name", name).execute()
        
        if not check_player.data:
            return {"success": False, "message": f"No se encontró al jugador '{name}'."}
        
        player_id = check_player.data[0]["id"]
        
        # 3. Ejecutamos la actualización
        result = supabase.table("players").update(update_data).eq("id", player_id).execute()

        if result.data:
            return {"success": True, "message": f"✅ Perfil de {name} actualizado: {', '.join(update_data.keys())}."}
        return {"success": False, "message": "No se pudo realizar la actualización."}

    except Exception as e:
        return {"success": False, "message": f"Error técnico en el update: {str(e)}"}
    
def get_player(name: str):
    try:
        # 1. Buscamos al jugador
        player_query = supabase.table("players").select("*").ilike("name", name).execute()
        
        if not player_query.data:
            return {"success": False, "message": f"🔍 No encontré a ningún jugador llamado '{name}'."}
        
        player = player_query.data[0]
        player_id = player["id"]

        # 2. Consultamos sus deudas y calculamos el total
        debts_query = supabase.table("debts").select("amount").eq("player_id", player_id).execute()
        total_debt = sum(d["amount"] for d in debts_query.data) if debts_query.data else 0
        
        # 3. Construimos la ficha técnica mejorada
        info = f"👤 Ficha de {player['name']}:\n"
        info += f"🔹 Apodo: {player.get('nickname') or '---'}\n"
        info += f"🔹 DNI: {player.get('dni') or '---'}\n"
        info += f"🔹 Goles: {player.get('goals', 0)}\n"
        info += f"🔹 Amarillas: {player.get('yellow_cards', 0)}\n"
        info += f"🔹 Suspendido: {'SÍ 🔴' if player.get('is_suspended') else 'NO 🟢'}\n"
        
        # Agregamos la información de deuda
        if total_debt > 0:
            info += f"💰 Deuda Total: ${total_debt} ⚠️"
        else:
            info += f"💰 Deuda Total: Sin deudas ✅"
        
        return {"success": True, "data": player, "message": info}

    except Exception as e:
        return {"success": False, "message": f"Error al obtener jugador: {str(e)}"}

