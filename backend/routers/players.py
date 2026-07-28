from fastapi import APIRouter, HTTPException
from schemas import Player, PlayerSync
from database import supabase

router = APIRouter(prefix="/players", tags=["players"])

PROTECTED_FIELDS = {"is_admin", "telegram_id", "auth_id"}

@router.post("/")
async def create_player(player: Player):
    try:
        response = supabase.table("players").insert({
            "name": player.name,
            "nickname": player.nickname,
            "dni": player.dni,
            "email": player.email
        }).execute()
        return {"player": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear el jugador: {str(e)}")

@router.post("/sync")
async def sync_player(player: PlayerSync):
    """
    Sincroniza un jugador desde la API oficial.
    Usa el DNI como clave para actualizar si ya existe.
    Nunca pisa campos protegidos (is_admin, telegram_id, auth_id).
    """
    try:
        query = supabase.table("players").select("*")
        if player.dni:
            query = query.eq("dni", player.dni)
        else:
            query = query.eq("name", player.name)

        existing = query.execute()

        player_data = player.model_dump(exclude=PROTECTED_FIELDS)

        if len(existing.data) > 0:
            response = supabase.table("players")\
                .update(player_data)\
                .eq("id", existing.data[0]["id"])\
                .execute()
        else:
            response = supabase.table("players").insert(player_data).execute()

        return {"status": "success", "data": response.data[0]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al sincronizar jugador: {str(e)}")
