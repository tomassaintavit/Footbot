from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import supabase

router = APIRouter(prefix="/api/admin", tags=["admin"])
security = HTTPBearer()


def _verify_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        auth_response = supabase.auth.get_user(credentials.credentials)
        auth_user = auth_response.user
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    player_query = supabase.table("players").select("*").eq("auth_id", auth_user.id).execute()
    if not player_query.data:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found in players")
    player = player_query.data[0]
    if not player.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an admin")
    return player


@router.get("/me")
async def get_me(admin: dict = Depends(_verify_admin)):
    return admin


@router.get("/debts")
async def get_debts(admin: dict = Depends(_verify_admin)):
    response = supabase.table("debts").select("*, players(name)").eq("is_paid", False).order("created_at", desc=True).execute()
    result = []
    for d in response.data:
        result.append({
            "id": d["id"],
            "player_id": d["player_id"],
            "player_name": d["players"]["name"],
            "amount": d["amount"],
            "is_paid": d["is_paid"],
            "created_at": d["created_at"],
        })
    return result


@router.get("/debts/summary")
async def get_debts_summary(admin: dict = Depends(_verify_admin)):
    response = supabase.table("debts").select("*, players(name)").execute()
    by_player = {}
    total_debt = 0.0
    total_paid = 0.0
    for d in response.data:
        pid = d["player_id"]
        name = d["players"]["name"]
        amount = d["amount"]
        is_paid = d["is_paid"]
        if pid not in by_player:
            last_name = name.split()[-1] if name.split() else name
            by_player[pid] = {"player_name": name, "last_name": last_name, "total_debt": 0, "total_paid": 0, "has_unpaid": False}
        if is_paid:
            by_player[pid]["total_paid"] += amount
            total_paid += amount
        else:
            by_player[pid]["total_debt"] += amount
            by_player[pid]["has_unpaid"] = True
            total_debt += amount
    players_list = []
    for data in by_player.values():
        players_list.append({
            "player_name": data["player_name"],
            "last_name": data["last_name"],
            "total_debt": data["total_debt"],
            "total_paid": data["total_paid"],
            "has_unpaid": data["has_unpaid"],
            "is_fully_paid": not data["has_unpaid"] and data["total_paid"] > 0,
        })
    return {
        "total_debt": total_debt,
        "total_paid": total_paid,
        "by_player": sorted(players_list, key=lambda x: x["total_debt"], reverse=True),
    }
