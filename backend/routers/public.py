from fastapi import APIRouter
from database import supabase
from datetime import datetime, timezone

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/players/top-scorers")
async def get_top_scorers():
    response = supabase.table("players").select("name,goals").order("goals", desc=True).limit(3).execute()
    return response.data


@router.get("/players/top-yellow")
async def get_top_yellow():
    response = supabase.table("players").select("name,yellow_cards").order("yellow_cards", desc=True).limit(3).execute()
    return response.data


@router.get("/players/top-red")
async def get_top_red():
    response = supabase.table("players").select("name,red_cards").order("red_cards", desc=True).limit(3).execute()
    return response.data


@router.get("/matches/last")
async def get_last_match():
    now = datetime.now(timezone.utc).isoformat()
    response = supabase.table("matches").select("*").lt("match_date", now).order("match_date", desc=True).limit(1).execute()
    return response.data[0] if response.data else None


@router.get("/matches/upcoming")
async def get_upcoming_matches():
    now = datetime.now(timezone.utc).isoformat()
    response = supabase.table("matches").select("*").gte("match_date", now).order("match_date").limit(3).execute()
    return response.data


@router.get("/positions")
async def get_positions():
    response = supabase.table("positions").select("*").order("position").execute()
    return response.data
