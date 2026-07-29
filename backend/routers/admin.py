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
    response = supabase.table("debts").select("*, players(name)").eq("is_paid", False).execute()
    by_player = {}
    total = 0.0
    for d in response.data:
        name = d["players"]["name"]
        amount = d["amount"]
        total += amount
        entry = by_player.get(name)
        if entry:
            entry["total"] += amount
            entry["count"] += 1
        else:
            by_player[name] = {"player_name": name, "total": amount, "count": 1}
    return {
        "total_debt": total,
        "by_player": sorted(by_player.values(), key=lambda x: x["total"], reverse=True),
    }
