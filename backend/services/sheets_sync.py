import os
import logging
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


def sync_debts() -> dict:
    updated = 0
    skipped = 0
    errors = 0

    rows = get_rows()
    if not rows:
        return {"success": True, "updated": 0, "message": "El sheet está vacío."}

    for row in rows:
        row = {k.strip(): v for k, v in row.items()}
        dni = (row.get("DNI") or "").strip()
        nombre = (row.get("Nombre") or "").strip()
        deuda_str = (row.get("Deuda") or "0").strip().replace("$", "").replace(",", "")

        if not dni:
            skipped += 1
            continue

        try:
            amount = float(deuda_str)
        except ValueError:
            logger.warning(f"Deuda inválida para DNI {dni}: '{deuda_str}'")
            errors += 1
            continue

        players = supabase.table("players").select("id,name").eq("dni", dni).execute()
        if not players.data:
            logger.warning(f"Jugador con DNI {dni} no encontrado en Supabase ({nombre})")
            skipped += 1
            continue

        player = players.data[0]

        supabase.table("debts").delete().eq("player_id", player["id"]).execute()
        supabase.table("debts").insert({"player_id": player["id"], "amount": amount, "is_paid": False}).execute()
        updated += 1

    msg = f"Deudas sincronizadas: {updated} actualizadas"
    if skipped:
        msg += f", {skipped} saltadas (sin DNI o sin deuda)"
    if errors:
        msg += f", {errors} errores"

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

    sheet.update_cells(cells)
    sync_result = sync_debts()
    return {"success": True, "updated": updated, "sync": sync_result}


def reduce_debt(dni: str, payment: float) -> dict:
    sheet = _get_sheet()
    all_rows = sheet.get_all_values()
    if not all_rows:
        return {"success": False, "error": "Sheet vacío"}

    header = all_rows[0]
    cols = _find_column_indices(header)

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
        sync_debts()
        return {
            "success": True,
            "player_name": player_name,
            "previous_debt": current,
            "new_debt": new_value,
        }

    return {"success": False, "error": f"DNI {dni} no encontrado en el sheet"}
