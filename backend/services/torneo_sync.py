import logging
import httpx
from database import supabase
from services import torneo_api

logger = logging.getLogger(__name__)

PROTECTED_FIELDS = {"is_admin", "telegram_id", "auth_id"}


def _mapear_jugador(j: dict) -> dict:
    jug = j.get("jugador", {})
    nombre = jug.get("nombre", "")
    apellido = jug.get("apellido", "")
    full_name = f"{nombre} {apellido}".strip()

    sancionado = j.get("sancionado", False) or j.get("tieneSancionVigente", False) or j.get("inhabilitado", False)

    return {
        "name": full_name,
        "dni": str(jug.get("dni", "")) if jug.get("dni") else None,
        "email": jug.get("email"),
        "goals": j.get("goles", 0),
        "yellow_cards": j.get("amarillas", 0),
        "red_cards": j.get("rojas", 0),
        "is_suspended": sancionado,
        "suspension_reason": None,
    }


def sync_players() -> dict:
    inserted = 0
    updated = 0
    errors = 0

    try:
        jugadores = torneo_api.get_jugadores()
    except httpx.HTTPError as e:
        logger.error(f"Error al obtener jugadores de Torneo Golden: {e}")
        return {"success": False, "error": str(e)}

    for j in jugadores:
        try:
            player_data = _mapear_jugador(j)
            dni = player_data.get("dni")

            query = supabase.table("players").select("id")
            if dni:
                query = query.eq("dni", dni)
            else:
                query = query.eq("name", player_data["name"])

            existing = query.execute()

            if existing.data:
                supabase.table("players").update(player_data).eq("id", existing.data[0]["id"]).execute()
                updated += 1
            else:
                supabase.table("players").insert(player_data).execute()
                inserted += 1
        except Exception as e:
            logger.error(f"Error al sincronizar jugador: {e}")
            errors += 1

    return {"success": True, "inserted": inserted, "updated": updated, "errors": errors}


def sync_positions() -> dict:
    try:
        zonas = torneo_api.get_posiciones()
    except httpx.HTTPError as e:
        logger.error(f"Error al obtener posiciones de Torneo Golden: {e}")
        return {"success": False, "error": str(e)}

    if not zonas:
        return {"success": True, "inserted": 0, "message": "No hay posiciones disponibles (el torneo aún no comenzó)."}

    supabase.table("positions").delete().neq("id", 0).execute()

    rows = []
    for zona in zonas:
        for p in zona.get("posiciones", []):
            eq = p.get("equipo", {})
            rows.append({
                "position": p.get("pos"),
                "team_name": eq.get("nombre", ""),
                "points": p.get("puntos", 0),
                "played": p.get("pj", 0),
                "won": p.get("pg", 0),
                "drawn": p.get("pe", 0),
                "lost": p.get("pp", 0),
                "goals_for": p.get("gf", 0),
                "goals_against": p.get("gc", 0),
                "goal_diff": p.get("dg", 0),
            })

    if rows:
        supabase.table("positions").insert(rows).execute()

    return {"success": True, "inserted": len(rows)}


def sync_matches() -> dict:
    try:
        fechas = torneo_api.get_partidos()
    except httpx.HTTPError as e:
        logger.error(f"Error al obtener partidos de Torneo Golden: {e}")
        return {"success": False, "error": str(e)}

    synced = 0
    for fecha in fechas:
        match_date = fecha.get("fecha", "")[:10]
        for p in fecha.get("partidos", []):
            eq1 = p.get("equipo1", {})
            eq2 = p.get("equipo2", {})
            if eq1.get("_id") == torneo_api.EQUIPO_ID:
                opponent = eq2.get("nombre", "")
            elif eq2.get("_id") == torneo_api.EQUIPO_ID:
                opponent = eq1.get("nombre", "")
            else:
                continue

            match_data = {
                "match_date": match_date,
                "opponent": opponent,
                "field": p.get("cancha", {}).get("nombre"),
            }

            existing = supabase.table("matches").select("id").eq("match_date", match_date).eq("opponent", opponent).execute()

            if existing.data:
                supabase.table("matches").update(match_data).eq("id", existing.data[0]["id"]).execute()
            else:
                supabase.table("matches").insert(match_data).execute()
            synced += 1

    return {"success": True, "synced": synced}


def sync_all() -> dict:
    players = sync_players()
    positions = sync_positions()
    matches = sync_matches()

    return {
        "success": True,
        "players": players,
        "positions": positions,
        "matches": matches,
    }
