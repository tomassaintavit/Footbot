from datetime import datetime
from database import supabase
from services import sheets_sync


def delete_debt_by_player_name(player_name: str):
    try:
        player_query = supabase.table("players")\
            .select("id, name, dni")\
            .or_(f"name.ilike.%{player_name}%,nickname.ilike.%{player_name}%")\
            .execute()
        if not player_query.data:
            return {"success": False, "message": f"No encontré a ningún jugador que se llame '{player_name}'."}
        player = player_query.data[0]

        txs = supabase.table("transactions").select("amount").eq("player_id", player["id"]).execute()
        balance = sum(t["amount"] for t in txs.data)

        if balance <= 0:
            return {"success": True, "message": f"✅ {player['name']} no tiene deudas."}

        year, month = datetime.now().year, datetime.now().month
        supabase.table("transactions").insert({
            "player_id": player["id"],
            "amount": -balance,
            "description": "Perdón de deuda",
            "year": year,
            "month": month,
        }).execute()

        if player.get("dni"):
            sheets_sync.set_player_debt(player["dni"], 0)

        return {"success": True, "message": f"✅ Deuda eliminada. {player['name']} ahora debe $0."}

    except Exception as e:
        return {"success": False, "message": f"Error al borrar la deuda: {str(e)}"}


def create_debt_by_player_name(player_name: str, amount: float):
    try:
        player_query = supabase.table("players")\
            .select("id, name, dni")\
            .or_(f"name.ilike.%{player_name}%,nickname.ilike.%{player_name}%")\
            .execute()

        if not player_query.data:
            return {"success": False, "message": f"No encontré a '{player_name}' para asignarle la deuda."}

        player = player_query.data[0]

        if player.get("dni"):
            result = sheets_sync.add_to_player_debt(player["dni"], amount)
            if result.get("success"):
                return {"success": True, "message": f"✅ Deuda de ${amount:,.0f} agregada a {player['name']}. Total: ${result['new_debt']:,.0f}."}

        year, month = datetime.now().year, datetime.now().month
        supabase.table("transactions").insert({
            "player_id": player["id"],
            "amount": amount,
            "description": "Cargo adicional",
            "year": year,
            "month": month,
        }).execute()
        return {"success": True, "message": f"✅ Se cargó una deuda de ${amount:,.0f} para {player['name']}."}

    except Exception as e:
        return {"success": False, "message": f"Error al crear la deuda: {str(e)}"}


def get_debts_list():
    try:
        rows = supabase.table("transactions").select("amount, player_id, players(name, nickname)").execute()
        if not rows.data:
            return {
                "success": True,
                "message": "✅ <b>¡Buenas noticias!</b> No hay deudas pendientes en el equipo."
            }

        from collections import defaultdict
        balances = defaultdict(float)
        names = {}

        for t in rows.data:
            pid = t["player_id"]
            balances[pid] += t["amount"]
            pi = t.get("players")
            if pi:
                names[pid] = pi.get("name") or pi.get("nickname") or "Jugador sin nombre"

        debtors = {pid: b for pid, b in balances.items() if b > 0}
        if not debtors:
            return {
                "success": True,
                "message": "✅ <b>¡Buenas noticias!</b> No hay deudas pendientes en el equipo."
            }

        name_width = max(len(names.get(pid, "Jugador sin nombre")) for pid in debtors)
        name_width = max(name_width, 10)

        message = "💸 <b>Deudas Pendientes</b>\n<pre>\n"
        message += f"{'Jugador'.ljust(name_width)}  {'Deuda':>10}\n"
        message += f"{'─' * name_width}  {'─' * 10}\n"

        total_team_debt = 0
        for pid in sorted(debtors, key=lambda p: debtors[p], reverse=True):
            amount = debtors[pid]
            name = names.get(pid, "Jugador sin nombre")
            message += f"{name.ljust(name_width)}  ${amount:>8,.0f}\n"
            total_team_debt += amount

        message += f"{'─' * name_width}  {'─' * 10}\n"
        message += f"{'Total'.ljust(name_width)}  ${total_team_debt:>8,.0f}\n"
        message += "</pre>"

        return {"success": True, "message": message}

    except Exception as e:
        return {"success": False, "message": f"Error al obtener la lista de deudas: {str(e)}"}
