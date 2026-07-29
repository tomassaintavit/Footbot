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
    players_resp = supabase.table("players").select("id, name").execute()
    debts_resp = supabase.table("debts").select("player_id, amount, is_paid").execute()
    debt_map = {}
    for d in debts_resp.data:
        pid = d["player_id"]
        if pid not in debt_map:
            debt_map[pid] = {"total_debt": 0, "total_paid": 0, "has_unpaid": False}
        if d["is_paid"]:
            debt_map[pid]["total_paid"] += d["amount"]
        else:
            debt_map[pid]["total_debt"] += d["amount"]
            debt_map[pid]["has_unpaid"] = True
    total_debt = 0.0
    total_paid = 0.0
    by_player = []
    for p in players_resp.data:
        pid = p["id"]
        name = p["name"]
        di = debt_map.get(pid, {"total_debt": 0, "total_paid": 0, "has_unpaid": False})
        by_player.append({
            "player_name": name,
            "last_name": name.split()[-1] if name.split() else name,
            "total_debt": di["total_debt"],
            "total_paid": di["total_paid"],
            "has_unpaid": di["has_unpaid"],
            "is_fully_paid": not di["has_unpaid"],
        })
        total_debt += di["total_debt"]
        total_paid += di["total_paid"]
    by_player.sort(key=lambda x: x["total_debt"], reverse=True)
    return {"total_debt": total_debt, "total_paid": total_paid, "by_player": by_player}
