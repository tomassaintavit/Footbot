import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from database import supabase
from services import intelligence, debts, players, attendance, matches, positions, logs

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

_application: Application | None = None


def find_or_link_player(telegram_id: str, telegram_name: str = None):
    query = supabase.table("players").select("*").eq("telegram_id", telegram_id).execute()
    if query.data:
        return query.data[0]

    if telegram_name:
        query = supabase.table("players").select("*").ilike("name", telegram_name).execute()
        if query.data:
            player = query.data[0]
            supabase.table("players").update({"telegram_id": telegram_id}).eq("id", player["id"]).execute()
            logger.info(f"Jugador '{player['name']}' vinculado con Telegram ID {telegram_id}")
            return player

    return None


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
            "🤖 **¡Soy Footbot! Aquí tienes lo que puedo hacer por el equipo:**\n\n"
            "⚽ **Partidos**\n"
            "• *¿Cuándo jugamos?* → Próximo partido\n"
            "• *Tabla de posiciones* → Cómo vamos en el torneo\n\n"
            "📝 **Asistencia**\n"
            "• *¿Quiénes van?* → Confirmados para el próximo partido\n"
            "• *Subir lista* → Pega la lista de WhatsApp y la proceso\n\n"
            "💸 **Deudas**\n"
            "• *¿Quién debe plata?* → Deudores y montos\n\n"
            "👤 **Jugadores**\n"
            "• *Ver lista* → Todos los registrados\n"
            "• *Información de [Nombre]* → Goles, tarjetas, suspensión\n\n"
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
        f"⚽ ¡Hola {user.first_name}! Soy **Footbot**, tu asistente del equipo.\n\n"
        "Escribime con lenguaje natural y te entiendo.\n"
        "Ej: *¿Cuándo jugamos?*, *¿Quiénes van?*, *¿Cuánto debe Tomás?*\n\n"
        "Usá /help para ver todo lo que puedo hacer."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    player = find_or_link_player(telegram_id)
    if player:
        result = process_message(player, "ayuda")
        await update.message.reply_text(result)
    else:
        await update.message.reply_text(
            "No estás registrado en Footbot. Pídele a un administrador que te registre."
        )


async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    name = " ".join(context.args) if context.args else ""

    if not name:
        await update.message.reply_text(
            "Usá `/link Tu Nombre` para vincular tu cuenta de Telegram con tu perfil de Footbot."
        )
        return

    query = supabase.table("players").select("*").ilike("name", name).execute()
    if not query.data:
        await update.message.reply_text(f"No encontré ningún jugador con el nombre '{name}'.")
        return

    player = query.data[0]
    supabase.table("players").update({"telegram_id": telegram_id}).eq("id", player["id"]).execute()
    logger.info(f"Jugador '{player['name']}' vinculado manualmente con Telegram ID {telegram_id}")
    await update.message.reply_text(
        f"✅ ¡Listo! Vinculé tu Telegram con **{player['name']}**.\n"
        f"{'🔑 Tenés permisos de administrador.' if player.get('is_admin') else ''}"
    )


async def jugadores_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    player = find_or_link_player(telegram_id)
    if not player:
        await update.message.reply_text("Primero vinculá tu cuenta con /link Tu Nombre")
        return
    result = players.get_players_list()["message"]
    await update.message.reply_text(result)


async def deudas_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    player = find_or_link_player(telegram_id)
    if not player:
        await update.message.reply_text("Primero vinculá tu cuenta con /link Tu Nombre")
        return
    result = debts.get_debts_list()["message"]
    await update.message.reply_text(result)


async def partidos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    player = find_or_link_player(telegram_id)
    if not player:
        await update.message.reply_text("Primero vinculá tu cuenta con /link Tu Nombre")
        return
    result = matches.get_next_matches()["message"]
    await update.message.reply_text(result)


async def asistencia_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    player = find_or_link_player(telegram_id)
    if not player:
        await update.message.reply_text("Primero vinculá tu cuenta con /link Tu Nombre")
        return
    result = attendance.get_match_attendance()["message"]
    await update.message.reply_text(result)


async def posiciones_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    player = find_or_link_player(telegram_id)
    if not player:
        await update.message.reply_text("Primero vinculá tu cuenta con /link Tu Nombre")
        return
    result = positions.get_positions_table()["message"]
    await update.message.reply_text(result)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = str(user.id)
    text = update.message.text.strip()

    player = find_or_link_player(telegram_id, user.first_name)
    if not player:
        await update.message.reply_text(
            f"Hola {user.first_name}! 👋\n\n"
            "No encontré tu cuenta en Footbot. Para registrarte:\n\n"
            "1️⃣ Un administrador debe darte de alta desde la web\n"
            "2️⃣ Después envía cualquier mensaje acá para vincular tu cuenta"
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

    _application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    _application.add_handler(CommandHandler("start", start))
    _application.add_handler(CommandHandler("help", help_command))
    _application.add_handler(CommandHandler("link", link_command))
    _application.add_handler(CommandHandler("jugadores", jugadores_command))
    _application.add_handler(CommandHandler("deudas", deudas_command))
    _application.add_handler(CommandHandler("partidos", partidos_command))
    _application.add_handler(CommandHandler("asistencia", asistencia_command))
    _application.add_handler(CommandHandler("posiciones", posiciones_command))
    _application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await _application.initialize()
    await _application.start()
    await _application.updater.start_polling()
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
