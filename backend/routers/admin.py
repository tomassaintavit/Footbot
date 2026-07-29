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
    txs = supabase.table("transactions").select("player_id, amount, description, created_at, players(name)").execute()
    balances = {}
    for t in txs.data:
        pid = t["player_id"]
        if pid not in balances:
            balances[pid] = {"balance": 0, "transactions": []}
        balances[pid]["balance"] += t["amount"]
        balances[pid]["transactions"].append(t)

    result = []
    for pid, data in balances.items():
        player_name = "Jugador sin nombre"
        if data["transactions"]:
            pi = data["transactions"][0].get("players")
            if pi:
                player_name = pi.get("name", "Jugador sin nombre")
        result.append({
            "player_id": pid,
            "player_name": player_name,
            "balance": data["balance"],
            "transaction_count": len(data["transactions"]),
        })

    result.sort(key=lambda x: x["balance"], reverse=True)
    return result


@router.get("/debts/summary")
async def get_debts_summary(admin: dict = Depends(_verify_admin)):
    players_resp = supabase.table("players").select("id, name").execute()
    txs = supabase.table("transactions").select("player_id, amount").execute()

    charged_map = {}
    paid_map = {}

    for t in txs.data:
        pid = t["player_id"]
        amt = t["amount"]
        if amt > 0:
            charged_map[pid] = charged_map.get(pid, 0) + amt
        else:
            paid_map[pid] = paid_map.get(pid, 0) + abs(amt)

    all_pids = set(charged_map.keys()) | set(paid_map.keys()) | {p["id"] for p in players_resp.data}

    total_charged = 0.0
    total_paid = 0.0
    by_player = []

    for p in players_resp.data:
        pid = p["id"]
        name = p["name"]
        charged = charged_map.get(pid, 0)
        paid = paid_map.get(pid, 0)
        balance = charged - paid

        by_player.append({
            "player_name": name,
            "last_name": name.split()[-1] if name.split() else name,
            "total_debt": balance,
            "total_paid": paid,
            "has_unpaid": balance > 0,
            "is_fully_paid": balance <= 0,
        })
        total_charged += charged
        total_paid += paid

    by_player.sort(key=lambda x: x["total_debt"], reverse=True)

    return {
        "total_debt": total_charged - total_paid,
        "total_paid": total_paid,
        "total_charged": total_charged,
        "by_player": by_player,
    }
