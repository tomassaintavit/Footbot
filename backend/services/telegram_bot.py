import os
import asyncio
import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, Defaults
from telegram.error import Conflict as TelegramConflict

from database import supabase
from services import intelligence, debts, players, attendance, matches, positions, logs

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

_application: Application | None = None


def find_player_by_telegram_id(telegram_id: str):
    query = supabase.table("players").select("*").eq("telegram_id", telegram_id).execute()
    return query.data[0] if query.data else None


def process_message(player, text: str, model: str = "llama3") -> str:
    intent = intelligence.extract_intent(text, model)
    action = intent.get("action")
    params = intent.get("params", {})
    response_text = intent.get("response", "Lo siento, no pude procesar eso.")

    critical_actions = ["delete_debt", "update_debt", "add_debt", "add_player", "delete_player", "update_player"]
    if action in critical_actions and not player.get("is_admin"):
        return "⛔ No tienes permisos de administrador para realizar esta acción."

    if action == "delete_debt":
        result = debts.delete_debt_by_player_name(params.get("player_name"))
        if result.get("success"):
            logs.create_log(player["id"], "delete_debt", f"Eliminó deudas de {params.get('player_name')}")
        return result["message"]

    elif action == "get_help":
        return (
            "🤖 <b>¡Soy Footbot! Aquí tienes lo que puedo hacer por el equipo:</b>\n\n"
            "⚽ <b>Partidos</b>\n"
            "• ¿Cuándo jugamos? → Próximo partido\n"
            "• Tabla de posiciones → Cómo vamos en el torneo\n\n"
            "📝 <b>Asistencia</b>\n"
            "• ¿Quiénes van? → Confirmados para el próximo partido\n"
            "• Subir lista → Pega la lista de WhatsApp y la proceso\n\n"
            "💸 <b>Deudas</b>\n"
            "• ¿Quién debe plata? → Deudores y montos\n\n"
            "👤 <b>Jugadores</b>\n"
            "• Ver lista → Todos los registrados\n"
            "• Información de [Nombre] → Goles, tarjetas, suspensión\n\n"
            "¡Pregúntame lo que necesites!"
        )

    elif action == "get_debts_list":
        return debts.get_debts_list()["message"]

    elif action in ["add_debt", "update_debt"]:
        amount = params.get("amount", 0)
        result = debts.create_debt_by_player_name(params.get("player_name"), amount)
        if result.get("success"):
            logs.create_log(player["id"], action, f"Añadió/Actualizó deuda de ${amount} a {params.get('player_name')}")
        return result["message"]

    elif action == "add_player":
        name = params.get("player_name")
        result = players.create_player(name)
        if result.get("success"):
            logs.create_log(player["id"], "add_player", f"Creó al jugador {name}")
        return result["message"]

    elif action == "delete_player":
        name = params.get("player_name")
        result = players.delete_player(name)
        if result.get("success"):
            logs.create_log(player["id"], "delete_player", f"Eliminó al jugador {name}")
        return result["message"]

    elif action == "update_player":
        name = params.get("player_name")
        result = players.update_player(
            name=name,
            nickname=params.get("nickname"),
            dni=params.get("dni"),
            email=params.get("email"),
            goals=params.get("goals"),
            yellow_cards=params.get("yellow_cards"),
            red_cards=params.get("red_cards"),
            is_suspended=params.get("is_suspended"),
        )
        if result.get("success"):
            logs.create_log(player["id"], "update_player", f"Actualizó datos de {name}")
        return result["message"]

    elif action == "get_player":
        name = params.get("player_name")
        return players.get_player(name)["message"]

    elif action == "upload_attendance":
        return attendance.process_attendance_list(text, model)["message"]

    elif action == "get_players_list":
        return players.get_players_list()["message"]

    elif action == "get_next_matches":
        return matches.get_next_matches()["message"]

    elif action == "get_attendance_list":
        return attendance.get_match_attendance()["message"]

    elif action == "get_positions_table":
        return positions.get_positions_table()["message"]

    return response_text


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"⚽ ¡Hola {user.first_name}! Soy <b>Footbot</b>, tu asistente del equipo.\n\n"
        "Escribime con lenguaje natural o usá los comandos:\n\n"
        "<b>Comandos:</b>\n"
        "• /jugadores — Lista de jugadores\n"
        "• /deudas — Deudas pendientes\n"
        "• /partidos — Próximos partidos\n"
        "• /asistencia — Confirmados\n"
        "• /posiciones — Tabla de posiciones\n\n"
        "<b>Admin:</b> /nuevo_jugador, /borrar_jugador, /actualizar_jugador, /nueva_deuda, /borrar_deuda"
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
        "• /borrar_deuda — Eliminar deudas\n\n"
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


# ── Conversation states ──────────────────────────────────────────
(
    NJ_NAME, NJ_NICKNAME, NJ_DNI, NJ_CONFIRMAR,
    BJ_NAME, BJ_CONFIRMAR,
    ND_NAME, ND_AMOUNT, ND_CONFIRMAR,
    BD_NAME, BD_CONFIRMAR,
    UJ_NAME, UJ_FIELD, UJ_VALUE, UJ_CONFIRMAR,
) = range(15)

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
    context.user_data["bj_name"] = update.message.text.strip()
    await update.message.reply_text(
        f"¿Eliminar a <b>{context.user_data['bj_name']}</b>?\n\n"
        f"✅ Escribí si para confirmar\n"
        f"❌ Cualquier otra cosa para cancelar"
    )
    return BJ_CONFIRMAR

async def bj_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text in ("si", "sí", "s"):
        name = context.user_data["bj_name"]
        result = players.delete_player(name)
        admin = context.user_data["admin_player"]
        if result.get("success"):
            logs.create_log(admin["id"], "delete_player", f"Eliminó al jugador {name}")
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
    context.user_data["nd_name"] = update.message.text.strip()
    await update.message.reply_text("💰 <b>Monto de la deuda:</b>\n(Ej: 5000)")
    return ND_AMOUNT

async def nd_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip().replace("$", "").replace(",", ""))
        context.user_data["nd_amount"] = amount
        await update.message.reply_text(
            f"<b>Resumen:</b>\n"
            f"👤 Jugador: {context.user_data['nd_name']}\n"
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
        result = debts.create_debt_by_player_name(
            context.user_data["nd_name"], context.user_data["nd_amount"]
        )
        admin = context.user_data["admin_player"]
        if result.get("success"):
            logs.create_log(admin["id"], "add_debt",
                f"Añadió deuda de ${context.user_data['nd_amount']:,.0f} a {context.user_data['nd_name']}")
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
    context.user_data["bd_name"] = update.message.text.strip()
    await update.message.reply_text(
        f"¿Borrar todas las deudas de <b>{context.user_data['bd_name']}</b>?\n\n"
        f"✅ Escribí si para confirmar\n"
        f"❌ Cualquier otra cosa para cancelar"
    )
    return BD_CONFIRMAR

async def bd_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text in ("si", "sí", "s"):
        result = debts.delete_debt_by_player_name(context.user_data["bd_name"])
        admin = context.user_data["admin_player"]
        if result.get("success"):
            logs.create_log(admin["id"], "delete_debt",
                f"Eliminó deudas de {context.user_data['bd_name']}")
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
    result = players.get_player(name)
    if not result.get("data"):
        await update.message.reply_text(f"❌ No encontré a '{name}'.")
        return ConversationHandler.END
    context.user_data["uj_player"] = result["data"]
    context.user_data["uj_name"] = name
    msg = (
        f"<b>Jugador:</b> {name}\n\n"
        f"<b>¿Qué campo querés actualizar?</b>\n\n"
    )
    for k, (field, label) in EDITABLE_FIELDS.items():
        msg += f"`{k}` → {label}\n"
    msg += "\nRespondé con el número o nombre del campo:"
    await update.message.reply_text(msg)
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


# ── ConversationHandler ──────────────────────────────────────────

conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("nuevo_jugador", nj_start),
        CommandHandler("borrar_jugador", bj_start),
        CommandHandler("nueva_deuda", nd_start),
        CommandHandler("borrar_deuda", bd_start),
        CommandHandler("actualizar_jugador", uj_start),
    ],
    states={
        NJ_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, nj_name)],
        NJ_NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, nj_nickname)],
        NJ_DNI: [MessageHandler(filters.TEXT & ~filters.COMMAND, nj_dni)],
        NJ_CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, nj_confirmar)],
        BJ_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bj_name)],
        BJ_CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, bj_confirmar)],
        ND_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, nd_name)],
        ND_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, nd_amount)],
        ND_CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, nd_confirmar)],
        BD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bd_name)],
        BD_CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, bd_confirmar)],
        UJ_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, uj_name)],
        UJ_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, uj_field)],
        UJ_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, uj_value)],
        UJ_CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, uj_confirmar)],
    },
    fallbacks=[CommandHandler("cancelar", cancelar)],
    name="admin_conversations",
    persistent=False,
)


async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Usá `/start` para ver los comandos disponibles."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = str(user.id)
    text = update.message.text.strip()

    player = find_player_by_telegram_id(telegram_id)
    if not player:
        await update.message.reply_text(
            "No estás registrado en Footbot.\n"
            "Pedile al administrador que te vincule."
        )
        return

    logger.info(f"Mensaje de {player['name']} (TG:{telegram_id}): {text}")
    response = process_message(player, text)
    await update.message.reply_text(response)


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
