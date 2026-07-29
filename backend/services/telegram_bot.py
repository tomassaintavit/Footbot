import os
import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, Defaults
from telegram.error import Conflict as TelegramConflict

from database import supabase
from services import debts, players, attendance, matches, positions, logs, torneo_sync, sheets_sync

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

_application: Application | None = None


def find_player_by_telegram_id(telegram_id: str):
    query = supabase.table("players").select("*").eq("telegram_id", telegram_id).execute()
    return query.data[0] if query.data else None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"⚽ ¡Hola {user.first_name}! Soy <b>Footbot</b>, el asistente de <b>Buen Palo FC</b>.\n\n"
        "Usá <b>/help</b> para ver todos los comandos disponibles."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 <b>Footbot — Comandos disponibles</b>\n\n"
        "<b>Información</b>\n"
        "• /jugadores — Lista de jugadores\n"
        "• /deudas — Deudas pendientes\n"
        "• /partidos — Próximos partidos\n"
        "• /asistencia — Confirmados\n"
        "• /posiciones — Tabla de posiciones\n\n"
        "<b>Administración</b>\n"
        "• /nuevo_jugador — Agregar jugador\n"
        "• /borrar_jugador — Eliminar jugador\n"
        "• /actualizar_jugador — Modificar datos\n"
        "• /nueva_deuda — Cargar deuda\n"
        "• /borrar_deuda — Eliminar deudas\n"
        "• /pagar — Registrar pago de un jugador\n"
        "• /pagar_lote MONTO — Pagos múltiples por selección\n"
        "• /agregar_deuda_mes — Sumar cuota mensual a todos\n"
        "• /sincronizar — Sincronizar datos con Torneo Golden\n"
        "• /sincronizar_deudas — Sincronizar deudas desde Google Sheets\n\n"
        "<b>Vincular jugador</b>\n"
        "• /link Nombre TelegramID — Asocia un jugador a su Telegram\n"
        "  El jugador obtiene su ID de @userinfobot\n\n"
        "<b>Cancelar</b>\n"
        "• /cancelar — Cancela cualquier operación en curso\n\n"
        "🔐 El bot es solo para administradores del equipo."
    )


async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller_id = str(update.effective_user.id)
    caller = find_player_by_telegram_id(caller_id)
    if not caller or not caller.get("is_admin"):
        await update.message.reply_text(
            "⛔ Solo administradores pueden vincular jugadores.\n"
            "Pedile al admin de tu equipo que te registre."
        )
        return

    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text(
            "Usá: <code>/link NombreDelJugador TelegramUserId</code>\n\n"
            "El jugador obtiene su ID mandándole cualquier mensaje a @userinfobot."
        )
        return

    name = " ".join(args[:-1])
    target_telegram_id = args[-1]
    target_telegram_id = target_telegram_id.lstrip("@")

    query = supabase.table("players").select("*").ilike("name", name).execute()
    if not query.data:
        await update.message.reply_text(f"No encontré ningún jugador con el nombre '{name}'.")
        return

    existing = supabase.table("players").select("id").eq("telegram_id", target_telegram_id).execute()
    if existing.data:
        other = existing.data[0]
        if other["id"] != query.data[0]["id"]:
            await update.message.reply_text("❌ Ese Telegram ID ya está vinculado a otro jugador.")
            return

    player = query.data[0]
    supabase.table("players").update({"telegram_id": target_telegram_id}).eq("id", player["id"]).execute()
    logger.info(f"Admin '{caller['name']}' vinculó a '{player['name']}' con Telegram ID {target_telegram_id}")
    await update.message.reply_text(
        f"✅ Vinculaste a <b>{player['name']}</b> con Telegram ID {target_telegram_id}.\n"
        f"{'🔑 Tiene permisos de administrador.' if player.get('is_admin') else ''}"
    )


async def _admin_only(update: Update) -> bool:
    player = find_player_by_telegram_id(str(update.effective_user.id))
    if not player:
        await update.message.reply_text("No estás registrado. Pedile al admin que te vincule con /link.")
        return False
    if not player.get("is_admin"):
        await update.message.reply_text("⛔ Solo administradores.")
        return False
    return True


async def jugadores_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _admin_only(update):
        return
    result = players.get_players_list()["message"]
    await update.message.reply_text(result)


async def deudas_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _admin_only(update):
        return
    result = debts.get_debts_list()["message"]
    await update.message.reply_text(result)


async def partidos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _admin_only(update):
        return
    result = matches.get_next_matches()["message"]
    await update.message.reply_text(result)


async def asistencia_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _admin_only(update):
        return
    result = attendance.get_match_attendance()["message"]
    await update.message.reply_text(result)


async def posiciones_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _admin_only(update):
        return
    result = positions.get_positions_table()["message"]
    await update.message.reply_text(result)


async def sincronizar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _admin_only(update):
        return
    await update.message.reply_text("🔄 Sincronizando con Torneo Golden...")
    try:
        result = torneo_sync.sync_all()
        msg = "✅ <b>Sincronización completa</b>\n\n"
        if result["players"]["success"]:
            msg += f"👥 <b>Jugadores:</b> {result['players']['inserted']} nuevos, {result['players']['updated']} actualizados"
            if result['players']['errors']:
                msg += f", {result['players']['errors']} errores"
            msg += "\n"
        if result["positions"]["success"]:
            pos_inserted = result['positions'].get('inserted', 0)
            pos_msg = result['positions'].get('message', f"{pos_inserted} registros")
            msg += f"📊 <b>Posiciones:</b> {pos_msg}\n"
        if result["matches"]["success"]:
            msg += f"⚽ <b>Partidos:</b> {result['matches']['synced']} sincronizados\n"
        await update.message.reply_text(msg)
    except Exception as e:
        logger.exception("Error en sincronización")
        await update.message.reply_text(f"❌ Error al sincronizar: {str(e)}")


async def sincronizar_deudas_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _admin_only(update):
        return
    await update.message.reply_text("🔄 Sincronizando deudas desde Google Sheets...")
    try:
        result = sheets_sync.sync_debts()
        if result["success"]:
            await update.message.reply_text(f"✅ {result['message']}")
        else:
            await update.message.reply_text(f"❌ {result['message']}")
    except Exception as e:
        logger.exception("Error al sincronizar deudas")
        await update.message.reply_text(f"❌ Error al sincronizar deudas: {str(e)}")


# ── /pagar ───────────────────────────────────────────────────────

async def pg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = find_player_by_telegram_id(str(update.effective_user.id))
    if not player or not player.get("is_admin"):
        await update.message.reply_text("⛔ Solo administradores.")
        return ConversationHandler.END
    context.user_data["admin_player"] = player
    await update.message.reply_text("💰 <b>Nombre del jugador que pagó:</b>")
    return PG_NAME


async def pg_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    candidates = search_players(name)
    if not candidates:
        await update.message.reply_text(f"🔍 No encontré a '{name}'.")
        return ConversationHandler.END
    if len(candidates) == 1:
        context.user_data["selected_player"] = candidates[0]
        monto_msg = f"💰 <b>Monto que pagó {candidates[0]['name']}:</b>\n(Ej: 5000)"
        await update.message.reply_text(monto_msg)
        return PG_AMOUNT
    context.user_data["candidates"] = candidates
    msg = f"Encontré varios jugadores:\n\n{format_players_for_selection(candidates)}\n\nRespondé con el número:"
    await update.message.reply_text(msg)
    return PG_SELECT


async def pg_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected = _resolve_player_selection(update, context)
    if not selected:
        await update.message.reply_text("❌ Número inválido. Cancelado.")
        return ConversationHandler.END
    context.user_data["selected_player"] = selected
    monto_msg = f"💰 <b>Monto que pagó {selected['name']}:</b>\n(Ej: 5000)"
    await update.message.reply_text(monto_msg)
    return PG_AMOUNT


async def pg_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip().replace("$", "").replace(",", ""))
        if amount <= 0:
            await update.message.reply_text("❌ El monto debe ser mayor a cero.")
            return PG_AMOUNT
        context.user_data["pg_amount"] = amount
        player = context.user_data["selected_player"]
        await update.message.reply_text(
            f"<b>Resumen:</b>\n"
            f"👤 Jugador: {player['name']}\n"
            f"💰 Pagó: ${amount:,.0f}\n\n"
            f"✅ Escribí <b>si</b> para confirmar\n"
            f"❌ Cualquier otra cosa para cancelar"
        )
        return PG_CONFIRM
    except ValueError:
        await update.message.reply_text("❌ Monto inválido. Usá solo números.\nEj: 5000")
        return PG_AMOUNT


async def pg_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text in ("si", "sí", "s"):
        player = context.user_data["selected_player"]
        amount = context.user_data["pg_amount"]
        if not player.get("dni"):
            await update.message.reply_text(f"❌ {player['name']} no tiene DNI registrado. No se puede actualizar.")
            return ConversationHandler.END
        result = sheets_sync.reduce_debt(player["dni"], amount)
        admin = context.user_data["admin_player"]
        if result.get("success"):
            logs.create_log(admin["id"], "payment",
                f"Registró pago de ${amount:,.0f} de {result['player_name']} "
                f"(deuda anterior: ${result['previous_debt']:,.0f})")
            await update.message.reply_text(
                f"✅ <b>Pago registrado</b>\n"
                f"👤 {result['player_name']}\n"
                f"💰 Pagó: ${amount:,.0f}\n"
                f"📉 Deuda anterior: ${result['previous_debt']:,.0f}\n"
                f"📊 Deuda actual: <b>${result['new_debt']:,.0f}</b>"
            )
        else:
            await update.message.reply_text(f"❌ {result.get('error', 'Error desconocido')}")
    else:
        await update.message.reply_text("❌ Cancelado.")
    return ConversationHandler.END


# ── Helpers ──────────────────────────────────────────────────────

def _parse_selection(text: str, max_num: int) -> set[int]:
    parts = text.replace(" ", ",").split(",")
    selected = set()
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            try:
                a, b = part.split("-", 1)
                for i in range(int(a), int(b) + 1):
                    if 1 <= i <= max_num:
                        selected.add(i)
            except ValueError:
                pass
        else:
            try:
                i = int(part)
                if 1 <= i <= max_num:
                    selected.add(i)
            except ValueError:
                pass
    return selected


def _last_name(name: str) -> str:
    parts = name.split()
    return parts[-1] if parts else name


def _reduce_debt_direct(player_id: str, amount: float) -> dict:
    txs = supabase.table("transactions").select("amount").eq("player_id", player_id).execute()
    balance = sum(t["amount"] for t in txs.data)
    new_balance = max(0, balance - amount)
    if amount > 0:
        supabase.table("transactions").insert({
            "player_id": player_id,
            "amount": -amount,
            "description": "Pago",
            "year": datetime.now().year,
            "month": datetime.now().month,
        }).execute()
    return {"success": True, "previous_debt": balance, "new_debt": new_balance}


def _format_player_grid(players: list[dict]) -> str:
    half = (len(players) + 1) // 2
    lines = []
    for i in range(half):
        p1 = players[i]
        left = f"{i+1}. {_last_name(p1['name'])}"
        if i + half < len(players):
            p2 = players[i + half]
            right = f"{i+half+1}. {_last_name(p2['name'])}"
            lines.append(f"{left:<24}{right}")
        else:
            lines.append(left)
    return "<pre>" + "\n".join(lines) + "</pre>"


# ── /pagar_lote ──────────────────────────────────────────────────

async def pl_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = find_player_by_telegram_id(str(update.effective_user.id))
    if not player or not player.get("is_admin"):
        await update.message.reply_text("⛔ Solo administradores.")
        return ConversationHandler.END
    context.user_data["admin_player"] = player

    args = context.args or []
    if not args:
        await update.message.reply_text("Usá: <code>/pagar_lote MONTO</code>\nEj: <code>/pagar_lote 5000</code>")
        return ConversationHandler.END
    try:
        amount = float(args[0].replace("$", "").replace(",", ""))
        if amount <= 0:
            await update.message.reply_text("❌ El monto debe ser mayor a cero.")
            return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Monto inválido.\nEj: <code>/pagar_lote 5000</code>")
        return ConversationHandler.END

    players = supabase.table("players").select("id, name, nickname, dni").order("name").execute()
    all_players = players.data or []
    if not all_players:
        await update.message.reply_text("No hay jugadores registrados.")
        return ConversationHandler.END

    context.user_data["pl_amount"] = amount
    context.user_data["pl_players"] = all_players

    grid = _format_player_grid(all_players)
    await update.message.reply_text(
        f"💰 <b>Pago lote — ${amount:,.0f} c/u</b>\n"
        f"Seleccioná los números (ej: 1,3,5 o 1-3,6):\n\n{grid}"
    )
    return PL_SELECT


async def pl_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    all_players = context.user_data.get("pl_players", [])
    indices = _parse_selection(text, len(all_players))
    if not indices:
        await update.message.reply_text("❌ Selección inválida. Probá con números como 1,3,5 o 1-3,6")
        return PL_SELECT

    selected = [all_players[i - 1] for i in sorted(indices)]
    context.user_data["pl_selected"] = selected
    amount = context.user_data["pl_amount"]

    names = "\n".join(f"• {p['name']}" for p in selected)
    await update.message.reply_text(
        f"📋 <b>Resumen</b>\n"
        f"💰 ${amount:,.0f} c/u — <b>{len(selected)} jugadores</b>\n"
        f"💵 Total: ${amount * len(selected):,.0f}\n\n"
        f"{names}\n\n"
        f"✅ Escribí <b>si</b> para confirmar\n"
        f"❌ Cualquier otra cosa para cancelar"
    )
    return PL_CONFIRM


async def pl_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text not in ("si", "sí", "s"):
        await update.message.reply_text("❌ Cancelado.")
        return ConversationHandler.END

    selected = context.user_data.get("pl_selected", [])
    amount = context.user_data["pl_amount"]
    admin = context.user_data["admin_player"]
    ok = []
    failed = []
    for p in selected:
        if p.get("dni"):
            result = sheets_sync.reduce_debt(p["dni"], amount)
        else:
            result = _reduce_debt_direct(p["id"], amount)
        if result.get("success"):
            ok.append(f"✅ {_last_name(p['name'])} — ${result['previous_debt']:,.0f} → ${result['new_debt']:,.0f}")
            logs.create_log(admin["id"], "payment",
                f"Pago lote: ${amount:,.0f} de {p['name']} (deuda anterior: ${result['previous_debt']:,.0f})")
        else:
            failed.append(f"❌ {_last_name(p['name'])} — {result.get('error', 'error')}")

    msg_parts = [f"✅ <b>{len(ok)} pagos registrados</b> — ${amount * len(ok):,.0f}"]
    if ok:
        msg_parts.append("")
        msg_parts.extend(ok)
    if failed:
        msg_parts.append("")
        msg_parts.append(f"⚠️ <b>{len(failed)} errores</b>")
        msg_parts.extend(failed)
    await update.message.reply_text("\n".join(msg_parts))
    return ConversationHandler.END


# ── Conversation states ──────────────────────────────────────────
(
    NJ_NAME, NJ_NICKNAME, NJ_DNI, NJ_CONFIRMAR,
    BJ_NAME, BJ_SELECT, BJ_CONFIRMAR,
    ND_NAME, ND_AMOUNT, ND_SELECT, ND_CONFIRMAR,
    BD_NAME, BD_SELECT, BD_CONFIRMAR,
    UJ_NAME, UJ_SELECT, UJ_FIELD, UJ_VALUE, UJ_CONFIRMAR,
    MF_AMOUNT, MF_CONFIRM,
    PG_NAME, PG_SELECT, PG_AMOUNT, PG_CONFIRM,
    PL_SELECT, PL_CONFIRM,
) = range(27)

EDITABLE_FIELDS = {
    "1": ("nickname", "Apodo"),
    "2": ("dni", "DNI"),
    "3": ("goals", "Goles"),
    "4": ("yellow_cards", "Tarjetas amarillas"),
    "5": ("red_cards", "Tarjetas rojas"),
    "6": ("is_suspended", "Suspendido (si/no)"),
    "7": ("email", "Email"),
}

FIELD_KEYWORDS = {
    "apodo": "nickname", "apellido": "nickname", "nickname": "nickname",
    "dni": "dni", "documento": "dni",
    "goles": "goals", "gol": "goals",
    "amarillas": "yellow_cards", "amarilla": "yellow_cards", "yellow": "yellow_cards",
    "rojas": "red_cards", "roja": "red_cards", "red": "red_cards",
    "suspendido": "is_suspended", "suspension": "is_suspended",
    "email": "email", "mail": "email", "correo": "email",
}


def find_player_by_telegram_id(telegram_id: str):
    query = supabase.table("players").select("*").eq("telegram_id", telegram_id).execute()
    return query.data[0] if query.data else None


def search_players(name: str):
    query = supabase.table("players").select("id, name, nickname, dni").ilike("name", f"*{name}*").execute()
    return query.data or []


def format_players_for_selection(players):
    lines = []
    for i, p in enumerate(players, 1):
        nick = f" ({p.get('nickname')})" if p.get("nickname") else ""
        lines.append(f"{i}. {p['name']}{nick}")
    return "\n".join(lines)


def _resolve_player_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    candidates = context.user_data.get("candidates", [])
    try:
        idx = int(text) - 1
        if 0 <= idx < len(candidates):
            return candidates[idx]
    except ValueError:
        pass
    return None


def _format_uj_fields(player_name: str):
    msg = (
        f"<b>Jugador:</b> {player_name}\n\n"
        f"<b>¿Qué campo querés actualizar?</b>\n\n"
    )
    for k, (field, label) in EDITABLE_FIELDS.items():
        msg += f"{k} → {label}\n"
    msg += "\nRespondé con el número o nombre del campo:"
    return msg


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operación cancelada.")
    return ConversationHandler.END


# ── /nuevo_jugador ───────────────────────────────────────────────

async def nj_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = find_player_by_telegram_id(str(update.effective_user.id))
    if not player or not player.get("is_admin"):
        await update.message.reply_text("⛔ Solo administradores.")
        return ConversationHandler.END
    context.user_data["admin_player"] = player
    await update.message.reply_text("🏃 <b>Nombre del nuevo jugador:</b>")
    return NJ_NAME

async def nj_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nj_name"] = update.message.text.strip()
    await update.message.reply_text("📝 <b>Apodo</b> (opcional, - para saltar):")
    return NJ_NICKNAME

async def nj_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text != "-":
        context.user_data["nj_nickname"] = text
    await update.message.reply_text("📄 <b>DNI</b> (opcional, - para saltar):")
    return NJ_DNI

async def nj_dni(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text != "-":
        context.user_data["nj_dni"] = text
    name = context.user_data["nj_name"]
    nickname = context.user_data.get("nj_nickname", "—")
    dni = context.user_data.get("nj_dni", "—")
    await update.message.reply_text(
        f"<b>Resumen:</b>\n"
        f"👤 Nombre: {name}\n"
        f"📝 Apodo: {nickname}\n"
        f"📄 DNI: {dni}\n\n"
        f"✅ Escribí si para confirmar\n"
        f"❌ Cualquier otra cosa para cancelar"
    )
    return NJ_CONFIRMAR

async def nj_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text in ("si", "sí", "s"):
        name = context.user_data["nj_name"]
        result = players.create_player(name)
        if result.get("success"):
            if "nj_nickname" in context.user_data:
                players.update_player(name, nickname=context.user_data["nj_nickname"])
            if "nj_dni" in context.user_data:
                players.update_player(name, dni=context.user_data["nj_dni"])
            admin = context.user_data["admin_player"]
            logs.create_log(admin["id"], "add_player", f"Creó al jugador {name}")
        await update.message.reply_text(result["message"])
    else:
        await update.message.reply_text("❌ Cancelado.")
    return ConversationHandler.END


# ── /borrar_jugador ──────────────────────────────────────────────

async def bj_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = find_player_by_telegram_id(str(update.effective_user.id))
    if not player or not player.get("is_admin"):
        await update.message.reply_text("⛔ Solo administradores.")
        return ConversationHandler.END
    context.user_data["admin_player"] = player
    await update.message.reply_text("🗑️ <b>Nombre del jugador a eliminar:</b>")
    return BJ_NAME

async def bj_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    candidates = search_players(name)
    if not candidates:
        await update.message.reply_text(f"🔍 No encontré a '{name}'.")
        return ConversationHandler.END
    if len(candidates) == 1:
        context.user_data["selected_player"] = candidates[0]
        await update.message.reply_text(
            f"¿Eliminar a <b>{candidates[0]['name']}</b>?\n\n"
            f"✅ Escribí si para confirmar\n"
            f"❌ Cualquier otra cosa para cancelar"
        )
        return BJ_CONFIRMAR
    context.user_data["candidates"] = candidates
    msg = f"Encontré varios jugadores con ese nombre:\n\n{format_players_for_selection(candidates)}\n\nRespondé con el número:"
    await update.message.reply_text(msg)
    return BJ_SELECT

async def bj_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected = _resolve_player_selection(update, context)
    if not selected:
        await update.message.reply_text("❌ Número inválido. Cancelado.")
        return ConversationHandler.END
    context.user_data["selected_player"] = selected
    await update.message.reply_text(
        f"¿Eliminar a <b>{selected['name']}</b>?\n\n"
        f"✅ Escribí si para confirmar\n"
        f"❌ Cualquier otra cosa para cancelar"
    )
    return BJ_CONFIRMAR

async def bj_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text in ("si", "sí", "s"):
        player = context.user_data["selected_player"]
        result = players.delete_player(player["name"])
        admin = context.user_data["admin_player"]
        if result.get("success"):
            logs.create_log(admin["id"], "delete_player", f"Eliminó al jugador {player['name']}")
        await update.message.reply_text(result["message"])
    else:
        await update.message.reply_text("❌ Cancelado.")
    return ConversationHandler.END


# ── /nueva_deuda ─────────────────────────────────────────────────

async def nd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = find_player_by_telegram_id(str(update.effective_user.id))
    if not player or not player.get("is_admin"):
        await update.message.reply_text("⛔ Solo administradores.")
        return ConversationHandler.END
    context.user_data["admin_player"] = player
    await update.message.reply_text("💸 <b>Nombre del jugador:</b>")
    return ND_NAME

async def nd_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    candidates = search_players(name)
    if not candidates:
        await update.message.reply_text(f"🔍 No encontré a '{name}'.")
        return ConversationHandler.END
    if len(candidates) == 1:
        context.user_data["selected_player"] = candidates[0]
        await update.message.reply_text(f"💰 <b>Monto de la deuda:</b>\n(Ej: 5000)")
        return ND_AMOUNT
    context.user_data["candidates"] = candidates
    msg = f"Encontré varios jugadores:\n\n{format_players_for_selection(candidates)}\n\nRespondé con el número:"
    await update.message.reply_text(msg)
    return ND_SELECT

async def nd_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected = _resolve_player_selection(update, context)
    if not selected:
        await update.message.reply_text("❌ Número inválido. Cancelado.")
        return ConversationHandler.END
    context.user_data["selected_player"] = selected
    await update.message.reply_text(f"💰 <b>Monto de la deuda:</b>\n(Ej: 5000)")
    return ND_AMOUNT

async def nd_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip().replace("$", "").replace(",", ""))
        context.user_data["nd_amount"] = amount
        player = context.user_data["selected_player"]
        await update.message.reply_text(
            f"<b>Resumen:</b>\n"
            f"👤 Jugador: {player['name']}\n"
            f"💰 Monto: ${amount:,.0f}\n\n"
            f"✅ Escribí si para confirmar\n"
            f"❌ Cualquier otra cosa para cancelar"
        )
        return ND_CONFIRMAR
    except ValueError:
        await update.message.reply_text("❌ Monto inválido. Usá solo números.\nEj: 5000")
        return ND_AMOUNT

async def nd_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text in ("si", "sí", "s"):
        player = context.user_data["selected_player"]
        result = debts.create_debt_by_player_name(
            player["name"], context.user_data["nd_amount"]
        )
        admin = context.user_data["admin_player"]
        if result.get("success"):
            logs.create_log(admin["id"], "add_debt",
                f"Añadió deuda de ${context.user_data['nd_amount']:,.0f} a {player['name']}")
        await update.message.reply_text(result["message"])
    else:
        await update.message.reply_text("❌ Cancelado.")
    return ConversationHandler.END


# ── /borrar_deuda ────────────────────────────────────────────────

async def bd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = find_player_by_telegram_id(str(update.effective_user.id))
    if not player or not player.get("is_admin"):
        await update.message.reply_text("⛔ Solo administradores.")
        return ConversationHandler.END
    context.user_data["admin_player"] = player
    await update.message.reply_text("🗑️ <b>Nombre del jugador para borrarle la deuda:</b>")
    return BD_NAME

async def bd_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    candidates = search_players(name)
    if not candidates:
        await update.message.reply_text(f"🔍 No encontré a '{name}'.")
        return ConversationHandler.END
    if len(candidates) == 1:
        context.user_data["selected_player"] = candidates[0]
        await update.message.reply_text(
            f"¿Borrar todas las deudas de <b>{candidates[0]['name']}</b>?\n\n"
            f"✅ Escribí si para confirmar\n"
            f"❌ Cualquier otra cosa para cancelar"
        )
        return BD_CONFIRMAR
    context.user_data["candidates"] = candidates
    msg = f"Encontré varios jugadores:\n\n{format_players_for_selection(candidates)}\n\nRespondé con el número:"
    await update.message.reply_text(msg)
    return BD_SELECT

async def bd_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected = _resolve_player_selection(update, context)
    if not selected:
        await update.message.reply_text("❌ Número inválido. Cancelado.")
        return ConversationHandler.END
    context.user_data["selected_player"] = selected
    await update.message.reply_text(
        f"¿Borrar todas las deudas de <b>{selected['name']}</b>?\n\n"
        f"✅ Escribí si para confirmar\n"
        f"❌ Cualquier otra cosa para cancelar"
    )
    return BD_CONFIRMAR

async def bd_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text in ("si", "sí", "s"):
        player = context.user_data["selected_player"]
        result = debts.delete_debt_by_player_name(player["name"])
        admin = context.user_data["admin_player"]
        if result.get("success"):
            logs.create_log(admin["id"], "delete_debt",
                f"Eliminó deudas de {player['name']}")
        await update.message.reply_text(result["message"])
    else:
        await update.message.reply_text("❌ Cancelado.")
    return ConversationHandler.END


# ── /actualizar_jugador ──────────────────────────────────────────

async def uj_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = find_player_by_telegram_id(str(update.effective_user.id))
    if not player or not player.get("is_admin"):
        await update.message.reply_text("⛔ Solo administradores.")
        return ConversationHandler.END
    context.user_data["admin_player"] = player
    await update.message.reply_text("👤 <b>Nombre del jugador a actualizar:</b>")
    return UJ_NAME

async def uj_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    candidates = search_players(name)
    if not candidates:
        await update.message.reply_text(f"🔍 No encontré a '{name}'.")
        return ConversationHandler.END
    if len(candidates) == 1:
        result = players.get_player(candidates[0]["name"])
        context.user_data["uj_player"] = result.get("data", candidates[0])
        context.user_data["uj_name"] = candidates[0]["name"]
        msg = _format_uj_fields(candidates[0]["name"])
        await update.message.reply_text(msg)
        return UJ_FIELD
    context.user_data["candidates"] = candidates
    msg = f"Encontré varios jugadores:\n\n{format_players_for_selection(candidates)}\n\nRespondé con el número:"
    await update.message.reply_text(msg)
    return UJ_SELECT
    for k, (field, label) in EDITABLE_FIELDS.items():
        msg += f"`{k}` → {label}\n"
    msg += "\nRespondé con el número o nombre del campo:"
    await update.message.reply_text(msg)
    return UJ_FIELD

async def uj_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected = _resolve_player_selection(update, context)
    if not selected:
        await update.message.reply_text("❌ Número inválido. Cancelado.")
        return ConversationHandler.END
    result = players.get_player(selected["name"])
    context.user_data["uj_player"] = result.get("data", selected)
    context.user_data["uj_name"] = selected["name"]
    await update.message.reply_text(_format_uj_fields(selected["name"]))
    return UJ_FIELD

async def uj_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    field = EDITABLE_FIELDS.get(text)
    if field:
        context.user_data["uj_field"] = field[0]
        context.user_data["uj_field_label"] = field[1]
    elif text in FIELD_KEYWORDS:
        context.user_data["uj_field"] = FIELD_KEYWORDS[text]
        context.user_data["uj_field_label"] = text.capitalize()
    else:
        await update.message.reply_text("❌ Campo inválido. Elegí un número de la lista.")
        return UJ_FIELD
    await update.message.reply_text(
        f"<b>Nuevo valor para {context.user_data['uj_field_label']}:</b>"
    )
    return UJ_VALUE

async def uj_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()
    field = context.user_data["uj_field"]
    if field == "is_suspended":
        value_bool = value.lower() in ("si", "sí", "s", "true", "1")
        context.user_data["uj_value"] = value_bool
        display = "Sí 🔴" if value_bool else "No 🟢"
    else:
        context.user_data["uj_value"] = value
        display = value
    await update.message.reply_text(
        f"<b>Resumen:</b>\n"
        f"👤 Jugador: {context.user_data['uj_name']}\n"
        f"✏️ Campo: {context.user_data['uj_field_label']}\n"
        f"📝 Nuevo valor: {display}\n\n"
        f"✅ Escribí si para confirmar\n"
        f"❌ Cualquier otra cosa para cancelar"
    )
    return UJ_CONFIRMAR

async def uj_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text in ("si", "sí", "s"):
        name = context.user_data["uj_name"]
        field = context.user_data["uj_field"]
        value = context.user_data["uj_value"]
        result = players.update_player(name, **{field: value})
        admin = context.user_data["admin_player"]
        if result.get("success"):
            logs.create_log(admin["id"], "update_player",
                f"Actualizó {field} de {name} a {value}")
        await update.message.reply_text(result["message"])
    else:
        await update.message.reply_text("❌ Cancelado.")
    return ConversationHandler.END


# ── /agregar_deuda_mes ───────────────────────────────────────────

async def mf_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = find_player_by_telegram_id(str(update.effective_user.id))
    if not player or not player.get("is_admin"):
        await update.message.reply_text("⛔ Solo administradores.")
        return ConversationHandler.END
    context.user_data["admin_player"] = player
    await update.message.reply_text("💰 <b>¿Cuál es el monto por jugador?</b>\n(Ej: 5000)")
    return MF_AMOUNT


async def mf_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip().replace("$", "").replace(",", ""))
        if amount <= 0:
            await update.message.reply_text("❌ El monto debe ser mayor a cero.")
            return MF_AMOUNT
        context.user_data["mf_amount"] = amount
        await update.message.reply_text(
            f"📋 <b>Resumen:</b>\n"
            f"💰 Vas a sumar <b>${amount:,.0f}</b> a cada jugador.\n\n"
            f"✅ Escribí <b>si</b> para confirmar\n"
            f"❌ Cualquier otra cosa para cancelar"
        )
        return MF_CONFIRM
    except ValueError:
        await update.message.reply_text("❌ Monto inválido. Usá solo números.\nEj: 5000")
        return MF_AMOUNT


async def mf_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text in ("si", "sí", "s"):
        amount = context.user_data["mf_amount"]
        result = sheets_sync.add_monthly_fee(amount)
        admin = context.user_data["admin_player"]
        if result.get("success"):
            logs.create_log(admin["id"], "add_monthly_fee",
                f"Agregó cuota mensual de ${amount:,.0f} a {result['updated']} jugadores")
            await update.message.reply_text(
                f"✅ Cuota mensual de <b>${amount:,.0f}</b> agregada a "
                f"<b>{result['updated']}</b> jugadores."
            )
        else:
            await update.message.reply_text(f"❌ Error: {result.get('error', 'desconocido')}")
    else:
        await update.message.reply_text("❌ Cancelado.")
    return ConversationHandler.END


# ── ConversationHandler ──────────────────────────────────────────

conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("nuevo_jugador", nj_start),
        CommandHandler("borrar_jugador", bj_start),
        CommandHandler("nueva_deuda", nd_start),
        CommandHandler("borrar_deuda", bd_start),
        CommandHandler("actualizar_jugador", uj_start),
        CommandHandler("agregar_deuda_mes", mf_start),
        CommandHandler("pagar", pg_start),
        CommandHandler("pagar_lote", pl_start),
    ],
    states={
        NJ_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, nj_name)],
        NJ_NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, nj_nickname)],
        NJ_DNI: [MessageHandler(filters.TEXT & ~filters.COMMAND, nj_dni)],
        NJ_CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, nj_confirmar)],
        BJ_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bj_name)],
        BJ_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bj_select)],
        BJ_CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, bj_confirmar)],
        ND_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, nd_name)],
        ND_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, nd_amount)],
        ND_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, nd_select)],
        ND_CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, nd_confirmar)],
        BD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bd_name)],
        BD_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bd_select)],
        BD_CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, bd_confirmar)],
        UJ_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, uj_name)],
        UJ_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, uj_select)],
        UJ_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, uj_field)],
        UJ_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, uj_value)],
        UJ_CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, uj_confirmar)],
        MF_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, mf_amount)],
        MF_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, mf_confirm)],
        PG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, pg_name)],
        PG_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pg_select)],
        PG_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pg_amount)],
        PG_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, pg_confirm)],
        PL_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pl_select)],
        PL_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, pl_confirm)],
    },
    fallbacks=[CommandHandler("cancelar", cancelar)],
    name="admin_conversations",
    persistent=False,
)


async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Usá `/start` para ver los comandos disponibles."
    )


async def start_bot():
    global _application
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN no está configurado. Bot de Telegram desactivado.")
        return

    _application = Application.builder().token(TELEGRAM_BOT_TOKEN).defaults(Defaults(parse_mode=ParseMode.HTML)).build()

    _application.add_handler(CommandHandler("start", start))
    _application.add_handler(CommandHandler("help", help_command))
    _application.add_handler(CommandHandler("link", link_command))
    _application.add_handler(CommandHandler("jugadores", jugadores_command))
    _application.add_handler(CommandHandler("deudas", deudas_command))
    _application.add_handler(CommandHandler("partidos", partidos_command))
    _application.add_handler(CommandHandler("asistencia", asistencia_command))
    _application.add_handler(CommandHandler("posiciones", posiciones_command))
    _application.add_handler(CommandHandler("sincronizar", sincronizar_command))
    _application.add_handler(CommandHandler("sincronizar_deudas", sincronizar_deudas_command))
    _application.add_handler(conv_handler)
    _application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message))

    await _application.initialize()
    await _application.bot.delete_webhook(drop_pending_updates=True)
    await _application.start()
    for attempt in range(3):
        try:
            await _application.updater.start_polling()
            break
        except TelegramConflict:
            if attempt < 2:
                wait = (attempt + 1) * 5
                logger.warning(f"Conflicto con otra instancia, reintentando en {wait}s...")
                await asyncio.sleep(wait)
            else:
                logger.error("No se pudo iniciar el bot después de 3 intentos.")
                raise
    logger.info("Bot de Telegram iniciado en modo polling")


async def stop_bot():
    global _application
    if _application:
        logger.info("Deteniendo bot de Telegram...")
        await _application.updater.stop()
        await _application.stop()
        await _application.shutdown()
        _application = None
        logger.info("Bot de Telegram detenido")


def main():
    """Entry point standalone para desarrollo local"""
    import asyncio

    async def _run():
        await start_bot()
        try:
            while True:
                await asyncio.sleep(3600)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        finally:
            await stop_bot()

    asyncio.run(_run())
