from fastapi import APIRouter, HTTPException
from schemas import MatchSync
from database import supabase

router = APIRouter(prefix="/matches", tags=["matches"])

@router.post("/sync")
async def sync_match(match: MatchSync):
    """
    Sincroniza un partido oficial desde n8n.
    Si el partido ya existe (misma fecha y rival), lo actualiza.
    Si no, lo crea.
    """
    try:
        # Buscamos si ya existe un partido en esa fecha y contra ese rival
        existing = supabase.table("matches").select("*")\
            .eq("match_date", match.match_date)\
            .eq("opponent", match.opponent)\
            .execute()
        
        match_data = {
            "match_date": match.match_date,
            "opponent": match.opponent,
            "field": match.field,
            "category": match.category
        }

        if len(existing.data) > 0:
            # Actualizamos el existente
            response = supabase.table("matches")\
                .update(match_data)\
                .eq("id", existing.data[0]["id"])\
                .execute()
        else:
            # Insertamos uno nuevo
            response = supabase.table("matches").insert(match_data).execute()

        return {"status": "success", "data": response.data[0]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al sincronizar partido: {str(e)}")
