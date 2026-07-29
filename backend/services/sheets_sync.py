import os
import logging
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from database import supabase

logger = logging.getLogger(__name__)

SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
CREDS_PATH = os.getenv("GOOGLE_SHEETS_CREDS_PATH", "google-creds.json")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_sheet():
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).sheet1


def _player_map_by_dni() -> dict:
    players = supabase.table("players").select("id, dni").execute().data
    return {p["dni"]: p["id"] for p in players if p.get("dni")}


def get_rows() -> list[dict]:
    sheet = _get_sheet()
    all_rows = sheet.get_all_values()
    if not all_rows:
        return []
    header = all_rows[0]
    return [dict(zip(header, row)) for row in all_rows[1:] if any(cell.strip() for cell in row)]


def _find_column_indices(header):
    h = [c.strip() for c in header]
    return {
        "dni": h.index("DNI"),
        "nombre": h.index("Nombre"),
        "deuda": h.index("Deuda"),
    }


def _now_ym():
    now = datetime.now()
    return now.year, now.month


def sync_debts() -> dict:
    """
    Reconciliation mode: reads sheet, compares balance with transactions table,
    inserts adjustments if they differ.
    """
    rows = get_rows()
    if not rows:
        return {"success": True, "updated": 0, "message": "El sheet está vacío."}

    players = _player_map_by_dni()
    year, month = _now_ym()
    updated = 0
    skipped = 0
    errors = 0
    adjustments = []

    existing = supabase.table("transactions").select("player_id, amount").execute().data
    tx_sums = {}
    for tx in existing:
        pid = tx["player_id"]
        tx_sums[pid] = tx_sums.get(pid, 0) + tx["amount"]

    for row in rows:
        row = {k.strip(): v for k, v in row.items()}
        dni = (row.get("DNI") or "").strip()
        nombre = (row.get("Nombre") or "").strip()
        deuda_str = (row.get("Deuda") or "0").strip().replace("$", "").replace(",", "")

        if not dni:
            skipped += 1
            continue

        try:
            sheet_balance = float(deuda_str)
        except ValueError:
            logger.warning(f"Deuda inválida para DNI {dni}: '{deuda_str}'")
            errors += 1
            continue

        player_id = players.get(dni)
        if not player_id:
            logger.warning(f"Jugador con DNI {dni} no encontrado en Supabase ({nombre})")
            skipped += 1
            continue

        tx_balance = tx_sums.get(player_id, 0)
        diff = round(sheet_balance - tx_balance, 2)
        if diff != 0:
            supabase.table("transactions").insert({
                "player_id": player_id,
                "amount": diff,
                "description": "Ajuste por conciliación",
                "year": year,
                "month": month,
            }).execute()
            adjustments.append(f"{nombre}: {tx_balance:,.0f} → {sheet_balance:,.0f} (ajuste {diff:+,.0f})")
            updated += 1

    msg = f"Deudas reconciliadas: {len(adjustments)} ajustes"
    if skipped:
        msg += f", {skipped} saltadas (sin DNI)"
    if errors:
        msg += f", {errors} errores"
    if adjustments:
        msg += "\n" + "\n".join(adjustments)

    return {"success": True, "updated": updated, "skipped": skipped, "errors": errors, "message": msg}


def _format_amount(value: float) -> str:
    return f"${int(value)}" if value == int(value) else f"${value:.2f}"


def add_monthly_fee(amount: float) -> dict:
    sheet = _get_sheet()
    all_rows = sheet.get_all_values()
    if not all_rows:
        return {"success": False, "error": "Sheet vacío"}

    header = all_rows[0]
    cols = _find_column_indices(header)
    deuda_letter = chr(65 + cols["deuda"])
    num_rows = len(all_rows)
    updated = 0
    players = _player_map_by_dni()
    year, month = _now_ym()
    txs = []

    cells = sheet.range(f"{deuda_letter}2:{deuda_letter}{num_rows}")
    for i, cell in enumerate(cells):
        row_idx = i + 1
        row = all_rows[row_idx]
        dni = row[cols["dni"]].strip()
        if not dni:
            continue

        raw = row[cols["deuda"]].strip().replace("$", "").replace(",", "")
        try:
            current = float(raw) if raw else 0
        except ValueError:
            current = 0

        cell.value = _format_amount(current + amount)
        updated += 1

        player_id = players.get(dni)
        if player_id:
            txs.append({
                "player_id": player_id,
                "amount": amount,
                "description": "Cuota mensual",
                "year": year,
                "month": month,
            })

    sheet.update_cells(cells)

    if txs:
        supabase.table("transactions").insert(txs).execute()

    return {"success": True, "updated": updated}


def _player_id_by_dni(dni: str):
    players = supabase.table("players").select("id").eq("dni", dni).execute().data
    return players[0]["id"] if players else None


def set_player_debt(dni: str, amount: float) -> dict:
    sheet = _get_sheet()
    all_rows = sheet.get_all_values()
    if not all_rows:
        return {"success": False, "error": "Sheet vacío"}

    header = all_rows[0]
    cols = _find_column_indices(header)
    year, month = _now_ym()
    player_id = _player_id_by_dni(dni)

    for i in range(1, len(all_rows)):
        row = all_rows[i]
        if row[cols["dni"]].strip() != dni:
            continue

        raw = row[cols["deuda"]].strip().replace("$", "").replace(",", "")
        try:
            current = float(raw) if raw else 0
        except ValueError:
            current = 0

        diff = round(amount - current, 2)
        formatted = _format_amount(max(0, amount))
        sheet.update_cell(i + 1, cols["deuda"] + 1, formatted)
        player_name = row[cols["nombre"]].strip()

        if player_id and diff != 0:
            supabase.table("transactions").insert({
                "player_id": player_id,
                "amount": diff,
                "description": "Ajuste manual",
                "year": year,
                "month": month,
            }).execute()

        return {
            "success": True,
            "player_name": player_name,
            "new_debt": max(0, amount),
        }

    return {"success": False, "error": f"DNI {dni} no encontrado en el sheet"}


def add_to_player_debt(dni: str, amount: float) -> dict:
    sheet = _get_sheet()
    all_rows = sheet.get_all_values()
    if not all_rows:
        return {"success": False, "error": "Sheet vacío"}

    header = all_rows[0]
    cols = _find_column_indices(header)
    year, month = _now_ym()
    player_id = _player_id_by_dni(dni)

    for i in range(1, len(all_rows)):
        row = all_rows[i]
        if row[cols["dni"]].strip() != dni:
            continue

        raw = row[cols["deuda"]].strip().replace("$", "").replace(",", "")
        try:
            current = float(raw) if raw else 0
        except ValueError:
            current = 0

        new_value = current + amount
        formatted = _format_amount(new_value)
        sheet.update_cell(i + 1, cols["deuda"] + 1, formatted)
        player_name = row[cols["nombre"]].strip()

        if player_id:
            supabase.table("transactions").insert({
                "player_id": player_id,
                "amount": amount,
                "description": "Cargo adicional",
                "year": year,
                "month": month,
            }).execute()

        return {
            "success": True,
            "player_name": player_name,
            "previous_debt": current,
            "new_debt": new_value,
        }

    return {"success": False, "error": f"DNI {dni} no encontrado en el sheet"}


def reduce_debt(dni: str, payment: float) -> dict:
    sheet = _get_sheet()
    all_rows = sheet.get_all_values()
    if not all_rows:
        return {"success": False, "error": "Sheet vacío"}

    header = all_rows[0]
    cols = _find_column_indices(header)
    year, month = _now_ym()
    player_id = _player_id_by_dni(dni)

    for i in range(1, len(all_rows)):
        row = all_rows[i]
        if row[cols["dni"]].strip() != dni:
            continue

        raw = row[cols["deuda"]].strip().replace("$", "").replace(",", "")
        try:
            current = float(raw) if raw else 0
        except ValueError:
            current = 0

        new_value = max(0, current - payment)
        formatted = _format_amount(new_value)
        sheet.update_cell(i + 1, cols["deuda"] + 1, formatted)

        player_name = row[cols["nombre"]].strip()

        if player_id:
            supabase.table("transactions").insert({
                "player_id": player_id,
                "amount": -payment,
                "description": "Pago",
                "year": year,
                "month": month,
            }).execute()

        return {
            "success": True,
            "player_name": player_name,
            "previous_debt": current,
            "new_debt": new_value,
        }

    return {"success": False, "error": f"DNI {dni} no encontrado en el sheet"}
